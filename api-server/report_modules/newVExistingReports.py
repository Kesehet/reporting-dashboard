from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *
from DB import Q
from utils import *





def generate_newVExisting_report_variants_by_filters(start_date, end_date, params, base_filters=[]):
    sql = SQLConn()
    sql.connect()

    intervals = get_list_of_months_between(start_date, end_date)
    
    items = ["New", "Existing"]
    listOfItems = []
    for item in items:
        dataNow = []
        for interval in intervals:
            dataNow.append(
                Q(sql=sql, columns=[countColumn], where=[in_between_sql_condition(interval), f"NewCustomer = '{item}'", ] + base_filters, params=params)
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

def generate_newVExisting_report_table_variants_by_filters(start_date, end_date, params, base_filters=[]):
    sql = SQLConn()
    sql.connect()
    
    intervals = get_list_of_months_between(start_date, end_date)
    rows = []
    items = ["New", "Existing"]
    for item in items:
        row = [item]
        for interval in intervals:
            row.append(
                Q(sql=sql, columns=[countColumn], where=[in_between_sql_condition(interval), f"NewCustomer = '{item}'", ] + base_filters, params=params)
            )
        rows.append(row)
    sql.disconnect()
    return {
       "headers": ["-"] + [get_header(interval)['field'] for interval in intervals],
       "rows": rows
    }






    

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"

