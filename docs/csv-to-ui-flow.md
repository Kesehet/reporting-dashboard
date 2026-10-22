# CSV to UI Data Flow in eStore

This document describes the full end-to-end path for transaction data in the eStore system. It covers how CSV/XLS files are detected, read, cleansed, mapped, stored, and finally returned to the UI for chart rendering.

## 0. High-Level Flow Diagram

```mermaid
flowchart LR
  A[Upload file into uploads/reports] --> B[csvLoader.get_csv() scans folder]
  B --> C[ctrl.conf check skips processed files]
  C --> D[read_file() reads CSV/XLS with encoding fallback]
  D --> E[prepare_rows() normalizes account number and DataSource]
  E --> F[core_process() sorts rows and groups by tracking code]
  F --> G[Transaction.set_transaction_from_list_of_dicts() maps and loads rows]
  G --> H[SQL Server Transactions table stores cleaned data]
  H --> I[serve.py /charts/<name> queries Transactions for charts]
  I --> J[Frontend renders charts and tables]
```

## 1. Data Arrival and Monitoring

### 1.1 Where files are stored
- Uploaded files are placed in `uploads/reports`
- Accepted formats:
  - `*.csv`
  - `*.xlsx`
  - `*.xls`
- The CSV loader logic lives in `api-server/csvLoader.py`

### 1.2 How incoming files are discovered
- The entry point is `csvLoader.get_csv(folder_path="uploads/reports")`
- It lists files in the folder and filters on extensions: `.csv`, `.xlsx`, `.xls`
- The function runs only when `AUTO_UPDATE_CSV` is enabled in environment configuration:
  - `true`
  - `True`
  - `1`
- If this setting is disabled, `get_csv()` immediately returns the message:
  - "Enable AUTO_UPDATE_CSV to run csv loader"

### 1.3 Preventing duplicate processing
- A control file named `ctrl.conf` is used to record file names that have already been processed
- `file_exists_in_conf(file_name, folder_path)` reads this file and returns `True` if the file name exists
- `update_conf(file_name, folder_path)` appends new files after successful processing
- This ensures each file is processed only once

### 1.4 Operational logging and monitoring
- Each run writes a status log using `csvLoader.log_file(ret, csv_file, folder_path)`
- Logs are stored in `uploads/reports/logs`
- The log includes:
  - filenames processed
  - files skipped because they already existed in `ctrl.conf`
  - files that could not be found
  - files with no rows
  - SQL execution success/failure messages
- This log is saved as HTML so it can be reviewed in a browser

## 2. Reading and Parsing the File

### 2.1 File format detection
- `read_file(file_path)` detects file type by extension
- CSV files are processed with `pandas.read_csv()` first
- Excel files are processed with `pandas.read_excel()` if the extension is `.xlsx` or `.xls`
- If a CSV cannot be read with common encodings, a fallback to Excel parsing also runs

### 2.2 Encoding fallback strategy
- The loader tries multiple encodings in sequence:
  - `utf-8`
  - `utf-16`
  - `latin-1`
  - `windows-1252`
  - `iso-8859-1`
  - `cp1252`
  - `utf-8-sig`
- If all specified encodings fail, `detect_encoding(file_path)` reads the first 10KB of raw bytes and uses `chardet.detect()` to infer encoding
- Finally, it attempts `pandas.read_csv()` with the detected encoding

### 2.3 Handling parse failures
- Parse errors are caught and do not raise directly to the user
- If `read_csv()` fails due to parser errors or Unicode issues, it tries `read_excel()` before giving up
- If parsing ultimately fails, `read_file()` returns an empty DataFrame

### 2.4 Converting file contents into rows
- `prepare_rows(file_path)` reads the file into a DataFrame
- If the DataFrame is empty, it returns an empty list immediately
- Otherwise, it iterates over each row in the DataFrame using `df.iterrows()` and converts rows into a plain Python row object

### 2.5 Enriching rows with metadata
- For every row, `prepare_rows()` adds two fields:
  - `DataSource`: the source filename of the uploaded document
  - `AccountNumber`: a normalized account number value produced by `utils.process_account_number(row.get("Product Account Number", ""))`
- This helps with downstream reporting and identification of the source file

## 3. Validation and Pre-processing

### 3.1 Initial file validation
- Files are validated before processing continues
- If the file does not exist on disk, `get_csv()` logs a "File not found" message and skips further work for that file
- If the file has no rows, `get_csv()` logs "No rows found in file" and does not add the file to `ctrl.conf`

### 3.2 Duplicate and control-file filtering
- If the file name already exists inside `ctrl.conf`, the file is skipped entirely
- This is checked before row preparation begins
- Files are only written into `ctrl.conf` after successful row processing and database operations

