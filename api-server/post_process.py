import base64
import logging

import os
from datetime import datetime
from datetime import datetime
from metrics import update_metrics, update_metrics_from_sql
from report_modules.condition_utils import *
from DB import SQLConn, Transaction, Properties, WorkspaceExtract
import sys
from utils import process_account_number
from helper.encryption_helper import encrypt_decrypt_string, is_encrypted

logger = logging.getLogger(__name__)


def post_process_txns(sql, txn, tracking_codes_added_this_run=None):
    if tracking_codes_added_this_run is None:
        tracking_codes_added_this_run = set()

    print("Starting post processing of transactions...")
    we = WorkspaceExtract()

    try:
        ensure_properties_table(txn)
    except Exception as e:
        print("Error creating Properties table" + str(e))

    try:
        populate_properties_table(sql, txn)
    except Exception as e:
        print("Error populating Properties table" + str(e))

    try:
        process_dds_amounts(sql, txn)
    except Exception as e:
        print("Error processing DDS amounts" + str(e))

    try:
        account_status_fetch(sql, txn)
    except Exception as e:
        print("Error in account_status_fetch" + str(e))

    try:
        encrypt_all_pii_columns(sql, txn)
    except Exception as e:
        logger.exception("PII encryption failed; do not silently persist unencrypted data")
        raise
    
    try:
        load_workspace_data(we, txn, tracking_codes_added_this_run)
    except Exception as e:
        print("Error in extract_workspace_data" + str(e))

    
    print("Finished post processing of transactions.")


def ensure_properties_table(txn):
    txn.sql_conn.execute(f'''
        IF OBJECT_ID('[DigitalReport].[dbo].[Properties]', 'U') IS NULL
        BEGIN
            CREATE TABLE [DigitalReport].[dbo].[Properties] (
                eCATrackingCode VARCHAR(50) NOT NULL PRIMARY KEY,
                AppStartDate DATETIME NULL,
                PrimaryName NVARCHAR(100) NOT NULL,
                PrimarySSN NVARCHAR(100) NOT NULL,
                Property VARCHAR(100) NOT NULL,
                PropertyValue NVARCHAR(MAX) NULL
            );
        END
        ELSE
        BEGIN
            IF COL_LENGTH('[DigitalReport].[dbo].[Properties]', 'eCATrackingCode') IS NULL
                ALTER TABLE [DigitalReport].[dbo].[Properties]
                ADD eCATrackingCode VARCHAR(50) NOT NULL DEFAULT('');

            IF COL_LENGTH('[DigitalReport].[dbo].[Properties]', 'AppStartDate') IS NULL
                ALTER TABLE [DigitalReport].[dbo].[Properties]
                ADD AppStartDate DATETIME NULL;

            IF COL_LENGTH('[DigitalReport].[dbo].[Properties]', 'PrimaryName') IS NULL
                ALTER TABLE [DigitalReport].[dbo].[Properties]
                ADD PrimaryName NVARCHAR(100) NOT NULL DEFAULT('');

            IF COL_LENGTH('[DigitalReport].[dbo].[Properties]', 'PrimarySSN') IS NULL
                ALTER TABLE [DigitalReport].[dbo].[Properties]
                ADD PrimarySSN NVARCHAR(100) NOT NULL DEFAULT('');

            IF COL_LENGTH('[DigitalReport].[dbo].[Properties]', 'Property') IS NULL
                ALTER TABLE [DigitalReport].[dbo].[Properties]
                ADD Property VARCHAR(100) NOT NULL DEFAULT('');

            IF COL_LENGTH('[DigitalReport].[dbo].[Properties]', 'PropertyValue') IS NULL
                ALTER TABLE [DigitalReport].[dbo].[Properties]
                ADD PropertyValue NVARCHAR(MAX) NULL;

            IF NOT EXISTS (
                SELECT 1
                FROM sys.key_constraints
                WHERE name = 'PK_Properties'
            )
            BEGIN
                ALTER TABLE [DigitalReport].[dbo].[Properties]
                ADD CONSTRAINT PK_Properties PRIMARY KEY (eCATrackingCode);
            END
        END
    ''')
    print("Checked for Properties table and created if not exists, also added missing columns if any.")


