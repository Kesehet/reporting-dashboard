"""End-to-end crypto API flows with real AES, async worker, SQL-like transactions.

Only a synthetic in-memory SQL fixture is used. No network, real keys, or PII.
All assertions evaluate API responses, durable filesystem state and SQL rollback.
"""
import base64
import copy
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from Crypto.Cipher import AES
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from helper import encryption_helper as crypto
from helper import crypto_rotation as rot
from test_crypto_rotation import FakeSQL, FakeConnection

ADMIN = {"X-Crypto-Admin-Token": "A" * 36}


def ecb(raw, value):
    raw_value = value.encode("utf-8")
    count = AES.block_size - len(raw_value) % AES.block_size
    return base64.b64encode(AES.new(raw, AES.MODE_ECB).encrypt(
        raw_value + bytes([count] * count))).decode("ascii")


class EncryptionHttpFlow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.patcher = mock.patch.dict(os.environ, {
            "CRYPTO_STATE_DIR": self.temp.name,
            "CRYPTO_LEGACY_MODE": "AES_ECB_PKCS7",
            "CRYPTO_ADMIN_TOKEN": ADMIN["X-Crypto-Admin-Token"],
            "ENCRYPTION_KEY": "",
            "CRYPTO_LEGACY_SAMPLE_CIPHERTEXT": "",
            "CRYPTO_LEGACY_SAMPLE_SHA256": "",
        })
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.cwd = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.cwd)
        self.raw = b"L" * 32
        archive = Path(self.temp.name) / "import"
        archive.mkdir()
        (archive / "prior-year.key").write_text(base64.b64encode(self.raw).decode())
        sample = "safe-known-non-personal-test"
        os.environ["CRYPTO_LEGACY_SAMPLE_CIPHERTEXT"] = ecb(self.raw, sample)
        os.environ["CRYPTO_LEGACY_SAMPLE_SHA256"] = hashlib.sha256(sample.encode()).hexdigest()
        self.before = {
            "Transactions": {
                1: [ecb(self.raw, "Alice"), ecb(self.raw, "000-00-0001")],
                2: [ecb(self.raw, "Bob"), ecb(self.raw, "000-00-0002")],
            },
            "Properties": {"P-01": [ecb(self.raw, "Carol"), ecb(self.raw, "000-00-0003")]},
        }
        self.db = copy.deepcopy(self.before)
        self.connections = []
        self.fail_pk = None
        def sql_factory():
            sql = FakeSQL(self.db, self.fail_pk)
            self.connections.append(sql)
            return sql
        self.mock_sql = mock.patch.object(rot, "_connection", side_effect=sql_factory)
        self.mock_sql.start()
        self.addCleanup(self.mock_sql.stop)
        app = Flask(__name__)
        app.testing = True
        app.register_blueprint(rot.crypto_api)
        self.client = app.test_client()
        self.addCleanup(self._clean_threads)

    def _clean_threads(self):
        # Tests never let worker threads escape a temporary directory.
        end = time.monotonic() + 8
        while (rot._active or (Path(self.temp.name) / "migration.lock").exists()) and time.monotonic() < end:
            time.sleep(0.01)

    def api(self, method, path, payload=None, *, authenticated=True):
        args = {"headers": ADMIN} if authenticated else {}
        if payload is not None:
            args["json"] = payload
        response = self.client.open("/crypto" + path, method=method, **args)
        data = response.get_json()
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertNotIn('"material"', response.get_data(as_text=True))
        return response.status_code, data

    def wait_for_state(self, run_id, states=("completed", "failed", "rolled_back", "restore_failed", "reconciliation_required")):
        end = time.monotonic() + 8
        while time.monotonic() < end:
            code, status = self.api("GET", "/status")
            self.assertEqual(code, 200)
            if status["job"].get("run_id") == run_id and status["job"]["state"] in states and not rot._active:
                return status["job"]
            time.sleep(0.02)
        self.fail("A simulated migration did not reach a terminal state")

    def activate(self):
        code, data = self.api("POST", "/keys/rotate", {"confirm": "CREATE_GCM_KEY"})
        self.assertEqual(code, 201, data)
        return data["key_id"]

    def start(self):
        code, data = self.api("POST", "/start", {"confirm": "MIGRATE_PII"})
        self.assertEqual(code, 202, data)
        self.assertEqual(len(data["run_id"]), 32)
        return data["run_id"]

    def assert_no_ddl(self):
        forbidden = ("CREATE TABLE", "ALTER TABLE", "DROP TABLE", "TRUNCATE TABLE",
                     "CREATE INDEX", "DROP INDEX")
        for connection in self.connections:
            for query in connection.connection.statements:
                for phrase in forbidden:
                    self.assertNotIn(phrase, query.upper())

    def test_entire_http_lifecycle_legacy_to_gcm_then_full_restoration(self):
        status, result = self.api("GET", "/status", authenticated=False)
        self.assertEqual(status, 403)
        self.assertNotIn("keyring", result)
        status, result = self.api("POST", "/start", {"confirm": "MIGRATE_PII"})
        self.assertEqual(status, 409)  # cannot migrate until active key exists
        status, result = self.api("POST", "/preflight", {})
        self.assertEqual(status, 200)
        self.assertFalse(result["ready"])
        key_id = self.activate()
        status, result = self.api("GET", "/status")
        self.assertEqual(result["keyring"]["current_id"], key_id)
        self.assertEqual(len(result["keyring"]["keys"]), 2)
        self.assertIn("AES_ECB_PKCS7", {k["algorithm"] for k in result["keyring"]["keys"]})

        status, data = self.api("POST", "/decrypt", {"value": self.before["Transactions"][1][0]})
        self.assertEqual(status, 200)
        self.assertEqual(data["plaintext"], "Alice")
        for endpoint, payload in (("/keys/rotate", {"confirm": "no"}),
                                  ("/start", {"confirm": "no"})):
            self.assertEqual(self.api("POST", endpoint, payload)[0], 409)
        status, report = self.api("POST", "/preflight", {})
        self.assertEqual(status, 200)
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["scanned"], 3)
        self.assertEqual(report["values_to_rotate"], 6)
        self.assertEqual(self.db, self.before, "preflight must never write to SQL")
        value_path = Path(self.temp.name) / "values"
        self.assertFalse(value_path.exists(), "preflight must not create overflow files")

        run_id = self.start()
        job = self.wait_for_state(run_id)
        self.assertEqual(job["state"], "completed", job)
        self.assertEqual(job["updated"], 3)
        self.assertEqual(job["processed"], 3)
        self.assertNotEqual(self.db, self.before)
        for table, rows in self.db.items():
            for row_id, (name, ssn) in rows.items():
                self.assertTrue(name.startswith("v2f:"), (table, row_id, name))
                self.assertTrue(ssn.startswith(("v2:", "v2f:")))
                self.assertEqual(crypto.decrypt_string(name),
                                 {"1": "Alice", "2": "Bob", "P-01": "Carol"}[str(row_id)])
        self.assertEqual(len(list(value_path.glob("*.enc"))), 6 if all(
            row[1].startswith("v2f:") for table in self.db.values() for row in table.values()) else 3)
        archive = Path(self.temp.name) / "backups" / (run_id + ".jsonl")
        self.assertTrue(archive.is_file())
        raw_snapshot = archive.read_text()
        self.assertNotIn("Alice", raw_snapshot)
        self.assertNotIn("000-00-0001", raw_snapshot)
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), job["backup_sha256"])
        self.assertEqual(len(archive.read_text().splitlines()), job["backup_rows"])
        self.assertEqual(self.api("POST", "/start", {"confirm": "wrong"})[0], 409)
        self.assertEqual(self.api("POST", "/rollback", {"run_id": run_id, "confirm": "wrong"})[0], 400)
        code, data = self.api("POST", "/rollback", {"run_id": run_id, "confirm": "RESTORE_ORIGINAL"})
        self.assertEqual(code, 202, data)
        restored = self.wait_for_state(run_id)
        self.assertEqual(restored["state"], "rolled_back", restored)
        self.assertEqual(self.db, self.before)
        self.assert_no_ddl()
        self.assertTrue(all(c.connection.autocommit is False if hasattr(c.connection, "autocommit") else True
                            for c in self.connections))

    def test_atomic_rollback_on_mid_transaction_injected_failure(self):
        self.activate()
        self.fail_pk = 2
        run_id = self.start()
        final = self.wait_for_state(run_id)
        self.assertEqual(final["state"], "failed", final)
        self.assertEqual(self.db, self.before)
        self.assertEqual(sum(c.connection.commits for c in self.connections), 0)
        self.assertGreater(sum(c.connection.rollbacks for c in self.connections), 0)
        self.assertEqual(list((Path(self.temp.name) / "values").glob("*.enc")), [])
        self.assert_no_ddl()

    def test_concurrent_endpoints_blocked_for_running_worker(self):
        self.activate()
        inside = threading.Event()
        release = threading.Event()
        original = rot._compare_update
        def slow_update(*args, **kwargs):
            inside.set()
            if not release.wait(timeout=6):
                raise RuntimeError("Simulated lock timeout")
            return original(*args, **kwargs)
        with mock.patch.object(rot, "_compare_update", side_effect=slow_update):
            try:
                run_id = self.start()
                self.assertTrue(inside.wait(timeout=4))
                self.assertEqual(self.api("POST", "/start", {"confirm": "MIGRATE_PII"})[0], 409)
                self.assertEqual(self.api("POST", "/keys/rotate", {"confirm": "CREATE_GCM_KEY"})[0], 409)
                self.assertEqual(self.api("POST", "/preflight", {})[0], 409)
                code, status = self.api("GET", "/status")
                self.assertEqual(code, 200)
                self.assertEqual(status["job"]["run_id"], run_id)
                self.assertIn(status["job"]["state"], ("running", "committing"))
            finally:
                release.set()
            self.assertEqual(self.wait_for_state(run_id)["state"], "completed")
        self.assert_no_ddl()

    def test_recovery_refuses_tampered_snapshot_and_preserves_sql(self):
        self.activate()
        run_id = self.start()
        self.assertEqual(self.wait_for_state(run_id)["state"], "completed")
        migrated = copy.deepcopy(self.db)
        backup_path = Path(self.temp.name) / "backups" / (run_id + ".jsonl")
        backup_path.write_text(backup_path.read_text() + "tampered\n")
        status, data = self.api("POST", "/rollback",
                                {"run_id": run_id, "confirm": "RESTORE_ORIGINAL"})
        self.assertEqual(status, 202)
        self.assertEqual(self.wait_for_state(run_id)["state"], "restore_failed")
        self.assertEqual(self.db, migrated)
        self.assert_no_ddl()

    def test_recovery_refuses_clobbering_newer_concurrent_data(self):
        self.activate()
        run_id = self.start()
        self.assertEqual(self.wait_for_state(run_id)["state"], "completed")
        self.db["Transactions"][2][0] = "manually-modified-after-rotation"
        changed = copy.deepcopy(self.db)
        code, result = self.api("POST", "/rollback", {"run_id": run_id, "confirm": "RESTORE_ORIGINAL"})
        self.assertEqual(code, 202, result)
        self.assertEqual(self.wait_for_state(run_id)["state"], "restore_failed")
        self.assertEqual(self.db, changed)
        self.assert_no_ddl()

    def test_sql_commit_timeout_is_reconciliation_not_false_rollback(self):
        self.activate()
        original = FakeConnection.commit
        def uncertain_commit(conn):
            original(conn)
            raise TimeoutError("Simulated lost SQL acknowledgment after commit")
        with mock.patch.object(FakeConnection, "commit", uncertain_commit):
            run_id = self.start()
            state = self.wait_for_state(run_id)
        self.assertEqual(state["state"], "reconciliation_required")
        self.assertNotEqual(self.db, self.before)
        self.assertEqual(self.api("POST", "/keys/rotate", {"confirm": "CREATE_GCM_KEY"})[0], 409)
        code, result = self.api("POST", "/rollback", {"run_id": run_id, "confirm": "RESTORE_ORIGINAL"})
        self.assertEqual(code, 202, result)
        self.assertEqual(self.wait_for_state(run_id)["state"], "rolled_back")
        self.assertEqual(self.db, self.before)

    def test_legacy_unknown_mode_blocks_all_sql_changes(self):
        self.activate()
        os.environ["CRYPTO_LEGACY_MODE"] = ""
        code, info = self.api("POST", "/preflight", {})
        self.assertEqual(code, 200)
        self.assertFalse(info["ready"])
        self.assertEqual(info["failures"], 6)
        self.assertEqual(self.db, self.before)
        self.assert_no_ddl()


if __name__ == "__main__":
    unittest.main()
