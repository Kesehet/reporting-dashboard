from report_modules.BOR import get_bor_monthly_analytics_line, get_bor_reports
from report_modules.business_deposit_reports import get_bdr_monthly_analytics_line, get_business_deposit_reports
from report_modules.lendingAndDepositControl import get_lending_and_deposit_reports
from report_modules.abandonment import get_abandonment_reports
from report_modules.fundingType import get_funding_type_reports, get_funding_type_reports_line
from report_modules.zeroProductApps import get_zero_product_apps_bar, get_zero_product_apps_reports
from report_modules.declined_report import get_declined_reports, type_of_decline_reasons_table, type_of_decline_reasons_bar
from report_modules.multiProduct import *
from DB import Q
from report_modules.condition_utils import *
from report_modules.monthlyReports import get_monthly_in_branch_report, get_monthly_consumer_facing_report, get_monthly_business_deposits_report, get_monthly_bpm_and_crif_report, get_in_branch_vs_bpm_crif_report, get_monthly_all_report
from report_modules.newVExistingReports import generate_newVExisting_report_variants_by_filters, generate_newVExisting_report_table_variants_by_filters

def getPieChart(labels,dataset):
    return {
            "labels": labels,
            "list": dataset
        }


def getBasicTable(headers, rows):
    return {
        "headers": headers,
        "rows": rows
    }

def getLineChart(labels,datasetMap):
    return {
        "labels" : labels,
        "datasetMap" : datasetMap
    }


def divideTwoQueries(q1, q2):
    q1 = float(q1)
    q2 = float(q2)
    if q2 == 0:
        return 0
    return round(q1 / q2, 2)

def subtractTwoQueries(q1,q2):
    q1 = float(q1)
    q2 = float(q2)
    return q1-q2

def getPercentile(n):
    n = float(n)
    return str(round(n*100,2))+"%"

def getChangeProdsApps(p1,p2):
    return str(p1) + " / " + str(p2)

