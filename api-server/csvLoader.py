import pandas as pd

from DB import Transaction, SQLConn
from application import update_JMExtract
from config import get_env_value
from datetime import datetime, timedelta
from report_modules.condition_utils import get_date_filter
from collections import defaultdict
from post_process import post_process_txns
from metrics import update_metrics
from utils import process_account_number
import random
import os
import sys
import time
import chardet
import json

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # Read the first 10KB for encoding detection
    result = chardet.detect(raw_data)
    return result['encoding']


def read_file(file_path):
    try:
        if file_path.endswith('.csv'):
            with open(file_path, 'rb') as raw_file:
                header = raw_file.read(4)

            if header.startswith(b'\xff\xfe'):
                encodings_to_try = ['utf-16', 'utf-16-le', 'utf-8-sig', 'utf-8', 'windows-1252']
            elif header.startswith(b'\xfe\xff'):
                encodings_to_try = ['utf-16', 'utf-16-be', 'utf-8-sig', 'utf-8', 'windows-1252']
            elif b'\x00' in header:
                encodings_to_try = ['utf-16-le', 'utf-16-be', 'utf-8-sig', 'utf-8', 'windows-1252']
            else:
                encodings_to_try = ['utf-8-sig', 'utf-8', 'utf-16-le', 'utf-16-be', 'windows-1252', 'latin-1']

            for enc in encodings_to_try:
                try:
                    return pd.read_csv(file_path, encoding=enc)
                except UnicodeDecodeError:
                    continue
                except pd.errors.ParserError:
                    # If parsing fails, try reading as Excel
                    try:
                        return pd.read_excel(file_path)
                    except Exception:
                        continue
            encoding = detect_encoding(file_path)
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except pd.errors.ParserError:
                try:
                    return pd.read_excel(file_path)
                except Exception:
                    pass
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV, XLSX, and XLS are allowed.")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return pd.DataFrame()

def list_csv_report_files(folder_path="uploads/reports", processed_files=None, status_filter="all", date_filter="all"):
    if processed_files is None:
        processed_files = set()

    if not os.path.exists(folder_path):
        return []

    status_filter = (status_filter or "all").lower()
    date_filter = str(date_filter or "all").lower()
    now = datetime.now()

    csv_files = []
    for file_name in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, file_name)
        if not os.path.isfile(file_path):
            continue
        if not file_name.lower().endswith(('.csv', '.xlsx', '.xls')):
            continue

        try:
            df = read_file(file_path)
            row_count = int(len(df.index)) if hasattr(df, 'index') else 0
        except Exception:
            row_count = 0

        file_status = "loaded" if file_name in processed_files else "pending"
        if status_filter != "all" and file_status != status_filter:
            continue

        modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if date_filter != "all":
            try:
                max_age_days = int(date_filter)
                if (now - modified_time).days > max_age_days:
                    continue
            except ValueError:
                pass

        csv_files.append({
            "name": file_name,
            "path": file_path,
            "row_count": row_count,
            "status": file_status,
            "processed": file_name in processed_files,
            "last_modified": modified_time.isoformat(),
            "modified_date": modified_time.date().isoformat(),
        })

    return csv_files


def get_tracking_codes_from_file(file_name, folder_path="uploads/reports"):
    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        return []

    df = read_file(file_path)
    if df is None or df.empty:
        return []

    tracking_codes = []
    seen = set()
    for _, row in df.iterrows():
        tracking_code = str(row.get("eCA Tracking Code", "")).strip()
        if tracking_code and tracking_code.lower() not in {"nan", "none", "null", ""} and tracking_code not in seen:
            tracking_codes.append(tracking_code)
            seen.add(tracking_code)

    return tracking_codes


def _load_skipped_tracking_metrics():
    metrics_path = os.path.join(os.getcwd(), "metrics.json")
    if not os.path.exists(metrics_path):
        return {}

    try:
        with open(metrics_path, "r", encoding="utf-8", errors="replace") as metrics_file:
            return json.load(metrics_file) or {}
    except Exception:
        return {}


