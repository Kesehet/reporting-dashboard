import pyodbc
import requests
import logging
pyodbc.pooling = False
from datetime import datetime
from dateutil import parser
import json
from datetime import datetime
from decimal import Decimal
import sys
from dotenv import load_dotenv
from config import get_env_value
from metrics import update_metrics
import pandas as pd
import time
from report_modules.condition_utils import *
from utils import get_product_name, process_account_number, process_product_id, get_branch_name, process_branch_id, params_to_condition_list
import os
import sys
import base64
import hashlib
import pickle
import unicodedata
from typing import Optional
from urllib.parse import urljoin


logger = logging.getLogger(__name__)


load_dotenv()


def sanitize_csv_text(value):
    """Keep CSV text safe for the loader's SQL and log strings."""
    normalized = unicodedata.normalize("NFD", str(value))
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.encode("ascii", errors="ignore").decode("ascii")


def safe_parse_date(value):
    if value is None:
        return None

    if isinstance(value, (list, tuple, set, dict)):
        if len(value) != 1:
            return None
        value = next(iter(value))

    if hasattr(value, "tolist") and not isinstance(value, (str, bytes, bytearray)):
        try:
            value = value.tolist()
        except Exception:
            return None
        if isinstance(value, (list, tuple, set)):
            if len(value) != 1:
                return None
            value = next(iter(value))
        else:
            return None

    value = str(value).strip()
    if value in {"", "nan", "None", "NULL", "null"}:
        return None

    try:
        return parser.parse(value)
    except (TypeError, ValueError, OverflowError):
        return None


class SQLConn:
    def __init__(self, kind="", connection_string=None ):
        self.kind = kind
        if kind != "":
            kind = kind + "_"        
        self.user = get_env_value(kind+'SQL_USER')
        self.password = get_env_value(kind+'SQL_PASSWORD')
        self.host =  get_env_value(kind+'SQL_HOST')
        self.database =  get_env_value(kind+'SQL_DATABASE')
        self.connection = None
        self.connection_string = connection_string

    def connect(self):
        try:
            if self.connection_string is None:
                connection_string = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.host};"
                    f"DATABASE={self.database};"
                    f"Encrypt=yes;"
                    f"TrustServerCertificate=yes;"
                    f"Connection Timeout=10;"
                )
                if self.user and self.password:
                    connection_string += f"UID={self.user};PWD={self.password};"
                else:
                    connection_string += "Trusted_Connection=Yes;"
            else:
                connection_string = self.connection_string
            self.connection = pyodbc.connect(connection_string)
        except pyodbc.Error as e:
            print(f"    {e}")
            self.connection = None
            return

    def disconnect(self):
        if self.connection:
            self.connection.close()
            # print("SQL Connection closed")

    def log_tables(self):
        if not self.connection:
            print("No active connection")
            return
        cursor = self.connection.cursor()
        cursor.execute( "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS " if self.kind.endswith("EDW") > 0 else "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"   )
        tables = cursor.fetchall()
        print("Tables in the database:")
        for table in tables:
            print(table.TABLE_NAME)
        return tables

    def get_columns(self, table_name):
        if not self.connection:
            print("No active connection")
            return
        cursor = self.connection.cursor()
        query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?"
        cursor.execute(query, (table_name,))
        columns = cursor.fetchall()
        
        # Convert the tuples to simple strings
        column_names = [column[0] for column in columns]
        
        print(f"Columns in table '{table_name}':")
        for column_name in column_names:
            print(column_name)
        return column_names

    def pull_data(self, table_name, columns):
        if not self.connection:
            print("No active connection")
            return
        cursor = self.connection.cursor()
        
        # Ensure columns are strings
        columns_str = ', '.join(columns)
        
        query = f"SELECT {columns_str} FROM {table_name}"
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows

    def push_data(self, table_name, columns, values):
        if not self.connection:
            print("No active connection")
            return
        cursor = self.connection.cursor()
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['?'] * len(columns))
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        cursor.executemany(query, values)
        self.connection.commit()
        # print(f"Data inserted into '{table_name}'")


    def execute(self,query, debug=False, retries = 10):
        if not self.connection:
            print("No active connection")
            return False
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
        except pyodbc.Error as e:
            # Retry if connection is busy with results for another command
            error_msg = str(e)
            if "Connection is busy with results for another command" in error_msg:
                
                for attempt in range(retries):
                    try:
                        time.sleep(0.5)
                        cursor.execute(query)
                        break
                    except pyodbc.Error as e2:
                        if attempt == retries - 1 or "Connection is busy with results for another command" not in str(e2):
                            if debug:
                                print(f"Error executing query after retry: {e2} \nQuery: {query}")
                            else:
                                print("Connection is Busy.")
                            return False
            else:
                print(f"Error executing query: {e} \nQuery: {query}")
                return False
        


        if debug:
            if len(query) > 300:
                    with open("SQL Failed.txt", 'a') as f:
                        f.write(query+"\n")
            print(f"Executed query: {query[0:50]}")
        self.connection.commit()
        return True
    
    def run_query(self, query, debug=False):
        if not self.connection:
            print("No active connection")
            return
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
            return results
        except pyodbc.Error as e:
            print(f"Error executing query: {e} \nQuery: {query}")
            return None

    def setup(self):
        if not self.connection:
            print("No active connection")
            return
        cursor = self.connection.cursor()
        # Create table if it does not exist
        columns_str = ', '.join([f"{col} {col_type}" for col, col_type in TABLE_STRUCTURE.items()])

        create_table_query = f"""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Transactions]') AND type in (N'U'))
        BEGIN
            CREATE TABLE [dbo].[Transactions] (
            {columns_str}
            )
        END
        """
        cursor.execute(create_table_query)
        self.connection.commit()
        # Check existing columns
        cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Transactions'")
        existing_columns = {row[0]: row for row in cursor.fetchall()}
        for col, coltype in TABLE_STRUCTURE.items():
            if col not in existing_columns:
                print(f"ALTER TABLE [dbo].[Transactions] ADD {col} {coltype}")
                # Add missing column
                cursor.execute(f"ALTER TABLE [dbo].[Transactions] ADD {col} {coltype}")
            else:
                # Check type and alter if needed
                row = existing_columns[col]
                dtype = row[1]
                if "NVARCHAR" in coltype:
                    if dtype != "nvarchar":
                        cursor.execute(f"ALTER TABLE [dbo].[Transactions] ALTER COLUMN {col} {coltype}")
                elif "DATETIME" in coltype:
                    if dtype != "datetime":
                        cursor.execute(f"ALTER TABLE [dbo].[Transactions] ALTER COLUMN {col} {coltype}")
                elif "BIT" in coltype:
                    if dtype != "bit":
                        cursor.execute(f"ALTER TABLE [dbo].[Transactions] ALTER COLUMN {col} {coltype}")
                elif "INT" in coltype:
                    if dtype != "int":
                        cursor.execute(f"ALTER TABLE [dbo].[Transactions] ALTER COLUMN {col} {coltype}")
                elif "DECIMAL" in coltype:
                    if dtype != "decimal":
                        cursor.execute(f"ALTER TABLE [dbo].[Transactions] ALTER COLUMN {col} {coltype}")
                elif "FLOAT" in coltype:
                    if dtype != "float":
                        cursor.execute(f"ALTER TABLE [dbo].[Transactions] ALTER COLUMN {col} {coltype}")
        self.connection.commit()
        

