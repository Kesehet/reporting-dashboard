DOLLAR_SIGN = " $ "


'''
____________________________________________________________________________________________________________________________________________________________________________________________
                                FILTERS
____________________________________________________________________________________________________________________________________________________________________________________________
'''
SUBMITTED_FOR_LOAN_COMMITMENT = [
    'Fiserv Failure and Retry',
    'Onboarding Error',
    'Onboarding Error Application Complete',
    'Review Application',
    'LOS Submitted',
    'Decline Application Complete'
]
SUBMITTED_APPS_STATUSES = [
    'Fiserv Failure and Retry',
    'Onboarding Error',
    'Onboarding Error Application Complete',
    'Review Application',
    'Approve Application Endpoint',
    'Approve Application',
    'Approve Application Complete',
    'Approved',
    'Approved Pending Microdeposits',
    'BPM Submitted',
    'Deposit Approved Queue',
    'Post Approval Customer Tasks',
    'Fiserv Failure and Retry Appliation Complete',
    'Fiserv Failure and Retry Application Endpoint',
    'Loans Approved and Deposit Approved Queue',
    'Loans Approved Queue',
    'LOS Submitted',
    'Decline Application Complete'
]
APPROVED_APPS_STATUSES = [
    'Approve Application Endpoint',
    'Approve Application',
    'Approve Application Complete',
    'Approved',
    'Approved Pending Microdeposits',
    'BPM Submitted',
    'Deposit Approved Queue',
    'Post Approval Customer Tasks',
    'Fiserv Failure and Retry Appliation Complete',
    'Fiserv Failure and Retry Application Endpoint',
    'Loans Approved and Deposit Approved Queue',
    'Loans Approved Queue']

APPROVED_APPS_FILTER = " AND PrimarySSN IS NOT NULL AND PrimarySSN != '' AND AppStatus IN ( "+','.join([f'\'{app}\'' for app in APPROVED_APPS_STATUSES])+ ") "
SUBMITTED_APPS_FILTER = " AND PrimarySSN IS NOT NULL AND PrimarySSN != '' AND AppStatus IN ( "+','.join([f'\'{app}\'' for app in SUBMITTED_APPS_STATUSES])+ ") "
SUBMITTED_FOR_LOAN_COMMITMENT_FILTER = "AND PrimarySSN IS NOT NULL AND PrimarySSN != '' AND AppStatus IN ( "+','.join([f'\'{app}\'' for app in SUBMITTED_FOR_LOAN_COMMITMENT])+ ") "

table = "[DigitalReport].[dbo].[Transactions]" # Table name
TABLE_NAME = "[DigitalReport].[dbo].[Transactions]"


consumerTransaction = "eCATrackingCode like 'C-%'"
businessTransaction = "ecaTrackingCode like 'B-%'"

# Prevention of repetitions 

distinctValues = "Select DISTINCT (ecaTrackingCode), * from [DigitalReport].[dbo].[Transactions]"

#lending and deposit control 

applicationsApprovedAwaitingEntry = "AppStatus IN ('Deposit Approved Queue','Loans Approved and Deposit Approved Queue','Loans Approved Queue','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks')"
applicationsApprovedFundingOngoing = "AppStatus IN ('Approved Pending Microdeposits')"

# check for underwriting and funding ongoing from edw - talk to nicholas
applicationsApprovedInUnderwriting = "AppStatus IN ('LOS Submitted')"
applicationsApprovedOnboarded = "AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','BPM Submitted','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Opened','Completed')"
applicationsDeclined = " AppStatus IN ('Decline Application','Decline Application Complete','Denied')"
applicationsExpired = " AppStatus IN ('Expired')"
applicationsInProgressAbandoned = " ((AppStatus like 'Abandoned%') OR AppStatus IN ('Cancel Application','Cancel Endpoint')) "
applicationsInProgressSaved = " AppStatus IN ('Pending','Saved')"
applicationsInProgressStarted = " AppStatus IN ('Address Add','Start','Started')"
applicationsMissing = " AppStatus IN ('Unknown')"
applicationsSubmittedError = "AppStatus IN ('Fiserv Failure and Retry','Onboarding Error','Onboarding Error Application Complete')"
applicationsSubmittedUnderReview = "AppStatus IN ('Review Application')"
applicationsSubmitted = "AppStatus IN ('Deposit Submitted','LOS Submitted')"


#### Abandoned","                                # Address Add","                                        # Fiserv Failure and Retry Application Complete
#### Abandoned:document_uploads      ","        # Approve Application","                                # Fiserv Failure and Retry Application Endpoint
#### Abandoned:employment","                    # Approve Application Complete","                        # Loans Approved and Deposit Approved Queue
#### Abandoned:existing_customer_verify_phone","# Approve Application Endpoint","                        # Loans Approved Queue
#### Abandoned:funding","                        # Approved","                                            # LOS Submitted
#### Abandoned:getting_Started","                # Approved Pending Microdeposits","                    # Onboarding Error
#### Abandoned:id_and_citizenship","            # BPM Submitted","                                        # Onboarding Error Application Complete
#### Abandoned:loading","                        # Cancel Application","                                # Opened
#### Abandoned:personal_information","            # Cancel Endpoint","                                    # Pending
#### Abandoned:product_info_008_e5aa6d27-e609-4073-8bc9-6b4f749a9552","# Completed","                    # Post-Approval Approved Tasks
#### Abandoned:product_info_011_968edb70-90a3-41ff-84ca-b6910cfcc720","# Decline Application","        # Post-Approval Customer Tasks
#### Abandoned:product_info_23602_cdc31647-22d3-409e-88e5-cb42a60bb4d3","# Decline Application Complete","# Post-BPM Entry Tasks
#### Abandoned:product_info_24201_670a50a7-f00a-4d8d-8e32-c98575296100","# Denied","                    # Review Application
#### Abandoned:prove_waiting","                # Deposit Approved Queue","                            # Saved
#### Abandoned:sb-primary-personal-details","    # Deposit Submitted","                                    # Start
#### Abandoned:sb-primary-prove-waiting","        # Expired","                                            # Started
#### Abandoned:vouched_transition","            # Fiserv Failure and Retry","                            # Unknown



