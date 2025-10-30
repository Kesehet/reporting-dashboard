from DB import Transaction, SQLConn
from report_modules.condition_utils import *


def get_abandonment_reports(start_date, end_date, branch_id=None, application_type=None, ecaTrackingCodeFilter=None):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    
    BRANCH_IDS = []
    if branch_id is not None:
        BRANCH_IDS = [branch_id]  # Filter to only the specified branch ID
    else:
        BRANCH_IDS = transaction.get_transactions_by_sql_query(
            f"Select Distinct(BranchID) from {table} WHERE BranchID IS NOT NULL AND AppStartdate IS NOT NULL AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' Order By BranchID ASC"
        )
        BRANCH_IDS = [int(branch['BranchID']) for branch in BRANCH_IDS]
        BRANCH_IDS = ['All'] + BRANCH_IDS  # Add 0 to the list of branch IDs
        BRANCH_IDS = list(set(BRANCH_IDS))
        print(f"Processing {len(BRANCH_IDS)} Branches.")
    
    rows = []
    for branch_id in BRANCH_IDS:
        rows.append(get_row(branch_id, application_type, start_date, end_date, transaction, ecaTrackingCodeFilter))
    sql.disconnect()
    return {
                        "headers": [
                            { "field": 'Grand-Total', "label": 'Grand Total' }
                        ], 
                        "rows": rows                        
            }
def get_row(branch_id, application_type, start_date, end_date, transaction, ecaTrackingCodeFilter):
    columns = "eCAID, eCATrackingCode, AppStartDate, AppSubmitDate, AppUpdateDate, AppStatus,PrimaryName, ProductSetId, NumLendingProducts, NumDepositProducts, BranchID, Application_type, EmployeeResponsibilityCode"
    branch_id_filter = f"AND BranchID = '{str(branch_id)}'"
    if branch_id == 'All':
        branch_id_filter = ""
    application_type_filter = ""
    if application_type is not None and application_type != 'All':
        if application_type.lower() == 'banker assisted':
            application_type_filter = "AND APPLICATION_TYPE = 'Banker Assisted'"
        elif application_type.lower() == 'online':
            application_type_filter = "AND APPLICATION_TYPE = 'Online'"
    
    print(f"Processing Branch ID: {branch_id} for Application Type: {application_type} from {start_date} to {end_date}")
    return {
        "Date": f"""{start_date} 
        to             {end_date}""",
        "Start-Date": start_date,
        "End-Date": end_date,
        "BranchID": branch_id,
        "Abandoned-acknowledgements": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:acknowledgements' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-debit_card_options":
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:debit_card_options' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-demographic_information": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:demographic_information' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} "
        ,
        "Abandoned-employment": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:employment' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        , 
        "Abandoned-fiserv_presubmit_loading": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:fiserv_presubmit_loading' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-funding": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:funding' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-getting_started": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:getting_started' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-id_and_citizenship": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:id_and_citizenship' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-loading": 
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:loading' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-microdeposit_pending":
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:microdeposit_pending' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-None":
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:None' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-order_checks":
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:order_checks' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-personal_information":
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:personal_information' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-residence":
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:residence' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        ,
        "Abandoned-vouched_transition":
            f"SELECT  Count(*) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:vouched_transition' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} " 
        , 
        "Bot Data":
            f"""
            WITH UniqueTrackingCodes AS (
                SELECT eCATrackingCode
                FROM [Digitalreport].[dbo].[Transactions]
                WHERE eCATrackingCode IS NOT NULL AND eCATrackingCode != ''
                GROUP BY eCATrackingCode
                HAVING COUNT(*) = 1
            )
            SELECT  Count(*) as data from {table} as t WHERE 
            t.PrimaryName IS NOT NULL AND t.PrimaryName != '' AND
            {branch_id_filter}
            AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' AND 
            t.eCATrackingCode IN (SELECT eCATrackingCode FROM UniqueTrackingCodes) AND
            t.PrimaryName NOT IN (
                SELECT PrimaryName 
                FROM [DigitalReport].[dbo].[Transactions] 
                GROUP BY PrimaryName 
                HAVING COUNT(*) <= 35
            )
            """
        ,   
        "_report_Abandoned-acknowledgements": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStartdate IS NOT NULL AND AppStatus = 'Abandoned:acknowledgements' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC"
        , 
        "_report_Abandoned-debit_card_options":
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:debit_card_options' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-demographic_information": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:demographic_information' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC"
        ,
        "_report_Abandoned-employment": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:employment' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        , 
        "_report_Abandoned-fiserv_presubmit_loading": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:fiserv_presubmit_loading' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-funding": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:funding' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-getting_started": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:getting_started' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-id_and_citizenship": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:id_and_citizenship' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-loading": 
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:loading' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-microdeposit_pending":
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:microdeposit_pending' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-None":
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:None' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-order_checks":
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:order_checks' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-personal_information":
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:personal_information' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-residence":
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:residence' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,
        "_report_Abandoned-vouched_transition":
            f"SELECT {columns} from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:vouched_transition' AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' {branch_id_filter} {application_type_filter} AND {excludeBotData} AND {excludeZeroProductApps} order by AppStartDate DESC" 
        ,   
        "_report_Bot Data":
            f"""
            WITH UniqueTrackingCodes AS (
                SELECT eCATrackingCode
                FROM [Digitalreport].[dbo].[Transactions]
                WHERE eCATrackingCode IS NOT NULL AND eCATrackingCode != ''
                GROUP BY eCATrackingCode
                HAVING COUNT(*) = 1
            )
            SELECT {columns} from {table} t WHERE 
                t.PrimaryName IS NOT NULL AND t.PrimaryName != '' AND
                {branch_id_filter}
                AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' AND 
                t.eCATrackingCode IN (SELECT eCATrackingCode FROM UniqueTrackingCodes) AND
                t.PrimaryName NOT IN (
                    SELECT PrimaryName 
                    FROM [DigitalReport].[dbo].[Transactions] 
                    GROUP BY PrimaryName 
                    HAVING COUNT(*) <= 35
                )
            """ 
        ,   
    }