def populate_properties_table(sql, txn):
    properties = Properties(sql)
    PIPE_SEPERATED_COLUMNS = ["AccountNumber", "DepositAcctStatus", "LoanAcctStatus"]
    all_txns = txn.get_transactions_by_sql_query(f'''
        SELECT APPStartDate, eCATrackingCode, PrimaryName, PrimarySSN, {", ".join(PIPE_SEPERATED_COLUMNS)} FROM [DigitalReport].[dbo].[Transactions]
        WHERE PrimarySSN IS NOT NULL AND PrimarySSN != ''
          AND {excludeBotData} AND {excludeZeroProductApps}
          AND {approvedAppsForBPMandCRIF}
    ''')
    if all_txns == 0:
        all_txns = []

    for txn_row in all_txns:
        eCATrackingCode = txn_row.get("eCATrackingCode")
        if properties.ecaTrackingCode_exists(eCATrackingCode):
            continue

        for column in PIPE_SEPERATED_COLUMNS:
            account_numbers = process_account_number(txn_row.get(column) or "")
            for i, account_number in enumerate(account_numbers):
                txn_row[f"{column}_{i}"] = account_number
            txn_row.pop(column, None)

        properties.set_properties_for_ecaTrackingCode(eCATrackingCode, txn_row)


def process_dds_amounts(sql, txn):
    all_ecatrackingCodes_with_null_accounts = txn.get_transactions_by_sql_query('''
        SELECT eCATrackingCode, AppStartDate, AccountNumber, PrimaryName, PrimarySSN
        FROM [DigitalReport].[dbo].[Transactions]
        WHERE NumLendingProducts > 0
        ORDER BY AppStartDate DESC
    ''')
    if all_ecatrackingCodes_with_null_accounts == 0:
        all_ecatrackingCodes_with_null_accounts = []

    properties = Properties(sql)
    total_items = len(all_ecatrackingCodes_with_null_accounts)
    runs = 0

    for item in all_ecatrackingCodes_with_null_accounts:
        tcc = item.get("eCATrackingCode")
        appstartdate = item.get("AppStartDate")
        accNo = item.get("AccountNumber")
        if not accNo:
            continue

        for acc in process_account_number(accNo):
            doll_amt = get_dds_dollar_amount(acc, appstartdate)
            if doll_amt is None:
                continue

            sql.execute(f'''
                UPDATE [DigitalReport].[dbo].[Transactions]
                SET DDSTranAmount = {doll_amt}
                WHERE eCATrackingCode = '{tcc}'
            ''')
            sql.connection.commit()

            month_year = datetime.now().strftime("%m_%Y")
            property_key = f"Account_{acc}_{month_year}"
            properties.set_properties_for_ecaTrackingCode(tcc, {
                "AppStartDate": appstartdate,
                "PrimaryName": item.get("PrimaryName"),
                "PrimarySSN": item.get("PrimarySSN"),
                property_key: doll_amt
            })

            runs += 1
            if total_items:
                sys.stdout.write(f"\r{int((runs / total_items) * 100)}% - DDS dollar amount for account number {acc}. - {doll_amt}     ")
                sys.stdout.flush()