#Bot data and Zero Product Applications
excludeBotData = "PrimaryName NOT LIKE '%test%' AND PrimarySSN IS NOT NULL AND PrimarySSN != '' AND PrimaryName IS NOT NULL AND PrimaryName != '' AND PrimaryName != 'TlVMTA==' AND PrimaryName IN (SELECT PrimaryName FROM [DigitalReport].[dbo].[Transactions] GROUP BY PrimaryName HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) <= 25)" # Filter for Bot data- PrimaryName with less than 500 transactions
includeBotData = "PrimaryName IS NOT NULL AND PrimaryName != '' AND PrimaryName != 'TlVMTA==' AND PrimaryName NOT IN (SELECT PrimaryName FROM [DigitalReport].[dbo].[Transactions] GROUP BY PrimaryName HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) <= 25)" # Filter for Bot data - PrimaryName with more than 500 transactions
#Zero Product Applications 
excludeZeroProductApps = 'NOT(NumLendingProducts = 0 AND NumDepositProducts =0)' # Apps that have at least one product
onlyZeroProductApps = '(NumLendingProducts = 0 AND NumDepositProducts =0)' #Apps that have no products
 
 
#Loan, Deposit and Approved Apps
loanApprovedApps = "AppStatus IN ('Loans Approved and Deposit Approved Queue','Loans Approved Queue')" # Apps that are Loan Only and Approved
depositApprovedApps = "AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','Approved Pending Microdeposits','BPM Submitted','Completed','Deposit Approved Queue','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Opened','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks')" # Apps that are Deposit Only and Approved  
mixedApprovedApps = "AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','Approved Pending Microdeposits','BPM Submitted','Completed','Deposit Approved Queue','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','Opened','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks')" # Apps that are Mixed Applications and Approved
approvedApps = "AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','Approved Pending Microdeposits','BPM Submitted','Completed','Deposit Approved Queue','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','Opened','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks')" # Apps that are approved and completed
##############################'Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','Approved Pending Microdeposits','BPM Submitted','Completed','Deposit Approved Queue','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','Opened','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks'
approvedAppsForBPMandCRIF = "AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','Approved Pending Microdeposits','BPM Submitted','Completed','Deposit Approved Queue','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','Opened','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks','LOS Submitted')"
submittedApps = "AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','Approved Pending Microdeposits','BPM Submitted','Completed','Decline Application','Decline Application Complete','Denied','Deposit Approved Queue','Deposit Submitted','Fiserv Failure and Retry','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','LOS Submitted','Onboarding Error','Onboarding Error Application Complete','Opened','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks')" # apps that are submitted
loanSubmittedApps = "AppStatus IN ('Loans Approved and Deposit Approved Queue','Loans Approved Queue','Decline Application','Decline Application Complete','Denied','LOS Submitted','Onboarding Error','Onboarding Error Application Complete','Review Application','Fiserv Failure and Retry')" # apps that are Loan Only and submitted
depositSubmittedApps = "AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved','Approved Pending Microdeposits','BPM Submitted','Completed','Decline Application','Decline Application Complete','Denied','Deposit Approved Queue','Deposit Submitted','Fiserv Failure and Retry','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Onboarding Error','Onboarding Error Application Complete','Opened','Post-Approval Approved Tasks','Post-Approval Customer Tasks','Post-BPM Entry Tasks')" # apps that are submitted
startedApps = 'AppStartDate IS NOT NULL' # Apps that are started
loanApps = 'NumLendingProducts > 0 AND NumDepositProducts = 0' # Apps that are Loan Only
depositApps = 'NumLendingproducts = 0 AND NumDepositProducts > 0' # Apps that are Deposit Only
mixedApps = 'NumLendingProducts >= 1 AND NumDepositProducts >= 1' # Apps that are Mixed Applications 
multiApps = '((NumDepositproducts > 1 AND NumLendingProducts = 0) OR (NumDepositProducts = 0 AND NumLendingProducts > 1))' # Apps that are Multi Product Aplications - updated as part of lending and deposit applications on 06/2025 - applies to the whole data set
multiLoanApps = 'NumLendingProducts > 1 AND NumDepositProducts = 0'
singleLoanApps = 'NumLendingProducts = 1 AND NumDepositProducts = 0'
multiDepositApps = 'NumLendingProducts = 0 AND NumDepositProducts > 1'
singleDepositApps = 'NumLendingProducts = 0 AND NumDepositProducts = 1'
singleApps = '((NumDepositProducts = 1 AND NumLendingProducts = 0) OR (NumDepositProducts = 0 AND NumLendingProducts = 1))' # Apps that are Single Product Applications - updated as part of lending and deposit applications on 06/2025 - applies to the whole data set
hasPromoCode = "PromoCodes IS NOT NULL AND PromoCodes != ''" # Apps that have a promo code

# Date filters 
dataFromYearStart = "AppStartDate >= DATEFROMPARTS(YEAR(CURRENT_TIMESTAMP),1,1) AND AppStartDate <= CURRENT_TIMESTAMP" # data from the start of the year to current date 
currentMonth = "AppStartDate >= DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()) AND AppStartDate < DATEADD(MONTH, 1, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from the current month
lastMonth = "AppStartDate >= DATEADD(MONTH, -1, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())" # data from the last month
twoMonthsAgo = "AppStartDate >= DATEADD(MONTH, -2, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -1, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from two months ago
threeMonthsAgo = "AppStartDate >= DATEADD(MONTH, -3, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -2, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from three months ago
fourMonthsAgo = "AppStartDate >= DATEADD(MONTH, -4, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -3, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from four months ago
fiveMonthsAgo = "AppStartDate >= DATEADD(MONTH, -5, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -4, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from five months ago
sixMonthsAgo = "AppStartDate >= DATEADD(MONTH, -6, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -5, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from six months ago
sevenMonthsAgo = "AppStartDate >= DATEADD(MONTH, -7, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -6, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from seven months ago
eightMonthsAgo = "AppStartDate >= DATEADD(MONTH, -8, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -7, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from eight months ago
nineMonthsAgo = "AppStartDate >= DATEADD(MONTH, -9, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -8, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from nine months ago
tenMonthsAgo = "AppStartDate >= DATEADD(MONTH, -10, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -9, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from ten months ago
elevenMonthsAgo = "AppStartDate >= DATEADD(MONTH, -11, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -10, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from eleven months ago
twelveMonthsAgo = "AppStartDate >= DATEADD(MONTH, -12, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE())) AND AppStartDate < DATEADD(MONTH, -11, DATEADD(DAY, 1 - DAY(GETDATE()), GETDATE()))" # data from eleven months ago