class Transaction:
    def __init__(self, sql_conn):
        self.sql_conn = sql_conn

    def get_transaction_by_id(self, transaction_id):
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT * FROM Transactions WHERE tId = ?"
        cursor.execute(query, (transaction_id,))
        transaction = cursor.fetchone()
        if transaction:
            transaction_data = self.row_to_dict(cursor.description, transaction)
            return json.dumps(transaction_data)
        else:
            return json.dumps({"error": "Transaction not found"})

    def row_to_dict(self, description, row):
        return {description[i][0]: row[i] for i in range(len(row))}

    def format_date(self, date_str):
        try:
            return parser.parse(date_str)
        except ValueError:
            return None

    


    def create_transaction_from_json(self, transaction_data):
        eCAID = transaction_data.get("eCAID")

        # Check if the transaction already exists
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT tId, AppUpdateDate FROM Transactions WHERE eCAID = ?"
        cursor.execute(query, (eCAID,))
        result = cursor.fetchone()
        exists = result is not None

        if exists:
            existing_tid, existing_app_update_date = result
            new_app_update_date = parser.parse(transaction_data.get("AppUpdateDate"))

            # Check if AppUpdateDate is different
            if existing_app_update_date != new_app_update_date:
                update_columns = ["AppStatus", "DeclineReason"]
                update_data = {col: transaction_data[col] for col in update_columns if col in transaction_data}

                if update_data:
                    update_query = "UPDATE Transactions SET " + ", ".join(f"{col} = ?" for col in update_data.keys()) + " WHERE eCAID = ?"
                    cursor.execute(update_query, (*update_data.values(), eCAID))

                    self.sql_conn.connection.commit()
                    return {"success": f"Transaction with eCAID {eCAID} has been updated.", "tId": existing_tid}
                else:
                    return {"error": "No valid columns to update."}
            else:
                return {"error": f"Transaction with eCAID {eCAID} already exists and AppUpdateDate is the same.", "tId": existing_tid}

        # Format date fields properly
        date_fields = ["AppStartDate", "AppSubmitDate", "AppUpdateDate"]
        for field in date_fields:
            if field in transaction_data:
                try:
                    formatted_date = parser.parse(transaction_data[field] if transaction_data[field] else "")
                    transaction_data[field] = formatted_date
                except Exception as e:
                    print(f"Invalid date format for field {field}: {transaction_data[field]}")
                    return {"error": f"Invalid date format for field {field}"}

        # Convert numeric fields to appropriate types
        numeric_fields = ["NumCoApplicant", "NumDepositProducts", "NumLendingProducts"]
        for field in numeric_fields:
            if field in transaction_data and transaction_data[field] is not None:
                try:
                    transaction_data[field] = float(transaction_data[field])
                except ValueError:
                    print(f"Invalid numeric format for field {field}: {transaction_data[field]}")
                    return {"error": f"Invalid numeric format for field {field}"}

        # Exclude the identity column (tId) from the insert
        columns = [key for key in transaction_data.keys() if key != 'tId']
        values = tuple(transaction_data[key] for key in columns)

        self.sql_conn.push_data("Transactions", columns, [values])

        # Retrieve the tId of the newly inserted transaction
        query = "SELECT tId FROM Transactions WHERE eCAID = ?"
        cursor.execute(query, (eCAID,))
        new_tid = cursor.fetchone()[0]
        return {"success": f"Transaction with eCAID {eCAID} has been created.", "tId": new_tid}

    def get_all_transactions(self):
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT * FROM Transactions"
        cursor.execute(query)
        rows = cursor.fetchall()
        transactions = [self.row_to_dict(cursor.description, row) for row in rows]
        return json.dumps(transactions, cls=CustomJSONEncoder)
    
    def get_transactions_by_date_range(self, start_date, end_date):
        cursor = self.sql_conn.connection.cursor()
        query = """
            SELECT * FROM Transactions
            WHERE AppStartDate BETWEEN ? AND ?
        """
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        transactions = []
        for row in rows:
            transaction = self.row_to_dict(cursor.description, row)
            # TODO products columns
            transactions.append(transaction)
        return json.dumps(transactions, cls=CustomJSONEncoder)

    def row_to_dict(self, description, row):
        return {description[i][0]: row[i] for i in range(len(row))}


    def get_transactions_by_column(self, column_name, value):
        cursor = self.sql_conn.connection.cursor()
        query = f"SELECT * FROM Transactions WHERE {column_name} = ?"
        cursor.execute(query, (value,))
        rows = cursor.fetchall()
        transactions = [self.row_to_dict(cursor.description, row) for row in rows]
        return self.clean_response(transactions)
    
    def get_eCATrackingCodes(self):
        cursor = self.sql_conn.connection.cursor()
        query = f"SELECT eCATrackingCode FROM  [DigitalReport].[dbo].[Transactions] Order by AppStartDate Desc"
        cursor.execute(query)
        rows = cursor.fetchall()
        transactions = [self.row_to_dict(cursor.description, row) for row in rows]
        list_of_codes = self.clean_response(transactions)
        # Remove duplicates
        list_of_codes = list({code["eCATrackingCode"] for code in list_of_codes})
        return list_of_codes
    
    def get_transactions_by_category(self, category):
        cursor = self.sql_conn.connection.cursor()
        query = f"SELECT * FROM Transactions WHERE NumDepositProducts >= 1 AND NumLendingProducts >= 1"
        cursor.execute(query, ())
        rows = cursor.fetchall()
        transactions = [self.row_to_dict(cursor.description, row) for row in rows]
        
        return self.clean_response(transactions)
    
    def get_transactions_by_sql_query(self, query, debug=False, use_cache=True):

        # Create cache directory if it doesn't exist
        cache_dir = ".cache_requests"
        os.makedirs(cache_dir, exist_ok=True)

        # Generate a unique filename based on the query hash
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_file = os.path.join(cache_dir, f"{query_hash}.pkl")

        # Try loading from cache
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print("SQL Error: Failed to load cache:", e)

        if debug:
            print("SQL Error: Executing SQL query:")
            print(query)
            print("-----------------------------------------")

        if "()" in query:
            query = query.replace("IN ()", "IN ('0000','00000')")
            query = query.replace("in ()", "in ('0000','00000')")

        resp = 0
        query_started = time.perf_counter()
        try:
            cursor = self.sql_conn.connection.cursor()
            cursor.execute(query, ())
            rows = cursor.fetchall()
            transactions = [self.row_to_dict(cursor.description, row) for row in rows]

            cleaned_resp = self.clean_response(transactions)
            if len(cleaned_resp) == 0:
                resp = 0
            elif "as data" in query.lower():
                resp = cleaned_resp[0].get("data", 0) or 0
            else:
                # if response contains ProductSetId column, append another column called ProductSetName with the name of the product
                if len(cleaned_resp) > 0 and "ProductSetId" in cleaned_resp[0]:
                    for r in cleaned_resp:
                        r["ProductSetName"] = get_product_name(r["ProductSetId"])
                        r["ProductSetId"] = "|".join([str(p) for p in process_product_id(r["ProductSetId"])])
                
                # if response contains BranchId column, append another column called BranchName with the name of the branch
                if len(cleaned_resp) > 0 and ("BranchId" in cleaned_resp[0] or "BranchID" in cleaned_resp[0]):
                    for r in cleaned_resp:
                        if r.get("BranchID") is not None and r.get("BranchID") != "":
                            r["BranchName"] = "|".join([str(p) + " - "+ get_branch_name(r.get("BranchId", r.get("BranchID"))) for p in process_branch_id(r.get("BranchId", r.get("BranchID"))) ])
                        elif r.get("BranchId") is not None and r.get("BranchId") != "":
                            r["BranchName"] = "|".join([str(p) + " - "+ get_branch_name(r.get("BranchId", r.get("BranchID"))) for p in process_branch_id(r.get("BranchId", r.get("BranchID")))  ])
                resp = cleaned_resp
        except Exception:
            logger.exception(
                "SQL query failed (query_hash=%s, query_length=%d)",
                query_hash,
                len(query),
            )

        try:
            resp = float(resp)
        except:
            # print("SQL Error: Failed To Convert To Float")
            pass

        if debug:
            logger.info(
                "SQL query completed (query_hash=%s, result_type=%s, result_is_zero=%s, duration_ms=%.1f, cache_enabled=%s)",
                query_hash,
                type(resp).__name__,
                resp == 0,
                (time.perf_counter() - query_started) * 1000,
                use_cache,
            )

        # Diagnostic requests bypass both cache reads and writes so a previously
        # cached zero cannot conceal the current database result.
        if use_cache:
            try:
                with open(cache_file, "wb") as f:
                    pickle.dump(resp, f)
            except Exception as e:
                print("SQL Error: Failed to save cache:", e)

        return resp

        
        
    def tracking_code_exists(self, tracking_code):
        tracking_code = sanitize_csv_text(tracking_code)
        if tracking_code in {None, "", "nan", "NULL", "None"}:
            return False

        cursor = self.sql_conn.connection.cursor()
        cursor.execute(
            "SELECT TOP 1 eCATrackingCode FROM [DigitalReport].[dbo].[Transactions] WHERE eCATrackingCode = ?",
            (tracking_code,),
        )
        return cursor.fetchone() is not None

    def record_skipped_tracking_code(self, tracking_code, reason):
        tracking_code = sanitize_csv_text(tracking_code)
        if tracking_code in {None, "", "nan", "NULL", "None"}:
            return

        try:
            metrics_path = os.path.join(os.getcwd(), "metrics.json")
            metrics = {}
            if os.path.exists(metrics_path):
                with open(metrics_path, "r", encoding="utf-8") as f:
                    try:
                        metrics = json.load(f) or {}
                    except json.JSONDecodeError:
                        metrics = {}

            skipped = metrics.get("skipped_tracking_codes", [])
            if not isinstance(skipped, list):
                skipped = []

            entry = {
                "tracking_code": str(tracking_code),
                "reason": str(reason),
            }
            if not any(
                item.get("tracking_code") == entry["tracking_code"] and item.get("reason") == entry["reason"]
                for item in skipped
            ):
                skipped.append(entry)

            metrics["skipped_tracking_codes"] = skipped
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=4)
        except Exception as exc:
            print(f"Failed to update skipped tracking metrics: {exc}")

    def set_transaction_from_list_of_dicts(self, sql: SQLConn, all_rows, dataSource="unknown"):

        #__________________________________________________________________________________________________________________________________
        trackingCode = ""
        ret = ""
        ctr = 0
        insert_statements = []  # Collect all insert statements here
        update_statements = []  # Collect all update statements here
        old_txns = [code for code in self.get_eCATrackingCodes() if code is not None and code != ""]
        if not old_txns:
            old_txns = []
        
        
        # ____________________________________________ THE LOOP ______________________________________________________
        seen_tracking_codes = set()

        

        for row in all_rows:
            values = []
            tracking_code = sanitize_csv_text(row.get("eCA Tracking Code", ""))
            dataSource = sanitize_csv_text(row['DataSource'])
            if dataSource.find("business") != -1:
                M_CSV_TO_SQL_COLUMNS = {
                    ("Business Name" if k == "Primary Name" else
                    "Business TIN" if k == "Primary SSN" else k): v
                    for k, v in CSV_TO_SQL_COLUMNS.items()
                }
            else:
                M_CSV_TO_SQL_COLUMNS = CSV_TO_SQL_COLUMNS

            sql_columns_list = list(M_CSV_TO_SQL_COLUMNS.values())
            prefix_insert_statement = f"INSERT INTO {TABLE_NAME} ({', '.join(sql_columns_list)}) VALUES"

            if str(tracking_code).lower() == "nan" or str(tracking_code).lower() == "" or str(tracking_code).lower() == None:
                self.record_skipped_tracking_code(tracking_code, "Tracking code is null or missing")
                ret += f"ECa Tracking code is ignored in row as its null <pre>{sanitize_csv_text(row)}</pre>.<br>"
                continue

            
            primary_name = sanitize_csv_text(row.get("Primary Name", ""))
            if primary_name.lower() in PRIMARY_NAME_IGNORE or "test" in primary_name.lower():
                self.record_skipped_tracking_code(tracking_code, "Primary name ignored by filter")
                ret += f"Primary Name is ignored in row <pre>{sanitize_csv_text(row)}</pre>.<br>"
                continue

            if tracking_code in seen_tracking_codes:
                self.record_skipped_tracking_code(tracking_code, "Duplicate tracking code in current file")
                ret += f"Duplicate ECa Tracking code found and ignored <pre>{sanitize_csv_text(row)}</pre>.<br>"
                continue

            seen_tracking_codes.add(tracking_code)
            tracking_exists = tracking_code in old_txns or self.tracking_code_exists(tracking_code)

            sys.stdout.write(f"\r        {int((ctr/len(all_rows))*100)} %  -  {ctr}/{len(all_rows)} preprocessed. ")
            sys.stdout.flush()
            for csv_column, sql_column in M_CSV_TO_SQL_COLUMNS.items():
                value = sanitize_csv_text(row.get(csv_column, "")).strip() if pd.notna(row.get(csv_column, "")) else "NULL"

                if sql_column in {"AppStartDate", "AppSubmitDate", "AppUpdateDate"} and value not in {"NULL", ""}:
                    parsed_date = safe_parse_date(value)
                    if parsed_date is not None:
                        value = f"{parsed_date.strftime('%Y-%m-%d %H:%M:%S')}"
                    else:
                        value = "NULL"
                elif sql_column in {"DeclineReason"} and value not in {"NULL", ""}:
                    value = value.replace('\\n', ' ')
                    value = value.replace('\\n', ' ')
                    value = value.replace('''\n''', ' ')
                    value = value.replace('''\r''', ' ')
                elif sql_column in {"CustomerID"}:
                    value = '0'
                elif sql_column in {"DataSource"}:
                    value = dataSource
                elif sql_column in {"BranchID", 'NMLS_Id', "EmployeeResponsibilityCode", "NumDepositProducts", "NumLendingProducts", "NumCoApplicant"}:
                    if value == "" or value == "NULL":
                        value = "NULL"
                    else:
                        try:
                            value = str(int(float(value)))
                        except ValueError:
                            value = "NULL"
                    
                    
                elif value.replace('.', '', 1).isdigit():
                    pass

                if sql_column in {"eCATrackingCode"}:
                    trackingCode = value
                    

                value = value.replace("'", "''")
                value = value.strip()
                value = "'" + value + "'"

                if value == "" or value.lower() == "null" or value.lower().find("null") >= 0:
                    value = "NULL"

                values.append(value)
            
            inserter = []
            for col in sql_columns_list:
                inserter.append(values[sql_columns_list.index(col)])
            
            insert_statement = f" ({', '.join(inserter)})"
            
            if tracking_exists:
                update_set_clauses = []
                for column in sql_columns_list:
                    if column != "eCATrackingCode" and not (values[sql_columns_list.index(column)] == None or values[sql_columns_list.index(column)] == "" or values[sql_columns_list.index(column)] == "NULL"):
                        update_set_clauses.append(f"{column} = {values[sql_columns_list.index(column)]}")
                if update_set_clauses:
                    update_statements.append(
                        f"UPDATE {TABLE_NAME} SET {', '.join(update_set_clauses)} WHERE eCATrackingCode = '{trackingCode}'"
                    )
            else:
                insert_statements.append(insert_statement)
                self.record_skipped_tracking_code(tracking_code, "Tracking code not found in database; insert queued")
            ctr += 1
            

        print(f"We now have {len(insert_statements)} insert statements and {len(update_statements)} update statments.")

        
        # Execute all collected insert statements in one batch
        if insert_statements:
            batch_sizer = 999
            for i in range(0, len(insert_statements), batch_sizer):

                sys.stdout.write(f"\r        {int((i/len(insert_statements))*100)} %  -  {i}/{len(insert_statements)} inserts completed. ")
                sys.stdout.flush()
                print("")

                batch = insert_statements[i:i + batch_sizer]
                full_insert_statement = prefix_insert_statement + ", ".join(batch)
                try:
                    if not sql.execute(query=full_insert_statement):
                        raise RuntimeError("SQL execution failed")
                except Exception as e:
                    self.record_skipped_tracking_code(trackingCode, f"Insert failed: {str(e)}")
                    ret += f" <b style='color:red;'>Error running query => <strong>{str(e)}</strong></b><br>"
                ret += f"Running Query:  <b style='color:green;'>{full_insert_statement}</b><br>"
            ret += f"Running Query:  <b style='color:pink;'>{full_insert_statement}</b><br>"

        # Execute all collected update statements in one batch
        if update_statements:
            ctr = 1
            for update_statement in update_statements:
                sys.stdout.write(f"\r{int((ctr/len(update_statements))*100)} %  -  {ctr}/{len(update_statements)} updates completed. ")
                sys.stdout.flush()
                ctr+=1
                try:
                    if not sql.execute(query=update_statement):
                        raise RuntimeError("SQL execution failed")
                except Exception as e:
                    self.record_skipped_tracking_code(trackingCode, f"Update failed: {str(e)}")
                    ret += f" <b style='color:red;'>Error running query => <strong>{str(e)}</strong></b><br>"
                ret += f"Running Query:  <b style='color:yellow;'>{update_statement}</b><br>"

        return ret + " \n\n\n <hr/> Executed <b style='color:cyan;'>" + str(ctr) + "</b> txns.<hr/> "

    def clean_response(self,json):
        for i in range(len(json)):
            for key in json[i].keys():
                if isinstance(json[i][key], datetime):
                    json[i][key] = json[i][key].isoformat()
        return json


   
