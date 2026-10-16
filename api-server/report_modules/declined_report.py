from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *
from utils import get_header, get_list_of_months_between

def get_declined_reports(start_date, end_date):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    intervals = get_list_of_months_between(start_date, end_date)

    test_report_header, test_report_rows = generate_report(
        intervals, transaction,
        [
            {
                "sql": "SELECT Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM [DigitalReport].[dbo].[Transactions] WHERE AppStartDate IS NOT NULL AND AppStatus IN ('Decline Application Complete','Decline Application','Denied') AND "+excludeBotData+" AND "+excludeZeroProductApps+"",
                "label": "Decline Apps"
            },
        ]
    )
    sql.disconnect()
    return {
        "headers": test_report_header,
        "rows": test_report_rows
    }

def generate_report(intervals, transaction, query_list):
    headers = ["-"] + [get_header(interval)["label"] for interval in intervals if interval['start_date'] != interval['end_date']]
    
    rows = []
    for query in query_list:
        row_now = [query["label"]]
        for interval in intervals:
            queryNow = query["sql"] + f" AND {in_between_sql_condition(interval)} "
            num = transaction.get_transactions_by_sql_query(queryNow)
            row_now.append(num)
        rows.append(row_now)
    return headers, rows


def in_between_sql_condition(interval):
    return f"AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"


def type_of_decline_reasons_table(start_date,end_date,params):
    resp = type_of_decline_reasons_report(start_date, end_date)
    if len(resp) == 0:
        return {
            "headers": [],
            "rows": []
        }
    headers = list(resp[0].keys())
    rows = []
    for row in resp:
        row_now = []
        for item in headers:
            row_now.append(row.get(item))
        rows.append(row_now)

    return {
        "headers": headers,
        "rows": rows
    }



def type_of_decline_reasons_bar(start_date,end_date,params):
    resp = type_of_decline_reasons_report(start_date, end_date)
    if len(resp) == 0:
        return {
            "headers": [],
            "rows": []
        }
    ret =  { 
            "labels": [label.get("Name", "Unknown") for label in resp],
            "list": [point.get("ReasonCount", "0") for point in resp]
        }

    return ret

def type_of_decline_reasons_report(start_date,end_date):
    n_sql = SQLConn()
    camedw_sql = SQLConn(kind="CRFEDW")
    n_sql.connect()
    camedw_sql.connect()
    n_txn = Transaction(n_sql)
    camedw_txn = Transaction(camedw_sql)

    get_tracking_codes_query = f'''
        SELECT 
            eCATrackingCode,
            EDW_APPID as APPID
        FROM
            [DigitalReport].[dbo].[Transactions]
        WHERE 
            {get_date_filter(start_date,end_date)}
            AND EDW_APPID is not null;
        '''
    print("")
    print(get_tracking_codes_query)
    
    tcs = n_txn.get_transactions_by_sql_query(get_tracking_codes_query)
    print(get_tracking_codes_query)
    if tcs == 0:
        return []
    app_ids = []
    for tc in tcs:
        app_id = tc.get("APPID",None)
        if app_id != None:
            app_ids.append(app_id)
    
    resp = camedw_txn.get_transactions_by_sql_query(f'''
        SELECT r.ReasonID, r.Name, d.ReasonID, COUNT(*) AS ReasonCount
        FROM [CRF_EMPL_PII_V1].[CRF_APP_ACTION_DECLINES_CUR] AS d     
        JOIN [CRF_EMPL_PII_V1].[CRF_APP_REASONMASTER_CUR] AS r 
        ON d.ReasonID = r.ReasonID
        where APPID IN ('''+','.join([f'\'{app}\'' for app in app_ids])+ ''')
        GROUP BY r.ReasonID, r.Name, d.ReasonID
    ''')
    n_sql.disconnect()
    camedw_sql.disconnect()

    

    if resp == 0:
        return []
    resp = [{k: v for k, v in d.items() if k != "ReasonID"} for d in resp]
    return resp