### 3.3 Splitting rows by business/consumer tracking code
- After rows from all files are loaded, they are split into two groups:
  - rows where `eCA Tracking Code` starts with `B`
  - rows where `eCA Tracking Code` starts with `C`
- This is performed in `csvLoader.get_csv()` before calling `core_process()`
- The split allows separate handling for business and consumer transaction types

### 3.4 Sorting before batched processing
- `core_process(all_rows, sql, txn)` sorts rows by `eCA Tracking Code` in descending order
- This sorting ensures a predictable insertion/update order when batching rows into SQL commands

## 4. Field Mapping and Data Transformation

### 4.1 Mapping CSV columns to database columns
- The column translation map is defined in `api-server/report_modules/condition_utils.py` under `CSV_TO_SQL_COLUMNS`
- This is the exact mapping used by `DB.Transaction.set_transaction_from_list_of_dicts()`
- Example mappings:
  - `"eCA ID"` → `eCAID`
  - `"eCA Tracking Code"` → `eCATrackingCode`
  - `"Primary Name"` → `PrimaryName`
  - `"Primary SSN"` → `PrimarySSN`
  - `"Number of Lending Products"` → `NumLendingProducts`
  - `"Product Account Number"` → `AccountNumber`

### 4.2 Handling business-specific CSV columns
- For rows whose `DataSource` filename contains `business`, the loader remaps certain fields:
  - `Primary Name` becomes `Business Name`
  - `Primary SSN` becomes `Business TIN`
- This alternate mapping is created at runtime and used only for business file payloads

### 4.3 Normalizing dates
- Date columns are normalized in the insert loop inside `set_transaction_from_list_of_dicts()`
- The date fields normalized are:
  - `AppStartDate`
  - `AppSubmitDate`
  - `AppUpdateDate`
- If these values are present and not blank, they are parsed with `dateutil.parser.parse(value)` and formatted as `YYYY-MM-DD HH:MM:SS`
- This ensures SQL Server receives dates in a consistent format

### 4.4 Sanitizing text fields
- `DeclineReason` is cleaned by replacing line breaks and escape sequences:
  - `\n` → ` `
  - `\r` → ` `
- Text values are stripped of single quotes by replacing `'` with `''` to prevent SQL syntax issues
- Empty strings and literal `NULL` values are converted into SQL `NULL`

### 4.5 Converting numeric and ID fields
- The loader validates numeric fields such as:
  - `BranchID`
  - `NMLS_Id`
  - `EmployeeResponsibilityCode`
  - `NumDepositProducts`
  - `NumLendingProducts`
  - `NumCoApplicant`
- If these fields are present but not numeric, the loader converts them to `NULL`
- For `CustomerID`, the loader explicitly sets the value to `'0'`

### 4.6 Account number normalization
- `AccountNumber` is built from `Product Account Number`
- The helper function `utils.process_account_number()` returns a cleaned list of account numbers
- The loader then joins them with `'|'` to create a normalized string
- This provides a deterministic account identifier when the CSV field contains multiple or complex values

## 5. Duplicate Detection and Filtering

### 5.1 Tracking duplicates within a run
- `set_transaction_from_list_of_dicts()` maintains a `seen_tracking_codes` set
- If a row's `eCA Tracking Code` has already been processed in the current batch, the row is skipped
- This protects against duplicate rows in the same file or across files processed in the same run

### 5.2 Skipping invalid rows
- Rows are skipped if:
  - `eCA Tracking Code` is missing, blank, or `NaN`
  - `Primary Name` matches the ignore rules in `PRIMARY_NAME_IGNORE`
  - `Primary Name` contains the string `test`
- A human-readable log entry is created for each skipped row

### 5.3 Existing record detection
- The loader obtains existing tracking codes via `self.get_eCATrackingCodes()`
- If a row’s tracking code already exists in the database, the row is prepared as an UPDATE instead of INSERT
- This allows incremental updates without duplicating existing transactions

## 6. PII and Environment-Specific Privacy Rules

### 6.1 Development and QA masking
- The loader checks `CURRENT_ENV` from environment configuration
- If the environment is `dev` or `qa`, the loader masks sensitive data before writing:
  - `PrimarySSN` is overwritten with `NULL`
  - `PrimaryName` is Base64-encoded with `base64.b64encode()`
- This reduces the risk of exposing Personally Identifiable Information in non-production environments

### 6.2 PII column definitions
- `PII_COLUMNS` in `condition_utils.py` lists sensitive fields such as:
  - `PrimaryName`
  - `PrimarySSN`
  - `DDS Account Last4`
- Although only `PrimarySSN` and `PrimaryName` are transformed in the CSV loader, the list documents the fields of interest

## 7. Database Connection and Table Schema

### 7.1 Connection details
- `api-server/DB.py` contains the `SQLConn` class
- It builds the connection string using environment values:
  - `SQL_HOST`
  - `SQL_DATABASE`
  - `SQL_USER` (not used in trusted connection mode)
