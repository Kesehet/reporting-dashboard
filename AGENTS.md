# Agent Guide for `reporting-dashboard`

This document captures the expectations for contributors working in this repository. It applies to the entire project tree because it lives at the repo root. Create additional `AGENTS.md` files in subdirectories if you need to refine instructions for specific areas.

## Repository overview

- **Frontend** – The `src/` directory contains a Create React App single-page application. Styling is split between `index.css` and component-level styles. Use `npm start`, `npm test`, and `npm run build` for local feedback.
- **Backend** – The `api-server/` package is a Flask service. It exposes REST endpoints (notably `/charts/<name>`) backed by Microsoft SQL Server queries executed via helper classes in `DB.py`.
- **Shared data model** – `api-server/report_modules/` holds reusable query fragments, post-processing helpers, and feature-specific chart builders.
- **Caching & coordination** – `api-server/cache_manager.py` controls file-system caching for expensive chart requests. `api-server/helper/chat_serve.py` provides concurrency locks so only one worker computes a chart at a time.

## General contribution guidance

1. **Respect the cache layer**. When you introduce long-running computations, cache the results through `set_cached_item` and reuse `get_cached_item` to avoid duplicate work.
2. **Keep SQL reusable.** Centralize repeated predicates inside `report_modules/condition_utils.py` instead of embedding magic strings in multiple places.
3. **Handle date parameters carefully.** All routes accept ISO `YYYY-MM-DD` dates. Validate inputs and rely on helpers such as `get_date_filter`, `monthsFromJanToPreviousMonth`, and similar constants to maintain consistency.
4. **Avoid modifying authentication plumbing unless absolutely necessary.** `serve.py` contains token / API key checks used by downstream systems.
5. **Linting / testing.** There is no enforced linter configured, but you should run targeted checks (`npm test` for the frontend, appropriate Python unit or smoke tests) before raising a PR.

## Working with `api-server/charts.py`

`api-server/charts.py` is the heart of the reporting backend. Each chart definition lives in a dedicated `if/elif` block within the `getChartData` dispatcher.

- **Entry point signature**: `getChartData(name, transactions, start_date, end_date, request=None, params=None)` receives a `Transaction` instance for executing SQL via `transactions.get_transactions_by_sql_query(...)`. Always pass the existing `transactions` object rather than opening a new connection.
- **Chart helpers**: Use `getPieChart`, `getBasicTable`, and `getLineChart` to normalize response shape. Prefer returning simple dictionaries with `labels`, `list`, `datasetMap`, `headers`, and `rows` keys—this keeps the frontend consuming API stable.
- **Filters**:
  - Call `params = get_request_dict(request)` when `params` is `None` to normalize GET vs POST payloads.
  - Honor the `application_type` filter when present (`application_type_condition`) and rely on `CorBFilter` plus other helpers from `condition_utils` to build `WHERE` clauses.
  - Date ranges must respect the `start_date` / `end_date` arguments; leverage `get_date_filter(start_date, end_date)` or existing constants to avoid off-by-one issues.
- **String interpolation**: Queries are assembled with f-strings using values defined in `condition_utils.py`. Only interpolate sanitized or whitelisted parameters (e.g., values returned by `CorBFilter`). Never insert raw user input.
- **Adding a new chart**:
  1. Add an `elif name == "..."` block in `getChartData` following the structure of similar charts.
  2. Reuse predicates/constants from `condition_utils.py`. Introduce new constants there if a predicate will be shared in multiple charts.
  3. Return a serializable object composed of primitive types (no custom classes) so caching and JSON encoding work without modification.
  4. If the chart should be pre-cached, append its name to `LIST_OF_CHARTS` in `condition_utils.py`.
- **Supporting utilities**: `get_request_dict(request)` (defined at the bottom of the file) unifies payload parsing between GET and POST. Avoid duplicating request parsing logic elsewhere.
- **Performance awareness**: Some charts execute dozens of sequential queries. When expanding functionality, group related queries and reuse intermediate results when possible. Prefer `transactions.get_transactions_by_sql_query` for single-value queries and `transactions.get_transactions_by_sql_query_multiple` (if available) for batch operations.
- **Testing expectations**: After modifying `charts.py`, exercise the target chart via the `/charts/<name>` endpoint (using curl or Postman) to verify JSON structure and performance. If you change cache behavior, clear `.cache_requests/` during development to avoid stale data.

## Coordination with other modules

- `api-server/serve.py` handles routing, auth, and cache orchestration. Any change to chart inputs or cache keys must remain compatible with `_chart_key` and `_acquire_or_wait_for_slot` in `helper/chat_serve.py`.
- `api-server/cache_manager.py` relies on `getChartData` to warm caches. Ensure new chart names are discoverable if you expect them to be pre-computed.
- `api-server/report_modules/` houses specialized logic (BOR, abandonment, monthly reports, etc.). When implementing complex chart logic, consider delegating to a helper function inside this package rather than inflating `charts.py` further.

Keep this guide updated whenever you add new architectural patterns or conventions.