def getChartData(name,transactions,start_date,end_date, request=None, params=None):

    # Ctrl + K + 0 to fold all the code

    if params is None:
        params = get_request_dict(request)
    
    # Only parsed for abandonment report
    application_type = params.get("application_type", "").strip()
    application_type_condition = "" if application_type == "All" or not application_type else f"AND APPLICATION_TYPE = '{application_type}'"

    # eCATracking Like "C-%"
    ecaTrackingCodeFilter = CorBFilter(params.get("eCATrackingCode", "All"))
   
    # Application Volume By Product (All Started Apps)
    if name == "Application Volume By Product (All Started Apps) Pie - Year to Date":
        return getPieChart(
            [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed Product Apps",
               
            ],
            # data for the current year from Jan 1 to current date
            [
                        # no of loan apps from Jan 1 to current date
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND {excludeBotData} AND  {startedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};" 
                        ),
                        # avg loan apps per month from Jan 1 to current date
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND {excludeBotData} AND  {startedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        # total loan app products from Jan 1 to current date
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND {excludeBotData} AND  {startedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};" 
                        ),
            ]
        ) 
    
    #Table 1
    elif name == "Application Volume By Product (All Started Apps) Pie Table - Year to Date":  

        return getBasicTable(
            [   # headers for the table
                "Application Type",
                "Apps ",
                "Avg(Apps/Month) ",
                "Products     ",
                "Prods/Apps ",
            ],
            [   # rows for the table
                [
                    "Loan Product Applications", 
                    # no of loan apps from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg loan apps per month from Jan 1 to current date
                    round(divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT {monthsFromJanToPreviousMonth} AS data;"  # the number of months from the start of the year to the current date
                        )
                    )),
                    # total loan app products from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg loan app products per app from Jan 1 to current date
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                        )
                    ),
                ],
                [
                    "Deposit Product Applications",
                    # no of deposit apps from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg deposit apps per month from Jan 1 to current date
                    round(divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                        )
                    )),
                    # total deposit app products from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg deposit app products per app from Jan 1 to current date
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        )
                    ),
                ],
                [
                    "Mixed Product Applications",
                    # no of mixed apps from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg mixed apps per month from Jan 1 to current date
                    round(divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                        )
                    )),
                    # total mixed app products from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg mixed app products per app from Jan 1 to current date
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                        )
                    ),
                ],
                [
                    "Totals",
                    # total started apps from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg started apps per month from Jan 1 to current date
                    round(divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                        )
                    )),
                    # total started app products from Jan 1 to current date
                    transactions.get_transactions_by_sql_query(
                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                    ),
                    # avg started app products per app from Jan 1 to current date
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                        )
                    ),
                ],   
            ]
        ) 
    
    elif name == "Application Volume By Product (All Started Apps) Line":
        return getLineChart([ # labels for the line chart
            # Months from 12 months ago to current month 
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -12, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 11 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -11, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 10 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -10, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 9 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -9, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 8 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -8, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 7 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -7, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 6 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -6, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 5 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -5, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 4 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -4, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 3 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -3, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Months from 2 months ago to current month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -2, GETDATE())), 'MMM yyyy') AS data;"
            ),
            # Previous month
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -1, GETDATE())), 'MMM yyyy') AS data;"
            ),
            
        ],{ # datasetMap for the line chart
            "Loan Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {lastMonth};"
            ),
            ],
            "Deposit Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {lastMonth};"
            ),
            ],
           
            "Mixed Product Apps":
            [
             transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {lastMonth};"
            ),
            ],
        }
        )
    
    #Table 2
    elif name == "Application Volume By Product (All Started Apps) Line Table":
        return getBasicTable(
            [
                "Application Type",
                "Avg(Apps/Month) ",
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-4, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-4, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
                ),
                ],
                [
                transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
                ),                    
                ],
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
                ),
                ],
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                ],
                getChangeProdsApps(
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                ),
            ],
            [ 
                [
                    "Loan Product Applications", 
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {dataWorthPastFourCompleteQuarters}; "
                    ),12)),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {quarter3BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {quarter2BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {quarter1BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {previousQuarter};"
                    ),
                    getPercentile(
                    divideTwoQueries(
                        subtractTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {previousQuarter};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {quarter1BeforeLast};"
                        )
                        ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {quarter1BeforeLast};"
                    )
                    )
                    ),   
                ],
                [
                    "Deposit Product Applications",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {dataWorthPastFourCompleteQuarters}; "
                    ),12)),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {quarter3BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {quarter2BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {quarter1BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {previousQuarter};"
                    ),
                    getPercentile(
                    divideTwoQueries(
                        subtractTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {previousQuarter};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {quarter1BeforeLast};"
                        )
                        ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {quarter1BeforeLast};"
                    )
                    )
                    ),   
                ],
                [
                    "Mixed Product Applications",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {dataWorthPastFourCompleteQuarters}; "
                    ),12)),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {quarter3BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {quarter2BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {quarter1BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {previousQuarter};"
                    ),
                    getPercentile(
                    divideTwoQueries(
                        subtractTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {previousQuarter};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {quarter1BeforeLast};"
                        )
                        ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {quarter1BeforeLast};"
                    )
                    )
                    ),   
                ],
                [
                    "Totals",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {dataWorthPastFourCompleteQuarters}; "
                    ),12)),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {quarter3BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {quarter2BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                    ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {previousQuarter};"
                    ),
                    getPercentile(
                    divideTwoQueries(
                        subtractTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {previousQuarter};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                        )
                        ),
                    transactions.get_transactions_by_sql_query(
                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                    )
                    )
                    ),   
                ],   
            ]
        )
    
    elif name == "Application Volume By Product Quarterly (All Started Apps) Pie":
        return getPieChart(
            [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed Product Apps",
            ],
            [
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),
                    
            ]
        ) 
    
    #Table 3,4
    elif name == "Application Volume By Product Quarterly (All Started Apps) Table":
        return getBasicTable(
            [
                "Application Type",
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER, DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(1)) + '''' + RIGHT(CAST(YEAR(DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(4)), 2) AS data;"
                ),                
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER, DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(1)) + '''' + RIGHT(CAST(YEAR(DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(4)), 2) AS data;"
                ),                    
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                "Q Change in Apps / Q Change in Prods",
            ],
            [
                
                [
                    "Loan Product Applications",         
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            # data from the similar quarter from last year 
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {similarQuarterLastYear};" 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            # data from the similar quarter from last year 
                            f"SELECT SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {similarQuarterLastYear};" 
                        ),3)),             
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            # data from the latest completed quarter
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {latestCompletedQuarter};" 
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            # data from the latest completed quarter
                            f"SELECT SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {latestCompletedQuarter};" 
                        ),3)),                     
                        
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Deposit Product Applications",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)), 
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Mixed Product Applications",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)), 
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Period Totals",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),     
                    "",
                    "",
                ],
                [
                    "Grand Totals",
                        transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),                     
                        transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ), 
                        transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {latestCompletedQuarter};" # data from the latest completed quarter
                        ),                 
                        transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {latestCompletedQuarter};" # data from the latest completed quarter
                        ),                    
                        
                    "",
                    "",
                ],
                [
                    "Products per Application",  
                            
                    "",
                    
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select  SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ), 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),
                    ),

                    "",
                                            
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select  SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {latestCompletedQuarter};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {excludeZeroProductApps} AND {startedApps} AND {latestCompletedQuarter};" 
                        ),
                    ),
                        
                ],
                
            ]
        )
    
    elif name == "Application Volume By Product Quarterly (All Started Apps) Line":
        return getLineChart([
             transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -12, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -11, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -10, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -9, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -8, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -7, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -6, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -5, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -4, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -3, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -2, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -1, GETDATE())), 'MMM yyyy') AS data;"
            ),
           
        ],{
            "Loan Product Apps":
            [      
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {lastQuarter};"
            ),
            
            ],
            "Deposit Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {lastQuarter};"
            ),
            
            ],
            "Mixed Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {lastQuarter};"
            ),
            
            ],
        }
        )
    
    #Table 5
    elif name == "Application Volume by Product Current Quarter (All Started Apps) Pie":
        return getPieChart(
            [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed product Apps",
            ],
            [
                transactions.get_transactions_by_sql_query(
                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {currentQuarter};"
                ),
                transactions.get_transactions_by_sql_query(
                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {currentQuarter};"
                ),
                transactions.get_transactions_by_sql_query(
                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {currentQuarter};"
                ),

            ],
        )
    
    elif name == "Application Volume by Product Current Quarter (All Started Apps) Table":
        return getBasicTable(
            [
                "Application Type",
                "Apps ",
                "Products     ",
                "Prod/Apps ",
            ],
            [ 
                [
                    "Loan Product Applications", 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {currentQuarter};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {currentQuarter};"
                            )
                        ),
                ],
                [
                    "Deposit Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {currentQuarter};"
                        ),

                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {currentQuarter};"
                            )
                        ),        
                ],
                [
                    "Mixed Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {currentQuarter};"
                        ),
                        
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {currentQuarter};"
                            )
                        ),  
                ],
                [
                    "Total Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                        ),
                        
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                            )
                        ),
                ],
            ]
        )
   
    # Application Volume By Product (All Submitted Apps)
    elif name == "Application Volume By Product (All Submitted Apps) Pie - Year to Date":
        return getPieChart(
            [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed Product Apps",
               
            ],
            # data for the current year from Jan 1 to current date
            [
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND {excludeBotData} AND  {startedApps} AND {submittedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND {excludeBotData} AND  {startedApps} AND {submittedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND {excludeBotData} AND  {startedApps} AND {submittedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};" 
                        ),
            ]
        )
    
    #Table 1
    elif name == "Application Volume By Product (All Submitted Apps) Pie Table - Year to Date":
        return getBasicTable(
            [
                "Application Type",
                "Apps ",
                "Avg(Apps/Month) ",
                "Products     ",
                "Prod/Apps ",
            ],
            [ 
                [
                    "Loan Product Applications", 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],
                [
                    "Deposit Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {startedApps} AND {submittedApps} AND {excludeBotData} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],
                [
                    "Mixed Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],
                [
                    "Totals",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],   
            ]
        )
    
    elif name == "Application Volume By Product (All Submitted Apps) Line":
        return getLineChart([
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -12, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -11, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -10, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -9, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -8, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -7, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -6, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -5, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -4, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -3, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -2, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -1, GETDATE())), 'MMM yyyy') AS data;"
            ),
            
        ],{
             "Loan Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {lastMonth};"
            ),
            
            ],
            "Deposit Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {twelveMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {lastMonth};"
            ),
                    
            ],
            "Mixed Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {lastMonth};"
            ),
                   
            ],
            
        }
        )
    
    #Table 2
    elif name == "Application Volume By Product (All Submitted Apps) Line Table":
        return getBasicTable(
            [
                "Application Type",
                "Avg(Apps/Month)",
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-4, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
            ),
                ],
                [
                   transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
            ),                    
                ],
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
            ),
                ],
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
            ),
                ],
                getChangeProdsApps(
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                ),
            ],
            [ 
                [
                    "Loan Product Applications", 
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {quarter1BeforeLast};"
                            )
                            )
                        ),   
                ],
                [
                    "Deposit Product Applications",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {quarter1BeforeLast};"
                            )
                            )
                        ),   
                ],
                [
                    "Mixed Product Applications",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {quarter1BeforeLast};"
                            )
                            )
                        ),   
                ],
                [
                    "Totals",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                            )
                            )
                        ),   
                ],   
                ]
        )
    
    elif name == "Application Volume By Product Quarterly (All Submitted Apps) Pie":
        return getPieChart(
            [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed Product Apps",
            ],
            [               
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {previousQuarter};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {previousQuarter};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {previousQuarter};"
                        ),
                    
            ]
        )
    
    #Table 3,4
    elif name == "Application Volume By Product Quarterly (All Submitted Apps) Table":
        return getBasicTable(
            [
                "Application Type",
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER, DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(1)) + '''' + RIGHT(CAST(YEAR(DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(4)), 2) AS data;"
                ),                   
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER, DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(1)) + '''' + RIGHT(CAST(YEAR(DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(4)), 2) AS data;"
                ),                    
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                "Q Change in Apps / Q Change in Prods",
            ],
            [
                
                [
                    "Loan Product Applications",         
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),             
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Deposit Product Applications",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)), 
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Mixed Product Applications",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),             
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Period Totals",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),     
                    "",
                    "",
                ],
                [
                    "Grand Totals",
                        transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),                     
                        transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ), 
                        transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),                 
                        transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),                    
                        
                    "",
                    "",
                ],
                [
                    "Products per Application", 
                    "",
                    
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select  SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ), 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),
                    ), 

                    "",
                                            
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select  SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {latestCompletedQuarter};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {latestCompletedQuarter};" 
                        ),
                    ),
                               
                    
                        
                ],
                
            ]
        )
    
    elif name == "Application Volume By Product Quarterly (All Submitted Apps) Line": 
        return getLineChart([
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -12, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -11, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -10, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -9, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -8, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -7, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -6, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -5, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -4, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -3, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -2, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -1, GETDATE())), 'MMM yyyy') AS data;"
            ),
           
        ],{
            "Loan Product Apps":
            [  
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {twelveMonthsAgo};"
            ),    
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {loanApps} AND {lastMonth};"
            ),
           
            ],
            "Deposit Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {twelveMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {depositApps} AND {lastMonth};"
            ),
                    
            ],
            "Mixed Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {mixedApps} AND {lastMonth};"
            ),
           
            ],
        }
        )       
    
    elif name == "Application Volume by Product Current Quarter (All Submitted Apps) Pie":
        from report_modules.analytics import application_volume_by_product_current_quarter_all_submitted_apps_pie
        return application_volume_by_product_current_quarter_all_submitted_apps_pie(start_date,end_date,params)
    
    #Table 5
    elif name == "Application Volume by Product Current Quarter (All Submitted Apps) Table":
        return getBasicTable(
            [
                "Application Type",
                "Avg(Apps/Month) ",
                "Products     ",
                "Prod/Apps ",
            ],
            [ 
                [
                    "Loan Product Applications", 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {submittedApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {submittedApps} AND {currentQuarter};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {submittedApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {submittedApps} AND {currentQuarter};"
                            )
                        ),
                ],
                [
                    "Deposit Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {submittedApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {submittedApps} AND {currentQuarter};"
                        ),

                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {submittedApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {submittedApps} AND {currentQuarter};"
                            )
                        ),        
                ],
                [
                    "Mixed Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {submittedApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {submittedApps} AND {currentQuarter};"
                        ),
                        
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {submittedApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {submittedApps} AND {currentQuarter};"
                            )
                        ),  
                ],
                [
                    "Total Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                        ),
                        
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {submittedApps} AND {excludeZeroProductApps} AND {currentQuarter};"
                            )
                        ),
                ],
            ]
        )
   
    # Application Volume By Product (All Opened Or Approved Apps)
    elif name == "Application Volume By Product (All Opened Or Approved Apps) Pie - Year to Date":
        return getPieChart(
            [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed Product Apps",
               
            ],
            # data for the current year from Jan 1 to current date
            [
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND  {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND  {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND  {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};" 
                        ),
            ]
        )
    
    #Table 1
    elif name == "Application Volume By Product (All Opened Or Approved Apps) Pie Table - Year to Date":
        return getBasicTable(
            [
                "Application Type",
                "Apps ",
                "Avg(Apps/Month) ",
                "Products     ",
                "Prod/Apps ",
            ],
            [ 
                [
                    "Loan Product Applications", 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],
                [
                    "Deposit Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],
                [
                    "Mixed Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],
                [
                    "Totals",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        round(divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"SELECT {monthsFromJanToPreviousMonth} AS data;"
                            )
                        )),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {excludeZeroProductApps} AND {dataFromJanToPreviousMonth};"
                            )
                        ),
                ],   
            ]
        )
    
    elif name == "Application Volume By Product (All Opened Or Approved Apps) Line":
        return getLineChart([
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -12, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -11, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -10, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -9, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -8, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -7, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -6, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -5, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -4, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -3, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -2, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -1, GETDATE())), 'MMM yyyy') AS data;"
            ),
          
        ],{
            "Loan Product Apps":
            [
             transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {lastMonth};"
            ),

            ],
            "Deposit Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {twelveMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {lastMonth};"
            ),
                    
            ],
            "Mixed Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {twelveMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {lastMonth};"
            ),
                  
            ],
        }
        )
    
    #Table 2
    elif name == "Application Volume By Product (All Opened Or Approved Apps) Line Table":
        return getBasicTable(
            [
                "Application Type",
                "Avg(Apps/Month) ",
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-4, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
            ),
                ],
                [
                   transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-3, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
            ),                    
                ],
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
            ),
                ],
                [
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
            ),
                ],
                getChangeProdsApps(
                    transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2) AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-2, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                ),
            ],
            [ 
                [
                    "Loan Product Applications", 
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {quarter1BeforeLast};"
                            )
                        )
                    ),       
                ],
                [
                    "Deposit Product Applications",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {quarter1BeforeLast};"
                            )
                        )
                    ),       
                ],
                [
                    "Mixed Product Applications",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {quarter1BeforeLast};"
                            )
                        )
                    ),       
                ],
                
                [
                    "Totals",
                    round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {dataWorthPastFourCompleteQuarters};"
                        ),12)),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps}  AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {quarter3BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps}  AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {quarter2BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps}  AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                        ),
                    transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps}  AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {previousQuarter};"
                        ),
                    getPercentile(
                        divideTwoQueries(
                            subtractTwoQueries(
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {previousQuarter};"
                                ),
                                transactions.get_transactions_by_sql_query(
                                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                                )
                                ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {excludeZeroProductApps} AND {quarter1BeforeLast};"
                            )
                        )
                    ),      
                ],   
                ]
        )
    
    elif name == "Application Volume By Product Quarterly (All Opened Or Approved Apps) Pie":
        return getPieChart(
           [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed Product Apps",
            ],
           [
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {previousQuarter};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {previousQuarter};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {previousQuarter};"
                        ),
            ]
        )
    
    #Table 3,4
    elif name == "Application Volume By Product Quarterly (All Opened Or Approved Apps) Table":
        return getBasicTable(
            [
                "Application Type",
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER, DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(1)) + '''' + RIGHT(CAST(YEAR(DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(4)), 2) AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER, DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(1)) + '''' + RIGHT(CAST(YEAR(DATEADD(QUARTER, -5, CURRENT_TIMESTAMP)) AS VARCHAR(4)), 2) AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Q' + CAST(DATEPART(QUARTER,DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR) + '''' + RIGHT(CAST(DATEPART(YEAR, DATEADD(QUARTER,-1, CURRENT_TIMESTAMP)) AS VARCHAR), 2)  AS data;"
                ),
                "Q Change in Apps / Q Change in Prods",
            ],
            [
                
                [
                    "Loan Product Applications",         
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),             
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Deposit Product Applications",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)), 
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT Sum(NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        getChangeProdsApps(
                                getPercentile(
                                    divideTwoQueries(
                                        subtractTwoQueries(
                                            transactions.get_transactions_by_sql_query(
                                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {latestCompletedQuarter};"
                                            ),
                                            transactions.get_transactions_by_sql_query(
                                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                            )
                                            ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                        )
                                    )
                                ),
                                getPercentile(
                                    divideTwoQueries(
                                        subtractTwoQueries(
                                            transactions.get_transactions_by_sql_query(
                                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {latestCompletedQuarter};"
                                            ),
                                            transactions.get_transactions_by_sql_query(
                                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                            )
                                            ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                        )
                                    )
                                ),
                            ),
                ],
                [
                    "Mixed Product Applications",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),             
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM(NumLendingProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                     
                        
                        getChangeProdsApps(
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                            getPercentile(
                                divideTwoQueries(
                                    subtractTwoQueries(
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {latestCompletedQuarter};"
                                        ),
                                        transactions.get_transactions_by_sql_query(
                                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                        )
                                        ),
                                    transactions.get_transactions_by_sql_query(
                                        f"Select SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {similarQuarterLastYear};"
                                    )
                                )
                            ),
                        ),
                ],
                [
                    "Period Totals",
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),                     
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),3)),
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),                   
                        round(divideTwoQueries(transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),3)),     
                    "",
                    "",
                ],
                [
                    "Grand Totals",
                        transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),                     
                        transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ), 
                        transactions.get_transactions_by_sql_query(
                            f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),                 
                        transactions.get_transactions_by_sql_query(
                            f"SELECT SUM (NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {latestCompletedQuarter};" #data from the latest completed quarter
                        ),                    
                        
                    "",
                    "",
                ],
                [
                    "Products per Application",  
                     "",
                    
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select  SUM(NumLendingProducts + NumDepositProducts) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ), 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {similarQuarterLastYear};" # data from the similar quarter from last year 
                        ),
                    ),

                    "",
                                            
                    divideTwoQueries(
                        transactions.get_transactions_by_sql_query(
                            f"Select  SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {latestCompletedQuarter};" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {latestCompletedQuarter};" 
                        ),
                    ),                       
                ],
                
            ]
        )
   
    elif name == "Application Volume By Product Quarterly (All Opened Or Approved Apps) Line": 
        return getLineChart([
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -12, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -11, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -10, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -9, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -8, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -7, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -6, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -5, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -4, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -3, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -2, GETDATE())), 'MMM yyyy') AS data;"
            ),
            transactions.get_transactions_by_sql_query(
            "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -1, GETDATE())), 'MMM yyyy') AS data;"
            ),
            
        ],{
            "Loan Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {loanApps} AND {lastMonth};"
            ),
            
            ],
            "Deposit Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {twelveMonthsAgo};"
            ),  
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {depositApps} AND {lastMonth};"
            ),
                  
            ],
            "Mixed Product Apps":
            [
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {twelveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {elevenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {tenMonthsAgo};"
            ), 
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {nineMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {eightMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {sevenMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {sixMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {fiveMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {fourMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {threeMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {twoMonthsAgo};"
            ),
            transactions.get_transactions_by_sql_query(
            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND {mixedApps} AND {lastMonth};"
            ),
            
            ],
        }
        )       
    
    elif name == "Application Volume by Product Current Quarter (All Approved Apps) Pie":
        return getPieChart(
            [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed product Apps",
            ],
            [
                transactions.get_transactions_by_sql_query(
                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND  {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {currentQuarter};"
                ),
                transactions.get_transactions_by_sql_query(
                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND  {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {currentQuarter};"
                ),
                transactions.get_transactions_by_sql_query(
                    f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND  {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {currentQuarter};"
                ),

            ],
        )
   
    #Table 5
    elif name == "Application Volume by Product Current Quarter (All Approved Apps) Table":
        return getBasicTable(
            [
                "Application Type",
                "Apps ",
                "Products     ",
                "Prod/Apps ",
            ],
            [ 
                [
                    "Loan Product Applications", 
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {currentQuarter};"
                        ),
                    
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {loanApps} AND {approvedApps} AND {currentQuarter};"
                            )
                        ),
                ],
                [
                    "Deposit Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {currentQuarter};"
                        ),

                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {depositApps} AND {approvedApps} AND {currentQuarter};"
                            )
                        ),        
                ],
                [
                    "Mixed Product Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {currentQuarter};"
                        ),
                        
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {mixedApps} AND {approvedApps} AND {currentQuarter};"
                            )
                        ),  
                ],
                [
                    "Total Applications",
                        transactions.get_transactions_by_sql_query(
                            f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {currentQuarter};"
                        ),
                    
                        transactions.get_transactions_by_sql_query(
                            f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {currentQuarter};"
                        ),
                        
                        divideTwoQueries(
                            transactions.get_transactions_by_sql_query(
                                f"Select SUM(NumLendingProducts + NumDepositProducts) as data FROM {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {currentQuarter};"
                            ),
                            transactions.get_transactions_by_sql_query(
                                f"Select COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {ecaTrackingCodeFilter} AND {excludeBotData} AND {startedApps} AND {approvedApps} AND ({loanApps} OR {depositApps} OR {mixedApps}) AND {excludeZeroProductApps} AND {currentQuarter};"
                            )
                        ),
                ],
            ]
        )

    # data for the abandonement report
    elif name == "Abandonment Report by Week Bar":
        
        return getPieChart(
            [
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Week (' + FORMAT(DATEADD(DAY,-20 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ' - ' + FORMAT(DATEADD(DAY, -14 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ')' AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Week (' + FORMAT(DATEADD(DAY,-13 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ' - ' + FORMAT(DATEADD(DAY, -7 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ')' AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Week (' + FORMAT(DATEADD(DAY,-6 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ' - ' + FORMAT(DATEADD(DAY, 0 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ')' AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                    "SELECT 'Week (' + FORMAT(DATEADD(DAY,0 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ' - ' + FORMAT(DATEADD(DAY, 7 - DATEPART(WEEKDAY, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP), 'MMM dd') + ')' AS data;"
                    ),       
            ],
            # data for the current year from Jan 1 to current date
            [
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(WEEK, AppStartDate, CURRENT_TIMESTAMP) = 3 {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(WEEK, AppStartDate, CURRENT_TIMESTAMP) = 2 {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(WEEK, AppStartDate, CURRENT_TIMESTAMP) = 1 {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(WEEK, AppStartDate, CURRENT_TIMESTAMP) = 0 {application_type_condition} AND {excludeBotData} ;"
                ), 
            ]
        ) 
    
    elif name == "Abandonment Report by Month Pie":
         return getPieChart(
            [
                transactions.get_transactions_by_sql_query(
                        "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -3, GETDATE())), 'MMM yyyy') AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                        "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -2, GETDATE())), 'MMM yyyy') AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                        "SELECT FORMAT(EOMONTH(DATEADD(MONTH, -1, GETDATE())), 'MMM yyyy') AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                        "SELECT FORMAT(EOMONTH(DATEADD(MONTH, 0, GETDATE())), 'MMM yyyy') AS data;"
                    ),
            ],
            # data for the current year from Jan 1 to current date
            [
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(MONTH, AppStartDate, CURRENT_TIMESTAMP) = 3 {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(MONTH, AppStartDate, CURRENT_TIMESTAMP) = 2  {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(MONTH, AppStartDate, CURRENT_TIMESTAMP) = 1  {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(MONTH, AppStartDate, CURRENT_TIMESTAMP) = 0  {application_type_condition} AND {excludeBotData} ;" 
                ),   
            ]
        ) 
    
    elif name == "Abandonment Report by Year Pie":
         return getPieChart(
            [
                transactions.get_transactions_by_sql_query(
                        "SELECT CAST(YEAR(DATEADD(YEAR, -3, GETDATE())) AS VARCHAR(4)) AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                        "SELECT CAST(YEAR(DATEADD(YEAR, -2, GETDATE())) AS VARCHAR(4)) AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                        "SELECT CAST(YEAR(DATEADD(YEAR, -1, GETDATE())) AS VARCHAR(4)) AS data;"
                    ),
                transactions.get_transactions_by_sql_query(
                        "SELECT CAST(YEAR(GETDATE()) AS VARCHAR(4)) AS data;"
                    ),
            ],
            # data for the current year from Jan 1 to current date
            [
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(YEAR, AppStartDate, CURRENT_TIMESTAMP) = 3 {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(YEAR, AppStartDate, CURRENT_TIMESTAMP) = 2 {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(YEAR, AppStartDate, CURRENT_TIMESTAMP) = 1 {application_type_condition} AND {excludeBotData} ;" 
                ),
                transactions.get_transactions_by_sql_query(
                    f"SELECT COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data FROM {table} WHERE {ecaTrackingCodeFilter} AND AppStatus like '%Abandoned%' AND DATEDIFF(YEAR, AppStartDate, CURRENT_TIMESTAMP) = 0 {application_type_condition} AND {excludeBotData} ;" 
                ),                          
            ]
        ) 
    
    elif name == "Abandonment Report by Types of Abandonment Pie":
         return getPieChart(
            [
                "Abandoned : acknowledgements",
                "Abandoned : debit_card_options",
                "Abandoned : demographic_information",
                "Abandoned : employment",
                "Abandoned : fiserv_presubmit_loading",
                "Abandoned : funding",
                "Abandoned : getting_started",
                "Abandoned : id_and_citizenship",
                "Abandoned : loading",
                "Abandoned : microdeposit_pending",
                "Abandoned : None",
                "Abandoned : order_checks",
                "Abandoned : personal_information",
                "Abandoned : prove_waiting",
                "Abandoned : residence",
                "Abandoned : vouched_transition",
            ],
            # data for the current year from Jan 1 to current date
            [
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:acknowledgements'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:debit_card_options'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:demographic_information'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:employment'  {application_type_condition} AND {excludeBotData} ;" 
                        ), 
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:fiserv_presubmit_loading'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:funding' {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:getting_started'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:id_and_citizenship'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:loading'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:microdeposit_pending'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:None'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:order_checks'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:personal_information'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:residence'  {application_type_condition} AND {excludeBotData} ;" 
                        ),
                        transactions.get_transactions_by_sql_query(
                            f"SELECT  COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} WHERE {ecaTrackingCodeFilter} AND AppStatus = 'Abandoned:vouched_transition'  {application_type_condition} AND {excludeBotData} ;"  
                        ),   
            ]
        ) 
   
    elif name == "Abandonment Report":
        return get_abandonment_reports(start_date, end_date, branch_id=params.get("BranchID",""), application_type=params["application_type"], ecaTrackingCodeFilter=ecaTrackingCodeFilter)
    
    # Zero Product Applications
    elif name == "Zero Product Applications Bar":
        return get_zero_product_apps_bar(application_type_condition, params)
    
    elif name == "Zero Product Applications Table":
        return get_zero_product_apps_reports(start_date, end_date, application_type_condition)

    elif name == "Custom Quarterly Analytics Common App Table":
        from report_modules.analytics import get_custom_quarterly_analytics_common_app_table
        return get_custom_quarterly_analytics_common_app_table(start_date, end_date, params)
    elif name == "Custom Quarterly Analytics Customer eCA Table":
        from report_modules.analytics import get_custom_quarterly_analytics_customer_eCA_table
        return get_custom_quarterly_analytics_customer_eCA_table(start_date, end_date, params)
    elif name == "Custom Quarterly Analytics InBranch Common App Table":
        from report_modules.analytics import get_custom_quarterly_analytics_inBranch_common_app_table
        return get_custom_quarterly_analytics_inBranch_common_app_table(start_date, end_date, params)
    
    # BOR
    elif name == "Branch Originated Reports":
        return get_bor_reports(start_date, end_date, params)

    elif name == "Branch Originated Reports Monthly Analytics Line":
        return get_bor_monthly_analytics_line(start_date, end_date, params)

    # Business Deposit Reports
    elif name == "Business Deposit Reports":
        return get_business_deposit_reports(start_date, end_date, params)

    elif name == "Business Deposit Reports Monthly Analytics Line":
        return get_bdr_monthly_analytics_line(start_date, end_date, params)

    #Lending and Deposit Reports
    elif name == "Lending And Deposit Reports":
        return get_lending_and_deposit_reports(start_date, end_date, params)

    #Funding Type Reports
    elif name == "Funding Type Report":
        return get_funding_type_reports(start_date, end_date, ecaTrackingCodeFilter)
    
    elif name == "Funding Type Report Line":
        return get_funding_type_reports_line(start_date, end_date, ecaTrackingCodeFilter)

    #All Transactions
    elif name == "All Transactions":
        
        ignore_columns = [
            "PrimaryName", "PrimarySSN"
        ]

        available_columns = [column for column in ALL_COLUMNS if column not in PII_COLUMNS and column not in ignore_columns]
        rows_query_result = Q(columns=available_columns, where=[ecaTrackingCodeFilter, excludeBotData, get_date_filter(start_date,end_date)], order_by="AppStartDate DESC", params=params)
        if rows_query_result == 0:
            rows_query_result = []
        rows_lists = [list(item.values()) for item in rows_query_result]
        row_columns = list(rows_query_result[0].keys()) if rows_query_result else []
        return getBasicTable(
            row_columns,
            rows_lists
            )
    
    # All Branch Ids
    elif name == "All Branch Ids":
        # Ignore 'start_date' and 'end_date' in params when building conditions
        return {
            
            "rows": [key for key, _ in ALL_BRANCH_ID]
        }
    
    elif name == "Multi Products Product Set Id Table":
        return get_multi_product_product_set_id_report_table(start_date, end_date, ecaTrackingCodeFilter)
    
    elif name == 'Multi Products Daily Product Set Id Insights':
        return get_daily_multi_product_product_set_id_report_table(start_date,end_date,ecaTrackingCodeFilter)
    
    elif name == "Multi Products Product Set Id Bar":
        return get_multi_product_product_set_id_report_bar(start_date, end_date, ecaTrackingCodeFilter)
    
    elif name == "Multi Products Cross Sell Table":
        return get_multi_product_cross_sell_report_table(start_date, end_date, ecaTrackingCodeFilter)

    elif name == "Monthly Multi Product Reports Line":
        return get_monthly_multi_product_reports_line(start_date, end_date, ecaTrackingCodeFilter, params)
    
    elif name == "Multi Products Cross Sell Bar":
        return get_multi_product_cross_sell_report_bar(start_date, end_date, ecaTrackingCodeFilter)
    
    elif name == "Top 10 Single product with Cross Sell Products Bar":
        return get_single_product_cross_sell_report_bar(start_date,end_date, ecaTrackingCodeFilter)
    
    elif name == "Top 10 Single product with Cross Sell Products Table":
        return get_single_product_cross_sell_report_table(start_date,end_date, ecaTrackingCodeFilter)

    elif name == "Cross Sell Products Table":
        return getBasicTable(
            [
                "",
                "CrossSellProduct",
                "Product",
                "Total Apps",
                "In Branch",
                "Online",   
            ],
            [

            ]
        ),

    elif name == "Common App In Branch and Consumer Facing Report":
        return get_monthly_all_report(
            start_date,
            end_date,
            params,
            transactions=transactions,
        )

    elif name == "Monthly In Branch Report":
        return get_monthly_in_branch_report(start_date, end_date, params)
    
    elif name == "Monthly Consumer Facing Report":
        return get_monthly_consumer_facing_report(start_date, end_date, params)
    
    elif name == "Monthly Business Deposits And Loans Report":
        return get_monthly_business_deposits_report(start_date, end_date, params)

    elif name == "Monthly BPM and CRIF Report":
        return get_monthly_bpm_and_crif_report(start_date, end_date, params)
    
    elif name == "Monthly In Branch vs BPM and CRIF Report":
        import time
        time.sleep(20)
        return get_in_branch_vs_bpm_crif_report(start_date, end_date, params)

    elif name == "Cross Sell Products Presented and Accepted Table":
        
        return get_cross_sell_products_presented_and_accepted_table(start_date,end_date,params)
    
    elif name == "Cross Sell Products Presented and Accepted Line":
        return get_cross_sell_products_presented_and_accepted_line(start_date,end_date,params)

    elif name == "Declined Report Table":
        return get_declined_reports(start_date, end_date)   
    
    elif name == "Declined Report Line":
        table_data =  get_declined_reports(start_date, end_date) 
        return getLineChart(
            table_data["headers"][1:len(table_data["headers"])],
        {
            "Decline": table_data["rows"][0][1:len(table_data["rows"][0])]
        })
   
    elif name == "Type Of Decline Reasons Table":
        return type_of_decline_reasons_table(start_date,end_date,params)
    
    elif name == "Type Of Decline Reasons Bar":
        return type_of_decline_reasons_bar(start_date,end_date,params)
    
    elif name == "New vs Exisitng Customers":
        return generate_newVExisting_report_variants_by_filters(start_date, end_date, params, base_filters=[submittedApps])
    
    elif name == "New vs Existing Customers Table":
        return generate_newVExisting_report_table_variants_by_filters(start_date,end_date, params, base_filters=[submittedApps])
    
    elif name == "All Filters Table":
        from report_modules.all_filter_report import get_filters
        return get_filters(start_date,end_date, ecaTrackingCodeFilter, params["filters"], params.get("format","json"))
    
    elif name == "Loan Commitment Stacked Bar":
        from report_modules.loan_account_apps_and_commitments import get_stacked_bar_report
        return get_stacked_bar_report(start_date, end_date, params)
    
    elif name ==  "Loan Commitment Stacked Table":
        from report_modules.loan_account_apps_and_commitments import get_table_report
        return get_table_report(start_date,end_date, params)
    
    elif name ==  "Loan Commitment Bar And Line":
        from report_modules.loan_account_apps_and_commitments import get_bar_line_chart_report
        return get_bar_line_chart_report(start_date,end_date, params)
    
    elif name == "Loan Commitment Insights":
        from report_modules.loan_account_apps_and_commitments import get_insigths_report
        return get_insigths_report(start_date,end_date,params)
    
    elif name == "Spot And Current Balance Account Insights":
        from report_modules.spotAndCurrentBalanceAccount import get_insights
        return get_insights(start_date,end_date,params)
    
    elif name == "Spot And Current Balance Account Table":
        from report_modules.spotAndCurrentBalanceAccount import get_table
        return get_table(start_date,end_date,params)
    
    elif name == "Spot And Current Balance Account Stacked Chart":
        from report_modules.spotAndCurrentBalanceAccount import get_stacked_chart
        return get_stacked_chart(start_date,end_date,params)
    
    elif name == "Monthly Opening And Current Balance Table":
        from report_modules.spotAndCurrentBalanceAccount import get_monthly_opening_and_current_balance_table
        return get_monthly_opening_and_current_balance_table(start_date,end_date,params)
    
    elif name == "Document Center Insigths":
        from report_modules.documentCenterReports import get_document_center_insights
        return get_document_center_insights(params)

    elif name == "Document Center Monthly Insigths":
        from report_modules.documentCenterReports import get_document_center_monthly_insights
        return get_document_center_monthly_insights(start_date,end_date)
    
    elif name == "Document Center Monthly Insigths Line":
        from report_modules.documentCenterReports import get_document_center_monthly_insights_line
        return get_document_center_monthly_insights_line(start_date,end_date)
    
    elif name == "Direct Deposit Switch Reports Table":
        from report_modules.dds_report import direct_deposit_switch_report_table
        return direct_deposit_switch_report_table(start_date,end_date,params)
    
    elif name == "Direct Deposit Switch Reports Insights":
        from report_modules.dds_report import direct_deposit_switch_report_insights
        return direct_deposit_switch_report_insights(start_date,end_date,params)
    
    elif name == "Current Total DDS Amount and Switches Insights":
        from report_modules.dds_report import current_total_dds_amount
        return current_total_dds_amount(start_date, end_date, params)
    
    elif name == "All Bot Deduped Data Monthly Insights":
        from report_modules.all_filter_report import all_bot_deduped_data_monthly_insights
        return all_bot_deduped_data_monthly_insights(start_date,end_date, params)
    
    elif name == "Bot Generated Reports Insights":
        from report_modules.bot_generated_reports import bot_generated_reports_insights
        return bot_generated_reports_insights(start_date,end_date,params)

    elif name == "Bot Generated Reports Monthly Insights":
        from report_modules.bot_generated_reports import bot_generated_reports_monthly_insights
        return bot_generated_reports_monthly_insights(start_date,end_date, params)
    
    elif name == "Payment Switch Insights":
        from report_modules.payment_switch_report import get_payment_switch_insight
        return get_payment_switch_insight(start_date, end_date, params)

    elif name == "E-Delivery Report Insights":
        from report_modules.e_delivery_report import get_e_delivery_report_insights
        return get_e_delivery_report_insights()
    
    elif name == "Business Account Summary Number Of Apps Table":
        from report_modules.businessAccountsSummary import get_number_of_apps_by_product_type_summarized
        return get_number_of_apps_by_product_type_summarized(start_date, end_date, params)   
    
    elif name == "Business Account Summary Top 10 Products Table":
        from report_modules.businessAccountsSummary import get_top_10_products
        return get_top_10_products(start_date, end_date, params)
    elif name == "Business Account Summary Top 10 Branches Table":
        from report_modules.businessAccountsSummary import get_top_10_branches
        return get_top_10_branches(start_date, end_date, params)
    elif name == "Business Account Summary Current Balance and Initial Deposit Table":
        from report_modules.businessAccountsSummary import get_current_balance_and_initial_deposit
        return get_current_balance_and_initial_deposit(start_date, end_date, params)
    
    elif name == "E Delivery Report LOB Table":
        from report_modules.edelivery_report_lob import edelivery_report_table
        return edelivery_report_table(start_date, end_date)
    
    elif name == "Student Checking Report Insights":
        from report_modules.student_checking_report import student_checking_report_insights
        return student_checking_report_insights()
    
    elif name == "Student Checking Monthly Report Table":
        from report_modules.student_checking_report import student_checking_report_table
        return student_checking_report_table(start_date,end_date)
    
    elif name == "Transaction Logger Recent Txns":
        from report_modules.search_txn import search_txn
        return search_txn(params, start_date, end_date, True)
    
    elif name == "Transaction Logger":
        from report_modules.search_txn import search_txn
        return search_txn(params, start_date, end_date, False)

    elif name == "PennState Branch Report Insights":
        from report_modules.pennStateBankingReports import pennStateBranchReportsInsights 
        return pennStateBranchReportsInsights(params, start_date, end_date)

    elif name == "PennState Student Banking Reports Insights":
        from report_modules.pennStateBankingReports import pennStateStudentBankingReportsInsights
        return pennStateStudentBankingReportsInsights(params, start_date, end_date)

    elif name == "PennState Student Banking Reports Line":
        from report_modules.pennStateBankingReports import pennStateStudentBankingReportsLine
        return pennStateStudentBankingReportsLine(params, start_date, end_date)

    elif name == "Shot Clock Application Reports Insights":
        from report_modules.shotclockapplicationsReports import shot_clock_application_insights
        return shot_clock_application_insights(start_date,end_date,params)
    else:
        return {
            "message" : "No Charts specified.",
            "status" : "error",
            "name": name
        }

def get_request_dict(request):
    """
    Extracts the request data from the request object.
    """
    json = {}
    if request.method == 'POST':
        json = request.get_json()
    elif request.method == 'GET':
        json = request.args.to_dict()
    if json.get('api_key'):
        del json['api_key']
    return json