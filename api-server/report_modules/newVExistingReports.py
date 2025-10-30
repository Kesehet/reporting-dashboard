from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *
from DB import Q





def generate_newVExisting_report_variants_by_filters(start_date, end_date, base_filters=[]):
    sql = SQLConn()
    sql.connect()

    intervals = get_list_of_months_between(start_date, end_date)
    
    items = ["New", "Existing"]
    listOfItems = []
    for item in items:
        dataNow = []
        for interval in intervals:
            dataNow.append(
                Q(sql=sql, columns=[countColumn], where=[in_between_sql_condition(interval), f"NewCustomer = '{item}'", ] + base_filters)
            )
        listOfItems.append({
            "name": item,
            "data": dataNow
        })
    sql.disconnect()
    return {
       "labels": [get_header(interval)['field'] for interval in intervals],
       "list": listOfItems
    }

def generate_newVExisting_report_table_variants_by_filters(start_date, end_date, base_filters=[]):
    sql = SQLConn()
    sql.connect()
    
    intervals = get_list_of_months_between(start_date, end_date)
    rows = []
    items = ["New", "Existing"]
    for item in items:
        row = [item]
        for interval in intervals:
            row.append(
                Q(sql=sql, columns=[countColumn], where=[in_between_sql_condition(interval), f"NewCustomer = '{item}'", ] + base_filters)
            )
        rows.append(row)
    sql.disconnect()
    return {
       "headers": [get_header(interval)['field'] for interval in intervals],
       "rows": rows
    }






def get_header(interval):
    # Convert start date to format Jun-25
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%b-%Y")
    return {
        "field": start_date,
        "label": start_date
    }
    

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"


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