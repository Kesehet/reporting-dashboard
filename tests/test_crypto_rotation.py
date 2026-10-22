"""Crypto migration regressions using real PyCryptodome and an in-memory SQL mock.

No credentials, SQL Server, or side effects outside a temporary private directory.
"""
import base64
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from Crypto.Cipher import AES

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from helper import encryption_helper as crypto
from helper import crypto_rotation as rot


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.results = []
        self.rowcount = 0

    def execute(self, sql, params=()):
        self.connection.statements.append(sql)
        self.rowcount = 0
        if "CHARACTER_MAXIMUM_LENGTH" in sql:
            self.results = [("PrimaryName", 50), ("PrimarySSN", 100)]
        elif "SELECT TOP" in sql:
            table = "Transactions" if "[Transactions]" in sql else "Properties"
            after = params[1]
            self.results = sorted(
                [(key, *values) for key, values in self.connection.working[table].items()
                 if key > after], key=lambda row: row[0]
            )[:params[0]]
        elif "UPDATE " in sql:
            table = "Transactions" if "[Transactions]" in sql else "Properties"
            after = list(params[:2])
            identity = params[2]
            before = [params[3], params[5]]
            if identity == self.connection.fail_pk:
                raise RuntimeError("Simulated SQL write failure")
            row = self.connection.working[table].get(identity)
            if row == before:
                self.connection.working[table][identity] = after
                self.rowcount = 1
            self.results = []
        else:
            raise AssertionError("Unexpected SQL: " + sql)
        return self

    def fetchall(self):
        return list(self.results)


class FakeConnection:
    def __init__(self, db, fail_pk=None):
        self.db = db
        self.working = copy.deepcopy(db)
        self.fail_pk = fail_pk
        self.statements = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.db.clear()
        self.db.update(copy.deepcopy(self.working))
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1
        self.working = copy.deepcopy(self.db)


class FakeSQL:
    def __init__(self, db, fail_pk=None):
        self.connection = FakeConnection(db, fail_pk)

    def disconnect(self):
        pass


class CryptoRotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = mock.patch.dict(os.environ, {
            "CRYPTO_STATE_DIR": self.tmp.name,
            "CRYPTO_LEGACY_MODE": "AES_ECB_PKCS7",
            "CRYPTO_LEGACY_SAMPLE_CIPHERTEXT": "",
            "CRYPTO_LEGACY_SAMPLE_SHA256": "",
            "ENCRYPTION_KEY": "",
            "CRYPTO_LEGACY_ENV_FILE": "",
            "CRYPTO_LEGACY_KEY_DIR": "",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.legacy = mock.patch.object(crypto, "_legacy_env", return_value=None)
        self.legacy.start()
        self.addCleanup(self.legacy.stop)
        # Synthetic fixtures must never import host or checkout secrets.
        for name, source in (
            ("_legacy_env_files", lambda: [
                Path(os.environ.get("CRYPTO_LEGACY_ENV_FILE") or Path(self.tmp.name) / ".env")
            ]),
            ("_legacy_key_dirs", lambda: [
                Path(os.environ.get("CRYPTO_LEGACY_KEY_DIR") or self.tmp.name)
            ]),
        ):
            isolation = mock.patch.object(crypto, name, side_effect=source)
            isolation.start()
            self.addCleanup(isolation.stop)
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self.cwd)

    def test_no_secret_auto_created_on_import_or_status(self):
        self.assertIsNone(crypto.get_keyring()["current_id"])
        self.assertEqual(crypto.key_metadata()["keys"], [])
        self.assertFalse((Path(self.tmp.name) / "enc.key").exists())

    def test_atomic_write_retries_transient_windows_sharing_violations(self):
        output = Path(self.tmp.name) / "migration-status.json"
        real_replace = os.replace
        calls = []
        def sharing_violation(src, dst):
            calls.append(dst)
            if len(calls) <= 2:
                raise PermissionError(13, "synthetic transient sharing violation")
            return real_replace(src, dst)
        with mock.patch.object(crypto.os, "replace", side_effect=sharing_violation):
            with mock.patch.object(crypto.time, "sleep") as sleep:
                crypto._atomic_write(output, '{"state": "completed"}')
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(output.read_text(), '{"state": "completed"}')

    def test_atomic_write_keeps_existing_state_on_persistent_sharing_violation(self):
        output = Path(self.tmp.name) / "migration-status.json"
        output.write_text('{"state": "stable"}')
        with mock.patch.object(crypto.os, "replace",
                               side_effect=PermissionError(13, "persistent sharing violation")):
            with mock.patch.object(crypto.time, "sleep"):
                with self.assertRaises(PermissionError):
                    crypto._atomic_write(output, '{"state": "new"}')
        self.assertEqual(output.read_text(), '{"state": "stable"}')

    def test_status_reader_retries_transient_windows_sharing_violation(self):
        class FlakyState:
            def __init__(self):
                self.attempts = 0

            def is_file(self):
                return True

            def read_text(self, encoding):
                self.attempts += 1
                if self.attempts <= 2:
                    raise PermissionError(13, "synthetic transient Windows sharing")
                return '{"state": "completed"}'

        state = FlakyState()
        with mock.patch.object(rot, "_state_file", return_value=state):
            with mock.patch.object(rot.time, "sleep") as sleep:
                self.assertEqual(rot._status()["state"], "completed")
        self.assertEqual(state.attempts, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_status_reader_does_not_hide_permanent_permission_errors(self):
        class LockedState:
            def is_file(self):
                return True

            def read_text(self, encoding):
                raise PermissionError(13, "persistent Windows sharing")

        with mock.patch.object(rot, "_state_file", return_value=LockedState()):
            with mock.patch.object(rot.time, "sleep"):
                with self.assertRaises(PermissionError):
                    rot._status()

    def test_gcm_roundtrip_unicode_empty_and_nonce_uniqueness(self):
        crypto.key_rotation()
        for text in ("", "hello", "عربي اردو", "José \U0001f680", "x" * 750):
            one = crypto.encrypt_string(text)
            two = crypto.encrypt_string(text)
            self.assertNotEqual(one, two)
            self.assertTrue(one.startswith("v2:"))
            self.assertEqual(crypto.decrypt_string(one), text)

    def test_gcm_authentication_rejects_tampering(self):
        crypto.key_rotation()
        envelope = crypto.encrypt_string("confidential")
        prefix, kid, encoded = envelope.split(":", 2)
        bits = bytearray(base64.b64decode(encoded))
        bits[14] ^= 0x40  # tag bit flip; never return unauthenticated plaintext
        forged = ":".join((prefix, kid, base64.b64encode(bits).decode()))
        with self.assertRaises(ValueError):
            crypto.decrypt_string(forged)

    def test_every_historical_gcm_key_remains_readable(self):
        ids = []
        values = []
        for n in range(5):
            ids.append(crypto.key_rotation())
            values.append(crypto.encrypt_string("record " + str(n)))
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(len(crypto.key_metadata()["keys"]), 5)
        for n, value in enumerate(values):
            self.assertEqual(crypto.decrypt_string(value), "record " + str(n))
        self.assertEqual(crypto.key_metadata()["current_id"], ids[-1])

    def test_missing_key_never_falls_back_to_new_key(self):
        crypto.key_rotation()
        value = crypto.encrypt_string("original")
        ring = crypto.get_keyring()
        ring["keys"] = []
        crypto._save_ring(ring)
        with self.assertRaises(ValueError):
            crypto.decrypt_string(value)

    def test_legacy_ecb_only_with_explicit_mode_and_known_vector(self):
        raw = b"1" * 32
        import_path = Path(self.tmp.name) / "import"
        import_path.mkdir()
        (import_path / "historic.key").write_text(base64.b64encode(raw).decode())
        plaintext = "Known fixed ECB vector"
        padding = 16 - len(plaintext.encode()) % 16
        ciphertext = base64.b64encode(AES.new(raw, AES.MODE_ECB).encrypt(
            plaintext.encode() + bytes([padding] * padding))).decode()
        os.environ["CRYPTO_LEGACY_SAMPLE_CIPHERTEXT"] = ciphertext
        os.environ["CRYPTO_LEGACY_SAMPLE_SHA256"] = hashlib.sha256(plaintext.encode()).hexdigest()
        self.assertTrue(crypto.verify_legacy_probe())
        self.assertEqual(crypto.decrypt_string(ciphertext), plaintext)
        # The legacy ECB reader works by default, including on unmodified
        # production installations which only have ENCRYPTION_KEY in .env.
        os.environ["CRYPTO_LEGACY_MODE"] = ""
        self.assertEqual(crypto.decrypt_string(ciphertext), plaintext)
        os.environ["CRYPTO_LEGACY_MODE"] = "unsupported"
        with self.assertRaises(ValueError):
            crypto.decrypt_string(ciphertext)

    def test_raw_32_character_env_key_is_not_misread_as_base64(self):
        raw = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        self.assertEqual(len(raw), 32)
        with tempfile.TemporaryDirectory() as keys:
            env_file = Path(keys) / ".env"
            env_file.write_text("ENCRYPTION_KEY=" + raw.decode("ascii") + "\n")
            with mock.patch.dict(os.environ, {
                "ENCRYPTION_KEY": "",
                "CRYPTO_LEGACY_ENV_FILE": str(env_file),
                "CRYPTO_LEGACY_MODE": "",
            }):
                plaintext = "An original ECB value"
                pad = 16 - len(plaintext.encode("utf-8")) % 16
                data = plaintext.encode("utf-8") + bytes([pad] * pad)
                value = base64.b64encode(AES.new(raw, AES.MODE_ECB).encrypt(data)).decode()
                ring = crypto.get_keyring()
                self.assertIn(crypto._key_id(raw), {key["id"] for key in ring["keys"]})
                self.assertEqual(crypto.decrypt_string(value), plaintext)

    def test_unknown_base64_blocks_not_treated_as_plaintext(self):
        self.assertTrue(crypto.is_encrypted(base64.b64encode(b"Z" * 16).decode()))
        self.assertFalse(crypto.is_encrypted("Alice Smith"))

    def test_external_ciphertext_fits_fixed_column_and_detects_swaps(self):
        crypto.key_rotation()
        a = crypto.encrypt_string("a long customer name which will overflow the varchar field", max_length=50)
        b = crypto.encrypt_string("a completely different long customer name", max_length=50)
        self.assertTrue(a.startswith("v2f:"))
        self.assertLessEqual(len(a), 50)
        self.assertIn("customer", crypto.decrypt_string(a))
        self.assertEqual(len(list((Path(self.tmp.name) / "values").glob("*.enc"))), 2)
        apath = Path(self.tmp.name) / "values" / (a[4:] + ".enc")
        bpath = Path(self.tmp.name) / "values" / (b[4:] + ".enc")
        apath.write_text(bpath.read_text())
        with self.assertRaises(ValueError):
            crypto.decrypt_string(a)
        with self.assertRaises(ValueError):
            crypto.encrypt_string("ABC", max_length=20)

    def test_preflight_is_read_only_even_on_overflow(self):
        crypto.key_rotation()
        previous = crypto.encrypt_string("customer named long something")
        crypto.key_rotation()
        db = {"Transactions": {1: [previous, None]}, "Properties": {}}
        sqls = []
        def factory():
            sql = FakeSQL(db)
            sqls.append(sql)
            return sql
        with mock.patch.object(rot, "_connection", side_effect=factory):
            report = rot.inspect_database()
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["values_to_rotate"], 1)
        self.assertEqual(sqls[0].connection.commits, 0)
        self.assertEqual(db["Transactions"][1][0], previous)
        self.assertEqual(list((Path(self.tmp.name) / "values").glob("*.enc")) if
                         (Path(self.tmp.name) / "values").exists() else [], [])
        self.assertTrue(all("ALTER TABLE" not in query and "CREATE TABLE" not in query
                            for query in sqls[0].connection.statements))

    def test_migration_and_conditional_rollback_preserve_exact_originals(self):
        crypto.key_rotation()
        previous = crypto.encrypt_string("original customer long name")
        crypto.key_rotation()
        db = {"Transactions": {1: [previous, None]}, "Properties": {"X": [None, previous]}}
        connections = []
        def factory():
            sql = FakeSQL(db)
            connections.append(sql)
            return sql
        with mock.patch.object(rot, "_connection", side_effect=factory):
            rot._migrate("a" * 32)
            state = rot._status()
            self.assertEqual(state["state"], "completed", state)
            self.assertEqual(state["updated"], 2)
            self.assertNotEqual(db["Transactions"][1][0], previous)
            self.assertEqual(crypto.decrypt_string(db["Transactions"][1][0]), "original customer long name")
            self.assertEqual(crypto.decrypt_string(db["Properties"]["X"][1]), "original customer long name")
            rot._rollback("a" * 32)
        self.assertEqual(rot._status()["state"], "rolled_back")
        self.assertEqual(db["Transactions"][1][0], previous)
        self.assertEqual(db["Properties"]["X"][1], previous)
        self.assertTrue((Path(self.tmp.name) / "backups" / ("a" * 32 + ".jsonl")).exists())
        self.assertTrue(all("DROP " not in q.upper() and "ALTER " not in q.upper()
                            for c in connections for q in c.connection.statements))

    def test_snapshot_digest_matches_exact_disk_bytes(self):
        crypto.key_rotation()
        original = crypto.encrypt_string("before")
        crypto.key_rotation()
        db = {"Transactions": {1: [original, None]}, "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            rot._migrate("f" * 32)
        status = rot._status()
        self.assertEqual(status["state"], "completed")
        raw = (Path(self.tmp.name) / "backups" / ("f" * 32 + ".jsonl")).read_bytes()
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), status["backup_sha256"])

    def test_older_windows_crlf_snapshot_can_be_restored_safely(self):
        crypto.key_rotation()
        original = crypto.encrypt_string("before")
        crypto.key_rotation()
        db = {"Transactions": {1: [original, None]}, "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            rot._migrate("9" * 32)
            path = Path(self.tmp.name) / "backups" / ("9" * 32 + ".jsonl")
            original_bytes = path.read_bytes()
            self.assertNotIn(b"\r\n", original_bytes)
            path.write_bytes(original_bytes.replace(b"\n", b"\r\n"))
            rot._rollback("9" * 32)
        self.assertEqual(db["Transactions"][1][0], original)
        self.assertEqual(rot._status()["state"], "rolled_back")

    def test_sql_failure_rolls_back_all_prior_updates(self):
        crypto.key_rotation()
        previous = crypto.encrypt_string("before")
        crypto.key_rotation()
        db = {"Transactions": {1: [previous, None], 2: [previous, None]}, "Properties": {}}
        seen = []
        def factory():
            sql = FakeSQL(db, fail_pk=2)
            seen.append(sql)
            return sql
        with mock.patch.object(rot, "_connection", side_effect=factory):
            rot._migrate("b" * 32)
        self.assertEqual(rot._status()["state"], "failed")
        self.assertEqual(db["Transactions"][1][0], previous)
        self.assertEqual(db["Transactions"][2][0], previous)
        self.assertEqual(sum(s.connection.commits for s in seen), 0)
        self.assertGreaterEqual(sum(s.connection.rollbacks for s in seen), 2)

    def test_no_valid_legacy_key_blocks_entire_preflight(self):
        crypto.key_rotation()
        db = {"Transactions": {1: [base64.b64encode(b"A" * 16).decode(), None]},
              "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            result = rot.inspect_database()
        self.assertFalse(result["ready"])
        self.assertEqual(result["failures"], 1)

    def test_status_without_operator_token_exposes_only_key_metadata(self):
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(rot.crypto_api)
        crypto.key_rotation()
        client = app.test_client()
        result = client.get("/crypto/status")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["Cache-Control"], "no-store, private")
        self.assertNotIn('"material"', result.data.decode())
        self.assertTrue(result.json["keyring"]["current_id"])

    def test_preflight_rejects_tampered_ciphertext_and_preserves_database(self):
        crypto.key_rotation()
        value = crypto.encrypt_string("original")
        broken = value[:-2] + ("A" if value[-2] != "A" else "B") + value[-1]
        db = {"Transactions": {1: [broken, None]}, "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            result = rot.inspect_database()
        self.assertFalse(result["ready"])
        self.assertEqual(result["failures"], 1)
        self.assertEqual(db["Transactions"][1][0], broken)

    def test_preflight_rejects_missing_external_file(self):
        crypto.key_rotation()
        ref = crypto.encrypt_string("A long confidential customer name", max_length=50)
        (Path(self.tmp.name) / "values" / (ref[4:] + ".enc")).unlink()
        db = {"Transactions": {1: [ref, None]}, "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            report = rot.inspect_database()
        self.assertFalse(report["ready"])
        self.assertEqual(report["failures"], 1)

    def test_recovery_rejects_changed_row_without_overwriting_it(self):
        crypto.key_rotation()
        old = crypto.encrypt_string("before")
        crypto.key_rotation()
        db = {"Transactions": {1: [old, None]}, "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            rot._migrate("c" * 32)
            self.assertEqual(rot._status()["state"], "completed")
            newer = crypto.encrypt_string("newer value")
            db["Transactions"][1][0] = newer
            with self.assertRaises(RuntimeError):
                rot._rollback("c" * 32)
        self.assertEqual(db["Transactions"][1][0], newer)

    def test_corrupt_recovery_snapshot_never_updates_database(self):
        crypto.key_rotation()
        old = crypto.encrypt_string("before")
        crypto.key_rotation()
        db = {"Transactions": {1: [old, None]}, "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            rot._migrate("d" * 32)
            current = db["Transactions"][1][0]
            backup = Path(self.tmp.name) / "backups" / ("d" * 32 + ".jsonl")
            backup.write_text("corrupted snapshot")
            with self.assertRaises(ValueError):
                rot._rollback("d" * 32)
        self.assertEqual(db["Transactions"][1][0], current)

    def test_backward_compatible_two_part_gcm_from_merged_decryption_tab(self):
        legacy_key = bytes(range(32))
        key_dir = Path(self.tmp.name) / "import"
        key_dir.mkdir()
        (key_dir / "previous-dashboard.key").write_text(base64.b64encode(legacy_key).decode())
        cipher = AES.new(legacy_key, AES.MODE_GCM, nonce=b"N" * 12)
        encoded, tag = cipher.encrypt_and_digest("old dashboard text".encode())
        prior = "v2:" + base64.b64encode(cipher.nonce + tag + encoded).decode()
        crypto.key_rotation()
        self.assertEqual(crypto.decrypt_string(prior), "old dashboard text")
        self.assertIsNone(crypto.encrypted_key_id(prior))
        db = {"Transactions": {1: [prior, None]}, "Properties": {}}
        with mock.patch.object(rot, "_connection", side_effect=lambda: FakeSQL(db)):
            self.assertTrue(rot.inspect_database()["ready"])
            rot._migrate("e" * 32)
        self.assertEqual(rot._status()["state"], "completed")
        self.assertNotEqual(db["Transactions"][1][0], prior)
        self.assertEqual(crypto.decrypt_string(db["Transactions"][1][0]), "old dashboard text")

    def test_keyring_history_survives_multiple_rotations(self):
        for _ in range(4):
            crypto.key_rotation()
        snapshots = list((Path(self.tmp.name) / "keyring-history").glob("*.json"))
        self.assertGreaterEqual(len(snapshots), 3)
        self.assertEqual(len(crypto.get_keyring()["keys"]), 4)


if __name__ == "__main__":
    unittest.main()
