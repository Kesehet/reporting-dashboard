from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules.search_txn import FluentAPITransactionSearch, search_txn


class ExactTransactionSearchTests(unittest.TestCase):
    def test_exact_code_ignores_date_form_and_status(self):
        client = Mock()
        client.make_request.return_value = [{"id": 1, "trackingCode": "C-OLD"}]
        searcher = FluentAPITransactionSearch(client)
        with patch("report_modules.search_txn.get_list_of_days_between") as intervals:
            result = searcher.search_txn("C-OLD", "invalid", None, "unrelated-form", True, False)
        self.assertEqual(result, ["C-OLD"])
        intervals.assert_not_called()
        client.make_request.assert_called_once_with(
            "/txnquery/listValues", data={"withFormXml": "false", "setTrackingCode": "C-OLD", "setFetchLimit": "1"},
            retries=1, delay=2, use_cache=False)

    def test_exact_details_use_live_requests(self):
        client = Mock()
        client.make_request.side_effect = [
            [{"id": 1, "trackingCode": "B-OLD", "formName": "Other Form", "formStatus": "Completed"}],
            {"propertyMap": {}}, {"submissionGroupNames": []},
        ]
        rows = FluentAPITransactionSearch(client).search_txn("B-OLD", None, None, "fnb-consumer", False, False)
        self.assertEqual(rows[0]["Form Name"], "Other Form")
        self.assertEqual(rows[0]["tracking_code"], "B-OLD")
        self.assertTrue(all(call.kwargs.get("use_cache") is False for call in client.make_request.call_args_list))

    def test_recent_browse_keeps_form_date_filters(self):
        client = Mock()
        client.make_request.return_value = []
        with patch("report_modules.search_txn.get_list_of_days_between", return_value=[
            {"start_date": "2026-11-01", "end_date": "2026-11-02"}
        ]):
            FluentAPITransactionSearch(client).search_txn("", "2026-11-01", "2026-11-02", "fnb-consumer", True, False)
        self.assertEqual(client.make_request.call_count, 3)
        for call in client.make_request.call_args_list:
            payload = call.kwargs["data"]
            self.assertEqual(payload["setFormCode"], "fnb-consumer")
            self.assertIn("setStartDate", payload)
            self.assertIn("setEndDate", payload)

    def test_multiple_codes_skip_empty_entries(self):
        with patch("report_modules.search_txn.FluentAPITransactionSearch") as factory:
            factory.return_value.search_txn.return_value = []
            search_txn({"tracking_codes": "C-ONE, , B-TWO,C-ONE,"}, None, None, False)
            self.assertEqual([call.args[0] for call in factory.return_value.search_txn.call_args_list], ["C-ONE", "B-TWO"])
