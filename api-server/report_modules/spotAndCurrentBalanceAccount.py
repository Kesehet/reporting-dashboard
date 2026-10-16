from report_modules.condition_utils import APPROVED_APPS_STATUSES, get_date_filter, application_type_filter
from DB import get_EDW, SQLConn, Transaction, Q
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils import *


def get_insights(start_date,end_date,params):
    resp = get_responses(start_date,end_date)
    return {
        "Spot and Current Balance Report": len(resp),
        "_report_Spot and Current Balance Report": resp
    }
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from collections import defaultdict
from functools import lru_cache

# -------------------- Helpers (unchanged API-compatible behavior) --------------------

def find_first_fnb_account_number(data):
    """
    Depth-first scan for the first 'FnbAccountNumber' key in arbitrarily nested dict/list JSON.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "FnbAccountNumber" and value is not None:
                return value
            result = find_first_fnb_account_number(value)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_first_fnb_account_number(item)
            if result is not None:
                return result
    return None


def format_amounts(amt):
    amt_in_millions = amt / 1_000_000
    return f"$ {amt_in_millions:,.2f}"


def in_between_sql_condition(interval):
    # NOTE: replaced HTML entities with proper operators
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"




# -------------------- Internal utilities for batching & caching --------------------

def _chunked(iterable, size=1000):
    """
    Yield chunks of the iterable for IN(...) batching.
    Default chunk size chosen conservatively for SQL Server (parameter limit 2100).
    """
    buf = []
    for item in iterable:
        buf.append(item)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


def _normalize_int_account(accNo, code_for_log=None):
    """
    Normalize account number to int or return None.
    """
    if accNo is None or accNo == "":
        return None
    try:
        return int(str(accNo).strip())
    except Exception:
        print(f"Error Account number not int. ({accNo}) at {code_for_log}")
        return None


def _safe_select_list(items, is_numeric=True):
    """
    Convert a list/set of items into a SQL-friendly comma-separated list.
    If numeric, no quotes. If string, single-quote each, and escape single quotes.
    """
    if is_numeric:
        return ",".join(str(int(x)) for x in items if not (x == "None" or x is None or x == "") )
    return ",".join("'" + str(x).replace("'", "''") + "'" for x in items)


# -------------------- Optimized SQL + Python paths --------------------

def get_responses(start_date, end_date, amount_table="CAM_DDA_ACCT_CUR", amount_column="DDA_ACCT_NUM", where_clauses=False):
    """
      - Single query to DigitalReport to fetch all rows for the date window.
      - Parse JSON RawData once for account numbers.
      - Single batched IN lookup to CAMEDW per call to resolve balances.
      - Returns a list of dicts (same shape as before).
      - If no tracking codes, returns {'error': 'No tracking code found.'} (same as before).
    """
    n_sql = SQLConn()
    camedw_sql = SQLConn(kind="CAMEDW")
    n_sql.connect()
    camedw_sql.connect()
    n_txn = Transaction(n_sql)
    camedw_txn = Transaction(camedw_sql)

    # Single pull for the date window + statuses
    get_tracking_codes_query = f"""
        SELECT 
            t.AppStartDate,
            t.eCATrackingCode,
            t.AppStartDate,
            j.RawData,
            t.AccountNumber
        FROM [DigitalReport].[dbo].[Transactions] AS t
        JOIN [DigitalReport].[dbo].[JMExtract] AS j
              ON t.eCATrackingCode = j.tID
        WHERE {get_date_filter(start_date, end_date)}
          {"AND " + where_clauses if where_clauses else ""}
          AND t.AppStatus IN ({",".join([f"'{app}'" for app in APPROVED_APPS_STATUSES])});
    """
    tcs = n_txn.get_transactions_by_sql_query(get_tracking_codes_query)

    if not tcs or tcs == 0:
        camedw_sql.disconnect()
        n_sql.disconnect()
        return {"error": "No tracking code found."}

    # Extract accounts from RawData
    # Keep order consistent with input for determinism
    rows_with_accounts = []
    account_set = set()
    for row in tcs:
        code = row.get("eCATrackingCode")
        appStartDate = row.get("AppStartDate")
        raw = row.get("RawData", {})
        accts = process_account_number(row.get("AccountNumber", ''))
        for acc in accts:
            json_obj = None
            if isinstance(raw, dict):
                json_obj = raw
            else:
                try:
                    json_obj = json.loads(raw)
                except Exception:
                    # Optionally log: print(f"JSON issue in {code}")
                    json_obj = None
            if acc is None:
                acc = find_first_fnb_account_number(json_obj) if json_obj is not None else None
                acc = _normalize_int_account(acc, code_for_log=code)
            if acc is None:
                from post_process import process_tc
                tc, acc = process_tc(tc, n_sql)
            if acc is None:
                continue
            # split appStartDate to ensure string in YYYY-MM-DD
            appStartDate = appStartDate.split(":")[0].split("T")[0]
            rows_with_accounts.append((code, acc, appStartDate))
            account_set.add(acc)

    if not rows_with_accounts:
        camedw_sql.disconnect()
        n_sql.disconnect()
        return {"error": "No tracking code found."}

    # Batched CAMEDW fetch
    # Build a map {account_number: {'Initial_Deposit': x, 'Current_Balance': y}}
    account_to_amt = {}
    for chunk in _chunked(account_set, size=1000):
        in_list = _safe_select_list(chunk, is_numeric=True)
        cam_sql = f"""
            SELECT {amount_column} AS acct, Initial_Deposit, Current_Balance
            FROM [CAMEDW].[CAM_EMPL_PII_V1].[{amount_table}]
            WHERE {amount_column} IN ({in_list});
        """
        rows = camedw_txn.get_transactions_by_sql_query(cam_sql) or []
        for r in rows:
            acct = process_account_number(r.get("acct"))
            for acc in acct:
                account_to_amt[acc] = {
                    "Initial_Deposit": r.get("Initial_Deposit"),
                    "Current_Balance": r.get("Current_Balance"),
                }

    # Synthesize the response list in the same shape
    responses = []
    for code, acc, appStartDate in rows_with_accounts:
        amt = account_to_amt.get(acc)
        if not amt:
            continue
        responses.append({
            "Date": appStartDate,
            "eCATrackingCode": code,
            "Account Number": acc,
            "Initial_Deposit": amt.get("Initial_Deposit"),
            "Current_Balance": amt.get("Current_Balance"),
        })

    camedw_sql.disconnect()
    n_sql.disconnect()
    return responses


def get_stacked_chart(start_date, end_date, params):
    """
    Optimized replacement:
      - Single pull from DigitalReport for the entire window.
      - Extract account numbers once; bucketize by month.
      - For each product table, perform ONE CAMEDW lookup (batched) for all accounts across all months.
      - Compute monthly sums in Python from the cached lookup, minimizing DB round trips.
    """
    intervals = get_list_of_months_between(start_date, end_date)
    what_column_to_add = params.get("what_column_to_add", "Current_Balance")
    filters = []

    atype = params.get("application_type", False)
    app_filter = application_type_filter(atype) if atype else None
    if app_filter:
        filters.append(app_filter)

    where_clauses = " AND ".join(filters) if len(filters) > 0 else ""

    listicles = [
        {
            "name": "Certificate Of Deposit",
            "data": [],
            "table": "CAM_COD_ACCT_CUR",
            "column": "COD_ACCT_NUM",
        },
        {
            "name": "Savings/MM",
            "data": [],
            "table": "CAM_SAV_ACCT_CUR",
            "column": "SAV_ACCT_NUM",
        },
        {
            "name": "Consumer Checking",
            "data": [],
            "table": "CAM_DDA_ACCT_CUR",
            "column": "DDA_ACCT_NUM",
        },
    ]

    # ---- 1) Pull all tracking codes once for the whole range ----
    n_sql = SQLConn()
    camedw_sql = SQLConn(kind="CAMEDW")
    n_sql.connect()
    camedw_sql.connect()
    n_txn = Transaction(n_sql)
    camedw_txn = Transaction(camedw_sql)

    tracking_query = f"""
        SELECT 
            t.eCATrackingCode,
            t.AppStartDate,
            j.RawData,
            t.AccountNumber
        FROM [DigitalReport].[dbo].[Transactions] AS t
        JOIN [DigitalReport].[dbo].[JMExtract] AS j
             ON t.eCATrackingCode = j.tID
        WHERE {get_date_filter(start_date, end_date)}
          {"AND " + where_clauses if where_clauses else ""}
          AND t.AppStatus IN ({",".join([f"'{app}'" for app in APPROVED_APPS_STATUSES])});
    """
    tcs = n_txn.get_transactions_by_sql_query(tracking_query)

    if not tcs or tcs == 0:
        # Maintain compatibility: listicles filled with zeros
        for i in range(len(listicles)):
            listicles[i]["data"] = [0] * len(intervals)
        camedw_sql.disconnect()
        n_sql.disconnect()
        return {
            "labels": [get_header(interval)['field'] for interval in intervals],
            "list": listicles
        }

    # ---- 2) Extract accounts and bucketize by month interval ----
    # For each interval index, keep list of account numbers seen in that month
    month_accounts = [set() for _ in intervals]  # avoids duplicates per month
    all_accounts = set()

    def _find_interval_index(app_date_str):
        # Fast linear scan since intervals count is small; can be optimized to binary search if needed.
        for idx, iv in enumerate(intervals):
            if iv["start_date"] <= app_date_str <= iv["end_date"]:
                return idx
        return None

    for row in tcs:
        raw = row.get("RawData", {})
        app_date = row.get("AppStartDate")
        accts = process_account_number(row.get("AccountNumber", ''))
        for acc in accts:
            if not app_date:
                continue
            # Ensure string in YYYY-MM-DD; if datetime, cast
            if not isinstance(app_date, str):
                try:
                    app_date = app_date.strftime("%Y-%m-%d")
                except Exception:
                    continue

            json_obj = None
            if isinstance(raw, dict):
                json_obj = raw
            else:
                try:
                    json_obj = json.loads(raw)
                except Exception:
                    json_obj = None
            

            if acc is None:
                acc = find_first_fnb_account_number(json_obj) if json_obj is not None else None
                acc = _normalize_int_account(acc)
            if acc is None:
                from post_process import process_tc
                tc, acc = process_tc(tc, n_sql)
            if acc is None:
                continue

            idx = _find_interval_index(app_date)
            if idx is None:
                continue
            month_accounts[idx].add(acc)
            all_accounts.add(acc)

    # If no accounts found, return zeroed data
    if not all_accounts:
        for i in range(len(listicles)):
            listicles[i]["data"] = [0] * len(intervals)
        camedw_sql.disconnect()
        n_sql.disconnect()
        return {
            "labels": [get_header(interval)['field'] for interval in intervals],
            "list": listicles
        }

    # ---- 3) For each product, one batched CAMEDW lookup across ALL accounts ----
    # Build a per-product mapping: acct -> {Initial_Deposit, Current_Balance}
    for i, product in enumerate(listicles):
        amount_table = product["table"]
        amount_column = product["column"]

        account_to_amt = {}
        for chunk in _chunked(all_accounts, size=1000):
            in_list = _safe_select_list(chunk, is_numeric=True)
            cam_sql = f"""
                SELECT {amount_column} AS acct, Initial_Deposit, Current_Balance
                FROM [CAMEDW].[CAM_EMPL_PII_V1].[{amount_table}]
                WHERE {amount_column} IN ({in_list});
            """
            rows = camedw_txn.get_transactions_by_sql_query(cam_sql) or []
            for r in rows:
                acct = process_account_number(r.get("acct"))
                for acc in acct:
                    account_to_amt[acc] = {
                        "Initial_Deposit": r.get("Initial_Deposit"),
                        "Current_Balance": r.get("Current_Balance"),
                    }

        # ---- 4) Compute month aggregates using the map (fast, in-Python) ----
        dataNow = []
        for idx in range(len(intervals)):
            total = 0
            for acct in month_accounts[idx]:
                amt = account_to_amt.get(acct)
                if not amt:
                    continue
                val = amt.get(what_column_to_add)
                if val is None:
                    continue
                total += val
            dataNow.append(total)

        listicles[i]["data"] = dataNow

    camedw_sql.disconnect()
    n_sql.disconnect()

    return {
        "labels": [get_header(interval)['field'] for interval in intervals],
        "list": listicles
    }

def get_monthly_opening_and_current_balance_table(start_date, end_date, params):
    """
    Optimized replacement:
      - Single pull from DigitalReport for the entire range.
      - Extract account numbers once; bucketize by month.
      - Single CAMEDW lookup (batched) for all accounts across all months.
      - Compute monthly opening and current balances in Python from the cached lookup, minimizing DB round trips.
    """
    intervals = get_list_of_months_between(start_date, end_date)

    resp = get_responses(start_date, end_date)
    if not resp or resp == 0 or isinstance(resp, dict) and "error" in resp:
        return {"headers": [], "rows": []}

    headers = ["-"] + [get_header(interval)['field'] for interval in intervals] + [get_header(interval)['field'] for interval in intervals]
    rows = [
        ["Apps"],
        ["Products"],
        ["Opening Balance"],
        ["Current Balance"]
    ]

    for i, interval in enumerate(intervals):
        month_start = interval['start_date']
        month_end = interval['end_date']

        opening_balance = 0
        current_balance = 0
        unique_accounts = set()
        unique_tracking_codes = set()
        product_count = 0
        for record in resp:
            app_date = record.get("Date")
            if month_start <= app_date <= month_end:
                product_dat = Q(columns=["NumDepositProducts", "NumLendingProducts"], where=[f"eCATrackingCode = '{record.get('eCATrackingCode')}'"], params=params)[0]
                product_count += try_int(product_dat["NumDepositProducts"]) + try_int(product_dat["NumLendingProducts"])
                    
                current_balance += record.get("Current_Balance", 0)
                opening_balance += record.get("Initial_Deposit", 0)
                unique_accounts.add(record.get("Account Number"))
                unique_tracking_codes.add(record.get("eCATrackingCode"))


        rows[0].append(
            add_comma_to_long_numbers(len(unique_tracking_codes))
            )
        rows[1].append(
            add_comma_to_long_numbers(product_count)
            )
        rows[2].append(
            add_comma_to_long_numbers(opening_balance)
            )
        rows[3].append(
            add_comma_to_long_numbers(current_balance)
            )
        


    return {
        "headers": headers,
        "rows": rows
    }

def get_table(start_date, end_date, params):
    """
    Same signature. Preserves the rotated-table structure returned by original code:
      {
        "headers": headers_list,
        "rows": [ [col1 values...], [col2 values...], ... ]
      }
    """
    resp = get_responses(start_date, end_date)
    # Handle error shape or empty
    if not resp or resp == 0 or isinstance(resp, dict) and "error" in resp:
        return {"headers": [], "rows": []}

    headers = list(resp[0].keys()) if len(resp) > 0 else []
    rows = []
    for col in headers:
        rows.append([row.get(col) for row in resp])

    return {
        "headers": headers,
        "rows": rows
    }