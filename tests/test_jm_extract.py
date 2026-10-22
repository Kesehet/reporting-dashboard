"""Offline regression tests: no Journey Manager traffic or SQL Server required."""
import json
import os
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api-server"))

import application
from jm_endpoints import jm_fluent_base_url, jm_workspaces_url


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
    xml = "<Root><AvokaSmartForm><Application><Id>42</Id></Application></AvokaSmartForm></Root>"

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


if __name__ == "__main__":
    unittest.main()