currentQuarter = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP),0) AND AppStartDate < DATEADD(QUARTER,1,DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP),0))" # data from the current quarter
lastQuarter = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-1,0) AND AppStartDate < DATEADD (QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP),0)" # data from the last quarter
lastBeforeQuarter = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-2,0) AND AppStartDate < DATEADD (QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-1,0)" # data from the last before quarter
twoQuartersAgo = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-3,0) AND AppStartDate < DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-2,0)" # data from two quarters ago
dataWorthFourQuarters = "AppStartDate >= DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP)-3, 0) AND AppStartDate < DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP)+1, 0)" # data from the current and previous three quarters
dataFromJanToPreviousMonth = "AppStartDate >= DATEFROMPARTS(YEAR(GETDATE()), 1, 1) AND AppStartDate < DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE())+1, 1)"
previousQuarter = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-1,0) AND AppStartDate < DATEADD (QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP),0)" # data from the last quarter
quarter1BeforeLast = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-2,0) AND AppStartDate < DATEADD (QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-1,0)" # data from the last before quarter
quarter2BeforeLast = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-3,0) AND AppStartDate < DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-2,0)" # data from two quarters ago
quarter3BeforeLast = "AppStartDate >= DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-4,0) AND AppStartDate < DATEADD(QUARTER,DATEDIFF(QUARTER,0,CURRENT_TIMESTAMP)-2,0)" # data from two quarters ago
dataWorthFourQuarters = "AppStartDate >= DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP)-5, 0) AND AppStartDate < DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP)+1, 0)" # data from the current and previous three quarters
dataWorthPastFourCompleteQuarters = "AppStartDate >= DATEADD(QUARTER, DATEDIFF(QUARTER, 0, GETDATE()) - 4, 0) AND AppStartDate < DATEADD(QUARTER, DATEDIFF(QUARTER, 0, GETDATE()), 0)" # data from the past four completed quarters
monthsFromJanToPreviousMonth = "DATEDIFF(MONTH, DATEFROMPARTS(YEAR(GETDATE()), 1, 1), EOMONTH(GETDATE(), -1)) + 1" # the number of months from Jan to previous month in current year 
monthsSinceYearStart = "DATEDIFF(MONTH, DATEFROMPARTS(YEAR(GETDATE()), 1, 1), GETDATE()) + 1" # the number of months from the start of the year to the current date
similarQuarterLastYear = "AppStartDate >= CASE WHEN CURRENT_TIMESTAMP < DATEADD(QUARTER, 1, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) THEN DATEADD(QUARTER, -5, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) ELSE DATEADD(QUARTER, -4, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) END AND AppStartDate < CASE WHEN CURRENT_TIMESTAMP < DATEADD(QUARTER, 1, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) THEN DATEADD(QUARTER, -4, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) ELSE DATEADD(QUARTER, -3, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) END"# data from the similar quarter from last year
latestCompletedQuarter = "AppStartDate >= CASE WHEN CURRENT_TIMESTAMP < DATEADD(QUARTER, 1, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) THEN DATEADD(QUARTER, -1, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) ELSE DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0) END AND AppStartDate < CASE WHEN CURRENT_TIMESTAMP < DATEADD(QUARTER, 1, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) THEN DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0) ELSE DATEADD(QUARTER, 1, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CURRENT_TIMESTAMP), 0)) END" #data from the latest completed quarter"

#Cross Sell Presented, Accepted and acceptance rate

crossSellPresented = "CrossSellProducts IS NOT NULL AND CrossSellProducts != ''"
crossSellAccepted = "CrossSellProducts IS NOT NULL AND CrossSellProducts != '' AND Opted = 'Y'"
crossSellAcceptanceRateColumn = ''' CAST(
                                        SUM(CASE WHEN Opted = 'Y' THEN 1 ELSE 0 END) * 100.0
                                        / NULLIF(COUNT(*), 0)
                                        AS DECIMAL(10, 4)
                                    ) AS data
                                '''

#DDS Data
ddsFilter = "DDSStatus IS NOT NULL AND DDSStatus != ''"
# if AppStartDate < 2026-01-01 count of successful switches 
DDS_BACKFILL_SuccessfulSwitch = "DDSTranAmount IS NOT NULL AND DDSTranAmount !=0"
DDS_SUCCESSFUL = "DDSStatus IN ('FINISHED') AND "+ ddsFilter
DDS_FAILED = "DDSStatus IN ('ABANDONED', 'FAILED') AND "+ ddsFilter
DDSDescriptionFilter = "(Description1 like 'First National B TRANSFER%' OR Ach_Company_Id = '043318092')"

# Payment Switch 
paymentSwitchFilter = "PaymentSwitchStatus IS NOT NULL AND PaymentSwitchStatus != ''"
paymentSwitchStarted = "PaymentSwitchStatus IN ('Started from eCA') AND "+ paymentSwitchFilter

appStatusforDashboard = [
    "Deposit Approved Queue",
    "Deposit Submitted",
    "Loans Approved and Deposit Approved Queue",
    "Loans Approved Queue",
    "Post-Approval Customer Tasks",
    "Post-BPM Entry Tasks",
    "Fiserv Failure and Retry",
    "Onboarding Error",
    "Onboarding Error Application Complete",
    "Review Application",
    "NULL",
    "Abandoned",
    "Abandoned:existing_customer_verify_phone",
    "Abandoned:funding",
    "Abandoned:getting_started",
    "Abandoned:id_and_citizenship",
    "Abandoned:loading",
    "Abandoned:personal_information",
    "Abandoned:product_info_008_e5aa6d27-e609-4073-8bc9-6b4f749a9552",
    "Abandoned:product_info_23602_cdc31647-22d3-409e-88e5-cb42a60bb4d3",
    "Abandoned:prove_waiting",
    "Abandoned:residence",
    "Abandoned:vouched_transition",
    "Approved Pending Microdeposits",
    "Post-Approval Approved Tasks",
    "Decline Application",
    "Decline Application Complete",
    "Denied",
    "Expired",
    "Pending",
    "Saved",
    "Address Add",
    "Cancel Endpoint",
    "Completed",
    "Opened",
    "Start",
    "Started",
    "Unknown",
    "Approve Application",
    "Approve Application Complete",
    "Approve Application Endpoint",
    "Approved",
    "BPM Submitted",
    "Fiserv Failure and Retry Application Complete",
    "Fiserv Failure and Retry Application Endpoint",
]
# eCA Tracking Code filter 
isBusinessTxn = "eCATrackingCode like 'B-%'" # Business Transactions
isConsumerTxn = "eCATrackingCode like 'C-%'" # Consumer Transactions
countColumn = "COUNT(DISTINCT(ecaTrackingCode)) as data" # Count Column for SQL Queries
sumOfProducts = "Sum(NumLendingProducts+NumDepositProducts) as data" # sum of Products
def sumColumn(col_name):
    return f"SUM({col_name}) as data" # Sum Column for SQL Queries



