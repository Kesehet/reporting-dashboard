import pyodbc
pyodbc.pooling = False
from datetime import datetime
from dateutil import parser
import json
from datetime import datetime
from decimal import Decimal
import sys
from dotenv import load_dotenv
from config import get_env_value
from dateutil.parser import parse
import base64
import pandas as pd
import time
from report_modules.condition_utils import TABLE_STRUCTURE, PRIMARY_NAME_IGNORE, CSV_TO_SQL_COLUMNS, TABLE_NAME
import os
import hashlib
import pickle

load_dotenv()

class SQLConn:
    def __init__(self, kind="" ):
        self.kind = kind
        if kind != "":
            kind = kind + "_"        
        self.user = get_env_value(kind+'SQL_USER')
        self.host =  get_env_value(kind+'SQL_HOST')
        self.database =  get_env_value(kind+'SQL_DATABASE')
        self.connection = None

    def connect(self):
        try:
            connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.host};"
            f"DATABASE={self.database};"
            # f"UID={self.user};"
            f"Trusted_Connection=Yes;"
            f"ColumnEncryption=Enabled;"
            f"Integrated Security=Yes;"
            
            )
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
            return
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
            else:
                
                print(f"Error executing query: {e} \nQuery: {query}")
        


        if debug:
            if len(query) > 300:
                    with open("SQL Failed.txt", 'a') as f:
                        f.write(query+"\n")
            print(f"Executed query: {query[0:50]}")
        self.connection.commit()

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
            customer = Customer(self.sql_conn)
            blocked_customer_columns = ["Id", "PlaceHolder1","PlaceHolder2","tId","TypeConsumer"]
            customers = customer.get_customer_by_tid(transaction.get("tId"))
            for i in range(len(customers)):
                for key in customers[i].keys():
                    if key in blocked_customer_columns:
                        continue                  
                    transaction[f"Customer_{i}_{key}"] = customers[i][key]
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
    
    def get_transactions_by_sql_query(self, query, debug=False):

        # Create cache directory if it doesn't exist
        cache_dir = ".cache_requests"
        os.makedirs(cache_dir, exist_ok=True)

        # Generate a unique filename based on the query hash
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_file = os.path.join(cache_dir, f"{query_hash}.pkl")

        # Try loading from cache
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print("Failed to load cache:", e)

        if debug:
            print("Executing SQL query:")
            print(query)
            print("-----------------------------------------")

        resp = 0
        try:
            cursor = self.sql_conn.connection.cursor()
            cursor.execute(query, ())
            rows = cursor.fetchall()
            transactions = [self.row_to_dict(cursor.description, row) for row in rows]

            cleaned_resp = self.clean_response(transactions)
            if len(cleaned_resp) == 0:
                resp = 0
            elif "as data" in query.lower():
                resp = cleaned_resp[0]["data"] if cleaned_resp[0]["data"] else 0
            else:
                resp = cleaned_resp
        except Exception as e:
            print(e, query)

        try:
            resp = float(resp)
        except:
            pass

        # Save to cache
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(resp, f)
        except Exception as e:
            print("Failed to save cache:", e)

        return resp

        
        
    def set_transaction_from_list_of_dicts(self, sql: SQLConn, all_rows, dataSource="unknown"):

        #__________________________________________________________________________________________________________________________________
        trackingCode = ""
        ret = ""
        ctr = 0
        insert_statements = []  # Collect all insert statements here
        update_statements = []  # Collect all update statements here
        old_txns = [code for code in self.get_eCATrackingCodes() if code is not None or code != ""]
        if not old_txns:
            old_txns = []
        
        
        # ____________________________________________ THE LOOP ______________________________________________________
        seen_tracking_codes = set()

        

        for row in all_rows:
            values = []
            tracking_code = row.get("eCA Tracking Code")
            dataSource = row['DataSource']
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
                ret += f"ECa Tracking code is ignored in row as its null <pre>{row}</pre>.<br>"
                continue

            
            if tracking_code in seen_tracking_codes:
                    ret += f"Duplicate ECa Tracking code found and ignored <pre>{row}</pre>.<br>"
                    continue

            seen_tracking_codes.add(tracking_code)

            

            if str(row.get("Primary Name")).lower() in PRIMARY_NAME_IGNORE or str(row.get("Primary Name")).find("test") != -1:
                ret += f"Primary Name is ignored in row <pre>{row}</pre>.<br>"
                continue

            sys.stdout.write(f"\r        {int((ctr/len(all_rows))*100)} %  -  {ctr}/{len(all_rows)} preprocessed. ")
            sys.stdout.flush()
            for csv_column, sql_column in M_CSV_TO_SQL_COLUMNS.items():
                value = str(row.get(csv_column, "")).strip() if pd.notna(row.get(csv_column, "")) else "NULL"

                # Strip PII for development
                if (get_env_value("CURRENT_ENV") == "dev" or  get_env_value("CURRENT_ENV") == "qa") and  sql_column in {"PrimarySSN"}:
                    value = "NULL"
                
                if (get_env_value("CURRENT_ENV") == "dev" or  get_env_value("CURRENT_ENV") == "qa") and sql_column in {"PrimaryName"}:
                    # base64 encode the name
                    value_bytes = value.encode("utf-8")
                    value = base64.b64encode(value_bytes).decode("utf-8")

                if sql_column in {"AppStartDate", "AppSubmitDate", "AppUpdateDate"} and value not in {"NULL", ""}:
                    value = f"{parse(value).strftime('%Y-%m-%d %H:%M:%S')}"
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
            
            
            
            if trackingCode not in old_txns:
                insert_statements.append(insert_statement)
            else:
                update_set_clauses = []
                for column in sql_columns_list:
                    if column != "eCATrackingCode" and not (values[sql_columns_list.index(column)] == None or values[sql_columns_list.index(column)] == "" or values[sql_columns_list.index(column)] == "NULL"):
                        update_set_clauses.append(f"{column} = {values[sql_columns_list.index(column)]}")
                if update_set_clauses:
                    update_statements.append(
                        f"UPDATE {TABLE_NAME} SET {', '.join(update_set_clauses)} WHERE eCATrackingCode = '{trackingCode}'"
                    )
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
                    sql.execute(query=full_insert_statement)
                    sql.connection.commit()
                except Exception as e:
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
                    sql.execute(query=update_statement)
                    sql.connection.commit()
                except Exception as e:
                    ret += f" <b style='color:red;'>Error running query => <strong>{str(e)}</strong></b><br>"
                ret += f"Running Query:  <b style='color:yellow;'>{update_statement}</b><br>"

        return ret + " \n\n\n <hr/> Executed <b style='color:cyan;'>" + str(ctr) + "</b> txns.<hr/> "

    def clean_response(self,json):
        for i in range(len(json)):
            for key in json[i].keys():
                if isinstance(json[i][key], datetime):
                    json[i][key] = json[i][key].isoformat()
        return json



