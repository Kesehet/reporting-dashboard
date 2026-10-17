"""Focused HTTP, arithmetic, date, and existing regression tests alongside inventory coverage."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import quote

from runtime import BASE_PARAMS, ROOT, SqlFixture, runtime

PIE = 'Application Volume By Product (All Started Apps) Pie - Year to Date'
TABLE = 'Common App In Branch and Consumer Facing Report'


class ChartHttpTests(unittest.TestCase):
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
        def query(txn, sql, **kwargs):
            return self.fixture.execute(txn, sql, **kwargs)
        self.patch = patch.object(self.DB.Transaction, 'get_transactions_by_sql_query', query)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)

    def request(self, name=PIE, **params):
        return self.client.post('/charts/' + quote(name), json={
            **BASE_PARAMS, 'start_date': '2026-01-01', 'end_date': '2026-03-31', **params,
        })

    def test_numeric_values_and_label_order_survive_default_formatting(self):
        raw = self.request(showComma='false')
        wire = self.request(showComma='true')
        self.assertEqual(raw.status_code, 200)
        self.assertEqual(raw.json['labels'], ['Loan Product Apps', 'Deposit Product Apps', 'Mixed Product Apps'])
        self.assertEqual(raw.json['list'], [1234, 567, 89])
        self.assertEqual(wire.json['labels'], raw.json['labels'])
        self.assertEqual(wire.json['list'], ['1,234', '567', '89'])

    def test_no_rows_preserves_zero_series_and_does_not_return_nan(self):
        self.fixture.scenario = 'empty'
        r = self.request(showComma='false')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['list'], [0, 0, 0])
        json.dumps(r.json, allow_nan=False)

    def test_get_and_post_pass_the_same_chart_parameters(self):
        p = {**BASE_PARAMS, 'start_date':'2026-01-01', 'end_date':'2026-03-31', 'showComma':'false'}
        post = self.client.post('/charts/' + quote(PIE), json=p)
        get = self.client.get('/charts/' + quote(PIE), query_string=p)
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json, post.json)

    def test_missing_and_malformed_dates_are_400_before_queries(self):
        for params in [{'end_date': '2026-01-01'}, {'start_date': 'wrong', 'end_date':'2026-01-01'}]:
            for method in ['GET', 'POST']:
                with self.subTest(params=params, method=method):
                    r = self.client.get('/charts/'+quote(PIE), query_string=params) if method == 'GET' else self.client.post('/charts/'+quote(PIE), json=params)
                    self.assertEqual(r.status_code, 400)
                    self.assertIn('error', r.json)
        self.assertEqual(self.fixture.queries, [])

    def test_unknown_chart_returns_existing_error_envelope(self):
        r = self.request('contract-unknown-name')
        self.assertEqual(r.json, {'message':'No Charts specified.', 'status':'error', 'name':'contract-unknown-name'})

    def test_requested_date_ranges_and_tracking_filter_reach_real_queries(self):
        for start, end in [('2024-02-29','2024-02-29'), ('2025-12-01','2026-01-31')]:
            with self.subTest(start=start, end=end):
                self.fixture.queries.clear()
                r = self.request(TABLE, start_date=start, end_date=end, eCATrackingCode='B', showComma='false')
                self.assertEqual(r.status_code, 200)
                queries = '\n'.join(self.fixture.queries)
                self.assertIn(start, queries)
                self.assertIn(end, queries)
                self.assertIn("eCATrackingCode LIKE 'B-%'", queries)
                self.assertTrue(all(len(row) == len(r.json['headers']) for row in r.json['rows']))

    def test_deferred_query_endpoint_formats_the_same_numeric_result(self):
        sql = 'SELECT COUNT(*) as data FROM fixture'
        self.assertEqual(self.client.post('/query', json={'query': sql}).text, '1,890')
        self.assertEqual(self.client.post('/query', json={'query': sql, 'showComma':False}).text, '1890')
        self.assertEqual(self.client.post('/query', json={}).status_code, 400)

    def test_existing_python_regressions(self):
        # Existing tests use mocks/temp CSV files. Native ODBC and network remain blocked.
        suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test_*.py', top_level_dir=str(ROOT/'tests'))
        result = unittest.TestResult()
        suite.run(result)
        self.assertGreaterEqual(result.testsRun, 11)
        self.assertEqual(result.errors + result.failures, [])


if __name__ == '__main__':
    unittest.main()
