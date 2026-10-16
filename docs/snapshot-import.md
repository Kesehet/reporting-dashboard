# October 2026 source refresh

The application source, frontend assets, dependency manifests, build scripts,
documentation, and tests were imported from the supplied `api-server.zip`.
The ZIP contains the whole project; its contents belong at the repository root,
not inside an additional `api-server` directory.

## Import scope

- Updated `src/`, `public/`, and `api-server/` to the supplied application snapshot.
- Removed six application files absent from the ZIP: `api-server/Address.py`,
  `api-server/User.py`, `api-server/role_filter.py`,
  `src/Components/reportLoginComponent.jsx`,
  `src/Services/AuthorizationService.jsx`, and `src/Services/msalInstance.jsx`.
  The supplied application no longer imports these files.
- Preserved the repository's `AGENTS.md`, `handbook.md`, and `py_build.bat`.
  The handbook is historical documentation and may describe older behavior.
- Excluded `.env`, `enc.key`, request caches, coverage reports, generated logs,
  metrics, CSV output, editor project metadata, local build configuration, and
  the ignored `api-server/temp.py` scratch script.
- Included the supplied frontend tests and their mocks by removing the
  `*__test__*` ignore rule. Build output and old encryption keys are now ignored.
- Converted `requirements.txt` from UTF-16 to UTF-8 without changing its package
  pins, and replaced the BOM/comment header in `py_build.sh` with a Bash shebang.

## Local configuration

Copy `.env.example` to `.env` at the project root and supply your environment's
values. The template preserves configuration names only, with every value empty.
Credentials and encryption keys remain local. Existing encrypted data requires
the corresponding original encryption key; this import does not rotate it.

## Validation

Checked with Node.js 24 and Python 3.12 in the import environment:

- `npm ci --no-audit --no-fund`: passed.
- `npm run build`: passed with existing ESLint warnings from the snapshot.
- Python syntax parsing: passed for all imported Python source files.
- `bash -n py_build.sh`: passed.
- `python -m unittest discover -s tests -p test_account_number.py -v`: all three
  tests passed.
- `CI=true npm run test:nocov -- --runInBand`: failed on supplied test fixtures.
  The table test mocks an uninstalled `xlsx` package; the header test imports the
  removed `AuthorizationService`; the App test mocks the header's menu factory
  as a React element, causing `items.map` to fail. An asynchronous chart fixture
  also lacks `datasetMap`. These were retained for a separate test repair.
- Full Python test discovery was blocked by missing backend dependencies in the
  execution environment (`pyodbc` first). No live SQL Server or Journey Manager
  integration tests were performed.

The supplied `tests.sh` sends database-mutating requests with `clear_db: true`;
it is a manual integration script, not the unit-test command, and was not run.
The source refresh is not a claim that the application test suite or deployment
has passed end to end.
