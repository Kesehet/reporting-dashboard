"""Check optimized SQL against the original monthly SQL on identical synthetic rows.

SQLite is used only as a lightweight query evaluator.  It executes both the
original independent SELECT statements and the optimized conditional aggregates
over the same data (no production connectivity or customer information).
"""
import os
import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules import monthlyReports as monthly


class SyntheticTransaction:
    def __init__(self, connection):
        self.connection = connection
        self.queries = []

    def get_transactions_by_sql_query(self, sql, **kwargs):
        self.queries.append(sql)
        # SQL Server table qualification/hints only; all metric SQL is executed.
        statement = sql.replace("[DigitalReport].[dbo].[Transactions]", "Transactions")
        statement = statement.replace("WITH (NOLOCK)", "")
        cursor = self.connection.execute(statement)
        rows = [dict(row) for row in cursor.fetchall()]
        if " as data" in sql.lower():
            return (rows[0].get("data") or 0) if rows else 0
        return rows if rows else 0


def original_queries(base_filters, intervals, variant, txn):
    """The 2026-11-17 main-branch per-metric / per-month algorithm."""
    selected = "Applications" if variant == "All" else variant.split(" ")[0]
    categories = [
        ("Applications", None, monthly.countColumn),
        ("Products", None, monthly.sumColumn("NumLendingProducts+NumDepositProducts")),
        ("Loan Products", monthly.loanApps, monthly.sumColumn("NumLendingProducts+NumDepositProducts")),
        ("Deposit Products", monthly.depositApps, monthly.sumColumn("NumLendingProducts+NumDepositProducts")),
        ("Mixed Products", monthly.mixedApps, monthly.sumColumn("NumLendingProducts+NumDepositProducts")),
    ]
    stages = [
        ("Started", None),
        ("Submitted", monthly.submittedApps),
        ("Opened/Approved", monthly.approvedApps),
    ]
    rows = []
    for stage_name, stage_filter in stages:
        for category_name, category_filter, column in categories:
            label = stage_name + " " + category_name
            if selected not in label:
                continue
            condition = [p for p in (stage_filter, category_filter) if p] + base_filters
            sql = monthly.query_maker(columns=[column], where=condition)
            row = [label]
            for interval in intervals:
                row.append(txn.get_transactions_by_sql_query(
                    sql + " AND " + monthly.in_between_sql_condition(interval) + "  "
                ))
            rows.append(row)
    return {"headers": ["-"] + [monthly.get_header(m)["label"] for m in intervals], "rows": rows}


class MonthlyQueryEquivalence(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.row_factory = sqlite3.Row
        self.db.create_function("YEAR", 1, lambda d: int(d[:4]))
        self.db.create_function("MONTH", 1, lambda d: int(d[5:7]))
        self.db.create_function("CONCAT", 3, lambda *v: "".join("" if x is None else str(x) for x in v))
        self.db.execute("""CREATE TABLE Transactions (
            eCATrackingCode TEXT, eCAID TEXT, AppStartDate TEXT,
            NumLendingProducts INTEGER, NumDepositProducts INTEGER,
            AppStatus TEXT, Application_Type TEXT, PrimaryName TEXT,
            PrimarySSN TEXT
        )""")
        self.db.executemany(
            "INSERT INTO Transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("C-dup", "1", "2026-01-05", 1, 0, "Started", "Online", "Person A", "1"),
                ("C-dup", "2", "2026-01-15", 2, 0, "Approved", "Online", "Person A", "1"),
                ("C-dep", "3", "2026-01-31", 0, 1, "Deposit Submitted", "Banker Assisted", "Person B", "2"),
                ("B-mix", "4", "2026-01-20", 1, 2, "Opened", "Banker Assisted", "Person C", "3"),
                ("C-dep2", "5", "2026-02-12", 0, 3, "Completed", "Online", "Person D", "4"),
                ("B-loan", "6", "2026-02-15", 3, 0, "Denied", "Online", "Person E", "5"),
                ("C-mix", "7", "2026-02-28", 1, 1, "Started", "Online", "Person F", "6"),
                ("B-dep", "8", "2026-03-01", 0, 2, "Approved", "Banker Assisted", "Person G", "7"),
                ("C-null", "9", "2026-03-14", None, 1, "Completed", "Online", "Person H", "8"),
                ("B-zero", "10", "2026-03-15", 0, 0, "Completed", "Online", "Person I", "9"),
                ("C-empty", "11", "2026-03-16", 1, 0, "Completed", "Online", "", "9"),
                ("C-bot", "12", "2026-03-17", 1, 0, "Completed", "Online", "TlVMTA==", "9"),
            ],
        )

    def test_values_and_labels_match_original_for_every_variant_and_filter(self):
        variants = ("All", "Products", "Loan Products", "Deposit Products", "Mixed Products")
        windows = (
            ("2026-01-01", "2026-03-31"),
            ("2026-01-15", "2026-02-15"),
            ("2026-04-01", "2026-04-30"),
        )
        for variant in variants:
            for tracking in ("All", "C", "B"):
                for start, end in windows:
                    with self.subTest(variant=variant, tracking=tracking, start=start, end=end):
                        base = [
                            monthly.get_date_filter(start, end),
                            monthly.excludeZeroProductApps,
                            monthly.CorBFilter(tracking),
                            monthly.bot_filter(25),
                        ]
                        intervals = monthly.get_list_of_months_between(start, end)
                        old_txn = SyntheticTransaction(self.db)
                        new_txn = SyntheticTransaction(self.db)
                        original = original_queries(base, intervals, variant, old_txn)
                        optimized = monthly.generate_report_variants_by_filters(
                            base, intervals, variant, transactions=new_txn
                        )
                        self.assertEqual(optimized, original)
                        self.assertEqual(len(new_txn.queries), 1)
                        self.assertGreater(len(old_txn.queries), 1)
                        if variant == "All":
                            self.assertIn("COUNT(DISTINCT CASE WHEN", new_txn.queries[0])

    def test_application_totals_are_distinct_while_product_totals_are_not(self):
        filters = [
            monthly.get_date_filter("2026-01-01", "2026-01-31"),
            monthly.excludeZeroProductApps,
            monthly.CorBFilter("C"),
            monthly.bot_filter(25),
        ]
        interval = monthly.get_list_of_months_between("2026-01-01", "2026-01-31")
        apps = monthly.generate_report_variants_by_filters(
            filters, interval, "All", transactions=SyntheticTransaction(self.db)
        )
        products = monthly.generate_report_variants_by_filters(
            filters, interval, "Products", transactions=SyntheticTransaction(self.db)
        )
        self.assertEqual(apps["rows"][0], ["Started Applications", 2])
        self.assertEqual(products["rows"][0], ["Started Products", 4])


if __name__ == "__main__":
    unittest.main()
