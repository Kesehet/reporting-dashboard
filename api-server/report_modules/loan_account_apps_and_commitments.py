# Started - Select * from [DigitalReport].[dbo].[Transactions] where NumlendingProducts > 0 AND {SubmittedApps} AND {excludeBotData} AND {excludeZeroProductApps} AND {eCATrackingCodeFilter}
#Submitted - Select * from [DigitalReport].[dbo].[Transactions] where {SubmittedforLoanCommitemnt}
# excludeBotdata, excludeZeroproductApps, #appStatusforDashboard

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from DB import Q, get_EDW, SQLConn, Transaction
from report_modules.condition_utils import *
from report_modules.edw_condition_utils import *
from utils import get_header, get_list_of_months_between, get_quarter_header, get_list_of_quarters_between


logger = logging.getLogger(__name__)


def _get_edw_appids_for_interval(interval, params, txn, use_cache=True):
    transaction_rows = Q(
        columns=["EDW_APPID", "eCATrackingCode"],
        where=[
            lendingApps,
            in_between_sql_condition(interval),
            application_type_filter(params.get("application_type", "")),
            CorBFilter(params.get("eCATrackingCode", "%")),
        ],
        params=params,
        use_cache=use_cache,
    )
    if transaction_rows == 0:
        return {"source_rows": 0, "direct_appids": 0, "fallback_appids": 0, "appids": []}

    appids = list(dict.fromkeys(
        str(row["EDW_APPID"])
        for row in transaction_rows
        if row.get("EDW_APPID")
    ))
    tracking_codes = list(dict.fromkeys(
        str(row["eCATrackingCode"])
        for row in transaction_rows
        if not row.get("EDW_APPID") and row.get("eCATrackingCode")
    ))

    fallback_appids = []
    if tracking_codes:
        quote = "'"
        tracking_codes_sql = ", ".join(
            f"{quote}{tracking_code.replace(quote, quote + quote)}{quote}"
            for tracking_code in tracking_codes
        )
        mapped_rows = txn.get_transactions_by_sql_query(
            f"""
            SELECT DISTINCT APPID
            FROM {customfieldscurtable}
            WHERE Temenos_ID IN ({tracking_codes_sql})
            """,
            use_cache=use_cache,
        )
        if mapped_rows != 0:
            fallback_appids = list(dict.fromkeys(
                str(row["APPID"])
                for row in mapped_rows
                if row.get("APPID")
            ))

    direct_appid_count = len(appids)
    appids = list(dict.fromkeys(appids + fallback_appids))
    return {
        "source_rows": len(transaction_rows),
        "direct_appids": direct_appid_count,
        "fallback_appids": len(fallback_appids),
        "appids": appids,
    }