APP_PROD_SUB_HEADERS = [
    "",
    "Apps      ",
    "Prods     ",
    "Apps      ",
    "Prods     ",
    "Apps     /     Prods",

]

def CorBFilter(fill):
    if fill.lower().startswith("c"):
        return "eCATrackingCode LIKE 'C-%'"
    elif fill.lower().startswith("b"):
        return "eCATrackingCode LIKE 'B-%'"
    elif fill == "All":
        return "eCATrackingCode LIKE '%'"
    else:
        return "eCATrackingCode LIKE '%'"

def get_date_filter(start_date, end_date, column="AppStartDate"):    
    return f" {column} IS NOT NULL AND {column} >= '{start_date}' AND {column} <= '{end_date}' "

def bot_filter(primary_name_having_count_less_than = 25):
    return f"PrimaryName IS NOT NULL AND PrimaryName != '' AND PrimaryName != 'TlVMTA==' AND PrimaryName IN (SELECT PrimaryName FROM [DigitalReport].[dbo].[Transactions] GROUP BY PrimaryName HAVING COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) <= {primary_name_having_count_less_than})"

def application_type_filter(typeSelected):
    if typeSelected not in ALL_APPLICATION_TYPES:
        return ""
    return f"Application_Type = '{typeSelected}'"




'''
____________________________________________________________________________________________________________________________________________________________________________________________
                                STATIC LISTS
____________________________________________________________________________________________________________________________________________________________________________________________
'''


LIST_OF_CHARTS = [
    # Todo - Add more charts as needed
    "Branch Originated Reports",
    "Application Volume By Product (All Started Apps) Pie",
    "Application Volume By Product (All Started Apps) Pie Table",
    "Lending And Deposit Reports",
    "Abandonment Report",
    "Funding Type Report"
    ]

ALL_APP_STATUS = [
    "Deposit Approved Queue",
    "Deposit Submitted",
    "Loans Approved and Deposit Approved Queue",
    "Loans Approved Queue",
    "Post-Approval Customer Tasks",
    "Post-BPM Entry Tasks",
    "Fiserv Failure and Retry",
    "Onboarding Error",
    "Onboarding Error Application Complete",
    "Review Application",
    "NULL",
    "Abandoned",
    "Abandoned:existing_customer_verify_phone",
    "Abandoned:funding",
    "Abandoned:getting_started",
    "Abandoned:id_and_citizenship",
    "Abandoned:loading",
    "Abandoned:personal_information",
    "Abandoned:product_info_008_e5aa6d27-e609-4073-8bc9-6b4f749a9552",
    "Abandoned:product_info_23602_cdc31647-22d3-409e-88e5-cb42a60bb4d3",
    "Abandoned:prove_waiting",
    "Abandoned:residence",
    "Abandoned:vouched_transition",
    "Approved Pending Microdeposits",
    "Post-Approval Approved Tasks",
    "LOS Submitted",
    "Decline Application",
    "Decline Application Complete",
    "Denied",
    "Expired",
    "Pending",
    "Saved",
    "Address Add",
    "Cancel Endpoint",
    "Completed",
    "Opened",
    "Start",
    "Started",
    "Unknown",
    "Approve Application",
    "Approve Application Complete",
    "Approve Application Endpoint",
    "Approved",
    "BPM Submitted",
    "Fiserv Failure and Retry Application Complete",
    "Fiserv Failure and Retry Application Endpoint",
]

PRIMARY_NAME_IGNORE = [ # Ignore these names.
            "test testing",
            "testing test",
            "tester tester",
            "Joel Geisel",
            "cindy Hoffman",
            "Sophia Trentini",
            "Steven Ken",
            "carrie Stabile",
            "Christian Uhler",
            "Michael Delucia",
            "Luke Masters"
        ]
# Convert all names to lower case
PRIMARY_NAME_IGNORE = [name.lower() for name in PRIMARY_NAME_IGNORE]
# Split names and create combination of first name and last name
for first_name in [firstName.split()[0] for firstName in PRIMARY_NAME_IGNORE]:
    for last_name in [lastName.split()[1] for lastName in PRIMARY_NAME_IGNORE]:
        PRIMARY_NAME_IGNORE.append(f"{first_name} {last_name}")
        PRIMARY_NAME_IGNORE.append(f"{last_name} {first_name}")
# Remove duplicates
PRIMARY_NAME_IGNORE = list(set(PRIMARY_NAME_IGNORE))  + ["test"]

