#!/usr/bin/env python3
"""Append an honest compatibility summary to the CI report."""
import json
import os
from pathlib import Path
from collections import defaultdict

out = Path(__file__).resolve().parents[1] / 'contract-results'
issues = []
for name in ['backend-issues.json', 'frontend-issues.json']:
    p = out / name
    if p.exists():
        issues += json.loads(p.read_text())
by_chart = defaultdict(set)
for issue in issues:
    name = issue['case'].split(' | ')[0]
    if issue['kind'] == 'backend-error':
        by_chart[name].add('Backend: ' + issue['detail'])
    else:
        for detail in issue['detail']:
            by_chart[name].add('Frontend: ' + detail.replace('rawResponse:', '').replace('response:', ''))
report = out / 'summary.md'
text = report.read_text() if report.exists() else '# Chart response contract results\n'
text += '\n## Existing compatibility findings\n\n'
text += 'A passing run means no unreviewed regression against the recorded baseline. It does **not** mean every chart is correct. The following existing issues are still present. SQL fixtures do not validate real SQL Server results or live business totals.\n\n'
text += '| Chart | Existing finding |\n|---|---|\n'
for name, details in sorted(by_chart.items()):
    text += '| ' + name.replace('|', '/') + ' | ' + '; '.join(sorted(details)).replace('|', '/') + ' |\n'
report.write_text(text)
if os.getenv('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
        f.write(text)
print(f'Compatibility findings: {len(by_chart)} charts. See contract-results/summary.md.')
