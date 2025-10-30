from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *
from DB import query_maker

def get_funding_type_reports(start_date, end_date, ecaTrackingCodeFilter):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    intervals = get_list_of_months_between(start_date, end_date)
    intervals = intervals + intervals
    test_report_header, test_report_rows = generate_report(
        intervals, transaction,
        [
            {
                "sql": {
                    "count" : query_maker(columns=[countColumn], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0", "FundingMethod = 'CREDIT_OR_DEBIT'" ]), # Yellow
                    "amount" : query_maker(columns=[sumColumn('TotalFundingAmount')], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0", "FundingMethod = 'CREDIT_OR_DEBIT'" ]), # Green
                },
                "label": "CREDIT_OR_DEBIT" # Red
            },
            {
                "sql": {
                    "count" : query_maker(columns=[countColumn], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0", "FundingMethod = 'INTERNAL'" ]), # Yellow
                    "amount" : query_maker(columns=[sumColumn('TotalFundingAmount')], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0", "FundingMethod = 'INTERNAL'" ]), # Green
                },
                "label": "INTERNAL" # Red
            },
            {
                "sql": {
                    "count" : query_maker(columns=[countColumn], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0", "FundingMethod = 'ACH'" ]), # Yellow
                    "amount" : query_maker(columns=[sumColumn('TotalFundingAmount')], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0", "FundingMethod = 'ACH'" ]), # Green
                },
                "label": "ACH" # Red
            },
            {
                "sql": {
                    "count" : query_maker(columns=[countColumn], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0" ]), # Yellow
                    "amount" : query_maker(columns=[sumColumn('TotalFundingAmount')], where=[ecaTrackingCodeFilter,mixedApprovedApps,"NumDepositproducts > 0" ]), # Green
                },
                "label": "TOTAL" # Red
            },
            
            
        ]
    )
    

    sql.disconnect()
    return {
                "headers": test_report_header,
                "rows": test_report_rows
            }

def generate_report(intervals, transaction, query_list):
    headers = ["-"] 
    # Generate headers for each interval
    for interval in intervals:
        if interval['start_date'] != interval['end_date']:
            label = get_header(interval)["label"]
            headers.append(f"{label}")

    rows = []
    # Initialize rows with labels only
    for red in query_list:
        row = []
        row.append(
            red["label"]
        )
        for pink in intervals:
            
            queryNowA = red["sql"]["count"] + f" AND {in_between_sql_condition(pink)}"
            numA = transaction.get_transactions_by_sql_query(queryNowA)
            row.append(
                int(numA)
                )

            queryNowB = red["sql"]["amount"] + f" AND {in_between_sql_condition(pink)}"
            numB = transaction.get_transactions_by_sql_query(queryNowB)
            row.append(
                    "$ " + str(
                            "{:,}".format(round(numB, 2))
                        )
                    )
        rows.append(row)

    return headers, rows


def get_list_of_months_between(start_date, end_date):

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    months = []

    while start_date <= end_date:
        month_start = start_date.strftime("%Y-%m-01")  # July 1st
        next_month = datetime.strptime(month_start, "%Y-%m-%d") + relativedelta(months=1)  # Auguest 1st
        month_end = (next_month - relativedelta(days=1)).strftime("%Y-%m-%d") # Auguest 4th 
        months.append({"start_date": month_start, "end_date": month_end}) 
        start_date = next_month

    return months

def get_header(interval):
    # Convert start date to format Jun-25
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%b-%Y")
    return {
        "field": start_date,
        "label": start_date
    }
    

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"