ALL_PRODUCT_SET_ID = [  
("001","Penguins® Cash Back Credit Card"),
("002","FNB SmartCash℠ Credit Card"),
("003","FNB SmartRate℠ Credit Card"),
("004","FNB SmartRewards℠ Credit Card"),
("005","Automobile Loan"),
("006","Recreational Vehicle Loan"),
("007","Boat/Yacht Loan"),
("008","Secured Installment Loan"),
("009","Unsecured Installment Loan"),
("010","Home Equity Line of Credit"),
("011","Home Equity Installment Loan"),
("012","Secured Line of Credit"),
("013","Unsecured Line of Credit"),
("014","Physicians Education Refinance Loan - Fixed Rate"),
("015","Home Equity Line of Credit Plus"),
("016","Home Equity Installment Loan Plus"),
("101","Business Credit Card"),
("102","Asset Secured Term"),
("103","Equipment Term"),
("104","Vehicle Term"),
("105","Asset Secured Line of Credit"),
("106","Working Capital Lines of Credit"),
("107","Real Estate Term"),
("108","Real Estate Line of Credit"),
("109","Unsecured Term"),
("110","Unsecured Line of Credit"),
("10115","Compak Business Checking"),
("10347","Flex CD"),
("20601","Business First Checking"),
("20903","Free Small Business Checking"),
("20904","Small Business Financial Solutions"),
("21102","Business Interest Checking"),
("21201","FirstRate Business Money Market"),
("21801","Nonprofit Interest Checking"),
("21901","Nonprofit Checking"),
("22221","FirstRate Money Market"),
("22232","FirstRate Money Market Special"),
("23003","Workplace Banking Solutions"),
("23303","FNB Employee Checking"),
("23602","Lifestyle Checking"),
("23901","Freestyle Checking"),
("24001","FNB-U Student Checking"),
("24201","Premierstyle Checking"),
("24301","eStyle Account"),
("24501","eStyle Plus Account"),
("28401","Health Savings - Individual"),
("28402","Health Savings - Family"),
("28403","Health Savings Employee - Individual"),
("28404","Health Savings Employee - Family"),
("31121","FirstRate Savings"),
("34601","Savers Goal CD"),
("45401","Certificate of Deposit - 3-Month Term"),
("45402","Special Certificate of Deposit - 5-Month Term"),
("45801","Certificate of Deposit - 6-Month Term"),
("45804","Special Certificate of Deposit - 7-Month Term"),
("46201","Certificate of Deposit - 12-Month Term"),
("46202","Special Certificate of Deposit - 13-Month Term"),
("46601","Certificate of Deposit - 18-Month Term"),
("46602","Special Certificate of Deposit - 19-Month Term"),
("47001","Certificate of Deposit - 24-Month Term"),
("47003","Special Certificate of Deposit - 25-Month Term"),
("47008","Special Certificate of Deposit - 35-Month Term"),
("47401","Certificate of Deposit - 36-Month Term"),
("47801","Certificate of Deposit - 48-Month Term"),
("47802","Special Certificate of Deposit - 52-Month Term"),
("48201","Certificate of Deposit - 60-Month Term"),
("48203","Special Certificate of Deposit - 61-Month Term"),
("81121","FirstRate Business Savings"),
("85401","Certificate of Deposit - 3-Month Term"),
("85402","Special Certificate of Deposit - 5-Month Term"),
("85801","Certificate of Deposit - 6-Month Term"),
("85804","Special Certificate of Deposit - 7-Month Term"),
("86201","Certificate of Deposit - 12-Month Term"),
("86202","Special Certificate of Deposit - 13-Month Term"),
("86601","Certificate of Deposit - 18-Month Term"),
("86602","Special Certificate of Deposit - 19-Month Term"),
("87001","Certificate of Deposit - 24-Month Term"),
("87003","Special Certificate of Deposit - 25-Month Term"),
("87008","Special Certificate of Deposit - 35-Month Term"),
("87401","Certificate of Deposit - 36-Month Term"),
("87801","Certificate of Deposit - 48-Month Term"),
("87802","Special Certificate of Deposit - 52-Month Term"),
("88201","Certificate of Deposit - 60-Month Term"),
("88203","Special Certificate of Deposit - 61-Month Term"),

]