class Customer:
    def __init__(self, sql_conn):
        self.sql_conn = sql_conn

    def get_customer_by_tid(self, tId):
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT * FROM Customer WHERE tId = ?"
        cursor.execute(query, (tId,))
        rows = cursor.fetchall()
        customer_data = []
        for row in rows:
            if row:
                customer_data.append(self.row_to_dict(cursor.description, row))                
            else:
                return {"error": "Customer not found"}
        return customer_data

    def save_customer(self, customer_data):
        tId = customer_data.get("tId")
        SSN_TIN = customer_data.get("SSN_TIN")
        # Check if the customer already exists
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT COUNT(*) FROM Customer WHERE tId = ? and SSN_TIN  = ?"

        cursor.execute(query, (tId,SSN_TIN,))
        exists = cursor.fetchone()[0]

        if exists:
            return {"error": f"Customer with tId {tId} already exists."}

        columns = ["tId", "FirstName", "LastName", "isPrimary", "TypeConsumer", "SSN_TIN", "PhoneNumber", "EmailAddress", "AddressStreet1", "AddressStreet2", "AddressCity", "AddressState", "AddressZip", "PlaceHolder1", "PlaceHolder2"]
        values = tuple(customer_data.get(column) for column in columns)

        self.sql_conn.push_data("Customer", columns, [values])
        return {"success": f"Customer with tId {tId} has been created."}

    def get_all_customers(self):
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT * FROM Customer"
        cursor.execute(query)
        rows = cursor.fetchall()
        customers = [self.row_to_dict(cursor.description, row) for row in rows]
        return json.dumps(customers, cls=CustomJSONEncoder)

    def get_customers_by_column(self, column_name, value):
        cursor = self.sql_conn.connection.cursor()
        query = f"SELECT * FROM Customer WHERE {column_name} = ?"
        cursor.execute(query, (value,))
        rows = cursor.fetchall()
        customers = [self.row_to_dict(cursor.description, row) for row in rows]
        return json.dumps(customers)
    
    
    def row_to_dict(self, description, row):
        return {description[i][0]: row[i] for i in range(len(row))}
    