def load_workspace_data(workspace, txn, tracking_codes_added_this_run):
    trackingCodes_to_extract = txn.get_transactions_by_sql_query(f'''
        SELECT t.eCATrackingCode, w.tId FROM [DigitalReport].[dbo].[Transactions] AS t
        LEFT JOIN [DigitalReport].[dbo].[JMExtract] w ON t.eCATrackingCode = w.tID
        WHERE w.tID IS NOT NULL AND t.eCATrackingCode IS NOT NULL
          AND {excludeBotData} AND {excludeZeroProductApps}
    ''')
    if trackingCodes_to_extract == 0:
        trackingCodes_to_extract = []

    pending_tracking_codes = set([row.get("eCATrackingCode") for row in trackingCodes_to_extract])
    tracking_codes_to_process = pending_tracking_codes.union(tracking_codes_added_this_run)
    print(f"Found {len(pending_tracking_codes)} pending and {len(tracking_codes_added_this_run)} current-run tracking codes that need workspace data extraction...")

    for tracking_code in tracking_codes_to_process:
        if tracking_code is None:
            continue
        print(f"Extracting workspace data for tracking code {tracking_code}...")
        extract_workspace_data(workspace, tracking_code)


def extract_workspace_data(workspace, trackingCode):
    try:
        data = workspace.get_value(trackingCode)
        return data
        
    except Exception as e:
        print("Error in extract_workspace_data" + str(e))
        


def metrics_updater(sql, txn):
    try:
        all_app_status_filter = ','.join([f'\'{app}\'' for app in ALL_APP_STATUS])
        update_metrics_from_sql(
            "new_app_statuses",txn,
            f'''    Select DISTINCT AppStatus
                    From [DigitalReport].[dbo].[Transactions]
                    Where  AppStatus NOT IN ({all_app_status_filter});
            '''
        )
    except Exception as e:
        print("Error processing new app statuses" + str(e))


    try:
        update_metrics_from_sql("bot_users", txn,
                '''     SELECT TOP 10
                            PrimaryName,
                            COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS SeenCount
                        FROM 
                            [DigitalReport].[dbo].[Transactions]
                        WHERE 
                            AppStartDate >= DATEADD(DAY, -15, GETDATE())
                        GROUP BY 
                            PrimaryName
                        HAVING 
                            COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 100
                        ORDER BY 
                            SeenCount DESC;
                '''
                            )
    except Exception as e:
        print("Error processing bot users" + str(e))
        




