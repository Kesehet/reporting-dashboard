"""CSV encryption scope and historical-key discovery regressions.

Exercise the actual post_process function without importing the unrelated
reporting application's SQL, pandas and remote-service dependencies.
"""
import ast
import base64
import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_crypto_rotation import FakeConnection, FakeCursor
from helper import encryption_helper as crypto


def csv_encrypter():
    source = Path(__file__).resolve().parents[1] / "api-server" / "post_process.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "encrypt_all_pii_columns")
    namespace = {"is_encrypted": crypto.is_encrypted}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
    return namespace["encrypt_all_pii_columns"]


class ScopedCursor(FakeCursor):
    def execute(self, sql, params=()):
        if " WHERE eCATrackingCode IN (" in sql:
            self.connection.statements.append(sql)
            self.rowcount = 0
            table = "Transactions" if "[Transactions]" in sql else "Properties"
            wanted = set(params)
            self.results = [(key, *values)
                            for key, values in self.connection.working[table].items()
                            if self.connection.tracking[table].get(key) in wanted]
            return self
        return super().execute(sql, params)


class ScopedConnection(FakeConnection):
    def __init__(self, db, tracking, fail_pk=None):
        super().__init__(db, fail_pk)
        self.tracking = tracking
        self.autocommit = False

    def cursor(self):
        return ScopedCursor(self)


class ScopedSQL:
    def __init__(self, db, tracking, fail_pk=None):
        self.connection = ScopedConnection(db, tracking, fail_pk)


class CsvEncryptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = mock.patch.dict(os.environ, {
            "CRYPTO_STATE_DIR": self.temp.name,
            "ENCRYPTION_KEY": "",
            "CRYPTO_LEGACY_MODE": "",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.cwd = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.cwd)
        self.encrypt = csv_encrypter()

    def test_only_imported_tracking_codes_are_selected(self):
        crypto.key_rotation()
        historical = base64.b64encode(b"Z" * 16).decode("ascii")
        before = {
            "Transactions": {
                1: ["New customer", "987654321"],
                2: [historical, "Historical customer"],
                3: ["Unaffected plaintext", "ignored"],
            },
            "Properties": {
                "P-new": ["New property", "999"],
                "P-old": [historical, "old property"],
            },
        }
        db = copy.deepcopy(before)
        tracking = {
            "Transactions": {1: "NEW", 2: "NEW", 3: "OLD"},
            "Properties": {"P-new": "NEW", "P-old": "OLD"},
        }
        sql = ScopedSQL(db, tracking)
        self.encrypt(sql, None, {"NEW"})
        self.assertTrue(db["Transactions"][1][0].startswith(("v2:", "v2f:")))
        self.assertEqual(crypto.decrypt_string(db["Transactions"][1][0]), "New customer")
        self.assertEqual(db["Transactions"][2][0], historical)
        self.assertEqual(db["Transactions"][3], before["Transactions"][3])
        self.assertEqual(db["Properties"]["P-old"], before["Properties"]["P-old"])
        self.assertNotEqual(db["Properties"]["P-new"], before["Properties"]["P-new"])
        selections = [q for q in sql.connection.statements if " WHERE eCATrackingCode IN (" in q]
        self.assertEqual(len(selections), 2)
        self.assertTrue(all("WHERE eCATrackingCode IN (?)" in q for q in selections))
        self.assertEqual(sql.connection.commits, 1)

    def test_empty_import_never_scans_or_commits(self):
        sql = ScopedSQL({"Transactions": {}, "Properties": {}},
                        {"Transactions": {}, "Properties": {}})
        self.encrypt(sql, None, set())
        self.assertEqual(sql.connection.statements, [])
        self.assertEqual(sql.connection.commits, 0)

    def test_historical_ciphertext_does_not_require_a_new_key_or_legacy_probe(self):
        historical = base64.b64encode(b"X" * 16).decode("ascii")
        db = {"Transactions": {1: [historical, historical]}, "Properties": {}}
        sql = ScopedSQL(db, {"Transactions": {1: "TOUCHED"}, "Properties": {}})
        self.encrypt(sql, None, {"TOUCHED"})
        self.assertEqual(db["Transactions"][1], [historical, historical])
        self.assertEqual(sql.connection.commits, 1)
        self.assertEqual(crypto.get_keyring()["current_id"], None)

    def test_failed_row_rolls_back_and_does_not_leave_value_files(self):
        crypto.key_rotation()
        db = {"Transactions": {
            1: ["a new very long customer name that cannot fit within fifty chars", "111"],
            2: ["Second name", "222"],
        }, "Properties": {}}
        before = copy.deepcopy(db)
        sql = ScopedSQL(db, {"Transactions": {1: "NEW", 2: "NEW"}, "Properties": {}},
                        fail_pk=2)
        with self.assertRaises(RuntimeError):
            self.encrypt(sql, None, {"NEW"})
        self.assertEqual(db, before)
        self.assertEqual(sql.connection.commits, 0)
        self.assertEqual(sql.connection.rollbacks, 1)
        value_dir = Path(self.temp.name) / "values"
        self.assertEqual(list(value_dir.glob("*.enc")) if value_dir.exists() else [], [])


class LegacyDiscoveryTests(unittest.TestCase):
    def test_configured_legacy_files_survive_cwd_changes(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            secrets_dir = home / "historical"
            secrets_dir.mkdir()
            env_path = secrets_dir / ".env"
            old_raw = b"L" * 32
            file_raw = b"K" * 32
            env_path.write_text("ENCRYPTION_KEY=raw:" + old_raw.decode() + "\n")
            (secrets_dir / "old_enc.key").write_text(base64.b64encode(file_raw).decode())
            other = home / "other"
            other.mkdir()
            original_cwd = Path.cwd()
            with mock.patch.dict(os.environ, {
                "CRYPTO_STATE_DIR": str(home / "crypto-state"),
                "ENCRYPTION_KEY": "",
                "CRYPTO_LEGACY_ENV_FILE": str(env_path),
                "CRYPTO_LEGACY_KEY_DIR": str(secrets_dir),
            }):
                try:
                    os.chdir(other)
                    ring = crypto.get_keyring()
                finally:
                    os.chdir(original_cwd)
            ids = {item["id"] for item in ring["keys"]}
            self.assertIn(crypto._key_id(old_raw), ids)
            self.assertIn(crypto._key_id(file_raw), ids)
            self.assertEqual(len(ids), 2)

    def test_legacy_path_configuration_requires_absolute_paths(self):
        with mock.patch.dict(os.environ, {"CRYPTO_LEGACY_KEY_DIR": "relative"}):
            with self.assertRaisesRegex(ValueError, "must be absolute"):
                crypto._legacy_key_dirs()
        with mock.patch.dict(os.environ, {"CRYPTO_LEGACY_ENV_FILE": "relative"}):
            with self.assertRaisesRegex(ValueError, "must be absolute"):
                crypto._legacy_env_files()


if __name__ == "__main__":
    unittest.main()
