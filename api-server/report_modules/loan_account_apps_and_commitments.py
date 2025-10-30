# Started - Select * from [DigitalReport].[dbo].[Transactions] where NumlendingProducts > 0 AND {SubmittedApps} AND {excludeBotData} AND {excludeZeroProductApps} AND {eCATrackingCodeFilter}
#Submitted - Select * from [DigitalReport].[dbo].[Transactions] where {SubmittedforLoanCommitemnt}
# excludeBotdata, excludeZeroproductApps, #appStatusforDashboard

from datetime import datetime
from dateutil.relativedelta import relativedelta
from DB import Q, get_EDW, SQLConn, Transaction
from report_modules.condition_utils import *
from report_modules.edw_condition_utils import *


def get_insigths_report(start_date, end_date, params):
    common_filters = [get_date_filter(start_date,end_date)]
    started_conditions = [submittedApps, excludeBotData, excludeZeroProductApps, CorBFilter(params.get("eCATrackingCode","%"))] + common_filters
    started_query_all = Q(where=started_conditions, queryOnly=True)
    started_query_count = Q(columns=[countColumn], where=started_conditions, queryOnly=True)

    submitted_conditions = [SUBMITTED_FOR_LOAN_COMMITMENT_FILTER] + common_filters
    submitted_query_all = Q(where=submitted_conditions)
    
    sql = SQLConn(kind="CRFEDW")
    sql.connect()
    txn = Transaction(sql_conn=sql)
    tids = []
    for row in submitted_query_all: #submitted_query_all:
        tids.append(row.get("eCATrackingCode"))
        
    tids = ','.join([f'\'{tid}\'' for tid in tids])
    Opened_Approved_query_all = f"""
            SELECT DISTINCT
                app.APPID,
                app.APPDETAILID,
                app.ApplicationStart,
                app.ProductShortName,
                app.ProductGrouping,
                app.DecisionStatusName,
                app.AmountRequested,
                app.AccountNumber,
                rc.Name as DecisionReason,
                temp.Temenos_ID
            FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR] AS app
            LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMFIELDS_CUR] as temp
                ON temp.APPID = app.APPID
            LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_DECLINES_CUR] AS dc
                ON app.APPID = dc.APPID
            LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_REASONMASTER_CUR] AS rc
                ON rc.ReasonID = dc.ReasonID
                where temp.Temenos_ID is not null and temp.Temenos_ID != '' and temp.Temenos_ID IN ({tids}) and app.DecisionStatusName = 'Approved'
            """
    resp = txn.get_transactions_by_sql_query(Opened_Approved_query_all)
    if resp == 0:
        Opened_Approved_query_all = []
    else:
        Opened_Approved_query_all = resp
        
        
    sql.disconnect()

    return {

        "Started": started_query_count,
        "_report_Started": started_query_all,

        "Submitted": len(submitted_query_all),
        "_report_Submitted": submitted_query_all,

        "Opened/Approved": len(Opened_Approved_query_all),
        "_report_Opened/Approved": Opened_Approved_query_all,
        
    }




def get_stacked_bar_report(start_date, end_date, params=None, intervals=None):

    if intervals == None:
        intervals = get_list_of_months_between(start_date, end_date)

    sql = SQLConn(kind="CRFEDW")    
    sql.connect()
    txn = Transaction(sql)
    listOfItems = {
        "sec":[],
        "unsec":[]
    }
    for interval in intervals:
    
        dataThisInterval = {
            "sec":0,
            "unsec":0
        }
        for PGR in SECURED_PRODUCT_GROUPINGS+UNSECURED_PRODUCT_GROUPINGS:
            
            appid_response = Q(columns=["EDW_APPID"], where=[lendingApps, in_between_sql_condition(interval)])
            if appid_response == 0:
                continue
            appids = ["'"+str(tc.get("EDW_APPID"))+"'" for tc in appid_response if tc.get("EDW_APPID")]
            apps_filter = ', '.join(appids)
            
            product_groupings_resp = txn.get_transactions_by_sql_query(f'''
            Select ProductGrouping as name, Count(*) as data from [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]
                where APPID IN ({apps_filter}) and ProductGrouping = '{PGR}'
                group by ProductGrouping Having Count(*) > 0
            ''')

            if PGR in SECURED_PRODUCT_GROUPINGS:
                dataThisInterval["sec"] += product_groupings_resp
            if PGR in UNSECURED_PRODUCT_GROUPINGS:
                dataThisInterval["unsec"] += product_groupings_resp
        
        listOfItems["sec"].append(dataThisInterval["sec"])
        listOfItems["unsec"].append(dataThisInterval["unsec"])
        

    sql.disconnect()
    return {
       "labels": [get_header(interval)['field'] for interval in intervals],
       "list": [
           {
               "name": "Secured",
               "data": listOfItems["sec"]
           },
           {
               "name": "Unsecured",
               "data": listOfItems["unsec"]
           },
       ]
    }

