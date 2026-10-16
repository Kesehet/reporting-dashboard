from DB import Q, SQLConn, Transaction
from report_modules.condition_utils import *
from utils import *

printableColumns = [
        'eCAID', 
        'eCATrackingCode', 
        'PrimaryName',
        'AccountNumber',
        'PrimarySSN',  
        'AppStartDate', 
        'AppStatus', 
        'ProductSetId', 
        'NumLendingProducts', 
        'NumDepositProducts',
        'BranchID', 
        'APPLICATION_TYPE', 
        'EmployeeResponsibilityCode', 
        'NMLS_Id'
    ] + COMMON_EXPORT_COLUMNS


def get_business_deposit_reports(start_date,end_date, params=None):


    params = params or {}
    branch_id = params.get("BranchID", "All")
    application_type = params.get("application_type", "All")
    
    common_filters = [get_date_filter(start_date, end_date), isBusinessTxn, startedApps, excludeBotData, excludeZeroProductApps] + params_to_condition_list(params)
    
    if application_type and application_type.lower() != "all":
        common_filters.append(f" Application_Type = '{application_type}'" )

    rows = []
    rows.append(
        get_row(branch_id='All', start_date=start_date, end_date=end_date, common_filters=common_filters)
    )
    for branch_id, _ in ALL_BRANCH_ID:
        branch_filter = f"BranchID = '{str(branch_id)}'" if branch_id != 'All' else ''
        rows.append(get_row(branch_id, start_date, end_date, common_filters + [branch_filter]))

    

    return {"headers": [
        {
            "field": "Total-Started",
            "label": "Total Started"
        },
        {
            "field": "Total-Submitted",
            "label": "Total Submitted"
        },
        {
            "field": "Total-Opened/Approved",
            "label": "Total Updated/Approved"
        },
        {
            "field": "Grand-Total",
            "label": "Grand Total"
        }
    ], "rows":rows}

def get_row(branch_id, start_date, end_date, common_filters):

    commonOrderBy = "AppStartDate DESC"

    return {
        "Date"  : f"{start_date} to {end_date}",
        "Start-Date": start_date,
        "End-Date": end_date,
        'BranchID': branch_id,
        'Total-Started': Q(columns=[countColumn], where=common_filters+[excludeZeroProductApps], queryOnly=True),
            "Total-Started-[Lending]": Q(columns=[countColumn], where=common_filters+[loanApps, excludeZeroProductApps], queryOnly=True),
            "Total-Started-[Deposit]": Q(columns=[countColumn], where=common_filters+[depositApps, excludeZeroProductApps], queryOnly=True),
            "Total-Started-[Mixed]": Q(columns=[countColumn], where=common_filters+[mixedApps, excludeZeroProductApps], queryOnly=True),
            "Total-Started-[Multi]": Q(columns=[countColumn], where=common_filters+[multiApps, excludeZeroProductApps], queryOnly=True),
            "Total-Started-[Single]": Q(columns=[countColumn], where=common_filters+[singleApps, excludeZeroProductApps], queryOnly=True),
        "Total-Submitted": Q(columns=[countColumn], where=common_filters+[ SUBMITTED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Submitted-[Lending]": Q(columns=[countColumn], where=common_filters+[loanApps, SUBMITTED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Submitted-[Deposit]": Q(columns=[countColumn], where=common_filters+[depositApps, SUBMITTED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Submitted-[Mixed]": Q(columns=[countColumn], where=common_filters+[mixedApps, SUBMITTED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Submitted-[Multi]": Q(columns=[countColumn], where=common_filters+[multiApps, SUBMITTED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Submitted-[Single]": Q(columns=[countColumn], where=common_filters+[singleApps, SUBMITTED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
        "Total-Opened/Approved": Q(columns=[countColumn], where=common_filters+[APPROVED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Opened/Approved-[Lending]": Q(columns=[countColumn], where=common_filters+[ loanApps, APPROVED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Opened/Approved-[Deposit]": Q(columns=[countColumn], where=common_filters+[ depositApps, APPROVED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Opened/Approved-[Mixed]": Q(columns=[countColumn], where=common_filters+[ mixedApps, APPROVED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Opened/Approved-[Multi]": Q(columns=[countColumn], where=common_filters+[ multiApps, APPROVED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
                "Total-Opened/Approved-[Single]": Q(columns=[countColumn], where=common_filters+[ singleApps, APPROVED_APPS_FILTER, excludeZeroProductApps], queryOnly=True),
        "Grand-Total": Q(columns=[countColumn], where=common_filters+[excludeZeroProductApps], queryOnly=True),
        "_report_Total-Started": Q(columns=printableColumns, where=common_filters+[excludeZeroProductApps], order_by=commonOrderBy, queryOnly=True),
        "_report_Total-Submitted": Q(columns=printableColumns, where=common_filters+[SUBMITTED_APPS_FILTER, excludeZeroProductApps], order_by=commonOrderBy, queryOnly=True),
        "_report_Total-Opened/Approved": Q(columns=printableColumns, where=common_filters+[APPROVED_APPS_FILTER, excludeZeroProductApps], order_by=commonOrderBy, queryOnly=True),
        "_report_Grand-Total":Q(columns=printableColumns, where=common_filters+[excludeZeroProductApps], order_by=commonOrderBy, queryOnly=True),
    }

def get_bdr_monthly_analytics_line(start_date,end_date, params={}):
    variant = params.get("variant", "Started")
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    ret = {
            "labels": [],
            "datasetMap": {
                f"Total-{variant}-[Lending]": [],
                f"Total-{variant}-[Deposit]": [],
                f"Total-{variant}-[Mixed]": []
            }
        }
    months = get_list_of_months_between(start_date, end_date)

    application_type = params.get("application_type", "All")
    common_filters = [isBusinessTxn, startedApps, excludeBotData, excludeZeroProductApps]
    
    if application_type and application_type.lower() != "all":
        common_filters.append(f" Application_Type = '{application_type}'" )

    
    for month in months:
        common_filters_month = common_filters + [get_date_filter(month['start_date'], month['end_date'])]
        queries = get_row(branch_id='All', start_date=month['start_date'], end_date=month['end_date'], common_filters=common_filters_month)
        ret["labels"].append(get_header(month)['label'])
        ret["datasetMap"][f"Total-{variant}-[Lending]"].append(
            txn.get_transactions_by_sql_query(queries[f"Total-{variant}-[Lending]"]  )
        )
        ret["datasetMap"][f"Total-{variant}-[Deposit]"].append(txn.get_transactions_by_sql_query(queries[f"Total-{variant}-[Deposit]"]))
        ret["datasetMap"][f"Total-{variant}-[Mixed]"].append(txn.get_transactions_by_sql_query(queries[f"Total-{variant}-[Mixed]"]))
    sql.disconnect()
    return ret