def get_tracking_code_missing_reason(file_name, tracking_code, folder_path="uploads/reports"):
    if tracking_code is None:
        return "Missing tracking code."

    tracking_code = str(tracking_code).strip()
    if tracking_code.lower() in {"", "nan", "none", "null"}:
        return "Missing tracking code."

    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        return "CSV file not found."

    df = read_file(file_path)
    if df is None or df.empty:
        return "CSV is empty or unreadable."

    matching_rows = [
        row for _, row in df.iterrows()
        if str(row.get("eCA Tracking Code", "")).strip() == tracking_code
    ]

    if not matching_rows:
        return "Code not found in CSV."

    for row in matching_rows:
        primary_name = str(row.get("Primary Name", "") or "").strip()
        if primary_name.lower().find("test") != -1 or primary_name.lower() in {"test", "test user"}:
            return f"Filtered test name: {primary_name}."

        required_fields = [
            "App Start Date",
        ]
        missing_fields = [field for field in required_fields if pd.isna(row.get(field, "")) or str(row.get(field, "")).strip() in {"", "nan", "none", "null"}]
        if missing_fields:
            return f"Missing: {', '.join(missing_fields)}."

    metrics = _load_skipped_tracking_metrics()
    skipped = metrics.get("skipped_tracking_codes", [])
    for entry in skipped:
        if str(entry.get("tracking_code", "")).strip() == tracking_code:
            return str(entry.get("reason", "Code missing from DB."))

    matches = sum(1 for _, row in df.iterrows() if str(row.get("eCA Tracking Code", "")).strip() == tracking_code)
    if matches > 1:
        return "Duplicate code in CSV."

    return "Code missing from DB."


def prepare_rows(file_path):
    
    df = read_file(file_path)
    if df.empty:
        return []
    rows = list(df.iterrows())
    all_rows = []
    filename = os.path.basename(file_path)
    for _, row in rows:
        row['DataSource'] = filename
        row["AccountNumber"] = '|'.join([str(acc) for acc in process_account_number(row.get("Product Account Number", ""))])
        all_rows.append(row)
    
    # ret = txn.set_transaction_from_list_of_dicts(sql, all_rows, filename)
    
    return all_rows


def load_single_csv_file(file_name, folder_path="uploads/reports"):
    file_path = os.path.join(folder_path, file_name)
    if not os.path.exists(file_path):
        return {
            "success": False,
            "status": "not_found",
            "message": f"File not found: {file_name}",
        }

    if file_exists_in_conf(file_name, folder_path):
        return {
            "success": True,
            "status": "already_loaded",
            "message": f"File already processed: {file_name}",
            "loaded": True,
        }

    if get_env_value("AUTO_UPDATE_CSV") not in {"true", "True", "1"}:
        return {
            "success": False,
            "status": "disabled",
            "message": "AUTO_UPDATE_CSV is not enabled for csv loader.",
        }

    rows = prepare_rows(file_path)
    if len(rows) == 0:
        return {
            "success": False,
            "status": "empty",
            "message": f"No rows found in file: {file_name}",
        }

    file_rows = deduplicate_tracking_codes(rows)
    if len(file_rows) == 0:
        return {
            "success": False,
            "status": "invalid",
            "message": f"No valid rows found in file: {file_name}",
        }

    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    all_tracking_codes_updated_this_run = set()
    rows_starting_with_B = []
    rows_starting_with_C = []

    try:
        for row in file_rows:
            code = str(row.get("eCA Tracking Code", ""))
            all_tracking_codes_updated_this_run.add(code)
            if code.startswith("B"):
                rows_starting_with_B.append(row)
            elif code.startswith("C"):
                rows_starting_with_C.append(row)

        ret = ""
        try:
            ret += core_process(rows_starting_with_B, sql, txn)
        except Exception as exc:
            ret += f"Error processing B tracking codes: {exc}<br>"
        try:
            ret += core_process(rows_starting_with_C, sql, txn)
        except Exception as exc:
            ret += f"Error processing C tracking codes: {exc}<br>"

        update_conf(file_name, folder_path)
        post_process_txns(sql, txn, tracking_codes_added_this_run=all_tracking_codes_updated_this_run)
        log_file(ret, f"{datetime.now().isoformat()} run", folder_path)
        update_JMExtracts(sql, txn)

        return {
            "success": True,
            "status": "loaded",
            "message": f"File loaded successfully: {file_name}",
            "loaded": True,
            "row_count": len(rows),
            "tracking_count": len(file_rows),
            "details": ret,
        }
    except Exception as exc:
        return {
            "success": False,
            "status": "error",
            "message": str(exc),
            "loaded": False,
        }
    finally:
        sql.disconnect()