def get_insigths_report(start_date, end_date, params={}):
    common_filters = [get_date_filter(start_date,end_date), application_type_filter(params.get("application_type", "")),CorBFilter(params.get("eCATrackingCode","%"))]
    started_conditions = [submittedApps, excludeBotData, excludeZeroProductApps] + common_filters
    started_query_all = Q(where=started_conditions, queryOnly=True, params=params)
    started_query_count = Q(columns=[countColumn], where=started_conditions, queryOnly=True, params=params)

    submitted_conditions = [SUBMITTED_FOR_LOAN_COMMITMENT_FILTER] + common_filters
    submitted_query_all = Q(where=submitted_conditions, params=params)


    
    sql = SQLConn(kind="CRFEDW")
    sql.connect()
    txn = Transaction(sql_conn=sql)
    tids = []
    if submitted_query_all == 0:
        submitted_query_all = []
    for row in submitted_query_all: #submitted_query_all:
        tids.append(row.get("eCATrackingCode"))
        
    if tids:
        tracking_codes_sql = ','.join([f'\'{tid}\'' for tid in tids])
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
                where temp.Temenos_ID is not null and temp.Temenos_ID != '' and temp.Temenos_ID IN ({tracking_codes_sql}) and app.DecisionStatusName = 'Approved'
            """
        resp = txn.get_transactions_by_sql_query(Opened_Approved_query_all)
    else:
        resp = 0

    if resp == 0:
        Opened_Approved_query_all = []
    else:
        Opened_Approved_query_all = resp

    if tids:
        all_application_type_list = Q(columns=["Application_Type", "eCATrackingCode"], where=[f"eCATrackingCode IN ({tracking_codes_sql}) ", CorBFilter(params.get("eCATrackingCode","%"))], params=params)
    else:
        all_application_type_list = []
    all_application_type_dict = {}
    if all_application_type_list == 0:
        all_application_type_list = []
    for row in all_application_type_list:
        all_application_type_dict[row.get("eCATrackingCode")] = row.get("Application_Type")
    
    unique_query_by_tracking_code = {}
    for obj in Opened_Approved_query_all:
        if unique_query_by_tracking_code.get(obj["Temenos_ID"], None) == None:
            obj["ApplicationType"] = all_application_type_dict.get(obj["Temenos_ID"])
            unique_query_by_tracking_code[obj["Temenos_ID"]] = obj
        elif obj["DecisionReason"] != None and obj["DecisionReason"] != "":
            unique_query_by_tracking_code[obj["Temenos_ID"]]["DecisionReason"] += ", " + obj["DecisionReason"]

    
    Opened_Approved_query_all = list(unique_query_by_tracking_code.values())
        
    sql.disconnect()

    return {

        "Started": started_query_count,
        "_report_Started": started_query_all,

        "Submitted": len(submitted_query_all),
        "_report_Submitted": submitted_query_all,

        "Opened/Approved": len(Opened_Approved_query_all),
        "_report_Opened/Approved": Opened_Approved_query_all,
        
    }




def get_stacked_bar_report(start_date, end_date, params={}, intervals=None):

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
        appid_result = _get_edw_appids_for_interval(interval, params, txn)
        if not appid_result["appids"]:
            continue
        apps_filter = ", ".join(f"'{appid}'" for appid in appid_result["appids"])

        for PGR in SECURED_PRODUCT_GROUPINGS+UNSECURED_PRODUCT_GROUPINGS:
            
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

def get_bar_line_chart_report(start_date, end_date, params={}):
    
    intervals = get_list_of_quarters_between(start_date, end_date)
    diagnostics = str(params.get("diagnostics", "")).strip().lower() in {"1", "true", "yes"}

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
        appid_result = _get_edw_appids_for_interval(
            interval,
            params,
            txn,
            use_cache=not diagnostics,
        )
        if appid_result["source_rows"] == 0:
            if diagnostics:
                logger.warning(
                    "Loan commitment quarter has no source transactions (start=%s, end=%s, application_type=%s)",
                    interval["start_date"],
                    interval["end_date"],
                    params.get("application_type"),
                )
        source_rows = appid_result["source_rows"]
        appids = appid_result["appids"]
        apps_filter = ", ".join(f"'{appid}'" for appid in appids)
        groups_with_amount = 0
        groups_without_amount = 0

        if diagnostics and source_rows and not appids:
            logger.warning(
                "Loan commitment quarter has source transactions but no EDW_APPID values (start=%s, end=%s, application_type=%s, source_rows=%d)",
                interval["start_date"],
                interval["end_date"],
                params.get("application_type"),
                source_rows,
            )

        if diagnostics and appids:
            product_groupings = SECURED_PRODUCT_GROUPINGS + UNSECURED_PRODUCT_GROUPINGS
            product_groupings_sql = ", ".join(f"'{group}'" for group in product_groupings)
            grouped_amounts = txn.get_transactions_by_sql_query(f'''
                SELECT ProductGrouping, SUM(AmountRequested) AS commitment_amount
                FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]
                WHERE APPID IN ({apps_filter})
                  AND ProductGrouping IN ({product_groupings_sql})
                GROUP BY ProductGrouping
            ''', use_cache=False)
            amounts_by_group = {
                row.get("ProductGrouping"): row.get("commitment_amount") or 0
                for row in grouped_amounts
            } if grouped_amounts != 0 else {}
            groups_with_amount = sum(value != 0 for value in amounts_by_group.values())
            groups_without_amount = len(product_groupings) - groups_with_amount
            dataThisInterval["sec"] = sum(
                amounts_by_group.get(group, 0) for group in SECURED_PRODUCT_GROUPINGS
            )
            dataThisInterval["unsec"] = sum(
                amounts_by_group.get(group, 0) for group in UNSECURED_PRODUCT_GROUPINGS
            )
        else:
            for PGR in SECURED_PRODUCT_GROUPINGS+UNSECURED_PRODUCT_GROUPINGS:
                if not appids:
                    continue

                product_groupings_resp = txn.get_transactions_by_sql_query(f'''
                Select ProductGrouping as name, SUM(AmountRequested) as data from [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]
                    where APPID IN ({apps_filter}) and ProductGrouping = '{PGR}'
                    group by ProductGrouping Having Count(*) > 0
                ''')

                if PGR in SECURED_PRODUCT_GROUPINGS:
                    dataThisInterval["sec"] += product_groupings_resp
                if PGR in UNSECURED_PRODUCT_GROUPINGS:
                    dataThisInterval["unsec"] += product_groupings_resp
        
        quarter_total = dataThisInterval["sec"] + dataThisInterval["unsec"]
        listOfItems["total"].append(quarter_total)
        
        interval_name = get_quarter_header(interval).get("Y", "Missed")
        if interval_name not in listOfItems or not listOfItems[interval_name]:
            listOfItems[interval_name] = []

        listOfItems[interval_name].append(quarter_total)

        if diagnostics:
            log_method = logger.warning if quarter_total == 0 else logger.info
            log_method(
                "Loan commitment quarter totals (start=%s, end=%s, application_type=%s, source_rows=%d, direct_edw_appids=%d, temenos_fallback_appids=%d, usable_edw_appids=%d, product_groups_with_amount=%d, product_groups_zero=%d, commitment_total_is_zero=%s)",
                interval["start_date"],
                interval["end_date"],
                params.get("application_type"),
                source_rows,
                appid_result["direct_appids"],
                appid_result["fallback_appids"],
                len(appids),
                groups_with_amount,
                groups_without_amount,
                quarter_total == 0,
            )
        

    sql.disconnect()

    if params.get("show_line", False):
        liners_list = get_stacked_bar_report(start_date, end_date, params=params, intervals=intervals)["list"]
        line_data = [
            liners_list[0]["data"][i] + liners_list[1]["data"][i]
            for i in range(len(liners_list[0]["data"]))
        ]
        
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


def get_table_report(start_date, end_date, params={}):
    
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
        appid_result = _get_edw_appids_for_interval(interval, params, txn)
        if not appid_result["appids"]:
            continue
        apps_filter = ", ".join(f"'{appid}'" for appid in appid_result["appids"])

        for PGR in SECURED_PRODUCT_GROUPINGS+UNSECURED_PRODUCT_GROUPINGS:
            
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