def get_bar_line_chart_report(start_date, end_date, params=None):
    
    intervals = get_list_of_quarters_between(start_date, end_date)

    if not params.get("show_line", False):
        intervals = sorted(intervals, key=lambda x: get_quarter_header(x)['Q'])



    sql = SQLConn(kind="CRFEDW")    
    sql.connect()
    txn = Transaction(sql)
    listOfItems = {
        "total":[],

    }

    for interval in intervals:
    
        dataThisInterval = {
            "sec":0,
            "unsec":0,
        }
        for PGR in SECURED_PRODUCT_GROUPINGS+UNSECURED_PRODUCT_GROUPINGS:
            
            appid_response = Q(columns=["EDW_APPID"], where=[lendingApps, in_between_sql_condition(interval)])
            if appid_response == 0:
                continue
            appids = ["'"+str(tc.get("EDW_APPID"))+"'" for tc in appid_response if tc.get("EDW_APPID")]
            apps_filter = ', '.join(appids)
            
            product_groupings_resp = txn.get_transactions_by_sql_query(f'''
            Select ProductGrouping as name, SUM(AmountRequested) as data from [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]
                where APPID IN ({apps_filter}) and ProductGrouping = '{PGR}'
                group by ProductGrouping Having Count(*) > 0 
            ''')

            if PGR in SECURED_PRODUCT_GROUPINGS:
                dataThisInterval["sec"] += product_groupings_resp
            if PGR in UNSECURED_PRODUCT_GROUPINGS:
                dataThisInterval["unsec"] += product_groupings_resp
        
        listOfItems["total"].append(dataThisInterval["sec"] + dataThisInterval["unsec"])
        
        interval_name = get_quarter_header(interval).get("Y", "Missed")
        if interval_name not in listOfItems or not listOfItems[interval_name]:
            listOfItems[interval_name] = []

        listOfItems[interval_name].append(dataThisInterval["sec"] + dataThisInterval["unsec"])
        

    sql.disconnect()

    liners_list = get_stacked_bar_report(start_date,end_date, intervals=intervals)["list"]
    line_data = []
    for i in range(len(liners_list[0]["data"])):
        line_data.append(liners_list[0]["data"][i] + liners_list[1]["data"][i])


    if params.get("show_line", False):
        
        return {
            "labels": [get_quarter_header(interval)['field'] for interval in intervals],
            "list": [
                {
                    "name": "Commitments",
                    "type": "bar",
                    "data": listOfItems["total"]
                },
                {
                    "name": "Accounts",
                    "type": "line",
                    "data": line_data
                }
        ]
        }
    else:
        sorted_keys = sorted([
            item
            for item in listOfItems
            if item != "total"
        ])

        return {
                "labels": [ "Q1", "Q2", "Q3", "Q4", ],
                "list": [
                            {
                                "name": item,
                                "type": "bar",
                                "data": listOfItems.get(item) or []
                            }
                            for item in sorted_keys
                        ]

            }