ALL_BRANCH_ID = [
    ("2872","Carbondale"),
    ("2867","Clarks Summit"),
    ("2869","Dickson City"),
    ("2870","Forest City"),
    ("2862","Montrose"),
    ("2874","Scranton"),
    ("2864","Tunkhannock"),
    ("2089","Arsenal Road"),
    ("2852","Camp Hill"),
    ("2889","Carlisle"),
    ("2887","Hampden Center"),
    ("2091","Mount Zion Road"),
    ("2088","Queen Street"),
    ("2090","Red Lion"),
    ("2888","Simpson Ferry"),
    ("2087","York Crossing"),
    ("2897","Derry Street"),
    ("2894","Hummelstown"),
    ("2879","Linglestown Road"),
    ("2893","Mountain Road"),
    ("2895","North Second Street"),
    ("2898","Progress Avenue"),
    ("2093","East Cumberland"),
    ("2099","Exeter"),
    ("2849","Lancaster Avenue"),
    ("2882","Muhlenberg"),
    ("2092","Palmyra"),
    ("2881","State Hill Road"),
    ("2098","Lincoln Highway"),
    ("2096","Lititz Pike"),
    ("2097","Manheim Pike"),
    ("2095","Rohrerstown Road"),
    ("2851","Hazleton"),
    ("2857","McAdoo"),
    ("2034","Mountain Top"),
    ("2855","Shenandoah"),
    ("2876","Tannersville"),
    ("2037","Wilkes-Barre Arena"),
    ("2423","Cresson"),
    ("2405","East Hills"),
    ("2420","Ebensburg"),
    ("2421","Northern Cambria"),
    ("2427","Rt. 22"),
    ("2401","West End"),
    ("2046","Allen Street"),
    ("2045","East College Avenue"),
    ("2047","Bellefonte"),
    ("2058","Lemont"),
    ("2029","Lewisburg Downtown"),
    ("2028","Lewisburg Plaza (drive-thru)"),
    ("2030","Lock Haven"),
    ("2060","Loganton"),
    ("2041","Maynard St."),
    ("2025","Middleburg"),
    ("2071","Hollidaysburg"),
    ("2064","Lewistown"),
    ("2072","Martinsburg"),
    ("2056","Millheim"),
    ("2075","Wehnwood"),
    ("2602","Bedford"),
    ("2603","North Richard Street (No Goals)"),
    ("2074","Greenwood"),
    ("2051","Hills Plaza"),
    ("2082","Huntingdon"),
    ("2050","North Atherton"),
    ("2426","Plank Road"),
    ("2081","Tyrone"),
    ("2422","Clymer"),
    ("2610","Meyersdale"),
    ("2067","Reedsville"),
    ("2021","Selinsgrove"),
    ("2618","Somerset East"),
    ("2032","Shamokin"),
    ("2024","Sunbury"),
    ("2070","Thompsontown"),
    ("2026","Watsontown"),
    ("2404","Westmont"),
    ("2419","Main Street"),
    ("2831","Fairlawn"),
    ("2815","Lakewood-Clifton"),
    ("2828","Public Square"),
    ("2821","Medina"),
    ("2818","Mayfield Heights"),
    ("2814","Northfield Road"),
    ("2823","Solon"),
    ("2236","Butler Commons"),
    ("2232","Laurel"),
    ("2215","New Castle"),
    ("2216","Neshannock"),
    ("2230","Portersville"),
    ("2229","Slippery Rock-Plaza"),
    ("2810","Chardon"),
    ("2829","Hudson"),
    ("2822","Twinsburg"),
    ("2820","Bainbridge"),
    ("2813","LaPlace (Beachwood)"),
    ("2819","Macedonia"),
    ("2812","Mentor"),
    ("2832","University Circle"),
    ("2117","Franklin"),
    ("2110","Meadville"),
    ("2101","State Street"),
    ("2102","Summit"),
    ("2111","Vernon Twp."),
    ("2103","West 8th Street"),
    ("2824","Avon"),
    ("2816","North Royalton"),
    ("2825","Strongsville"),
    ("2830","Westlake"),
    ("2704","Austintown"),
    ("2703","Boardman"),
    ("2213","Brookfield"),
    ("2709","Canfield"),
    ("2702","Hubbard"),
    ("2706","Liberty"),
    ("2701","Federal Plaza"),
    ("2105","Airport"),
    ("2109","Corry"),
    ("2107","Girard"),
    ("2106","Grandview"),
    ("2202","Greenville"),
    ("2207","Hadley Road"),
    ("2201","Hermitage Square"),
    ("2210","Hickory Plaza"),
    ("2233","New Wilmington"),
    ("2120","North East Main"),
    ("2121","Harbor Creek (No goal/production)"),
    ("2211","Pine Grove Square"),
    ("2205","Sharon"),
    ("2206","Sharpsville"),
    ("2204","West Middlesex"),
    ("2772","Abingdon"),
    ("2787","Aberdeen"),
    ("2762","Dundalk"),
    ("2792","Rising Sun"),
    ("2771","White Marsh"),
    ("2789","Centennial"),
    ("2780","Columbia"),
    ("2767","Owings Mills"),
    ("2770","Timonium"),
    ("2783","Towson"),  
    ("2778","Bethesda"),
    ("2777","Gaithersburg"),
    ("2776","Germantown"),
    ("2781","Rockville"),
    ("2785","Tyson's Corner"),
    ("2782","Wisconsin Avenue"),
    ("2788","Canton"),
    ("2761","Catonsville"),
    ("2759","Lombard"),
    ("2793","Remington"),
    ("2758","Waugh Chapel"),
    ("2773","Bel Air"),
    ("2775","Hickory"),
    ("2791","Parkville"),
    ("2768","Perry Hall"),
    ("2769","Sparks"),
    ("2796","Alexandria"),
    ("2795","Arlington"),
    ("2797","National Landing"),
    ("2784","Nineteenth Street (DC)"),
    ("2786","Reston"),
    ("2750","Bestgate"),
    ("2751","Edgewater"),
    ("2790","Glen Burnie"),
    ("2753","Kent Island"),
    ("2754","Severna Park"),
    ("2748","West Broad"),
    ("2749","Willow Place"),
    ("1088","Ellis Road"),
    ("1066","Page Road"),
    ("1057","Holly Springs"),
    ("1062","Raleigh - Five Points"),
    ("1059","Raleigh Stonehenge "),
    ("1073","Roxboro"),
    ("1070","Youngsville"),
    ("1025","Burgaw"),
    ("1026","Calabash"),
    ("1032","Shallotte"),
    ("1034","Southport"),
    ("1071","Henderson"),
    ("1058","Independence Park"),
    ("1069","Oxford"),
    ("1065","Westgate"),
    ("1050","Apex"),
    ("1051","Cary Kildaire"),
    ("1054","Fuquay-Varina"),
    ("1060","Raleigh Downtown"),
    ("1064","Sanford"),
    ("1052","Cary Preston"),
    ("1053","Clayton"),
    ("1055","Garner"),
    ("1056","Hillsborough"),
    ("1061","Raleigh Falls of Neuse"),
    ("1005","Greenville Red Banks"),
    ("1006","Greenville UMC"),
    ("1036","Kinston"),
    ("1037","New Bern"),
    ("1014","Washington"),
    ("1015","Williamston"),
    ("1027","College Road"),
    ("1030","Jacksonville"),
    ("1028","Wilmington Eastwood"),
    ("1035","Wilmington Independence"),
    ("1000","Avon"),
    ("1007","Hatteras"),
    ("1250","Creedmoor"),
    ("1029","Fayetteville"),
    ("1067","Goldsboro"),
    ("1008","Hertford"),
    ("1009","Kitty Hawk"),
    ("1068","La Grange"),
    ("1072","Louisburg"),
    ("1010","Manteo"),
    ("1011","Nags Head"),
    ("1012","Ocracoke"),
    ("1033","Southern Pines"),
    ("1013","Swan Quarter"),
    ("1102","Arcadia"),
    ("1103","Clemmons"),
    ("1100","Kernersville"),
    ("1108","Stratford Road"),
    ("1075","Battleground"),
    ("1076","Burlington Main"),
    ("1087","Greensboro Downtown"),
    ("1084","Randleman Road"),
    ("1151","Cornelius"),
    ("1153","Huntersville"),
    ("1159","Mountain Island"),
    ("1161","Charlotte South Park"),
    ("1169","Charlotte Uptown"),
    ("1125","Blowing Rock Road"),
    ("1133","Mt. Jefferson"),
    ("1134","North Elkin"),
    ("1135","North Wilkesboro"),
    ("1138","Wilkesboro"),
    ("1104","Lexington Main"),
    ("1111","Uptown Express (Drive thru)"),
    ("1105","Lexington South"),
    ("1109","Thomasville"),
    ("1113","Welcome"),
    ("1154","Indian Trail"),
    ("1157","Mint Hill"),
    ("1158","Monroe Main"),
    ("1166","Rea Farms"),
    ("1162","Tega Cay"),
    ("1142","Biltmore Park"),
    ("1152","Gaffney"),
    ("1204","Greenville Downtown"),
    ("1201","Woodruff "),
    ("1165","Coleman Blvd."),
    ("1168","Freshfields at Kiawah"),
    ("1164","Meeting Street"),
    ("1203","Summerville"),
    ("1170","East Town Market"),
    ("1078","Eden"),
    ("1080","Greensboro Hicone"),
    ("1081","High Point"),
    ("1131","Jonesville"),
    ("1082","King"),
    ("1083","Madison"),
    ("1136","Northcross"),
    ("1160","Plaza Drive"),
    ("1085","Reidsville Main"),
    ("1107","Salisbury"),
    ("1137","Statesville Main"),
    ("1114","Tyro"),
    ("1167","University Place"),
    ("1112","Wallburg"),
    ("1205","West Ashley (Opening 2026)"),
    ("1163","Williamson Road"),
    ("1139","Yadkinville"),
    ("2972","Bridgeville"),
    ("2918","Chartiers Valley"),
    ("2966","Greentree Road"),
    ("2959","Crafton"),
    ("2953","Kennedy Township"),
    ("2223","Moon Township "),
    ("2920","Robinson Twp."),
    ("2921","Sewickley"),
    ("2903","Duncan Manor "),
    ("2904","Hampton Twp."),
    ("2906","McKnight Road"),
    ("2901","North Allegheny"),
    ("2905","McCandless "),
    ("2985","Mt Nebo Road"),
    ("2964","Wexford"),
    ("2979","Wexford Flats"),
    ("2955","Aliquippa "),
    ("2218","Beaver "),
    ("2222","Chippewa  "),
    ("2911","Cranberry Twp."),
    ("2924","Follansbee"),
    ("2929","Hollywood Plaza"),
    ("2316","Seven Fields "),
    ("2917","Bethel Park Office"),
    ("2916","Brentwood Town Square"),
    ("2310","Carson Street"),
    ("2913","Castle Shannon"),
    ("2873","Mt. Lebanon"),
    ("2949","Village Square"),
    ("2914","West Mifflin"),
    ("2522","Circleville "),
    ("2521","Fort Allen "),
    ("2520","Stone House"),
    ("2506","Triangle Drive "),
    ("2504","Unity Township"),
    ("2977","East Liberty"),
    ("2975","Wilkinsburg"),
    ("2910","Fox Chapel"),
    ("2938","Millvale"),
    ("2936","Monroeville"),
    ("2952","Oakmont"),
    ("2932","Brownsville"),
    ("2974","Canonsburg"),
    ("2512","Cherry Tree"),
    ("2930","Masontown"),
    ("2511","Uniontown"),
    ("2513","Peters Twp."),
    ("2518","Waynesburg"),
    ("2971","Hill District"),
    ("2960","Grant Street"),
    ("2912","One Oliver Plaza"),
    ("2940","Oakland"),
    ("2909","Pittsburgh Northside"),
    ("2908","Allegheny Professional"),
    ("2922","Shadyside"),
    ("2943","Squirrel Hill"),
    ("2976","Homestead"),
    ("2970","Bloomfield"),
    ("2946","Caste Village"),
    ("2615","Confluence"),
    ("2517","Dry Tavern"),
    ("2225","Eighteenth St.  "),
    ("2962","Fourth & Wood"),
    ("2617","Indian Head"),
    ("2309","Kittanning"),
    ("2505","Ligonier "),
    ("2980","Murrysville"),
    ("2305","Natrona Heights "),
    ("2302","New Kensington"),
    ("2524","North Main"),
    ("2307","North Washington/Avonmore"),
    ("2219","Northern Lights "),
    ("2944","Riverview"),
    ("2306","Sarver "),
    ("2508","South Greensburg "),
    ("2923","Wellsburg"),
    ("2907","West View "),
    ("2925","Wintersville"),
    ("2983",""),
    ("2963",""),
    ("2052",""),
    ("2237",""),
    ("2525",""),
    ("1115",""),
    ("2965",""),

]

