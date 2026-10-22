"""Offline regression tests: no Journey Manager traffic or SQL Server required."""
import ast
import json
import random
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import os
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api-server"))

import application
from jm_endpoints import jm_fluent_base_url, jm_workspaces_url, JM_RETENTION_DAYS


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self.rowcount = 0

    def execute(self, query, params):
        normalized = " ".join(query.split()).upper()
        if normalized.startswith("UPDATE "):
            raw, code = params
            if code in self.db.rows and self.db.rows[code] in (None, "", "null"):
                self.db.rows[code] = raw
                self.rowcount = 1
            else:
                self.rowcount = 0
        elif normalized.startswith("INSERT "):
            code, raw, checked_code = params
            assert code == checked_code
            if code not in self.db.rows:
                self.db.rows[code] = raw
                self.rowcount = 1
            else:
                self.rowcount = 0
        else:
            raise AssertionError("Unexpected SQL: " + query)
        return self

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows=None):
        self.rows = dict(rows or {})
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FakeSql:
    def __init__(self, rows=None):
        self.connection = FakeConnection(rows)


def jm_response(xml=None, status=200):
    payload = [{"formXml": xml}] if xml is not None else [{"formXml": ""}]
    return Mock(status_code=status, text=json.dumps(payload))


class EndpointTests(unittest.TestCase):
    def test_legacy_host_and_prefix(self):
        self.assertEqual(jm_fluent_base_url("https://jm.example"), "https://jm.example/secure/rest/fluentapi")
        self.assertEqual(jm_fluent_base_url("https://jm.example/"), "https://jm.example/secure/rest/fluentapi")
        self.assertEqual(jm_fluent_base_url("https://jm.example/proxy"),
                         "https://jm.example/proxy/secure/rest/fluentapi")

    def test_configured_paths_do_not_duplicate(self):
        for path in ("/secure/rest/fluentapi", "/manager/secure/rest/fluentapi"):
            with self.subTest(path=path):
                self.assertEqual(jm_fluent_base_url("https://jm.example" + path + "/"),
                                 "https://jm.example" + path)
        self.assertEqual(jm_fluent_base_url("https://jm.example/manager"),
                         "https://jm.example/manager/secure/rest/fluentapi")

    def test_workspace_variants(self):
        for value in ("https://jm.example", "https://jm.example/secure/rest/fluentapi",
                      "https://jm.example/manager/secure/rest/fluentapi"):
            self.assertEqual(jm_workspaces_url(value), "https://jm.example/workspaces")

    def test_invalid_configuration_does_not_make_request(self):
        for value in ("", "/secure/rest/fluentapi", "https://jm.example?key=abc"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    jm_fluent_base_url(value)


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.jm_config = patch("jm_endpoints.get_env_value", return_value="https://jm.example")
        self.jm_config.start()
        self.addCleanup(self.jm_config.stop)

    xml = "<Root><AvokaSmartForm><Application><Id>42</Id></Application></AvokaSmartForm></Root>"

    @patch.object(application, "make_request")
    def test_api_request_uses_jm_retention_window(self, request):
        fixed_now = datetime(2026, 10, 23, 12, 0, 0)
        request.return_value = jm_response(self.xml)
        with patch.object(application, "datetime") as frozen_datetime:
            frozen_datetime.now.return_value = fixed_now
            self.assertTrue(application.update_JMExtract(FakeSql(), "B-42"))
        payload = request.call_args.kwargs["data"]
        self.assertEqual(JM_RETENTION_DAYS, 15)
        self.assertEqual(payload["setStartDate"], "2026-10-08T12:00:00 MDT")
        self.assertEqual(payload["setEndDate"], "2026-10-23T12:00:00 MDT")

    @patch.object(application, "get_env_value")
    @patch.object(application, "make_request")
    def test_successful_insert_and_legacy_url(self, request, env):
        env.side_effect = lambda key: "https://jm.example" if key == "JM_BASE_URL" else "user"
        request.return_value = jm_response(self.xml)
        sql = FakeSql()
        self.assertTrue(application.update_JMExtract(sql, "B-42"))
        self.assertEqual(sql.connection.commits, 1)
        self.assertEqual(json.loads(sql.connection.rows["B-42"])["AvokaSmartForm"]["Application"]["Id"], "42")
        self.assertEqual(request.call_args.args[0], "https://jm.example/secure/rest/fluentapi/txnquery/listValues")

    @patch.object(application, "make_request")
    def test_existing_empty_row_is_recovered(self, request):
        request.return_value = jm_response(self.xml)
        sql = FakeSql({"B-42": ""})
        self.assertTrue(application.update_JMExtract(sql, "B-42"))
        self.assertTrue(sql.connection.rows["B-42"])

    @patch.object(application, "make_request")
    def test_good_existing_rawdata_never_overwritten(self, request):
        request.return_value = jm_response(self.xml)
        sql = FakeSql({"B-42": '{"existing":"valuable"}'})
        self.assertTrue(application.update_JMExtract(sql, "B-42"))
        self.assertEqual(sql.connection.rows["B-42"], '{"existing":"valuable"}')

    @patch.object(application, "make_request")
    def test_failed_http_does_not_write_placeholder(self, request):
        request.return_value = jm_response(self.xml, status=404)
        sql = FakeSql()
        self.assertFalse(application.update_JMExtract(sql, "B-42"))
        self.assertEqual(sql.connection.rows, {})
        self.assertEqual(sql.connection.commits, 0)

    @patch.object(application, "make_request")
    def test_exception_does_not_write_placeholder(self, request):
        request.side_effect = RuntimeError("connection failed")
        sql = FakeSql()
        self.assertFalse(application.update_JMExtract(sql, "B-42"))
        self.assertFalse(sql.connection.rows)

    @patch.object(application, "make_request")
    def test_missing_or_invalid_xml_does_not_write(self, request):
        for xml in ("", "<wrong><value>hi</value></wrong>", "<Root/>", "<Root><Broken></Root>"):
            with self.subTest(xml=xml):
                request.return_value = jm_response(xml)
                sql = FakeSql()
                self.assertFalse(application.update_JMExtract(sql, "B-42"))
                self.assertEqual(sql.connection.rows, {})

    @patch.object(application, "make_request")
    def test_invalid_json_is_not_saved(self, request):
        request.return_value = Mock(status_code=200, text="{")
        sql = FakeSql()
        self.assertFalse(application.update_JMExtract(sql, "B-42"))
        self.assertEqual(sql.connection.rows, {})

    @patch("application.time.sleep")
    @patch("application.requests.post")
    def test_requests_use_timeout_and_retry(self, post, sleep):
        post.side_effect = [
            Mock(status_code=503),
            Mock(status_code=200),
        ]
        with patch.object(application, "get_env_value", return_value="test"):
            response = application.make_request("https://jm.example/txnquery/listValues", {}, retries=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args.kwargs["timeout"], (10, 60))


def csv_loader_function(name, symbols):
    """Compile the unmodified production function without loading native SQL drivers."""
    source = Path(__file__).resolve().parent.parent / "api-server" / "csvLoader.py"
    module = ast.parse(source.read_text(encoding="utf-8-sig"))
    node = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
    isolated = ast.Module(body=[node], type_ignores=[])
    scope = dict(symbols)
    exec(compile(isolated, str(source), "exec"), scope)
    return scope[name]


class BatchExtractorTests(unittest.TestCase):
    def test_existing_empty_rawdata_is_not_considered_processed(self):
        responses = [
            [{"eCATrackingCode": "A"}, {"eCATrackingCode": "B"}],
            [{"code": "A"}],
        ]
        query_log = []
        class FakeTxn:
            def get_transactions_by_sql_query(self, query):
                query_log.append(query)
                return responses.pop(0)

        metrics = {}
        pulled = []
        extract = csv_loader_function("update_JMExtracts", {
            "datetime": datetime,
            "timedelta": timedelta,
            "random": random,
            "JM_RETENTION_DAYS": JM_RETENTION_DAYS,
            "sys": sys,
            "get_date_filter": lambda *args: "1=1",
            "update_metrics": lambda key, value: metrics.__setitem__(key, value),
            "update_JMExtract": lambda sql, code: (pulled.append(code) or True),
        })
        sql = type("SQL", (), {"connection": object()})()
        self.assertEqual(extract(sql, FakeTxn()), ["B"])
        self.assertEqual(pulled, ["B"])
        self.assertIn("RawData IS NOT NULL", query_log[1])
        self.assertEqual(metrics["manual_xml_pull_summary"]["saved"], 1)
        self.assertEqual(metrics["manual_xml_pull_summary"]["failed"], 0)

    def test_15_day_candidate_window_prioritizes_oldest_unfetched_codes(self):
        class FixedClock:
            @staticmethod
            def now():
                return datetime(2026, 10, 23, 12, 0, 0)
        queries = []
        window = []
        attempted = []
        responses = [
            [{"eCATrackingCode": "old"}, {"eCATrackingCode": "new"},
             {"eCATrackingCode": "old"}, {"eCATrackingCode": "already"}],
            [{"code": "already"}],
        ]
        class FakeTxn:
            def get_transactions_by_sql_query(self, query):
                queries.append(query)
                return responses.pop(0)
        def filter_for_window(start, end):
            window.append((start, end))
            return "1=1"
        extract = csv_loader_function("update_JMExtracts", {
            "datetime": FixedClock,
            "timedelta": timedelta,
            "JM_RETENTION_DAYS": JM_RETENTION_DAYS,
            "sys": sys,
            "get_date_filter": filter_for_window,
            "update_metrics": lambda key, value: None,
            "update_JMExtract": lambda sql, code: (attempted.append(code) or True),
        })
        sql = type("SQL", (), {"connection": object()})()
        self.assertEqual(extract(sql, FakeTxn()), ["old", "new"])
        self.assertEqual(attempted, ["old", "new"])
        self.assertEqual(window, [("2026-10-08T12:00:00", "2026-10-23T12:00:00")])
        self.assertIn("ORDER BY AppStartDate ASC", queries[0])

    def test_failed_candidate_query_never_claims_success(self):
        status = {}
        extract = csv_loader_function("update_JMExtracts", {
            "datetime": datetime,
            "timedelta": timedelta,
            "random": random,
            "JM_RETENTION_DAYS": JM_RETENTION_DAYS,
            "sys": sys,
            "get_date_filter": lambda *args: "1=1",
            "update_metrics": lambda key, value: status.__setitem__(key, value),
            "update_JMExtract": lambda *args: self.fail("must not fetch on SQL failure"),
        })
        sql = type("SQL", (), {"connection": object()})()
        txn = type("Txn", (), {"get_transactions_by_sql_query": lambda self, query: 0})()
        with self.assertRaises(RuntimeError):
            extract(sql, txn)
        self.assertTrue(status["manual_xml_pull"].startswith("failed"))
        self.assertEqual(status["manual_xml_pull_summary"]["saved"], 0)

    def test_scheduled_marker_written_only_after_xml_success(self):
        status = {"failed": 1}
        class FakeConnection:
            def connect(self):
                pass
            def disconnect(self):
                pass

        markers = {}
        scheduled = csv_loader_function("run_scheduled_job", {
            "os": os,
            "datetime": datetime,
            "timedelta": timedelta,
            "get_csv": lambda **kwargs: "ok",
            "SQLConn": FakeConnection,
            "Transaction": lambda sql: object(),
            "update_JMExtracts": lambda sql, txn: ["B"],
            "get_metrics": lambda: {"manual_xml_pull_summary": status},
            "update_metrics": lambda k, v: markers.__setitem__(k, v),
        })
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp:
            try:
                os.chdir(temp)
                self.assertEqual(scheduled(), 1)
                self.assertEqual(list(Path(".cache_requests").glob("*.tmp")), [])
                status["failed"] = 0
                self.assertEqual(scheduled(), 0)
                self.assertEqual(len(list(Path(".cache_requests").glob("*.tmp"))), 1)
                self.assertEqual(scheduled(), 0)
            finally:
                # On Windows CWD must be restored before TemporaryDirectory exits.
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