- The driver used is `ODBC Driver 17 for SQL Server`
- Connection settings include:
  - `Trusted_Connection=Yes`
  - `Integrated Security=Yes`
  - `ColumnEncryption=Enabled`

### 7.2 Schema management
- `SQLConn.setup()` can create the `Transactions` table if it does not exist
- It uses `TABLE_STRUCTURE` from `api-server/report_modules/condition_utils.py`
- The table definition includes typed fields such as:
  - `NVARCHAR(MAX)` for text columns
  - `DATETIME` for date/time fields
  - `FLOAT` and `DECIMAL` for numeric values
  - `INT` for integer counts
- Schema migration logic also checks existing columns and attempts ALTER TABLE when a new column is added to `TABLE_STRUCTURE`

### 7.3 Main target table
- The table is referenced as `TABLE_NAME = "[DigitalReport].[dbo].[Transactions]"`
- All CSV inserts and updates write to this table
- The same table is later read by the charting and reporting layer

## 8. Insert and Update Execution

### 8.1 Preparing SQL statements
- For each row, the loader produces a list of SQL values aligned with `sql_columns_list`
- It generates a partial SQL row string such as:
  - `(value1, value2, value3, ...)`
- Insert strings are collected into `insert_statements`
- Update strings are collected into `update_statements`

### 8.2 SQL insert batching
- The loader assembles inserts into batches using `batch_sizer = 999`
- Each batch becomes one large `INSERT INTO Transactions (...) VALUES ...` statement
- The list of row tuples is joined with commas for a single batched insert
- Batching improves performance compared to one-row inserts

### 8.3 Update strategy
- Updates are generated for existing records only
- The loader includes only non-empty columns in the `SET` clause
- Updates are executed sequentially, one statement at a time
- This balances correctness with the need to preserve already-stored data

### 8.4 Error handling during SQL execution
- Each batched insert and update is executed inside a try/except block
- If a SQL error occurs, the loader captures the exception message
- The failure is written to the HTML run log with a red error entry
- The loader continues processing remaining batches after errors

### 8.5 Final report from `set_transaction_from_list_of_dicts()`
- After all insert and update statements run, the function returns a status string
- The status string includes:
  - the number of rows executed
  - the SQL queries that were run
  - any errors encountered
- This status is appended to the overall loader log

## 9. Post-Processing After Load

### 9.1 Business rule post-processing
- `csvLoader.get_csv()` calls `post_process_txns(sql, txn)` after core insertion/update processing
- This function applies additional business logic to normalized transaction records
- It may update aggregated fields, correct data issues, or compute derived values

### 9.2 Journey Manager XML enrichment
- `update_JMExtracts(sql, txn)` runs after the main CSV load
- It performs the following:
  1. Calculates a date range from 15 days ago to today
  2. Builds a date filter through `get_date_filter()`
  3. Queries distinct `eCATrackingCode` values from the `Transactions` table
  4. Filters out codes already present in the `JMExtract` table
  5. Calls `update_JMExtract(sql, code)` for each remaining code
- This step enriches transaction data with external Journey Manager XML extract details

### 9.3 Metrics logging
- The function `update_metrics()` is called with keys such as `manual_xml_pull`
- Metrics are recorded when JM extract processing starts and ends
- These metrics can be used for monitoring how often XML enrichments run

## 10. Persistence and Control

### 10.1 Control file behavior
- The control file `uploads/reports/ctrl.conf` is used as a simple state store
- Each processed file name is appended once the file is successfully consumed
- If the loader crashes or a file has zero rows, the file is not added to `ctrl.conf`

### 10.2 Run log details
- `csvLoader.log_file()` creates a log file under `uploads/reports/logs`
- The log file name is derived from the run identifier, sanitized by replacing `:` with `-`
- The HTML log can contain:
  - `File already processed`
  - `File not found`
  - `No rows found`
  - the exact SQL INSERT or UPDATE string attempted
  - error messages returned by the database
- Logs are useful for debugging failed or partial loads

## 11. Retrieving Data for the UI

### 11.1 Chart API endpoint
- The frontend uses the endpoint `GET /charts/<name>` in `api-server/serve.py`
- Supported request methods are GET and POST
- Required query/body parameters:
  - `start_date`
  - `end_date`
- Optional parameters include:
  - `authorization`
  - filter parameters used by `get_request_dict()`

### 11.2 Authorization and security
- API access is controlled by either:
  - `Authorization` header token
  - `X-API-KEY` header (required for API-key clients)
- URL and JSON body `api_key` parameters no longer authenticate requests.
- If a token is present, the request is verified by `verify_token(token)`
- If no login token exists, the `X-API-KEY` header is checked against `ALL_FILTERS_CHART_API_KEY`
- Unauthenticated requests are rejected with a `401` or `400` error

