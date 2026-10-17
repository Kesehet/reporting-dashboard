#!/usr/bin/env python3
"""Generate real backend responses for the frontend suite; verify reviewed baselines."""
import argparse
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys

# Existing builders use set() for SQL columns. Pin the hash seed before imports
# so a baseline does not change with process hash randomization.
if os.environ.get('PYTHONHASHSEED') != '0':
    os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]], {**os.environ, 'PYTHONHASHSEED': '0'})

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests' / 'contracts'))
from runtime import chart_names, collect, digest

BASELINE = ROOT / 'tests/contracts/backend-baseline.json'
OUT = ROOT / 'contract-results'

# These are observed defects in existing code, not successful contracts. Any new
# error, changed error, or repaired error fails until explicitly reviewed here.
KNOWN_ERRORS = {
    ('Multi Products Product Set Id Bar', 'empty'): "'int' object is not iterable",
    ('Monthly In Branch vs BPM and CRIF Report', 'empty'): 'list index out of range',
    ('E-Delivery Report Insights', 'empty'): "object of type 'int' has no len()",
    ('Business Account Summary Top 10 Products Table', 'empty'): "'int' object is not iterable",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--accept-baseline', action='store_true', help='Explicitly record a reviewed baseline; never used by CI')
    args = parser.parse_args()
    consumers = json.loads(subprocess.check_output(['node', str(ROOT / 'scripts/chart-consumers.cjs')], cwd=ROOT))
    names = chart_names()
    assert len(names) == len(set(names)), 'Duplicate backend dispatch names'
    assert {c['name'] for c in consumers} <= set(names), 'Frontend references unknown chart handlers'
    cases = collect(consumers)
    OUT.mkdir(exist_ok=True)
    (OUT / 'cases').mkdir(exist_ok=True)
    expected, index, issues, failures = {}, [], [], []
    for i, case in enumerate(cases):
        responses = case['responses']
        for key, r in responses.items():
            known = KNOWN_ERRORS.get((case['name'], case['scenario']))
            if r['status'] != 200:
                if r['status'] != 500 or r['payload'].get('error') != known:
                    failures.append(f"{case['id']} {key}: unexpected backend error {r}")
            elif known:
                failures.append(f"{case['id']}: known defect now succeeds; review and remove its allowance")
        if responses['POST:false']['status'] != 200:
            issues.append({'case': case['id'], 'kind': 'backend-error', 'detail': responses['POST:false']['payload']['error']})
        # No approval flag can accept newly introduced HTTP failures.
        expected[case['id']] = {
            'responses': {k: {'status': v['status'], 'sha256': digest(v['payload'])} for k, v in responses.items()},
            'queries': case['query_count'], 'query_sha256': case['query_digest'],
            'deferred_queries': len(case['deferred']), 'rowsets': case['rowsets'],
        }
        # Smaller independent files keep Jest memory bounded. Retain actual SQL cells
        # and /query responses so the frontend resolver is exercised, not reimplemented.
        front = {k: case[k] for k in ['id', 'name', 'scenario', 'params', 'deferred']}
        front['response'] = responses['POST:true']
        front['rawResponse'] = responses['POST:false']
        filename = f'{i:03d}.json.gz'
        with gzip.open(OUT / 'cases' / filename, 'wt', encoding='utf-8') as f:
            json.dump(front, f, allow_nan=False)
        index.append({'id': case['id'], 'name': case['name'], 'scenario': case['scenario'], 'file': filename})
    inventory = {'backend_handlers': names, 'consumers': consumers, 'cases': index}
    (OUT / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    (OUT / 'backend-issues.json').write_text(json.dumps(issues, indent=2) + '\n')
    (OUT / 'backend-observed.json').write_text(json.dumps(expected, indent=2) + '\n')
    if args.accept_baseline:
        if failures:
            raise AssertionError('\n'.join(failures))
        BASELINE.write_text(json.dumps(expected, indent=2) + '\n')
    else:
        baseline = json.loads(BASELINE.read_text())
        if set(baseline) != set(expected):
            failures.append(f'Chart case inventory changed: added={set(expected)-set(baseline)}, removed={set(baseline)-set(expected)}')
        for key in expected.keys() & baseline.keys():
            if expected[key] != baseline[key]:
                failures.append(f'{key}: response or query baseline changed (see backend-observed.json)')
    summary = f'{len(names)} backend handlers; {len({c["name"] for c in consumers})} frontend endpoint names; {len(cases)} scenarios; {len(cases)*4} HTTP chart requests; {len(issues)} known failing scenarios.'
    print(summary)
    (OUT / 'summary.md').write_text('# Chart response contract results\n\n' + summary + '\n\nKnown backend errors are listed in `backend-issues.json`; they are not passing response contracts.\n')
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
