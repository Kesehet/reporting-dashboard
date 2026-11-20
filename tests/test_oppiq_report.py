import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))

from report_modules import oppiq


class FakeCursor:
    def __init__(self):
        self.query = None
        self.parameters = None
        self.closed = False
        self.batch_index = 0

    def execute(self, query, *parameters):
        self.query = query
        self.parameters = parameters
        return self

    def fetchall(self):
        return [
            (
                2, "Banker 1", "Manager 1", "Customer 1",
                10, 20, 30, "Product 1", datetime(2026, 11, 19, 10, 0), "Open",
            ),
        ]

    def fetchmany(self, size):
        if self.batch_index:
            return []
        self.batch_index += 1
        return [
            ("=HYPERLINK(1)", "Manager, A", "Customer 1", 10, 20, 30, "Product 1", datetime(2026, 11, 19, 10, 0), "Open"),
            ("Banker 2", "Manager 2", "Customer 2", 11, 21, 31, "Product 2", None, "UnAssigned"),
        ]

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.instance = FakeCursor()

    def cursor(self):
        return self.instance


class FakeSql:
    instances = []

    def __init__(self, kind=""):
        self.kind = kind
        self.connection = FakeConnection()
        self.closed = False
        self.instances.append(self)

    def connect(self):
        pass

    def disconnect(self):
        self.closed = True


class OppiqReportTests(unittest.TestCase):
    def setUp(self):
        FakeSql.instances.clear()
        app = Flask(__name__)
        app.register_blueprint(oppiq.oppiq_api)
        self.client = app.test_client()
        sql_patch = patch.object(oppiq, "SQLConn", FakeSql)
        sql_patch.start()
        self.addCleanup(sql_patch.stop)
        auth_patch = patch.object(oppiq, "request_identity", return_value={"role": "user"})
        self.auth_mock = auth_patch.start()
        self.addCleanup(auth_patch.stop)

    def test_query_retains_requested_joins_and_priority_threshold(self):
        self.assertIn("OppDeux.dbo.LEAD_STATUS", oppiq.PAGED_QUERY)
        self.assertIn("a.ACTIVEFLAG = 1", oppiq.PAGED_QUERY)
        self.assertIn("l.PRIORITYSCORE > 399", oppiq.PAGED_QUERY)
        self.assertIn("ls.LEADSTATUSID DESC", oppiq.PAGED_QUERY)
        self.assertIn("OFFSET ? ROWS FETCH NEXT ? ROWS ONLY", oppiq.PAGED_QUERY)

    def test_paged_response_uses_separate_connection(self):
        response = self.client.get("/oppiq-report?page=2&page_size=25")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["total"], 2)
        self.assertEqual(response.json["headers"], oppiq.HEADERS)
        self.assertEqual(response.json["rows"][0][0], "Banker 1")
        self.assertEqual(response.json["rows"][0][7], "2026-11-19 10:00:00")
        instance = FakeSql.instances[0]
        self.assertEqual(instance.kind, "OPPIQ")
        self.assertEqual(instance.connection.instance.parameters, (25, 25))
        self.assertTrue(instance.connection.instance.closed)
        self.assertTrue(instance.closed)

    def test_rejects_invalid_pagination(self):
        for query in ("page=0", "page=x", "page_size=500"):
            with self.subTest(query=query):
                response = self.client.get("/oppiq-report?" + query)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(FakeSql.instances, [])

    def test_export_returns_all_rows_with_safe_csv(self):
        response = self.client.get("/oppiq-report/export")
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertTrue(data.startswith("\ufeffBanker_Name,"))
        self.assertIn("'=HYPERLINK(1)", data)
        self.assertIn('"Manager, A"', data)
        self.assertIn("UnAssigned", data)
        self.assertEqual(len(data.splitlines()), 3)
        instance = FakeSql.instances[0]
        self.assertEqual(instance.connection.instance.query, oppiq.EXPORT_QUERY)
        self.assertTrue(instance.closed)

    def test_save_oppiq_csv_overwrites_one_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "OPPIQ Report" / "OPPIQ_Report.csv"
            output.parent.mkdir()
            output.write_text("previous data", encoding="utf-8")

            saved_path, row_count = oppiq.save_oppiq_csv(output)

            self.assertEqual(saved_path, output)
            self.assertEqual(row_count, 2)
            content = output.read_text(encoding="utf-8-sig")
            self.assertTrue(content.startswith("Banker_Name,"))
            self.assertIn("'=HYPERLINK(1)", content)
            self.assertNotIn("previous data", content)
            self.assertEqual([path.name for path in output.parent.iterdir()], ["OPPIQ_Report.csv"])
            self.assertTrue(FakeSql.instances[0].closed)

    def test_save_oppiq_csv_creates_missing_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "OPPIQ Report" / "OPPIQ_Report.csv"
            self.assertFalse(output.parent.exists())

            saved_path, row_count = oppiq.save_oppiq_csv(output)

            self.assertEqual(saved_path, output)
            self.assertEqual(row_count, 2)
            self.assertTrue(output.is_file())
            self.assertEqual([p.name for p in output.parent.iterdir()], ["OPPIQ_Report.csv"])

    def test_frozen_exe_dist_writes_at_project_root(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            executable = project / "exe_dist" / "prod_serve.exe"
            with patch.object(oppiq.sys, "frozen", True, create=True):
                with patch.object(oppiq.sys, "executable", str(executable)):
                    self.assertEqual(
                        oppiq.get_oppiq_csv_path(),
                        (project / "OPPIQ Report" / "OPPIQ_Report.csv").resolve(),
                    )

    def test_failed_csv_refresh_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "OPPIQ Report" / "OPPIQ_Report.csv"
            output.parent.mkdir()
            output.write_text("previous data", encoding="utf-8")

            with patch.object(oppiq, "_csv_cell", side_effect=ValueError("write failed")):
                with self.assertRaisesRegex(ValueError, "write failed"):
                    oppiq.save_oppiq_csv(output)

            self.assertEqual(output.read_text(encoding="utf-8"), "previous data")
            self.assertEqual([path.name for path in output.parent.iterdir()], ["OPPIQ_Report.csv"])
            self.assertTrue(FakeSql.instances[0].closed)

    def test_requires_login_for_both_routes(self):
        self.auth_mock.return_value = None
        self.assertEqual(self.client.get("/oppiq-report").status_code, 401)
        self.assertEqual(self.client.get("/oppiq-report/export").status_code, 401)
        self.assertEqual(FakeSql.instances, [])


if __name__ == "__main__":
    unittest.main()
