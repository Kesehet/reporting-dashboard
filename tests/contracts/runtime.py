"""Run real chart builders and Flask routes with only I/O boundaries replaced.

No chart function is mocked. The SQL provider models Transaction's scalar `AS data`
versus rowset contract, not SQL Server execution or real business totals.
"""
import ast
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / 'api-server'
sys.path.insert(0, str(API))


def chart_names():
    tree = ast.parse((API / 'charts.py').read_text(encoding='utf-8-sig'))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == 'name':
            for item in node.comparators:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    names.append(item.value)
    return names


BASE_PARAMS = {
    'application_type': 'All', 'eCATrackingCode': 'C', 'BranchID': '101',
    'monthlyReportProductTypeSelector': 'All', 'variant': 'Started',
    'stat_type': 'Submitted', 'filters': '', 'format': 'json',
    'start_date_for_left_graph': '2025-01-01', 'end_date_for_left_graph': '2025-03-31',
    'start_date_for_right_graph': '2026-01-01', 'end_date_for_right_graph': '2026-03-31',
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()


class SqlFixture:
    """Nonzero aggregates plus explicit rowset cases; unknown rowsets stay empty.

    The empty scenario returns 0 for absent rowsets, matching DB.py rather than
    using [] and accidentally concealing existing no-data failures.
    """
    def __init__(self, scenario):
        self.scenario = scenario
        self.queries = []
        self.rowsets = []

    def execute(self, txn, query, debug=False, use_cache=True):
        assert isinstance(query, str) and re.search(r'\bselect\b', query, re.I), 'Expected a read-only SELECT fixture'
        self.queries.append(query)
        low = query.lower()
        populated = self.scenario != 'empty'
        # The LOB report is one aggregate row even when the source table is empty.
        if ' as [total_started_applications' in low:
            aliases = re.findall(r'\bAS\s+\[([^]]+)\]', query, re.I)
            return [{alias: (17 if populated else 0) for alias in aliases}]
        # Match Transaction's AS data scalar convention.
        if re.search(r'\bas\s+data\b', low):
            if not populated:
                return 0
            # Distinct values ensure swapped series and mixed numeric formatting show up.
            flat = re.sub(r'\s+', '', low)
            literal = re.fullmatch(r'select(\d+)asdata;?', flat)
            if literal:
                return int(literal.group(1))
            if 'numlendingproducts>0andnumdepositproducts=0' in flat:
                return 1234
            if 'numlendingproducts=0andnumdepositproducts>0' in flat:
                return 567
            if 'numlendingproducts>=1andnumdepositproducts>=1' in flat:
                return 89
            return 1890
        if populated and 'rankeddailyproductcounts' in low:
            self.rowsets.append('daily-products')
            return [{'AppDate': '2026-01-15', 'ProductSetId': '100', 'product_count': 23}]
        if populated and 'select distinct value' in low:
            self.rowsets.append('product-ids')
            return [{'value': '100'}, {'value': '200'}]
        if populated and 'select distinct branchid' in low:
            self.rowsets.append('branch-ids')
            return [{'BranchId': '101'}]
        if populated and all('[' + key + ']' in low for key in ['id','table','key','month','value']):
            self.rowsets.append('edelivery-union')
            return [{'ID': 'fixture', 'Table': 'eDelivery', 'Key': 'Apps', 'Month': '2026-06', 'Value': 1234}]
        if populated and 'transactioncount' in low and 'productsetid' in low:
            self.rowsets.append('product-counts')
            return [
                {'ProductSetId': '100|200', 'CrossSellProducts': '300', 'TransactionCount': 23, 'OnlineCount': 17, 'BankerAssistedCount': 6},
                {'ProductSetId': '400|500', 'CrossSellProducts': '600', 'TransactionCount': 11, 'OnlineCount': 9, 'BankerAssistedCount': 2},
            ]
        if populated and re.search(r'\bselect\s+(?:top\s+\d+\s+)?\*\s+from\s+(?:\[DigitalReport\]\.\[dbo\]\.)?\[?Transactions\]?', query, re.I):
            self.rowsets.append('transactions')
            return [
                {'eCAID': 'fixture-1', 'eCATrackingCode': 'C-fixture-1', 'ProductSetId': '100', 'AppStartDate': '2026-01-15', 'NumLendingProducts': 1, 'NumDepositProducts': 0},
                {'eCAID': 'fixture-2', 'eCATrackingCode': 'C-fixture-2', 'ProductSetId': '200', 'AppStartDate': '2026-02-15', 'NumLendingProducts': 0, 'NumDepositProducts': 1},
            ]
        return 0


@contextlib.contextmanager
def runtime():
    from freezegun import freeze_time
    # Replace the native driver, not DB.py: real query construction and report logic run.
    driver = types.ModuleType('pyodbc')
    def forbidden(*args, **kwargs):
        raise AssertionError('Contract tests must not perform external I/O')
    driver.connect = forbidden
    # Encryption imports are now side-effect-free and tested independently.
    with tempfile.TemporaryDirectory() as folder, contextlib.ExitStack() as stack:
        previous = Path.cwd()
        stack.callback(os.chdir, previous)
        os.chdir(folder)
        stack.enter_context(freeze_time('2026-07-15 12:00:00'))
        # patch.dict(sys.modules) replaces the whole module mapping on exit.
        # That unloads already-imported numpy modules while their native
        # extensions remain loaded, breaking the next contract test class.
        had_driver = 'pyodbc' in sys.modules
        old_driver = sys.modules.get('pyodbc')
        sys.modules['pyodbc'] = driver
        def restore_driver():
            if had_driver:
                sys.modules['pyodbc'] = old_driver
            else:
                sys.modules.pop('pyodbc', None)
        stack.callback(restore_driver)
        stack.enter_context(patch.dict(os.environ, {'JM_BASE_URL': 'https://fixture.invalid'}))
        stack.enter_context(patch.object(socket.socket, 'connect', forbidden))
        stack.enter_context(patch('time.sleep'))
        import DB
        # Imports can create local cache/upload folders, so import inside the sandbox.
        with contextlib.redirect_stdout(io.StringIO()):
            server = importlib.import_module('serve')
        stack.enter_context(patch.object(DB.SQLConn, 'connect', return_value=None))
        stack.enter_context(patch.object(DB.SQLConn, 'disconnect', return_value=None))
        # A Session may call only the transaction-search endpoint. Empty HTTP data
        # exercises the real parsing/no-transactions path without contacting JM.
        def jm_response(session, method, url, **kwargs):
            assert url.startswith('https://fixture.invalid/') and '/txnquery/listValues' in url, url
            response = types.SimpleNamespace(text='[]', status_code=200)
            response.json = lambda: []
            return response
        stack.enter_context(patch('requests.sessions.Session.request', jm_response))
        stack.enter_context(patch.object(server, 'get_cached_item', return_value=None))
        stack.enter_context(patch.object(server, 'set_cached_item'))
        stack.enter_context(patch.object(server, 'log_unique_url'))
        yield server, DB


def collect(consumers):
    # Every handler has a baseline; literal FE prop variants get their own cases too.
    variants = {name: [{}] for name in chart_names()}
    for c in consumers:
        if c['name'] in variants and c['params'] and c['params'] not in variants[c['name']]:
            variants[c['name']].append(c['params'])
    cases = []
    with runtime() as (server, DB):
        client = server.app.test_client()
        for name, options in variants.items():
            for option in options:
                for scenario in ['empty', 'populated']:
                    fixture = SqlFixture(scenario)
                    params = {**BASE_PARAMS, **option, 'start_date': '2026-01-01', 'end_date': '2026-03-31'}
                    responses = {}
                    def query(txn, sql, **kwargs):
                        return fixture.execute(txn, sql, **kwargs)
                    with patch.object(DB.Transaction, 'get_transactions_by_sql_query', query), contextlib.redirect_stdout(io.StringIO()):
                        # Both real route methods, each with and without formatting.
                        for method in ['GET', 'POST']:
                            for comma in ['false', 'true']:
                                req = {**params, 'showComma': comma}
                                if method == 'GET':
                                    req = {k: str(v).lower() if isinstance(v, bool) else v for k, v in req.items()}
                                    response = client.get('/charts/' + name, query_string=req)
                                else:
                                    response = client.post('/charts/' + name, json=req)
                                payload = response.get_json()
                                if response.status_code != 200:
                                    payload = {'error': payload.get('error'), 'chartName': payload.get('chartName')}
                                responses[f'{method}:{comma}'] = {'status': response.status_code, 'payload': payload}
                        # Resolve deferred SQL cells through the actual /query route.
                        deferred = {}
                        def visit(value):
                            if isinstance(value, str) and re.search(r'^\s*select\b', value, re.I):
                                if value not in deferred:
                                    r = client.post('/query', json={'query': value})
                                    deferred[value] = {'status': r.status_code, 'value': r.get_json() if r.is_json else r.get_data(as_text=True)}
                            elif isinstance(value, dict):
                                for k, v in value.items():
                                    if not k.startswith('_report_'): visit(v)
                            elif isinstance(value, list):
                                for v in value: visit(v)
                        visit(responses['POST:true']['payload'])
                    cases.append({
                        'id': name + ' | ' + scenario + ' | ' + json.dumps(option, sort_keys=True),
                        'name': name, 'scenario': scenario, 'params': option, 'responses': responses,
                        'deferred': deferred, 'query_count': len(fixture.queries),
                        'query_digest': digest(sorted(fixture.queries)), 'rowsets': sorted(set(fixture.rowsets)),
                    })
    return cases