def get_table_report(start_date, end_date, params=None):
    
    intervals = get_list_of_quarters_between(start_date, end_date)

    
    sql = SQLConn(kind="CRFEDW")    
    sql.connect()
    txn = Transaction(sql)
    listOfItems = {
        "sec":[],
        "unsec":[],
        "avg": [],
        "total":[],
        "amt":[],
        "apps":[]
    }
    for interval in intervals:
    
        dataThisInterval = {
            "sec":0,
            "unsec":0,
            "sec_amt":0,
            "unsec_amt":0,
            "total":0,
            "total_amt":0,
            "total_avg":0
        }
        for PGR in SECURED_PRODUCT_GROUPINGS+UNSECURED_PRODUCT_GROUPINGS:
            
            appid_response = Q(columns=["EDW_APPID"], where=[lendingApps, in_between_sql_condition(interval)])
            if appid_response == 0:
                continue
            appids = ["'"+str(tc.get("EDW_APPID"))+"'" for tc in appid_response if tc.get("EDW_APPID")]
            apps_filter = ', '.join(appids)
            
            product_groupings_resp = txn.get_transactions_by_sql_query(f'''
            Select ProductGrouping as name, Count(*) as data from [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]
                where APPID IN ({apps_filter}) and ProductGrouping = '{PGR}'
                group by ProductGrouping Having Count(*) > 0 
            ''')
            
            product_groupings_sum_resp = txn.get_transactions_by_sql_query(f'''
            Select ProductGrouping as name, SUM(AmountRequested) as data from [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]
                where APPID IN ({apps_filter}) and ProductGrouping = '{PGR}'
                group by ProductGrouping Having Count(*) > 0 
            ''')

            if PGR in SECURED_PRODUCT_GROUPINGS:
                dataThisInterval["sec"] += product_groupings_resp
                dataThisInterval["sec_amt"] += product_groupings_sum_resp

            if PGR in UNSECURED_PRODUCT_GROUPINGS:
                dataThisInterval["unsec"] += product_groupings_resp
                dataThisInterval["unsec_amt"] += product_groupings_sum_resp
            
            dataThisInterval["total"] += product_groupings_resp
            dataThisInterval["total_amt"] += product_groupings_sum_resp
            
            dataThisInterval["total_avg"] = (
                dataThisInterval["total_amt"] / dataThisInterval["total"]
                if dataThisInterval["total"] > 0 else 0
            )

        
        listOfItems["sec"].append(dataThisInterval["sec"])
        listOfItems["unsec"].append(dataThisInterval["unsec"])
        listOfItems["sec"].append(format_amounts(dataThisInterval["sec_amt"]))
        listOfItems["unsec"].append(format_amounts(dataThisInterval["unsec_amt"]))
        
        listOfItems["apps"].append(dataThisInterval["total"])
        listOfItems["avg"].append(format_amounts(dataThisInterval["total_avg"]))
        listOfItems["amt"].append(format_amounts(dataThisInterval["total_amt"]))

        
        listOfItems["total"].append(str(dataThisInterval["total"]))
        listOfItems["total"].append(format_amounts(dataThisInterval["total_amt"]))

        
        
        

    sql.disconnect()
    rows = []
    header_multipplier = 2
    if params.get("send_sec_unsec", False):
        rows.append( ["Secured"] + listOfItems["sec"])
        rows.append(["Unsecured"] + listOfItems["unsec"])

    if params.get("send_avg", False):
        rows.append(["Consumer Loan Accounts"] + listOfItems["apps"] )
        rows.append(["Loan Commitments (in mil $)"] + listOfItems["amt"] )
        rows.append(["Average Commitments (in mil $)"] + listOfItems["avg"] )
        header_multipplier = 1

    
    if params.get("send_total", False):
        rows.append(["Total"] + listOfItems["total"] )
    
    
    header_list = [get_quarter_header(interval)['field'] for interval in intervals]
    headers = []
    for i in range(header_multipplier):
        headers += header_list
    return {
       "headers": ["-"]+ headers,
       "rows": rows
    }

'''
Bar with Line = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May"],
    list: [
        {
            name: "Revenue",
            type: "bar", // optional, defaults to 'bar'
            data: [12000, 15000, 18000, 17000, 20000]
        },
        {
            name: "Expenses",
            type: "bar",
            data: [8000, 9000, 10000, 9500, 11000]
        },
        {
            name: "Profit Trend",
            type: "line",
            data: [4000, 6000, 8000, 7500, 9000]
        }
    ]
}


'''



# ______________________________________________________________________________ HELPERS ______________________________________________________________________________

def format_amounts(amt):
    amt_in_millions = amt / 1_000_000
    return f"$ {amt_in_millions:,.2f}"



def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"

def get_header(interval):
    # Convert start date to format Jun-25
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%b-%Y")
    return {
        "field": start_date,
        "label": start_date
    }


def get_quarter_header(interval):
    date_obj = datetime.strptime(interval['start_date'], "%Y-%m-%d")
    year = date_obj.year
    month = date_obj.month
    quarter = (month - 1) // 3 + 1
    label = f"Q{quarter}-{year}"
    
    return {
        "field": label,
        "label": label,
        "Q": f"Q{quarter}",
        "Y": year
    }


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


def get_list_of_quarters_between(start_date, end_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    quarters = []

    # Align start_date to the beginning of its quarter
    start_month = ((start_date.month - 1) // 3) * 3 + 1
    start_date = datetime(start_date.year, start_month, 1)

    while start_date <= end_date:
        quarter_start = start_date.strftime("%Y-%m-%d")
        next_quarter = start_date + relativedelta(months=3)
        quarter_end = (next_quarter - relativedelta(days=1)).strftime("%Y-%m-%d")
        quarters.append({"start_date": quarter_start, "end_date": quarter_end})
        start_date = next_quarter

    return quarters
