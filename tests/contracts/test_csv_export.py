"""Regression coverage for the CSV export HTTP contract and serializer."""
import csv
import io
import unittest
from unittest.mock import patch
from urllib.parse import quote

from runtime import BASE_PARAMS, runtime
from daily_api_key import make_daily_api_key


INSIGHT = "CSV Contract Insight"
class CsvExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = runtime()
        cls.server, cls.DB = cls.ctx.__enter__()
        cls.client = cls.server.app.test_client()
        from utils import insight_report_to_csv_response, sql_response_to_csv
        cls.to_csv = staticmethod(sql_response_to_csv)
        cls.insight_to_csv = staticmethod(insight_report_to_csv_response)

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)

    def request(self, data, method="GET", headers=None, **options):
        params = {
            **BASE_PARAMS,
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "return_format": "csv",
            **options,
        }
        path = "/charts/" + quote(INSIGHT)
        valid_headers = {"X-API-KEY": make_daily_api_key("fixture-chart-api-key")}
        with patch.object(self.server, "getChartData", return_value=data):
            if method == "POST":
                return self.client.post(path, json=params, headers=valid_headers if headers is None else headers)
            return self.client.get(path, query_string=params, headers=valid_headers if headers is None else headers)

    def test_csv_writer_quotes_commas_newlines_and_double_quotes(self):
        source = [{"Count": 1234, "Customer": "Acme, Inc.", "Note": 'He said "yes"\nand left', "Null": None}]
        text = self.to_csv(source)
        self.assertEqual(list(csv.reader(io.StringIO(text))), [
            ["Count", "Customer", "Note", "Null"],
            ["1234", "Acme, Inc.", 'He said "yes"\nand left', ""],
        ])
        self.assertIn('"Acme, Inc."', text)
        self.assertIn('"He said ""yes""\nand left"', text)

    def test_csv_preserves_heterogeneous_columns_and_structured_tables(self):
        self.assertEqual(list(csv.reader(io.StringIO(self.to_csv([{"A": 1}, {"B": 2}])))), [
            ["A", "B"], ["1", ""], ["", "2"],
        ])
        table = {"headers": ["Account", "Amount"], "rows": [["0012", 4000], ["0099", None]]}
        self.assertEqual(list(csv.reader(io.StringIO(self.to_csv(table)))), [
            ["Account", "Amount"], ["0012", "4000"], ["0099", ""],
        ])

    def test_get_and_post_return_actual_csv_not_json_wrapped_string(self):
        report = {"_report_Example": [
            {"Amount": 1234, "Customer": "A, B", "Description": 'He said "Hello"'},
        ]}
        for method in ("GET", "POST"):
            with self.subTest(method=method):
                response = self.request(report, method)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "text/csv")
                self.assertIn("attachment", response.headers["Content-Disposition"])
                self.assertEqual(list(csv.reader(io.StringIO(response.get_data(as_text=True)))), [
                    ["Amount", "Customer", "Description"],
                    ["1234", "A, B", 'He said "Hello"'],
                ])
                self.assertFalse(response.is_json)

    def test_default_json_still_uses_existing_formatting(self):
        report = {"_report_Example": [{"Count": 1234}], "total": 1234}
        response = self.request(report, return_format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        self.assertEqual(response.json["total"], "1,234")

    def test_export_uses_requested_report_name_and_sql_rows(self):
        report = {"_report_First": [{"Id": 1}], "_report_Second": "SELECT Name, Amount FROM fixture"}
        with patch.object(self.DB.Transaction, "get_transactions_by_sql_query",
                          return_value=[{"Name": "North, East", "Amount": 2000}]) as query:
            response = self.request(report, report_name="Second")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(csv.reader(io.StringIO(response.get_data(as_text=True)))), [
            ["Name", "Amount"], ["North, East", "2000"],
        ])
        query.assert_called_once_with("SELECT Name, Amount FROM fixture")

    def test_empty_export_is_empty_csv_not_json_zero(self):
        response = self.request({"_report_Example": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertEqual(response.get_data(as_text=True), "")

    def test_cached_csv_and_concurrent_waiter_keep_csv_headers(self):
        payload = "Name,Amount\nAcme,1234\n"
        for waiter in (False, True):
            with self.subTest(waiter=waiter):
                with patch.object(self.server, "get_cached_item",
                                  side_effect=[None, payload] if waiter else [payload]) as cached:
                    if waiter:
                        with patch.object(self.server, "_acquire_or_wait_for_slot", return_value=("waiter", None)):
                            response = self.request({"_report_Example": []})
                    else:
                        response = self.request({"_report_Example": []})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "text/csv")
                self.assertEqual(response.get_data(as_text=True), payload)
                self.assertEqual(cached.call_count, 2 if waiter else 1)

    def test_invalid_format_with_trailing_apostrophe_is_not_silent_json(self):
        response = self.request({"_report_Example": [{"Count": 1}]}, return_format="csv'")
        self.assertEqual(response.status_code, 400)
        self.assertIn("return_format", response.json["error"])

    def test_missing_export_block_returns_clear_400(self):
        for report, name in [({"total": 1}, ""), ({"_report_First": []}, "missing")]:
            with self.subTest(report=report, name=name):
                response = self.request(report, report_name=name)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)
                self.assertIn("error", response.json)

    def test_csv_export_still_requires_authentication(self):
        response = self.request({"_report_Example": [{"Count": 1}]}, headers={})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
