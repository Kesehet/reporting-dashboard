from report_modules.condition_utils import *
from utils import *
from DB import SQLConn, Transaction



def bot_generated_reports_insights(start_date, end_date, params):

    columns = ["eCAID", "eCATrackingCode", "AppStartDate", "AppSubmitDate", "AppUpdateDate", "AppStatus","PrimaryName", "ProductSetId", "NumLendingProducts", "NumDepositProducts", 
    "BranchID", "Application_type", "EmployeeResponsibilityCode"] + COMMON_EXPORT_COLUMNS

    columns = ", ".join(list(set(columns)))

    table = "DigitalReport.dbo.Transactions"
    return {"Bot Data-Filter35":
                f"""
                WITH UniqueTrackingCodes AS (
                    SELECT eCATrackingCode
                    FROM [Digitalreport].[dbo].[Transactions]
                    WHERE eCATrackingCode IS NOT NULL AND eCATrackingCode != ''
                    GROUP BY eCATrackingCode
                    HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) = 1
                )
                SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} as t WHERE 
                t.PrimaryName IS NOT NULL AND t.PrimaryName != '' AND
                AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' AND 
                t.eCATrackingCode IN (SELECT eCATrackingCode FROM UniqueTrackingCodes) AND
                t.PrimaryName NOT IN (
                    SELECT PrimaryName 
                    FROM [DigitalReport].[dbo].[Transactions] 
                    GROUP BY PrimaryName 
                    HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) <= 35
                )
                """
            ,
            "Bot Data-Filter25":
                f"""
                WITH UniqueTrackingCodes AS (
                    SELECT eCATrackingCode
                    FROM [Digitalreport].[dbo].[Transactions]
                    WHERE eCATrackingCode IS NOT NULL AND eCATrackingCode != ''
                    GROUP BY eCATrackingCode
                    HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) = 1
                )
                SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} as t WHERE 
                t.PrimaryName IS NOT NULL AND t.PrimaryName != '' AND
                AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' AND 
                t.eCATrackingCode IN (SELECT eCATrackingCode FROM UniqueTrackingCodes) AND
                t.PrimaryName NOT IN (
                    SELECT PrimaryName 
                    FROM [DigitalReport].[dbo].[Transactions] 
                    GROUP BY PrimaryName 
                    HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) <= 25
                )
                """
            , 
            "Suspected Bot Transactions Report (No SSN)" :
                f"""Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE PrimaryName IS NOT NULL AND (PrimarySSN IS NULL OR PrimarySSN = '') AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}'   AND {excludeZeroProductApps}""",
            
            "_report_Bot Data-Filter35":
                f"""
                WITH UniqueTrackingCodes AS (
                    SELECT eCATrackingCode
                    FROM [Digitalreport].[dbo].[Transactions]
                    WHERE eCATrackingCode IS NOT NULL AND eCATrackingCode != ''
                    GROUP BY eCATrackingCode
                    HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) = 1
                )
                SELECT {columns} from {table} t WHERE 
                    t.PrimaryName IS NOT NULL AND t.PrimaryName != '' AND
                    AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' AND 
                    t.eCATrackingCode IN (SELECT eCATrackingCode FROM UniqueTrackingCodes) AND
                    t.PrimaryName NOT IN (
                        SELECT PrimaryName 
                        FROM [DigitalReport].[dbo].[Transactions] 
                        GROUP BY PrimaryName 
                        HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) <= 35
                    )
                """ 
            ,
            "_report_Bot Data-Filter25":
                f"""
                WITH UniqueTrackingCodes AS (
                    SELECT eCATrackingCode
                    FROM [Digitalreport].[dbo].[Transactions]
                    WHERE eCATrackingCode IS NOT NULL AND eCATrackingCode != ''
                    GROUP BY eCATrackingCode
                    HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) = 1
                )
                SELECT {columns} from {table} t WHERE 
                    t.PrimaryName IS NOT NULL AND t.PrimaryName != '' AND
                    AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' AND 
                    t.eCATrackingCode IN (SELECT eCATrackingCode FROM UniqueTrackingCodes) AND
                    t.PrimaryName NOT IN (
                        SELECT PrimaryName 
                        FROM [DigitalReport].[dbo].[Transactions] 
                        GROUP BY PrimaryName 
                        HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) <= 25
                    )
                """,
            "_report_Suspected Bot Transactions Report (No SSN)" :
                f"""Select * from {table} WHERE PrimaryName IS NOT NULL AND (PrimarySSN IS NULL OR PrimarySSN = '') AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}'   AND {excludeZeroProductApps} order by AppStartDate DESC""",

            "_report_Bot Generated Data - Current Page identifier" :
                f"""Select * from {table} WHERE PrimaryName IS NOT NULL AND (PrimarySSN IS NULL OR PrimarySSN = '') AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}'   AND {excludeZeroProductApps} AND CurrentPage = 'getting_started' order by AppStartDate desc""",
            
    }

def bot_generated_reports_monthly_insights(start_date, end_date, params):
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    ret = {}
    for interval in get_list_of_months_between(start_date, end_date):
        label = get_header(interval)['label'].split("-")
        label = label[1] + "-" + label[0]
        ret[label] = {
                        "Bot Data-Filter35": txn.get_transactions_by_sql_query(bot_generated_reports_insights(interval['start_date'], interval['end_date'], params)["Bot Data-Filter35"]),
                        "Suspected Bot Transactions":  txn.get_transactions_by_sql_query(bot_generated_reports_insights(interval['start_date'], interval['end_date'], params)["Suspected Bot Transactions Report (No SSN)"])
                      }
        ret[label]["Total"] = ret[label]["Bot Data-Filter35"] + ret[label]["Suspected Bot Transactions"]
        ret["_report_" + label] = bot_generated_reports_insights(interval['start_date'], interval['end_date'], params)["_report_Bot Data-Filter35"]
    sql.disconnect()
    return ret