def get_csv(folder_path = "uploads/reports"):

    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    ret = ""

    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv') or file.endswith('.xlsx') or file.endswith('.xls')]
    all_tracking_codes_updated_this_run = set()
    ctr = 0
    for csv_file in csv_files:
        if get_env_value("AUTO_UPDATE_CSV") == "true" or get_env_value("AUTO_UPDATE_CSV") == "True" or get_env_value("AUTO_UPDATE_CSV") == "1":
            pass
        else:
            return "Enable AUTO_UPDATE_CSV to run csv loader"
        ctr = ctr + 1
        update_metrics("csv_loader_progress", f"Processing {csv_file} - {ctr} / {len(csv_files)} files completed.")

        file_path = os.path.join(folder_path, csv_file)
        if file_exists_in_conf(csv_file, folder_path):
            ret += f"File already processed:  <b style='color:purple;'>{file_path}</b><br>"
            continue
        if not os.path.exists(file_path):
            ret += f"File not found:  <b style='color:red;'>{file_path}</b><br>"
            continue

        rows = prepare_rows(file_path)
        if len(rows) == 0:
            ret += f"No rows found in file:  <b style='color:orange;'>{file_path}</b><br>"
            continue

        file_rows = deduplicate_tracking_codes(rows)
        if len(file_rows) == 0:
            ret += f"No valid rows found in file:  <b style='color:orange;'>{file_path}</b><br>"
            continue

        print(f"Starting csv pull for {csv_file}.")
        rows_starting_with_B = []
        rows_starting_with_C = []

        for row in file_rows:
            code = str(row.get("eCA Tracking Code", ""))
            all_tracking_codes_updated_this_run.add(code)
            if code.startswith("B"):
                rows_starting_with_B.append(row)
            elif code.startswith("C"):
                rows_starting_with_C.append(row)

        try:
            print("\nPre processing B Tracking code")
            update_metrics("csv_loader_logs", f"Processing B tracking code for {csv_file} with {len(rows_starting_with_B)} rows.")
            ret += core_process(rows_starting_with_B,sql,txn)
        except Exception as e:
            update_metrics("csv_loader_errors", f"Processing B tracking code for {csv_file} failed with {e}")
            print(f"Pre Processing B Txn failed: {e}")
        try:
            print("\nPre processing C Tracking code")
            update_metrics("csv_loader_logs", f"Processing C tracking code for {csv_file} with {len(rows_starting_with_C)} rows.")
            ret += core_process(rows_starting_with_C,sql,txn)
        except Exception as e:
            update_metrics("csv_loader_errors", f"Processing C tracking code for {csv_file} failed with {e}")
            print(f"Pre Processing C Txn failed: {e}")

        update_conf(csv_file, folder_path)

    if all_tracking_codes_updated_this_run:
        post_process_txns(sql,txn, tracking_codes_added_this_run=all_tracking_codes_updated_this_run)
    log_file(ret,f"{datetime.now().isoformat()} run", folder_path)
    update_JMExtracts(sql,txn)
    return ret


