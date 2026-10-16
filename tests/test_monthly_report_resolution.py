import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api-server"))

import report_modules.monthlyReports as monthly_reports
import report_modules.loan_account_apps_and_commitments as loan_commitments
from utils import table_fix_for_api_response


class MonthlyReportResolutionTests(unittest.TestCase):
    def test_product_report_executes_only_selected_queries(self):
        transaction = Mock()
        transaction.get_transactions_by_sql_query.return_value = 17
        intervals = [{"start_date": "2025-01-01", "end_date": "2025-01-01"}]

        report = monthly_reports.generate_report_variants_by_filters(
            ["1 = 1"], intervals, "Products", transactions=transaction
        )

        self.assertEqual(len(report["rows"]), 12)
        self.assertTrue(all("Products" in row[0] for row in report["rows"]))
        self.assertTrue(all(row[1] == 17 for row in report["rows"]))
        self.assertEqual(transaction.get_transactions_by_sql_query.call_count, 12)
        self.assertTrue(
            all(
                "SELECT" in call.args[0]
                and "AppStartDate >= '2025-01-01'" in call.args[0]
                for call in transaction.get_transactions_by_sql_query.call_args_list
            )
        )

    def test_combined_monthly_report_applies_requested_tracking_filter(self):
        with (
            patch.object(monthly_reports, "get_date_filter", return_value="date condition"),
            patch.object(monthly_reports, "get_list_of_months_between", return_value=[]),
            patch.object(
                monthly_reports,
                "generate_report_variants_by_filters",
                return_value={"headers": [], "rows": []},
            ) as generate_report,
        ):
            monthly_reports.get_monthly_all_report(
                "2025-01-01",
                "2025-01-31",
                {"monthlyReportProductTypeSelector": "Products", "eCATrackingCode": "B"},
            )

        filters = generate_report.call_args.args[0]
        self.assertIn("eCATrackingCode LIKE 'B-%'", filters)

    def test_api_table_fix_preserves_header_and_row_alignment(self):
        report = {
            "headers": ["-", "March", "January", "February"],
            "rows": [["Apps", 3, 1, 2]],
        }

        self.assertIs(table_fix_for_api_response(report), report)
        self.assertEqual(report["headers"], ["-", "March", "January", "February"])
        self.assertEqual(report["rows"][0], ["Apps", 3, 1, 2])

    def test_loan_insights_skip_edw_lookup_when_no_tracking_codes_match(self):
        transaction = Mock()

        with (
            patch.object(loan_commitments, "Q", return_value=0) as query,
            patch.object(loan_commitments, "SQLConn") as sql_conn,
            patch.object(loan_commitments, "Transaction", return_value=transaction),
        ):
            report = loan_commitments.get_insigths_report(
                "2023-01-01",
                "2023-12-31",
                {"application_type": "undefined", "eCATrackingCode": "%"},
            )

        self.assertEqual(report["Submitted"], 0)
        self.assertEqual(report["Opened/Approved"], 0)
        self.assertEqual(query.call_count, 3)
        transaction.get_transactions_by_sql_query.assert_not_called()
        sql_conn.return_value.disconnect.assert_called_once()

    def test_loan_commitments_resolve_missing_edw_appids_from_tracking_codes(self):
        transaction = Mock()
        transaction.get_transactions_by_sql_query.return_value = [
            {"APPID": "APP-1"},
            {"APPID": "APP-2"},
        ]
        source_rows = [
            {"EDW_APPID": "APP-1", "eCATrackingCode": "C-direct"},
            {"EDW_APPID": None, "eCATrackingCode": "C-fallback-1"},
            {"EDW_APPID": "", "eCATrackingCode": "C-fallback-2"},
        ]

        with patch.object(loan_commitments, "Q", return_value=source_rows) as query:
            result = loan_commitments._get_edw_appids_for_interval(
                {"start_date": "2026-04-01", "end_date": "2026-06-30"},
                {"application_type": "undefined", "eCATrackingCode": "%"},
                transaction,
                use_cache=False,
            )

        self.assertEqual(result["source_rows"], 3)
        self.assertEqual(result["direct_appids"], 1)
        self.assertEqual(result["fallback_appids"], 2)
        self.assertEqual(result["appids"], ["APP-1", "APP-2"])
        query.assert_called_once()
        mapping_query = transaction.get_transactions_by_sql_query.call_args.args[0]
        self.assertIn("Temenos_ID IN ('C-fallback-1', 'C-fallback-2')", mapping_query)
        self.assertNotIn("C-direct", mapping_query)


if __name__ == "__main__":
    unittest.main()