ALL_APPLICATION_TYPES = [
    "Online",
    "Banker Assisted"
]

ALL_PROMOCODES = [
    "AUTO60024: Get $600 for opening an account",
    "AUTO60025: Get $600 for opening an account",
    "DE60024AR: Bringing better banking to Arlington and $600 to your wallet",
    "DE60024AX: Bringing better banking to Alexandria and $600 to your wallet",
    "DE60024GV: Better banking begins with $600",
    "DE60024NL: Better banking begins with $600",
    "DE60024WB: Better banking begins with $600",
    "DM6002403: Better banking begins with $600",
    "DM6002405: Better banking begins with $600",
    "DM6002407: New Customers Earn up to $600",
    "DM6002409: Better banking begins with $600",
    "DM6002502: Better banking begins with $600",
    "DM7002504: Earn up to $700 by applying for new savings and checking accounts!",
    "EM60024B: New Customers Earn up to $600",
    "EMAIL60024: Open a new checking account. Earn $600",
    "EMAIL60025: Open a new checking account. Earn $600",
    "FNBU2025: Get $100 for opening an account",
    "FNBUSRU2025: Get $100 for opening an account",
    "FNBUSRU24: Get $100 for opening an account",
    "MMA2308: BETTER RATE. BETTER HURRY.",
    "MORT50024: A unique checking offer for mortgage customers",
    "MORT50025: A Unique checking offer for mortgage customers.",
    "PENS: Penguins\u00ac\u00c6 Power Play Package",
    "PENS: Penguins\u00ae Power Play Package",
    "SAV2002504: Start Saving with FNB",
    "SE6002403: Better banking begins with $600",
    "SE6002405: Better banking begins with $600",
    "SE6002407: New Customers Earn up to $600",
    "SE6002409: Better banking begins with $600",
    "WFC150DD: Earn up to $150 new customer cash bonus"
]

TABLE_STRUCTURE = {
    "tId": "INT PRIMARY KEY NOT NULL",
    "eCAID": "VARCHAR(50) NOT NULL",
    "eCATrackingCode": "VARCHAR(50) NOT NULL",
    "CustomerID": "NVARCHAR(128) NOT NULL",
    "AppStartDate": "DATETIME NULL",
    "AppSubmitDate": "DATETIME NULL",
    "AppUpdateDate": "DATETIME NULL",
    "AppStatus": "VARCHAR(50) NULL",
    "DeclineReason": "NVARCHAR(MAX) NULL",
    "PrimaryName": "VARCHAR(50) NULL",
    "PrimarySSN": "NVARCHAR(100) NOT NULL",
    "NewCustomer": "VARCHAR(50) NULL",
    "NumCoApplicant": "INT NULL",
    "ProductSetId1": "NVARCHAR(MAX) NULL",
    "NumDepositProducts": "INT NULL",
    "NumLendingProducts": "INT NULL",
    "FundingMethod": "VARCHAR(50) NULL",
    "TotalFundingAmount": "FLOAT NULL",
    "UnderWriterStatus1": "VARCHAR(50) NULL",
    "UnderWriterStatus2": "VARCHAR(50) NULL",
    "BranchID": "VARCHAR(15) NULL",
    "BranchContactPerson": "VARCHAR(100) NULL",
    "BranchContactPhone": "VARCHAR(20) NULL",
    "Promotions": "NVARCHAR(MAX) NULL",
    "PromoCodes": "NVARCHAR(MAX) NULL",
    "CrossSellProducts": "NVARCHAR(MAX) NULL",
    "Opted": "VARCHAR(10) NULL",
    "APPLICATION_TYPE": "VARCHAR(100) NULL",
    "EmployeeResponsibilityCode": "NVARCHAR(MAX) NULL",
    "NMLS_Id": "NVARCHAR(MAX) NULL",
    "DataSource": "VARCHAR(250) NULL",
    "DDSStatus": "NVARCHAR(MAX) NULL",
    "DDSAccountName": "NVARCHAR(MAX) NULL",
    "DDSAccountType": "NVARCHAR(MAX) NULL",
    "DDSAccountLast4": "NVARCHAR(MAX) NULL",
    "AccountNumber": "NVARCHAR(MAX) NULL",
    "EDW_APPID": "NVARCHAR(MAX) NULL",
    "CurrentPage": "NVARCHAR(MAX) NULL",
    "DDSTranAmount": "FLOAT NULL",
    "PaymentSwitchMethod" : "NVARCHAR(MAX) NULL",
    "PaymentSwitchStatus" : "NVARCHAR(MAX) NULL",
    "DepositAcctStatus": "NVARCHAR(MAX) NULL",
    "LoanAcctStatus": "NVARCHAR(MAX) NULL",
    "Employer": "NVARCHAR(MAX) NULL",
    "PayrollProvider": "NVARCHAR(MAX) NULL",
}