def deduplicate_tracking_codes(rows):
    unique_rows = {}
    for row in rows:
        tracking_code = str(row.get("eCA Tracking Code", "")).strip()
        if tracking_code.lower() in {"", "nan", "none"}:
            continue
        current = unique_rows.get(tracking_code)
        if current is None or _row_completeness(row) > _row_completeness(current):
            unique_rows[tracking_code] = row
    return list(unique_rows.values())


def _row_completeness(row):
    values = row.values if hasattr(row, "values") else row.values()
    return sum(pd.notna(value) and str(value).strip().lower() not in {"", "nan", "none"} for value in values)

def core_process(all_rows,sql,txn):
    ret = ""
    
    # all_rows = merge_by_eca_tracking_id(all_rows)
    all_rows = sorted(all_rows, key=lambda x: str(x.get("eCA Tracking Code","")), reverse=True)

    speed = len(all_rows)
    if speed == 0 or speed == None:
        ret += "<br/> No txns were fond in the core process <br/>"
        return ret
    
    batch = len(all_rows) / speed

    for i in range(0, len(all_rows)):
        speed = speed - 1
        if batch < 50000:
            if speed == 0:
                speed = 1
            batch= len(all_rows)/speed
        if speed <= 1:
            break
    batch = int(batch)
    ret += f"<strong>Batch size is {batch}</strong> <br>"
    if not (batch == 0):
        ctr = 0
        for start in range(0,len(all_rows), batch):
            print(f"    Batch: {ctr}/{speed}")
            end = min(start+batch,len(all_rows))
            ret += txn.set_transaction_from_list_of_dicts(sql, all_rows[start:end])
            ctr += 1
    return ret
    
    


def log_file(ret, csv_file, folder_path="uploads/reports"):
    logs_path = os.path.join(folder_path, "logs")
    
    # Sanitize filename: replace ':' with '-' or remove it
    safe_filename = csv_file.replace(":", "-")
    final_path = os.path.join(logs_path, f"{safe_filename}.html")

    if not os.path.exists(logs_path):
        os.makedirs(logs_path)

    with open(final_path, "w", encoding="utf-8", errors="replace") as log_file:
        log_file.write(ret)

    print(f"Log file created: {final_path}")


def file_exists_in_conf(file_name, folder_path="uploads/reports"):
    log_file = os.path.join(folder_path, "ctrl.conf")
    
    if not os.path.exists(log_file):
        return False

    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        logged_files = set(f.read().splitlines())

    return file_name in logged_files

def update_conf(file_name, folder_path="uploads/reports"):
    log_file = os.path.join(folder_path, "ctrl.conf")
    if not file_exists_in_conf(file_name, folder_path):
        with open(log_file, "a", errors="replace", encoding="utf-8") as f:
            f.write(file_name + "\n")


