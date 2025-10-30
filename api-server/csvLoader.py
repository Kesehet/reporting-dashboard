import pandas as pd

import os
from DB import Transaction, SQLConn
from application import update_JMExtract
from config import get_env_value
from datetime import datetime, timedelta
from report_modules.condition_utils import get_date_filter
from collections import defaultdict
from post_process import post_process_txns
from metrics import update_metrics




def read_file(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Only CSV, XLSX, and XLS are allowed.")

def prepare_rows(file_path):
    
    df = read_file(file_path)
    rows = list(df.iterrows())
    all_rows = []
    filename = os.path.basename(file_path)
    for _, row in rows:
        row['DataSource'] = filename
        all_rows.append(row)
    
    # ret = txn.set_transaction_from_list_of_dicts(sql, all_rows, filename)
    
    return all_rows

def get_csv(folder_path = "uploads/reports"):

    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    ret = ""
    
    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv') or file.endswith('.xlsx') or file.endswith('.xls')]
    all_rows = []
    for csv_file in csv_files:
        if get_env_value("AUTO_UPDATE_CSV") == "true" or get_env_value("AUTO_UPDATE_CSV") == "True" or get_env_value("AUTO_UPDATE_CSV") == "1":
            pass
        else:
            return "Enable AUTO_UPDATE_CSV to run csv loader"
            
        file_path = os.path.join(folder_path, csv_file)
        if file_exists_in_conf(csv_file, folder_path):
            ret += f"File already processed:  <b style='color:purple;'>{file_path}</b><br>"
            continue
        if not os.path.exists(file_path):
            ret += f"File not found:  <b style='color:red;'>{file_path}</b><br>"
            continue
        all_rows += prepare_rows(file_path)
        
    print("Starting csv pull.")

    if not len(all_rows) == 0:
        rows_starting_with_B = []
        rows_starting_with_C = []

        for row in all_rows:
            code = str(row.get("eCA Tracking Code", ""))
            if code.startswith("B"):
                rows_starting_with_B.append(row)
            elif code.startswith("C"):
                rows_starting_with_C.append(row)   
         
        print("\nPre processing B Tracking code")
        ret += core_process(rows_starting_with_B,sql,txn)
        print("\nPre processing C Tracking code")
        ret += core_process(rows_starting_with_C,sql,txn)

        for csv_file in csv_files:
            update_conf(csv_file, folder_path)
        
        post_process_txns(sql,txn)
        

    
    log_file(ret,f"{datetime.now().isoformat()} run", folder_path)    
    update_JMExtracts(sql,txn)
    print(f"Insert statements generated.")
    return ret

def core_process(all_rows,sql,txn):
    ret = ""
    
    # all_rows = merge_by_eca_tracking_id(all_rows)
    all_rows = sorted(all_rows, key=lambda x: str(x.get("eCA Tracking Code","")), reverse=True)


    speed = len(all_rows)
    if speed == 0:
        ret += "<br/> No txns were fond in the core process <br/>"
        return ret
    batch= len(all_rows)/speed

    for i in range(0, len(all_rows)):
        speed = speed - 1
        if batch < 50000:
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

    with open(final_path, "w", encoding="utf-8") as log_file:
        log_file.write(ret)

    print(f"Log file created: {final_path}")


def file_exists_in_conf(file_name, folder_path="uploads/reports"):
    log_file = os.path.join(folder_path, "ctrl.conf")
    
    if not os.path.exists(log_file):
        return False

    with open(log_file, "r") as f:
        logged_files = set(f.read().splitlines())

    return file_name in logged_files

def update_conf(file_name, folder_path="uploads/reports"):
    log_file = os.path.join(folder_path, "ctrl.conf")
    if not file_exists_in_conf(file_name, folder_path):
        with open(log_file, "a") as f:
            f.write(file_name + "\n")


def update_JMExtracts(sql,txn):
    import sys
    update_metrics("manual_xml_pull", f"started {datetime.now().isoformat()}")
    startDate = datetime.now() - timedelta(days=15)
    endDate = datetime.now()
    date_filter = get_date_filter(startDate.isoformat().split(".")[0], endDate.isoformat().split(".")[0] )
    all_codes = txn.get_transactions_by_sql_query(f"SELECT eCATrackingCode FROM  [DigitalReport].[dbo].[Transactions] WHERE {date_filter} Order by AppStartDate Desc ")
    all_codes = list({code["eCATrackingCode"] for code in all_codes})
    already_processed = set()

    unique_codes = txn.get_transactions_by_sql_query("Select Distinct(tID) as code from [DigitalReport].[dbo].[JMExtract] WHERE tID IS NOT NULL AND tID != ''")
    for code in unique_codes:
        already_processed.add(code.get("code"))
    all_codes = list(set(all_codes) - already_processed)
    import random
    random.shuffle(all_codes)

    print(f"{len(all_codes)} codes to process JM Extracts")
    for code in all_codes:
        if code is not None and code != "":
            sys.stdout.write(f"\rJM XML Extract pulled for:- {code}")
            sys.stdout.flush()
            update_JMExtract(sql, code)
    print("All JM Extracts updated.")
    update_metrics("manual_xml_pull", f"ended {datetime.now().isoformat()}")
    return all_codes

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







# _______________________________________________________________________
from csvLoader import get_csv
update_metrics("scheduled_csv_push", f"started {datetime.now().isoformat()}")
updates = get_csv()
update_metrics("scheduled_csv_push", f"ended {datetime.now().isoformat()}")

