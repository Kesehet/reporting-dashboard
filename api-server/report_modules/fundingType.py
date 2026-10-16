from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *
from DB import query_maker
from utils import *

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

def get_funding_type_reports_line(start_date, end_date, ecaTrackingCodeFilter):
    data = get_funding_type_reports(start_date, end_date, ecaTrackingCodeFilter)
    ret_list = {}
    for row in data["rows"]:
        rows = [try_int(value) for value in row[1:]]
        # Remove None values
        rows = [value for value in rows if value is not None]
        data_id = row[0]
        ret_list[data_id] = rows


    return {
        "labels": (data["headers"][1:][:len(data['headers'][1:])//2]), # Get unique labels for count and amount
        "datasetMap": ret_list
    }



    

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"