def update_JMExtracts(sql,txn):
    """Pull missing JM data without treating empty RawData rows as completed."""
    import sys
    started_at = datetime.now().isoformat()
    update_metrics("manual_xml_pull", f"started {started_at}")
    stats = {"started_at": started_at, "attempted": 0, "saved": 0, "failed": 0}
    try:
        if not sql.connection:
            raise RuntimeError("No SQL connection available for JM extraction")

        startDate = datetime.now() - timedelta(days=30)
        endDate = datetime.now()
        date_filter = get_date_filter(
            startDate.isoformat().split(".")[0], endDate.isoformat().split(".")[0]
        )
        all_codes = txn.get_transactions_by_sql_query(
            f"SELECT eCATrackingCode FROM [DigitalReport].[dbo].[Transactions] "
            f"WHERE {date_filter} ORDER BY AppStartDate DESC"
        )
        if not isinstance(all_codes, list):
            raise RuntimeError("Failed to query transactions for JM extraction")
        all_codes = {
            row.get("eCATrackingCode") for row in all_codes
            if isinstance(row, dict) and row.get("eCATrackingCode")
        }

        valid_codes = txn.get_transactions_by_sql_query(
            "SELECT DISTINCT tID AS code FROM [DigitalReport].[dbo].[JMExtract] "
            "WHERE tID IS NOT NULL AND tID != '' AND RawData IS NOT NULL "
            "AND LTRIM(RTRIM(RawData)) NOT IN ('', 'null')"
        )
        if not isinstance(valid_codes, list):
            raise RuntimeError("Failed to query existing JM RawData")
        already_processed = {
            row.get("code") for row in valid_codes if isinstance(row, dict)
        }

        missing_codes = list(all_codes - already_processed)
        random.shuffle(missing_codes)
        stats["attempted"] = len(missing_codes)
        print(f"{len(missing_codes)} missing JM RawData codes to process")

        for code in missing_codes:
            sys.stdout.write(f"\rJM XML extraction for: {code}")
            sys.stdout.flush()
            try:
                if update_JMExtract(sql, code):
                    stats["saved"] += 1
                else:
                    stats["failed"] += 1
            except Exception as exc:
                stats["failed"] += 1
                print(f"JM XML extraction error for {code}: {type(exc).__name__}: {exc}")

        state = "ended" if not stats["failed"] else "partial_failure"
        update_metrics("manual_xml_pull", f"{state} {datetime.now().isoformat()} "
                       f"saved={stats['saved']} failed={stats['failed']}")
        print(f"JM XML run: {stats['saved']} saved, {stats['failed']} failed")
        return missing_codes
    except Exception as exc:
        update_metrics("manual_xml_pull", f"failed {datetime.now().isoformat()} "
                       f"{type(exc).__name__}")
        raise
    finally:
        stats["finished_at"] = datetime.now().isoformat()
        update_metrics("manual_xml_pull_summary", stats)

import math
def merge_by_eca_tracking_id(data):
    def is_missing(value):
        if value is None:
            return True
        if isinstance(value,str) and value.strip().upper() in {"", "Null"}:
            return True
        if isinstance(value, float) and math.isnan(value):
            return True
        return False
    
    def completeness(d):
        count = 0
        for v in d.values():
            if not is_missing(v):
                count += 1
        return count

    grouped = defaultdict(list)
    for entry in data:
        entry = dict(entry)
        key = entry.get("eCA Tracking Code")
        grouped[key].append(entry)

    merged_data = []
    for eca_id, entries in grouped.items():
        entries.sort(
            key=completeness, reverse=True)
        
        base = entries[0].copy()

        for entry in entries[1:]:
            for k, v in entry.items():
                if is_missing(base.get(k)) and not is_missing(v):
                    base[k] = v

        merged_data.append(base)

    return merged_data








if __name__ == "__main__":
    time.sleep(random.randint(10,30))

    # Directory for temp files (you can change this)
    temp_dir = ".cache_requests"
    os.makedirs(temp_dir, exist_ok=True)

    # Get today's and yesterday's dates
    today = datetime.today().date()       # Use .date() for cleaner filenames
    yesterday = today - timedelta(days=1)

    today_file = os.path.join(temp_dir, f"{today}.tmp")
    yesterday_file = os.path.join(temp_dir, f"{yesterday}.tmp")

    # Check if today's file exists
    if os.path.exists(today_file):
        print(f"Today's file already exists: {today_file}")
        sys.exit(0)

    # Delete yesterday's file if it exists
    if os.path.exists(yesterday_file):
        os.remove(yesterday_file)
        print(f"Deleted yesterday's file: {yesterday_file}")

    # Create today's file
    with open(today_file, "w", encoding="utf-8", errors="replace") as f:
        f.write("Temporary file for today\n")

    print(f"Created today's file: {today_file}")
    update_metrics("scheduled_csv_push", f"started {datetime.now().isoformat()}")
    get_csv()
    update_metrics("scheduled_csv_push", f"ended {datetime.now().isoformat()}")

