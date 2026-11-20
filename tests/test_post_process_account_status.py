"""Regression coverage for CRFEDW-only CSV account-status post-processing.

Extract the real function without importing the application's SQL drivers.
"""
import ast
import unittest
from pathlib import Path


POST_PROCESS = Path(__file__).resolve().parents[1] / "api-server" / "post_process.py"


def isolated_account_status(namespace):
    source = POST_PROCESS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "account_status_fetch"
    )
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 str(POST_PROCESS), "exec"), namespace)
    return namespace["account_status_fetch"]


class AccountStatusPostProcessTests(unittest.TestCase):
    def make_function(self, connect_succeeds=True, return_rows=True):
        connections = []
        queries = []
        updates = []

        class FakeSQLConn:
            def __init__(self, kind):
                connections.append(self)
                self.kind = kind
                self.connection = None
                self.disconnected = False

            def connect(self):
                if connect_succeeds:
                    self.connection = object()

            def disconnect(self):
                self.disconnected = True

        class FakeTransaction:
            def __init__(self, connection):
                self.connection = connection

            def get_transactions_by_sql_query(self, query):
                queries.append(query)
                if "CRF_APP_ACTION_CUSTOMER_CUR" in query:
                    return [{"APPID": "APP-1"}]
                if "CRF_APP_ACTION_APPLICATION_CUR" in query:
                    return [{"DecisionStatusName": "Approved"}]
                raise AssertionError(f"Unexpected EDW query: {query}")

        class FakeProperties:
            def __init__(self, sql):
                pass

            def ecaTrackingCode_exists(self, tracking_code):
                return False

            def set_properties_for_ecaTrackingCode(self, tracking_code, data):
                updates.append((tracking_code, data))

        class SourceTransaction:
            def get_transactions_by_sql_query(self, query):
                queries.append(query)
                self_query_expected = "[DigitalReport].[dbo].[Transactions]"
                if self_query_expected not in query:
                    raise AssertionError(f"Unexpected source query: {query}")
                if not return_rows:
                    return 0
                return [{
                    "PrimarySSN": "123-45-6789",
                    "ecaTrackingCode": "TEST-1",
                    "PrimaryName": "Test Customer",
                    "AppStartDate": "2026-01-01",
                }]

        namespace = {
            "SQLConn": FakeSQLConn,
            "Transaction": FakeTransaction,
            "Properties": FakeProperties,
            "excludeBotData": "1=1",
            "excludeZeroProductApps": "1=1",
            "approvedAppsForBPMandCRIF": "1=1",
        }
        function = isolated_account_status(namespace)
        return function, SourceTransaction(), connections, queries, updates

    def test_loan_enrichment_does_not_connect_to_ptyedw_or_query_deposits(self):
        function, source, connections, queries, updates = self.make_function()
        function(object(), source)
        self.assertEqual([conn.kind for conn in connections], ["CRFEDW"])
        self.assertTrue(connections[0].disconnected)
        self.assertTrue(any("CRF_APP_ACTION_CUSTOMER_CUR" in q for q in queries))
        self.assertTrue(any("CRF_APP_ACTION_APPLICATION_CUR" in q for q in queries))
        self.assertFalse(any("PTYEDW" in q or "PTYMSTR_DDA" in q or
                             "CAM_DDA_TRAN" in q for q in queries))
        self.assertTrue(any("AppID_0" in row for _, row in updates))
        self.assertTrue(any(row.get("AppID_0_LoanAcctStatus_0") == "Approved"
                            for _, row in updates))
        self.assertFalse(any("DepositAcctStatus" in key or "AccountNumber_" in key
                             for _, row in updates for key in row))

    def test_missing_crfedw_does_not_query_any_other_database(self):
        function, source, connections, queries, updates = self.make_function(
            connect_succeeds=False)
        function(object(), source)
        self.assertEqual([conn.kind for conn in connections], ["CRFEDW"])
        self.assertEqual(queries, [])
        self.assertEqual(updates, [])

    def test_no_loan_rows_still_disposes_of_crfedw_connection(self):
        function, source, connections, queries, updates = self.make_function(
            return_rows=False)
        function(object(), source)
        self.assertEqual([conn.kind for conn in connections], ["CRFEDW"])
        self.assertTrue(connections[0].disconnected)
        self.assertEqual(len(queries), 1)
        self.assertEqual(updates, [])


if __name__ == "__main__":
    unittest.main()
