from DB import SQLConn, Transaction
from dateutil.relativedelta import relativedelta
from datetime import datetime
from report_modules.condition_utils import get_date_filter
from utils import try_int, get_header, get_list_of_months_between


def _count_value(result, key="data"):
    if isinstance(result, list):
        if not result:
            return 0
        result = result[0]
    if isinstance(result, dict):
        result = result.get(key, 0)
    return try_int(result) or 0

def get_document_center_insights(params):
    left_year = params.get("start_date_for_left_graph").split("-")[0]
    right_year = params.get("start_date_for_right_graph").split("-")[0]
    rows = [
        [ f'Total number of documents uploaded <b>({left_year})</b>', count_of_docs(params.get("start_date_for_left_graph"),params.get("end_date_for_left_graph"))],
        [f'Total number of applications/users that resulted in at least 1 upload <b>({left_year})</b>', count_of_users(params.get("start_date_for_left_graph"),params.get("end_date_for_left_graph"))],
        [ f'Total number of documents uploaded <b>({right_year})</b>', count_of_docs(params.get("start_date_for_right_graph"),params.get("end_date_for_right_graph"))],
        [f'Total number of applications/users that resulted in at least 1 upload <b>({right_year})</b>', count_of_users(params.get("start_date_for_right_graph"),params.get("end_date_for_right_graph"))]
    ]
    return {
        "headers": ["Yearly Doc Center Upload Stats", "Count"],
        "rows": rows
    }


def count_of_users(start_date, end_date):
    sql = SQLConn(kind="CustomerDocumentCenter")
    sql.connect()
    txn = Transaction(sql)
    resp = txn.get_transactions_by_sql_query(f'''SELECT COUNT(DISTINCT combined.UserId) AS data
        FROM (
            SELECT app.UserId
            FROM [CustomerDocumentCenter].[dbo].[Applications] app
            UNION
            SELECT ap.UserId
            FROM [CustomerDocumentCenter].[dbo].[Applicants] ap
        ) AS combined
        INNER JOIN [CustomerDocumentCenter].[dbo].[DocumentCenter] dc
            ON dc.UserId = combined.UserId
        WHERE 
        {get_date_filter(start_date,end_date,"dc.CreatedDate")}
        ;''')
    sql.disconnect()
    return resp

def count_of_docs(start_date, end_date):
    sql = SQLConn(kind="CustomerDocumentCenter")
    sql.connect()
    txn = Transaction(sql)
    resp = txn.get_transactions_by_sql_query(f'''SELECT COUNT(DISTINCT dc.CreatedDate) AS data
        FROM (
            SELECT app.UserId
            FROM [CustomerDocumentCenter].[dbo].[Applications] app
            UNION
            SELECT ap.UserId
            FROM [CustomerDocumentCenter].[dbo].[Applicants] ap
        ) AS combined
        INNER JOIN [CustomerDocumentCenter].[dbo].[DocumentCenter] dc
            ON dc.UserId = combined.UserId
        WHERE {get_date_filter(start_date,end_date,"dc.CreatedDate")};''')
    sql.disconnect()
    return resp


def get_document_center_monthly_insights(start_date, end_date):
    intervals = get_list_of_months_between(start_date, end_date)
    headers = ["-"]
    rows = [
        ["Number Of Users"],
        ["Number of Documents"],
        ["Consumer"],
        ["Business"],
        ["Banker"]

    ]
    for interval in intervals:
        sql = SQLConn(kind="CustomerDocumentCenter")
        sql.connect()
        txn = Transaction(sql)
        resp = txn.get_transactions_by_sql_query(f'''
        SELECT COUNT(DISTINCT dc.CreatedDate) AS noofdocs, Count(DISTINCT(dc.UserId)) as numofusers
        FROM (
            SELECT app.UserId
            FROM [CustomerDocumentCenter].[dbo].[Applications] app
            UNION
            SELECT ap.UserId
            FROM [CustomerDocumentCenter].[dbo].[Applicants] ap
        ) AS combined
        INNER JOIN [CustomerDocumentCenter].[dbo].[DocumentCenter] dc
            ON dc.UserId = combined.UserId
        WHERE  {in_between_sql_condition(interval)}''')
        corBorB = ["Consumer", "Business", "Banker"]
        resp2 = []
        for category in corBorB:
            val = txn.get_transactions_by_sql_query(f'''
                Select Count(*) as data from ApplicantXProduct as prod
                join ApplicationDocuments as appdoc on prod.ApplicantXProductId = appdoc.ApplicantXProductId
                join DocumentCenter as dc on appdoc.ApplicationDocumentID = dc.ApplicationDocumentID
                where prod.Product = '{category}'
                and {in_between_sql_condition(interval)}  ''')
            resp2.append(_count_value(val))

        monthly_counts = resp[0] if isinstance(resp, list) and resp else {}
        rows[0].append(_count_value(monthly_counts, "numofusers"))
        rows[1].append(_count_value(monthly_counts, "noofdocs"))
        rows[2].append(resp2[0])
        rows[3].append(resp2[1])
        rows[4].append(resp2[2])

        headers.append(get_header(interval).get("label", "0"))

    return {
        "rows": rows, "headers": headers
    }


def get_document_center_monthly_insights_line(start_date, end_date):
    resp = get_document_center_monthly_insights(start_date, end_date)
    return {
            "labels": [item for item in resp["headers"] if item != "-"],
            "list": [
                {
                    "name": "Documents",
                    "type": "bar",
                    "data": resp["rows"][1][1:]
                },
                {
                    "name": "Users",
                    "type": "line",
                    "data": resp["rows"][0][1:]
                }
        ]
        }



# Created date - filter
# UserId - as key 
# get me monthly analysis table 




    

def in_between_sql_condition(interval):
    return f" CreatedDate >= '{interval['start_date']}' AND CreatedDate <= '{interval['end_date']}'"