class Properties:
    def __init__(self, sql_conn):
        self.sql_conn = sql_conn
        self.BASE_COLUMNS = ["AppStartDate", "PrimarySSN", "PrimaryName"]

    @staticmethod
    def row_to_dict(description, row):
        return {description[i][0]: row[i] for i in range(len(row))}

    def ecaTrackingCode_exists(self, ecaTrackingCode):
        return len(self.get_properties_by_ecaTrackingCode(ecaTrackingCode).keys()) > 0
    def get_properties_by_ecaTrackingCode(self, ecaTrackingCode):
        # eCATrackingCode can be single string ora list of strings. Use IN clause and join with the transactions table to get the properties
        cursor = self.sql_conn.connection.cursor()
        if isinstance(ecaTrackingCode, list):
            placeholders = ', '.join(['?'] * len(ecaTrackingCode))
            query = f"SELECT * FROM Properties WHERE eCATrackingCode IN ({placeholders})"
            cursor.execute(query, ecaTrackingCode)
        else:
            query = f"SELECT * FROM Properties WHERE eCATrackingCode = ?"
            cursor.execute(query, (ecaTrackingCode,))
        rows = cursor.fetchall()
        properties = [self.row_to_dict(cursor.description, row) for row in rows]
        # Lets return a dict where key is eCATrackingCode and value is dict of properties for that code. Like {"ecatrackingcode": {"column1": value1, "column2": value2}}
        properties_dict = {}
        for prop in properties:
            code = prop.get("eCATrackingCode")
            if code not in properties_dict:
                properties_dict[code] = []
            properties_dict[code].append(prop)
        return properties_dict
    
    def set_properties_for_ecaTrackingCode(self, eCaTrackingCode, properties_data):
        # properties_data is a dict of column name and value. Like {"column1": value1, "column2": value2}
        # Ensure base columns are set in properties data
        for column in self.BASE_COLUMNS:
            column_value = properties_data.get(column)
            if not column_value:
                return {"error": f"Base column {column} is required."}
        # First we ensure its not already set.. we check if Property and eCATrackingCode combination is unique
        cursor = self.sql_conn.connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT CONCAT(Property, '-', ecaTrackingCode)) FROM Properties WHERE eCATrackingCode = ?", (eCaTrackingCode,))
        exists = cursor.fetchone()[0]
        if exists:
            # Lets Update
            for column, value in properties_data.items():
                if column.lower() in [col.lower() for col in self.BASE_COLUMNS]:
                    continue
                query = f"UPDATE Properties SET PropertyValue = ? WHERE eCATrackingCode = ? and Property = ?"
                cursor.execute(query, (value, eCaTrackingCode, column))
            self.sql_conn.connection.commit()
            return {"success": f"Properties for eCATrackingCode {eCaTrackingCode} have been updated."}
        
        # We will find the columns in the database and insert the values
        columns = []
        values = []
        for column, value in properties_data.items():
            if column.lower() in [col.lower() for col in self.BASE_COLUMNS]:
                continue
            query = f'''
                Insert INTO Properties (eCATrackingCode, AppStartDate, PrimarySSN, PrimaryName, Property, PropertyValue)
                VALUES(?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (eCaTrackingCode, properties_data.get("AppStartDate"), properties_data.get("PrimarySSN"), properties_data.get("PrimaryName"), column, value))
            columns.append(column)
            self.sql_conn.connection.commit()
        
        return {"success": f"Properties for eCATrackingCode {eCaTrackingCode} have been set."}


class WorkspaceExtract:
    def __init__(self):
        self.base_url = get_env_value("JM_BASE_URL")+"/workspaces"
        self.username = get_env_value("REACT_APP_JOURNEY_MANAGER_USER")
        self.password = get_env_value("REACT_APP_JOURNEY_MANAGER_PASSWORD")
        self.session = None
        self.setup_table()

        
    def setup_table(self):
        try:
            sql = SQLConn()
            sql.connect()
            txn = Transaction(sql)
            create_table_query = """
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[WorkspaceExtract]') AND type in (N'U'))
                BEGIN
                    CREATE TABLE [dbo].[WorkspaceExtract](
                    trackingCode NVARCHAR(255) PRIMARY KEY,
                    currentQueue NVARCHAR(255),
                    assignedTo NVARCHAR(255),
                    formName NVARCHAR(255),
                    timeCreated DATETIME,
                    jobRefNumber NVARCHAR(255),
                    dump NVARCHAR(MAX)
                )
                END
            """
            txn.sql_conn.connection.execute(create_table_query)
            txn.sql_conn.connection.commit()
            sql.disconnect()
        except Exception as e:
            print("SQL Error: ", e)
    
    def save_to_db(self, all_data, raw_data):
        print("Saving workspace data to DB...")
        for data in all_data:
            try:
                sql = SQLConn()
                sql.connect()
                txn = Transaction(sql)
                query = """
                    MERGE INTO WorkspaceExtract AS target
                    USING (VALUES (?, ?, ?, ?, ?, ?, ?)) AS source (trackingCode, currentQueue, assignedTo, formName, timeCreated, jobRefNumber, dump)
                    ON (target.trackingCode = source.trackingCode)
                    WHEN MATCHED THEN
                        UPDATE SET
                            currentQueue = source.currentQueue,
                            assignedTo = source.assignedTo,
                            formName = source.formName,
                            timeCreated = source.timeCreated,
                            jobRefNumber = source.jobRefNumber,
                            dump = source.dump
                    WHEN NOT MATCHED THEN
                        INSERT (trackingCode, currentQueue, assignedTo, formName, timeCreated, jobRefNumber, dump)
                        VALUES (source.trackingCode, source.currentQueue, source.assignedTo, source.formName, source.timeCreated, source.jobRefNumber, source.dump);
                """
                txn.sql_conn.connection.execute(query, 
                                                (
                                                    data.get("tracking_code"), 
                                                    data.get("current_queue"), 
                                                    data.get("assigned_to"), 
                                                    data.get("form_name"), 
                                                    data.get("time_created"), 
                                                    data.get("job_ref_number"),
                                                    json.dumps(raw_data)
                                                    )
                                                )
                txn.sql_conn.connection.commit()
                sql.disconnect()
            except Exception as e:
                print("SQL Error: ", e)

    def get_value(self, tracking_code: str) -> list:
        sql = SQLConn()
        sql.connect()
        txn = Transaction(sql)
        query = f"""
            SELECT * FROM WorkspaceExtract WHERE trackingCode = '{tracking_code}'
        """
        resp = txn.get_transactions_by_sql_query(query)
        sql.disconnect()
        if resp == 0:
            workspace_result = self.query_by_tracking_code(tracking_code)
            if not workspace_result:
                return []
            resp, raw_resp = workspace_result
            self.save_to_db(resp, raw_resp)
            return resp
        else:
            return resp[0]

    def login(self) -> bool:
        # Set up the session
        self.session = requests.Session()
        self.session.verify = True  # SSL verification
        """Authenticate and establish a session."""
        login_url = urljoin(
            self.base_url.rstrip("/") + "/",
            "j_spring_security_check",
        )
        
        try:
            print(f"[*] Logging in as {self.username}...")
            response = self.session.post(
                login_url,
                data={
                    "j_username": self.username,
                    "j_password": self.password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            # Check for JSESSIONID cookie
            if "JSESSIONID" in self.session.cookies:
                print(f"[+] Authentication successful! Session ID: {self.session.cookies.get('JSESSIONID')[:20]}...")
                return True
            else:
                print(f"[-] Authentication failed. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[-] Login error: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if the session is authenticated"""     
        return self.session is not None and "JSESSIONID" in self.session.cookies
    
    def query_by_tracking_code(
        self, 
        tracking_code: str, 
        offset: int = 0, 
        limit: int = 20,
        include_expired: bool = True
    ) -> Optional[dict]:
        
        if not self.is_authenticated():
            if not self.login():
                return None
        """Query workspaces for form data by tracking code."""
        query_url = urljoin(
            self.base_url.rstrip("/") + "/",
            "secure/api/v1/txn/query",
        )
        
        payload = {
            "scope": "Form",
            "filters": [
                {
                    "operator": "and",
                    "criteria": [
                        "formStatus in ('Assigned','Completed','In Progress','Opened','Saved','Submitted')",
                    ]
                },
                {
                    "operator": "or",
                    "criteria": [
                        "trackingCode = {0}",
                        "job.jobRefNumber = {0}",
                        "properties['Link.FnbDashboardTrackingCode'] = {0}"
                    ],
                    "params": [tracking_code]
                }
            ],
            "attributes": [
                "formStatus",
                "userLoginName",
                "availableActions",
                "taskType",
                "formUrl",
                "receiptUrl",
                "submitKey",
                "groupName",
                "formName",
                "job",
                "job.jobRefNumber",
                "trackingCode",
                "submissionXml",
                "properties['PrimaryName']",
                "formDataMap['PrimaryName']",
                "properties['PrimaryEmail']",
                "formDataMap['PrimaryEmail']",
                "properties['Mobile']",
                "formDataMap['Phone Number']",
                "timeCreated"
            ],
            "sorts": ["job.timeCreated desc"],
            "fetchLimit": limit,
            "fetchOffset": offset
        }
        
        try:
            print(f"\n[*] Querying for tracking code: {tracking_code}")
            response = self.session.post(
                query_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"[+] Query successful! Found {len(data.get('result', []))} results")
                return self.extract_queue_and_assigned(data)
            else:
                print(f"[-] Query failed. Status: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"[-] Query error: {e}")
            return None
    
    def extract_queue_and_assigned(self, result: dict) -> list:
        """Extract Current Queue and Assigned To from query results."""
        extracted = []
        
        for form_result in result.get('result', []):
            item = {
                "tracking_code": form_result.get('trackingCode'),
                "current_queue": form_result.get('formStatus'),  # Current Queue
                "assigned_to": form_result.get('userLoginName'),  # Assigned To
                "form_name": form_result.get('formName'),
                # Convert timeCreated to ISO format if it's not None
                "time_created": form_result.get('timeCreated'),
                "job_ref_number": form_result.get('job', {}).get('jobRefNumber') if form_result.get('job') else None
            }
            if item["time_created"]:
                # the current string format is 2026-05-12T14:40:15-06:00
                item["time_created"] = item["time_created"].replace("T", " ").replace("-06:00", "")
            # Sort by time_created. Earliest time first
            extracted = sorted(extracted, key=lambda x: x["time_created"] if x["time_created"] else "9999-12-31 23:59:59")
            
            # remove \n from submissionXml in the result variable
            if form_result.get('submissionXml'):
                form_result['submissionXml'] = form_result['submissionXml'].replace('\n', '').replace('\r', '').replace("  ", " ")
            extracted.append(item)
            if item.get("tracking_code") is None:
                print(f"    Warning: tracking_code is None in form result: {form_result}")
        
        return extracted, result.get('result', [])

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def query_maker(tablename = "[DigitalReport].[dbo].[Transactions]", columns = [], where = [], order_by = None, limit = None, debug=False):
    if len(columns) == 0:
        columns = "*"
    else:
        columns = sorted(list(set(columns)))
        columns = ', '.join(columns)
    
    TOP = ""
    if limit:
        TOP = f" TOP {limit}"

    query = f"SELECT {TOP} {columns} FROM {tablename} WITH (NOLOCK)"
    
    if len(where) > 0:
        where_clauses = []
        for condition in where:
            if isinstance(condition, dict):
                for key, value in condition.items():
                    if isinstance(value, str):
                        value = f"'{value}'"
                    where_clauses.append(f"{key} = {value}")
            elif condition == "":
                continue
            else:
                where_clauses.append(condition)
        query += " WHERE " + " AND ".join(where_clauses)
    
    
    items = [item for item in query.split(" ") if item.strip()]
    for i in range(len(items)):
        items[i] = items[i].strip()
    
        
        
        # Get rid of double white space and double AND
        if items[i] == "AND" and i > 0 and items[i-1] == "AND":
            items[i] = ""
        if items[i] == "AND" and i > 0 and items[i-1] == "WHERE":
            items[i] = ""
    query = " ".join(items)


    
    
    if order_by:
        query += f" ORDER BY {order_by}"
    
    

    if debug:
        print(" ________________________________________________")
        print(query)
        print(" ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

    
    return query

def Q(sql=None, tablename="[DigitalReport].[dbo].[Transactions]", columns=[], where=[], order_by=None, limit=None, debug=False, filename=None, queryOnly=False, params=[], use_cache=True):
    """
    A function to query the database using a SQLConn object or a SQLite file.
    Parameters:
    - sql: An instance of SQLConn to connect to the database.
    - tablename: The name of the table to query.
    - columns: A list of columns to select. If empty, selects all columns.
    - where: A list of conditions to filter the results. Each condition can be a string or a dictionary.
    - order_by: The column to order the results by. Defaults to "ASC".
    - limit: The maximum number of results to return. If None, returns all results.
    - fileName: Optional. If provided, queries the specified SQLite database file instead of SQL Server.
    - queryOnly: If set to True, it returns just the query.
    - use_cache: If False, execute the query without reading or writing the SQL result cache.
    Returns:
    - A list of transactions matching the query.
    """

    if len(params) > 0:
        where = where + params_to_condition_list(params)

    if sql == None:
        sql = SQLConn()

    if debug:
        for c in columns:
            if c not in list(TABLE_STRUCTURE.keys()):
                print("Invalid column name:", c)

    query = query_maker(tablename, columns, where, order_by, limit)
    
    if queryOnly:
        return query
    if isinstance(sql, Transaction):
        txn = sql
    else:
        if not sql.connection:
            sql.connect()
        txn = Transaction(sql)
    
    return txn.get_transactions_by_sql_query(query, debug=debug, use_cache=use_cache)

def get_EDW( temenos_id, tables =[], join_columns=[], kind="CRFEDW", queryOnly=False, top = "TOP 1"):
    
    aliases = set()
    ctr = 1
    while len(aliases) < len(tables):
        alias = "table"+str(ctr)
        aliases.add(alias)
        ctr += 1

    aliases = list(aliases)
    extra_joins = ""
    join_cols = ""
    prefix_table = f"[{kind}].[CRF_EMPL_PII_V1]"
    # Add JOINs
    for i in range(0, len(tables)):
        join_condition = f"mt.APPDETAILID = {aliases[i]}.APPDETAILID"
        extra_joins += f"JOIN {prefix_table}.[{tables[i]}] AS {aliases[i]}\n    ON {join_condition}\n"
        join_cols += f"{aliases[i]}.*,"

    if len(join_columns) > 0:
        join_cols = ", ".join(join_columns)
    
    join_cols = join_cols.rstrip(",")

    query = f'''
    SELECT {top}
    {"*" if join_cols == "" else join_cols}
    FROM [{kind}].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMFIELDS_CUR] AS mt
    JOIN [{kind}].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR] AS ot
        ON mt.APPDETAILID = ot.APPDETAILID
    {extra_joins}
    WHERE mt.Temenos_ID = '{temenos_id}';
    '''
    if queryOnly:
        return query
    
    sql = SQLConn(kind=kind)
    sql.connect()
    txn = Transaction(sql)
    resp = txn.get_transactions_by_sql_query(query)
    sql.disconnect()
    if resp == 0:
        return None
    
    return resp[0]



def insert_unique_jmextract(connector, tid, raw_data):
    if not connector.connection:
        print("No active connection")
        return

    cursor = connector.connection.cursor()
    load_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Check if tID already exists
    cursor.execute("SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) FROM Transactions WHERE eCATrackingCode = ?", (tid,))
    exists = cursor.fetchone()[0]

    if exists:
        print(f"tID {tid} already exists. Please use a unique tID.")
    else:
        # Serialize raw_data to JSON
        raw_data_json = json.dumps(raw_data)

        # Insert new record
        query = "INSERT INTO JMExtract (tID, LoadDateTime, RawData) VALUES (?, ?, ?)"
        cursor.execute(query, (tid, load_datetime, raw_data_json))
        connector.connection.commit()
        print(f"Record with tID {tid} inserted successfully.")

    cursor.close()