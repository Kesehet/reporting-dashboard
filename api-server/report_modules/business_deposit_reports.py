from DB import Q
from report_modules.condition_utils import *

printableColumns = [
        'eCAID', 
        'eCATrackingCode', 
        'PrimaryName',  
        'AppStartDate', 
        'AppStatus', 
        'ProductSetId', 
        'NumLendingProducts', 
        'NumDepositProducts',
        'BranchID', 
        'APPLICATION_TYPE', 
        'EmployeeResponsibilityCode', 
        'NMLS_Id'
    ]


def get_business_deposit_reports(start_date,end_date, params=None):


    branch_id = params["BranchID"]
    application_type = params["application_type"]
    
    common_filters = [get_date_filter(start_date, end_date), isBusinessTxn, startedApps, excludeBotData, excludeZeroProductApps]
    
    if application_type != "All":
        common_filters.append(f" Application_Type = '{application_type}'" )


    
    if branch_id is not None:
        BRANCH_IDS = [branch_id]  # Filter to only the specified branch ID
    else:
        BRANCH_IDS = Q(columns=[' Distinct(BranchID)'], where=common_filters+[isBusinessTxn], order_by=['BranchID ASC'])
        BRANCH_IDS = [int(branch['BranchID']) for branch in BRANCH_IDS]
        BRANCH_IDS = ['All'] + BRANCH_IDS  # Add 0 to the list of branch IDs
        BRANCH_IDS = list(set(BRANCH_IDS))
        print(f"Processing {len(BRANCH_IDS)} Branches.")


    rows = []
    for branch_id in BRANCH_IDS:
        common_filters.append(f"BranchID = '{str(branch_id)}'") if branch_id != 'All' else None
        rows.append(get_row(branch_id, start_date, end_date, common_filters))

    

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