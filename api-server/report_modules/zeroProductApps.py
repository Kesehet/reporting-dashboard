from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *

def get_zero_product_apps_reports(start_date, end_date, application_type_condition):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    intervals = get_list_of_months_between(start_date, end_date)

    test_report_header, test_report_rows = generate_report(
        intervals, transaction,
        [
            {
                "sql": f"SELECT Count(*) as data FROM [DigitalReport].[dbo].[Transactions] WHERE {onlyZeroProductApps}  {application_type_condition} AND {excludeBotData}",
                                                                                                
                "label": "No Of Apps"
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
def get_list_of_months_between(start_date, end_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    months = []

    while start_date <= end_date:
        month_start = start_date.strftime("%Y-%m-01")
        next_month = start_date + relativedelta(months=1)
        month_end = (next_month - relativedelta(days=1)).strftime("%Y-%m-%d")
        months.append({"start_date": month_start, "end_date": month_end})
        start_date = next_month

    return months

def get_header(interval):
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%b-%Y")
    return {
        "field": start_date,
        "label": start_date
    }

def in_between_sql_condition(interval):
    return f"AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"