class Product:
    def __init__(self, sql_conn):
        self.sql_conn = sql_conn

    def get_product_by_id(self, product_id):
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT * FROM Product WHERE ProductID = ?"
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        if product:
            product_data = self.row_to_dict(cursor.description, product)
            return json.dumps(product_data)
        else:
            return json.dumps({"error": "Product not found"})

    def save_product(self, product_data):
        product_id = product_data.get("ProductID")
        if not product_id:
            return {"error": f"Product Id was null."}
        # Check if the product already exists
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT COUNT(*) FROM Product WHERE ProductID = ?"

        cursor.execute(query, (product_id,))
        exists = cursor.fetchone()[0]

        if exists:
            return {"error": f"Product with ProductID {product_id} already exists."}

        columns = [ "ProductID", "ProductName", "TypeDeposit", "ProductDescription", "AmontToFund", "isActive"]
        values = tuple(product_data.get(column) for column in columns)

        self.sql_conn.push_data("Product", columns, [values])
        return {"success": f"Product with ProductID {product_id} has been created."}

    def get_all_products(self):
        cursor = self.sql_conn.connection.cursor()
        query = "SELECT * FROM Product"
        cursor.execute(query)
        rows = cursor.fetchall()
        products = [self.row_to_dict(cursor.description, row) for row in rows]
        return json.dumps(products, cls=CustomJSONEncoder)

    def get_products_by_column(self, column_name, value):
        cursor = self.sql_conn.connection.cursor()
        query = f"SELECT * FROM Product WHERE {column_name} = ?"
        cursor.execute(query, (value,))
        rows = cursor.fetchall()
        products = [self.row_to_dict(cursor.description, row) for row in rows]
        return json.dumps(products)

    def row_to_dict(self, description, row):
        return {description[i][0]: row[i] for i in range(len(row))}



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
        columns = ', '.join(columns)
    
    TOP = ""
    if limit:
        TOP = f" TOP {limit}"

    query = f"SELECT {TOP} {columns} FROM {tablename}"
    
    if len(where) > 0:
        where_clauses = []
        for condition in where:
            if isinstance(condition, dict):
                for key, value in condition.items():
                    if isinstance(value, str):
                        value = f"'{value}'"
                    where_clauses.append(f"{key} = {value}")
            else:
                where_clauses.append(condition)
        query += " WHERE " + " AND ".join(where_clauses)
    
    # Get rid of double white space and double AND
    items = [item for item in query.split(" ") if item.strip()]
    for i in range(len(items)):
        items[i] = items[i].strip()
    
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

def Q(sql=None, tablename="[DigitalReport].[dbo].[Transactions]", columns=[], where=[], order_by=None, limit=None, debug=False, filename=None, queryOnly=False):
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
    Returns:
    - A list of transactions matching the query.
    """

    if sql == None:
        sql = SQLConn()

    query = query_maker(tablename, columns, where, order_by, limit)
    
    if queryOnly:
        return query
    if isinstance(sql, Transaction):
        txn = sql
    else:
        if not sql.connection:
            sql.connect()
        txn = Transaction(sql)
    
    return txn.get_transactions_by_sql_query(query, debug=debug)

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
    cursor.execute("SELECT COUNT(*) FROM Transactions WHERE eCATrackingCode = ?", (tid,))
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