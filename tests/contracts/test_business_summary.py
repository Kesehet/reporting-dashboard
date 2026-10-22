"""Business summary regressions through the real chart routes and SQL boundary."""
import contextlib
import io
import re
import unittest
from unittest.mock import patch

from daily_api_key import make_daily_api_key
from runtime import BASE_PARAMS, SqlFixture, runtime

APPS = 'Business Account Summary Number Of Apps Table'
PRODUCTS = 'Business Account Summary Top 10 Products Table'


class BusinessSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = runtime()
        cls.server, cls.DB = cls.context.__enter__()
        cls.client = cls.server.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def setUp(self):
        self.fixture = SqlFixture('populated')
        self.product_codes = ['20903', '20903.0', '20601.0', '20601', '101', '101.0']
        self.counts = {'20903': 91, '20601': 31, '101': 8}
        self.product_queries = []
        self.patch = patch.object(self.DB.Transaction, 'get_transactions_by_sql_query', self.query)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        stdout = contextlib.redirect_stdout(io.StringIO())
        stdout.__enter__()
        self.addCleanup(stdout.__exit__, None, None, None)

    def query(self, sql, **kwargs):
        if 'Select Distinct value' in sql:
            return [{'value': code} for code in self.product_codes]
        if "OR ProductSetId = '" in sql:
            self.product_queries.append(sql)
            code = re.search(r"ProductSetId = '([^']+)'", sql).group(1)
            count = self.counts.get(code, 1)
            self.assertIn('COUNT(DISTINCT eCATrackingCode) AS data', sql)
            self.assertNotIn('GROUP BY ProductSetId', sql)
            return float(count)
        if ' as data' in sql.lower():
            return 54.0  # DB.py returns scalar COUNT results as floats.
        return self.fixture.execute(None, sql, **kwargs)

    def request(self, name, method='POST', **params):
        args = {**BASE_PARAMS, 'start_date': '2026-01-01', 'end_date': '2026-03-31', **params}
        if method == 'GET':
            response = self.client.get('/charts/' + name, query_string=args, headers={'X-API-KEY': make_daily_api_key('fixture-chart-api-key')})
        else:
            response = self.client.post('/charts/' + name, json=args, headers={'X-API-KEY': make_daily_api_key('fixture-chart-api-key')})
        self.assertEqual(response.status_code, 200, response.json)
        return response.json

    def test_all_three_application_total_sections_render_whole_numbers(self):
        for method in ['GET', 'POST']:
            for formatting in ['true', 'false']:
                payload = self.request(APPS, method=method, showComma=formatting)
                self.assertEqual(len(payload['rows']), 27)
                totals = [row for row in payload['rows'] if row[0].startswith('Total ')]
                self.assertEqual(len(totals), 3)
                for row in totals:
                    self.assertEqual(len(row), len(payload['headers']))
                    for cell in row[1:]:
                        self.assertIn("<b class='greyed_out'>54</b>", cell)
                        self.assertNotIn('54.0', cell)

    def test_equivalent_codes_are_counted_once_without_doubling_totals(self):
        payload = self.request(PRODUCTS, showComma='false')
        self.assertEqual([row[1:] for row in payload['rows']], [['20903', 91], ['20601', 31], ['101', 8]])
        self.assertEqual(len(self.product_queries), 3)
        for sql in self.product_queries:
            self.assertIn('AppStartDate', sql)
            self.assertIn('2026-01-01', sql)
            self.assertIn('2026-03-31', sql)
            self.assertIn("ecatrackingcode like 'b-%'", sql.lower())

    def test_deduplication_happens_before_top_ten_limit(self):
        self.product_codes = [variant for code in range(100, 112) for variant in [str(code), f'{code}.0']]
        self.counts = {str(code): 200 - code for code in range(100, 112)}
        payload = self.request(PRODUCTS, showComma='false')
        self.assertEqual([row[1] for row in payload['rows']], [str(code) for code in range(100, 110)])
        self.assertEqual(len(self.product_queries), 12)

    def test_same_description_does_not_merge_different_product_codes(self):
        import report_modules.businessAccountsSummary as summary
        with patch.object(summary, 'get_product_name', return_value='Same description'):
            payload = self.request(PRODUCTS, showComma='false')
        self.assertEqual(len(payload['rows']), 3)

    def test_blank_codes_are_skipped_and_normalization_precedes_lookup(self):
        self.product_codes = [None, '', ' ', ' 20903.0 ', '20903', '20903.0']
        payload = self.request(PRODUCTS, showComma='false')
        self.assertEqual([row[1:] for row in payload['rows']], [['20903', 91]])
        self.assertEqual(len(self.product_queries), 1)

    def test_empty_product_list_returns_empty_rows(self):
        self.product_codes = []
        payload = self.request(PRODUCTS, showComma='false')
        self.assertEqual(payload['rows'], [])
        self.assertEqual(self.product_queries, [])

    def test_count_distinct_covers_both_spellings_without_counting_an_app_twice(self):
        import sqlite3
        import report_modules.businessAccountsSummary as summary
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.create_function('CONCAT', -1, lambda *values: ''.join(map(str, values)))
        db.execute('CREATE TABLE Transactions (ProductSetId TEXT, eCATrackingCode TEXT, AppStartDate TEXT, PrimaryName TEXT, PrimarySSN TEXT, eCAID TEXT, NumLendingProducts INT, NumDepositProducts INT, BranchId TEXT)')
        entries = [
            ('20903', 'B-1', '2026-02-01', 'Customer 1', '123', '1', 0, 1, '101'),
            ('20903.0', 'B-1', '2026-02-01', 'Customer 1', '123', '1', 0, 1, '101'),
            ('20903.0', 'B-2', '2026-02-02', 'Customer 2', '123', '2', 0, 1, '101'),
            ('20903', 'C-3', '2026-02-01', 'Customer 3', '123', '3', 0, 1, '101'),
            ('20903', 'B-4', '2025-02-01', 'Customer 4', '123', '4', 0, 1, '101'),
            ('20601', 'B-5', '2026-02-01', 'Customer 5', '123', '5', 0, 1, '101'),
        ]
        db.executemany('INSERT INTO Transactions VALUES (?,?,?,?,?,?,?,?,?)', entries)
        def execute(_txn, sql, **kwargs):
            sql = sql.replace('[DigitalReport].[dbo].[Transactions]', 'Transactions')
            return db.execute(sql).fetchone()[0]
        with patch.object(self.DB.Transaction, 'get_transactions_by_sql_query', execute):
            self.assertEqual(summary.get_product_count('20903', '2026-01-01', '2026-03-31'), 2)