### 11.3 Caching logic
- The route first checks `get_cached_item(name, start_date, end_date, params)`
- If a cached response exists, the endpoint returns it immediately
- If not, the request obtains an in-flight lock via `_acquire_or_wait_for_slot(key)`
- This prevents duplicate concurrent chart computation
- Once chart computation completes, `set_cached_item(resp, name, start_date, end_date, params)` stores the result

### 11.4 Chart computation
- Chart data is generated by calling `getChartData(name, transactions, start_date, end_date, params=params)`
- `transactions` is an instance of `DB.Transaction` created from a fresh `SQLConn`
- `getChartData()` translates chart name and filter parameters into SQL queries against `[DigitalReport].[dbo].[Transactions]`
- Query results are aggregated, formatted, and returned as JSON

### 11.5 Response formatting
- If the `showComma` parameter is set to `true`, `format_numbers_recursive(resp)` will format numeric values
- For insight reports with `return_format=csv`, `insight_report_to_csv_response(params, resp, transactions)` may return a CSV payload
- The endpoint always attempts to return structured JSON or CSV for the requested report

### 11.6 Other data endpoints
- `POST /query` allows raw SQL queries via `txn.get_transactions_by_sql_query(query)`
- Administrative endpoints exist for cache management:
  - `/generate_cache`
  - `/clear_cache`

## 12. UI Rendering and User Experience

### 12.1 Frontend data consumption
- The React frontend loads chart data by calling backend chart endpoints
- The JSON returned includes labels, series values, counts, and aggregate results
- The UI uses this JSON to render:
  - bar charts
  - line charts
  - pie charts
  - tabular reports

### 12.2 Dashboard use cases
- Common dashboard visuals are generated from transaction data such as:
  - application volume by product
  - approval and decline rates
  - branch-originated applications
  - monthly business deposit reports
  - abandonment reports
- All of these are sourced from the same `Transactions` table created during the CSV load

### 12.3 Authentication flow
- Users authenticate through endpoints in `api-server/serve.py`
- Once authorized, the frontend includes tokens in chart requests
- The backend verifies tokens before returning protected chart data

## 13. Full End-to-End Example Flow

1. A file named `reports_20260518.csv` is uploaded into `uploads/reports`
2. `csvLoader.get_csv()` runs and detects the new file
3. `file_exists_in_conf()` confirms it is not already processed
4. `read_file()` reads the file with encoding fallback and returns a DataFrame
5. `prepare_rows()` converts DataFrame rows to Python row objects and adds `DataSource` and `AccountNumber`
6. The loader groups rows into `B` and `C` tracking-code buckets
7. `core_process()` sorts rows and calls `txn.set_transaction_from_list_of_dicts(sql, rows)` for each bucket
8. Each row is mapped from CSV headers to SQL column names
9. Dates, text, numeric values, and PII fields are normalized and sanitized
10. New rows are batched into INSERT statements; existing rows generate UPDATE statements
11. SQL statements are executed against the `Transactions` table
12. The run log file is created under `uploads/reports/logs`
13. `post_process_txns()` applies business rules and cleans additional data
14. `update_JMExtracts()` pulls XML extract data for newly loaded tracking codes
15. The file name is appended to `uploads/reports/ctrl.conf`
16. Later, the frontend requests `/charts/Application%20Volume%20By%20Product` with date filters
17. The backend either returns cached chart data or computes fresh results from `Transactions`
18. The frontend renders the chart and table data for the user

## 14. Key Files to Review
- `api-server/csvLoader.py` — CSV ingestion, encoding detection, row preparation, logging, and load orchestration
- `api-server/DB.py` — SQL Server connection, `Transactions` schema management, insert/update logic
- `api-server/report_modules/condition_utils.py` — column mappings (`CSV_TO_SQL_COLUMNS`), schema definition (`TABLE_STRUCTURE`), filters, and constants
- `api-server/serve.py` — frontend API endpoints, chart request flow, caching, and authorization
- `api-server/charts.py` — chart data generation and SQL aggregation logic


## 15. Notes and Improvement Opportunities
- The current ingestion flow is file-driven, not event-driven; a file watcher or API upload endpoint could provide better reliability
- Deduplication relies on `eCATrackingCode`; if two distinct transactions share the same code, one may be ignored
- Existing update logic merges only non-empty values, which is safe but can hide cases where a user wants to explicitly clear a value
- PII masking in dev/qa is helpful, but production should still consider encryption-at-rest or field-level encryption
- Query performance depends on the `Transactions` table schema and indices; adding targeted indexes may improve chart query speed

---

This document is intended to explain the detailed CSV ingestion, transformation, storage, and UI delivery flow for the eStore application.