def account_status_fetch(sql, txn):

    sql_crfedw = SQLConn("CRFEDW")
    sql_crfedw.connect()
    sql_PTYEDW = SQLConn("PTYEDW")
    sql_PTYEDW.connect()
    if not sql_crfedw.connection or not sql_PTYEDW.connection:
        print("Skipping account status post processing because an EDW connection could not be established.")
        sql_crfedw.disconnect()
        sql_PTYEDW.disconnect()
        return
    txn_crfedw = Transaction(sql_crfedw)
    txn_PTYEDW = Transaction(sql_PTYEDW)
    properties = Properties(sql)
    
    # Select SSN, APPID from [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMER_CUR] where SSN IN (list of PrimarySSN from transactions ) - push appid to VSDISWEBPRD01
    # Select APPID, DecisionStatusName from [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR] where AppID IN (list of appid from above) - push decision status to VSDISWEBPRD01
    # Select SSN, DDA_ACCT_NUM from [PTYEDW].[PTY_EMPL_PII_V2].[PTYMSTR_DDA] where SSN IN (list of PrimarySSN from transactions]. push the acct num to VSDISWEBPRD01
    # Select Status_Code_desc, DDA_ACCT_NUM from [CAMEDW].[CAM_EMPL_PII_V1].[CAM_DDA_TRAN] where DDA_ACCT_NUM IN (list of acct num from above)  push the status code desc to VSDISWEBPRD01


    get_all_loans_ssn = txn.get_transactions_by_sql_query(f'''
        SELECT DISTINCT PrimarySSN, ecaTrackingCode, EDW_APPID, LoanAcctStatus, AppStartDate, PrimaryName FROM [DigitalReport].[dbo].[Transactions] WHERE 
                                                          PrimarySSN IS NOT NULL AND PrimarySSN != ''
                                                          AND {excludeBotData} AND {excludeZeroProductApps}
                                                          AND {approvedAppsForBPMandCRIF}
    ''')

    get_all_deposit_ssn = txn.get_transactions_by_sql_query(f'''
        SELECT DISTINCT PrimarySSN, ecaTrackingCode, AccountNumber, DepositAcctStatus, AppStartDate, PrimaryName FROM [DigitalReport].[dbo].[Transactions] WHERE 
                                                            PrimarySSN IS NOT NULL AND PrimarySSN != '' 
                                                            AND NumDepositProducts > 0
                                                            AND {excludeBotData} AND {excludeZeroProductApps}
                                                            AND {approvedAppsForBPMandCRIF}
    ''')
    
    print(f"Found {len(get_all_loans_ssn)} unique SSNs with loans and {len(get_all_deposit_ssn)} unique SSNs with deposit accounts to process for app ids, account numbers, and statuses...")
    try:
        for ssn_row in get_all_loans_ssn:
            if properties.ecaTrackingCode_exists(ssn_row.get("ecaTrackingCode")):
                continue
            ssn = ssn_row.get("PrimarySSN").replace("-", "")
            app_ids = txn_crfedw.get_transactions_by_sql_query(f'''
                SELECT DISTINCT APPID FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMER_CUR] WHERE SSN = '{ssn}'
            ''')
            
            if app_ids == 0:
                app_ids = []

            for i, app_id_row in enumerate(app_ids):
                properties.set_properties_for_ecaTrackingCode(ssn_row.get("ecaTrackingCode"), {
                    f"AppID_{i}": app_id_row.get("APPID"),
                    "PrimaryName": ssn_row.get("PrimaryName"),
                    "PrimarySSN": ssn_row.get("PrimarySSN"),
                    "AppStartDate": ssn_row.get("AppStartDate")
                })

            for i, app_id_row in enumerate(app_ids):
                app_id = app_id_row.get("APPID")

                # We push the decision status to VSDISWEBPRD01 by matching on appid
                decision_status = txn_crfedw.get_transactions_by_sql_query(f'''
                    SELECT DISTINCT DecisionStatusName FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR] WHERE APPID = '{app_id}'
                ''')
                if decision_status == 0:
                    decision_status = []

                for j, status_row in enumerate(decision_status):
                    properties.set_properties_for_ecaTrackingCode(ssn_row.get("ecaTrackingCode"), {
                        f"AppID_{i}_LoanAcctStatus_{j}": status_row.get("DecisionStatusName"),                        
                        "PrimaryName": ssn_row.get("PrimaryName"),
                        "PrimarySSN": ssn_row.get("PrimarySSN"),
                        "AppStartDate": ssn_row.get("AppStartDate")
                    })

    except Exception as e:
        print("Error processing loan account statuses" + str(e))

    print("Finished processing loan account statuses. Starting deposit account post processing...")
    try:
        for ssn_row in get_all_deposit_ssn:
            if properties.ecaTrackingCode_exists(ssn_row.get("ecaTrackingCode")):
                continue

            ssn = (ssn_row.get("PrimarySSN") or "").replace("-", "")
            account_numbers = txn_PTYEDW.get_transactions_by_sql_query(f'''
                SELECT DISTINCT DDA_ACCT_NUM FROM [PTYEDW].[PTY_EMPL_PII_V2].[PTYMSTR_DDA] WHERE SSN = '{ssn}'
            ''')
            if account_numbers == 0:
                account_numbers = []

            external_accounts = [str(ac.get("DDA_ACCT_NUM")) for ac in account_numbers if ac.get("DDA_ACCT_NUM")]
            all_account_numbers = process_account_number("|".join([str(ssn_row.get("AccountNumber") or "")] + external_accounts))

            for i, acc in enumerate(all_account_numbers):
                properties.set_properties_for_ecaTrackingCode(ssn_row.get("ecaTrackingCode"), {
                    f"AccountNumber_{i}": acc,
                    "PrimaryName": ssn_row.get("PrimaryName"),
                    "PrimarySSN": ssn_row.get("PrimarySSN"),
                    "AppStartDate": ssn_row.get("AppStartDate")
                })

                status_code = txn_PTYEDW.get_transactions_by_sql_query(f''' 
                    SELECT DISTINCT Status_Code_desc FROM [CAMEDW].[CAM_EMPL_PII_V1].[CAM_DDA_TRAN] WHERE DDA_ACCT_NUM = '{acc}'
                ''')
                if status_code == 0:
                    status_code = []

                for j, status_row in enumerate(status_code):
                    properties.set_properties_for_ecaTrackingCode(ssn_row.get("ecaTrackingCode"), {
                        f"AccountNumber_{i}_DepositAcctStatus_{j}": status_row.get("Status_Code_desc"),
                        "PrimaryName": ssn_row.get("PrimaryName"),
                        "PrimarySSN": ssn_row.get("PrimarySSN"),
                        "AppStartDate": ssn_row.get("AppStartDate")
                    })
                
    except Exception as e:
        print("Error processing deposit account statuses" + str(e))
        
    print("Finished processing deposit account statuses.")
    sql_crfedw.disconnect()
    sql_PTYEDW.disconnect()
    
                    

        
