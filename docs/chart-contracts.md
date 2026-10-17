# Chart response regression and frontend compatibility tests

Run the suite from the repository root:

```bash
python -m pip install -r tests/contracts/requirements.txt
npm ci --no-audit --no-fund
npm run test:charts
```

The `Chart response contracts` GitHub Actions workflow runs on pushes, pull
requests, and manual dispatch. Each run uploads `chart-contract-results` and
publishes a summary, including existing issues even when regression checks pass.

## Coverage

- Discover all 102 names from the real `getChartData` dispatcher using Python AST.
- Discover 98 distinct frontend endpoint names from JSX props, default report
  props, and literal `ChartDataService` calls using Babel AST. Reject frontend
  names without backend handlers. Four legacy backend endpoints have no current
  static frontend reference; their responses are still tested.
- Run 274 cases: empty and populated fixtures for every endpoint, plus literal
  frontend parameter variants (started/submitted/approved, balance selection,
  mixed-chart options, table summary options, etc.).
- Exercise the actual Flask chart route with GET and POST, both numeric and
  default comma-formatted output: 1,096 chart requests per run.
- Capture and resolve deferred table SQL through the actual `/query` route and
  the existing frontend `getCellData` function.
- Run every successful response through its actual frontend chart converter or
  payload normalizer, and validate positional table/row-set contracts. Preserve
  object-row contracts for branch report/tile components.
- Check series lengths, finite numeric values, label order, table widths,
  response serialization, and key preservation. Negative controls demonstrate
  that invalid series, NaN values, and extra table cells are detected.
- Additional HTTP tests cover invalid/missing dates, unknown names, GET/POST
  parity, exact numeric/comma conversion, zero values, leap-day and cross-year
  date ranges, and propagation of tracking filters. The 11 existing Python
  regression tests also run inside the isolated test environment.

## What is replaced

The real chart builders, report modules, query construction, Flask routes,
formatting functions, frontend request service, and chart adapters execute.
Only external I/O is replaced: SQL execution/connection, Journey Manager HTTP,
and chart-cache persistence. Native ODBC is a fail-fast stand-in so CI needs no
SQL Server driver or credentials. Unrelated ETL encryption is a fail-fast
stand-in because its module runs a crypto/filesystem demo at import time; no
chart under test uses it. Any unexpected network access fails.

The SQL fixture follows `Transaction`'s actual convention: a missing result is
`0`, not an invented empty list. Aggregate values differ between product types,
and explicit rowsets cover transactions, product counts/IDs, daily products,
branches, and the eDelivery aggregate/union reports. Other rowset queries stay
empty. This is **not** a SQL engine or a claim to reproduce production totals.
Journey Manager cases currently exercise its empty response, not a populated
transaction/XML integration.

Time is frozen at July 15, 2026, requests use January–March 2026, and the runner
pins Python's hash seed because existing SQL builders use unordered sets.
Concurrent query completion order is excluded from the SQL fingerprint; query
text and counts remain covered. Responses, including embedded SQL, have reviewed
SHA-256 baselines. Full wire responses and `/query` replies are available as
per-case compressed JSON artifacts, not committed production data.

## Existing findings retained for review

The suite intentionally preserves working application behavior. No chart SQL,
business calculation, response shape, authentication, or UI behavior was changed.
`CardReport` only gains a named export for its existing normalizer.

Four handlers have reproducible no-data failures with the real `DB.py` empty
result convention: `Multi Products Product Set Id Bar`, `Monthly In Branch vs
BPM and CRIF Report`, `E-Delivery Report Insights`, and `Business Account Summary
Top 10 Products Table`. Five scenarios currently return HTTP 500; the exact
endpoint/scenario/error is enumerated in the runner. New errors or a changed
known error fail the run.

Frontend checks currently flag 27 scenarios across 12 handlers. They include
quarterly/funding table column counts, funding/loan series lengths, abandonment
label/value counts, a decline bar response without labels, the legacy cross-sell
top-level array, and ragged LOB table rows. Some grouped report rows may be
intentional presentation conventions; review the actual artifact/UI before
changing them. One-cell section headings are explicitly supported by the checks.

Existing frontend mismatches are listed individually in
`tests/contracts/frontend-known-issues.json`. They remain visible in every run's
summary; they are not silently skipped or claimed to be correct. Any new
mismatch or repaired mismatch fails until its expectation is explicitly reviewed.
A green check therefore means **no new regression against this baseline**, not
that every chart is bug-free. Live SQL/Journey Manager data and full browser
rendering remain outside this suite.

## Reviewing intentional changes

Inspect `contract-results/backend-observed.json`, `frontend-observed.json`,
`summary.md`, and the per-case response artifacts before accepting any change.
To explicitly update the baseline after review:

```bash
python scripts/run_chart_contracts.py --accept-baseline
ACCEPT_CHART_BASELINE=1 npm run test:chart-frontend
```

Then review the baseline diff and rerun `npm run test:charts` without acceptance
flags. CI never passes acceptance flags. Do not update a baseline merely to turn
an unexplained failure green. The older UI tests with stale authentication/xlsx
mocks are outside this chart-focused workflow and have not been declared fixed.