ALL_COLUMNS = list(TABLE_STRUCTURE.keys())

CSV_TO_SQL_COLUMNS = {
            "eCA ID": "eCAID",
            "eCA Tracking Code": "eCATrackingCode",
            "CustomerID": "CustomerID",
            "App Start Date": "AppStartDate",
            "App Submit Date": "AppSubmitDate",
            "App Update Date": "AppUpdateDate",
            "App Status": "AppStatus",
            "Decline Reason": "DeclineReason",
            "Primary Name": "PrimaryName",
            "Primary SSN": "PrimarySSN",
            "New/Existing": "NewCustomer",
            "Number of Co-Applicants": "NumCoApplicant",
            "Product List": "ProductSetId",
            "Number of Deposit Products": "NumDepositProducts",
            "Number of Lending Products": "NumLendingProducts",
            "Funding Type": "FundingMethod",
            "Total Funding Amount": "TotalFundingAmount",
            # "Product Funding Amount": "ProductFundingAmount",
            "Promo Codes": "PromoCodes",
            "Cross Sell Product": "CrossSellProducts",""
            "Opt In": "Opted",
            "Application Type" : "APPLICATION_TYPE",
            "Branch Id": "BranchID",
            "Responsibility Code": "EmployeeResponsibilityCode",
            "NMLS Id": "NMLS_Id",
            "DataSource": "DataSource",
            "DDS Status":"DDSStatus",
            "DDS Account Name":"DDSAccountName",
            "DDS Account Type":"DDSAccountType",
            "DDS Account Last4":"DDSAccountLast4",
            "Product Account Number": "AccountNumber",
            "Payment Switch Status": "PaymentSwitchStatus",
            "Payment Switch Method": "PaymentSwitchMethod",
            "Employer": "Employer",
            "Payroll Provider":"PayrollProvider"
        }


PII_COLUMNS = [
    "PrimaryName",
    "PrimarySSN",
    "DDS Account Last4",
]

  
All_CHARTS = [
    "Application Volume By Product (All Started Apps) Pie - Year to Date",
    "Application Volume By Product (All Started Apps) Pie Table - Year to Date",
    "Application Volume By Product (All Started Apps) Line",
    "Application Volume By Product (All Started Apps) Line Table",
    "Application Volume By Product Quarterly (All Started Apps) Pie",
    "Application Volume By Product Quarterly (All Started Apps) Table",
    "Application Volume By Product Quarterly (All Started Apps) Line",
    "Application Volume By Product Current Quarter (All Started Apps) Pie",
    "Application Volume By Product Current Quarter (All Started Apps) Table",
    "Application Volume By Product (All Submitted Apps) Pie - Year to Date",
    "Application Volume By Product (All Submitted Apps) Pie Table - Year to Date",
    "Application Volume By Product (All Submitted Apps) Line",
    "Application Volume By Product (All Submitted Apps) Line Table",
    "Application Volume By Product Quarterly (All Submitted Apps) Pie",
    "Application Volume By Product Quarterly (All Submitted Apps) Table",
    "Application Volume By Product Quarterly (All Submitted Apps) Line",
    "Application Volume By Product Current Quarter (All Submitted Apps) Pie",
    "Application Volume By Product Current Quarter (All Submitted Apps) Table",
    "Application Volume By Product (All Opened Or Approved Apps) Pie - Year to Date",
    "Application Volume By Product (All Opened Or Approved Apps) Pie Table - Year to Date",
    "Application Volume By Product (All Opened Or Approved Apps) Line",
    "Application Volume By Product (All Opened Or Approved Apps) Line Table",
    "Application Volume By Product Quarterly (All Opened Or Approved Apps) Pie",
    "Application Volume By Product Quarterly (All Opened Or Approved Apps) Table",
    "Application Volume By Product Quarterly (All Opened Or Approved Apps) Line",
    "Application Volume By Product Current Quarter (All Approved Apps) Pie",
    "Application Volume By Product Current Quarter (All Approved Apps) Table",
    "Abandonment Report by Week Bar",
    "Abandonment Report by Month Pie",
    "Abandonment Report by Year Pie",
    "Abandonment Report by Types of Abandonment Pie",
    "Abandonment Report",
    "Zero Product Applications Bar",
    "Zero Product Applications Table",
    "Branch Originated Reports",
    "Business Deposit Reports",
    "Lending And Deposit Reports",
    "Funding Type Report",
    "Funding Type Report Line",
    "All Transactions", # Ommited
    "All Branch Ids",
    "Multi Products Product Set Id Table",
    "Multi Products Product Set Id Bar",
    "Multi Products Cross Sell Table",
    "Multi Products Cross Sell Bar",
    "Cross Sell Products Table",
    "Monthly In Branch Report",
    "Monthly Consumer Facing Report",
    "Monthly Business Deposits and Loans Report",
    "Declined Report Table",
    "Declined Report Line",
    "New vs Existing Customers",
    "New vs Existing Customers Table"
]


COMMON_EXPORT_COLUMNS = [
"AccountNumber",
"APPLICATION_TYPE",
"AppStartDate",
"AppStatus",
"BranchID",
"CrossSellProducts",
"DeclineReason",
"eCAID",
"eCATrackingCode",
"EDW_APPID",
"EmployeeResponsibilityCode",
"FundingMethod",
"NewCustomer",
"NMLS_Id",
"NumCoApplicant",
"NumDepositProducts",
"NumLendingProducts",
"Opted",
"PrimaryName",
"PrimarySSN",
"ProductSetId",
"PromoCodes",
"Promotions",
"TotalFundingAmount",
# "DepositAcctStatus",
# "LoanAcctStatus"
]