# SELECT ACCT_ID, ACCT_NUM, TAX_ID FROM [PTYEDW].[PTY_EMPL_PII_V2].[PTYMSTR_DDA] where TAX_ID IN ()
# SELECT APPID, SSN FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMER_CUR] where SSN IN ()




# appid1, appid2, acctid1, acctid2 = appid1|appid2|acctid1|acctid2

    


def get_dds_dollar_amount(acct_number, appstartdate):
    camedw_sql = SQLConn("CAMEDW")
    camedw_sql.connect()
    camedw_txn = Transaction(camedw_sql)
    appstartdate = str(appstartdate).split("T")[0] if appstartdate else None
    date_filter = f"AND Tran_Date <= '{appstartdate}'" if appstartdate else ""
    result = camedw_txn.get_transactions_by_sql_query(f'''
        SELECT TOP 1 [Tran_Amount] FROM [CAMEDW].[CAM_EMPL_PII_V1].[CAM_DDA_TRAN]
        WHERE [DDA_ACCT_NUM] = '{acct_number}'
          AND Tran_Amount IS NOT NULL
          AND Tran_Amount != 0
          AND {DDSDescriptionFilter}
          {date_filter}
        ORDER BY [Tran_Date] DESC
    ''')
    camedw_sql.disconnect()
    if result == 0 or not result:
        return None
    first_row = result[0]
    return first_row.get("Tran_Amount")



def encrypt_all_pii_columns(sql, txn):
    """Encrypt new plaintext only; migrate historic ciphertext separately."""
    for table_name in ("[DigitalReport].[dbo].[Transactions]",
                       "[DigitalReport].[dbo].[Properties]"):
        cursor = sql.connection.cursor()
        cursor.execute("SELECT eCATrackingCode, PrimaryName, PrimarySSN FROM " + table_name)
        rows = cursor.fetchall()
        for tracking_code, primary_name, primary_ssn in rows:
            updated = []
            for value in (primary_name, primary_ssn):
                if value is None or value == "" or is_encrypted(value):
                    updated.append(value)
                else:
                    updated.append(encrypt_decrypt_string(str(value), mode="encrypt"))
            if updated != [primary_name, primary_ssn]:
                cursor.execute(
                    "UPDATE " + table_name +
                    " SET PrimaryName=?, PrimarySSN=? "
                    "WHERE eCATrackingCode=? "
                    "AND (PrimaryName=? OR (PrimaryName IS NULL AND ? IS NULL)) "
                    "AND (PrimarySSN=? OR (PrimarySSN IS NULL AND ? IS NULL))",
                    (updated[0], updated[1], tracking_code,
                     primary_name, primary_name, primary_ssn, primary_ssn),
                )
                if cursor.rowcount != 1:
                    sql.connection.rollback()
                    raise RuntimeError("PII write conflict; transaction rolled back")
    sql.connection.commit()
