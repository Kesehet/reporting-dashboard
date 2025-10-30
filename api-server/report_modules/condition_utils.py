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

APPROVED_APPS_FILTER = " AND AppStatus IN ( "+','.join([f'\'{app}\'' for app in APPROVED_APPS_STATUSES])+ ") "
SUBMITTED_APPS_FILTER = " AND AppStatus IN ( "+','.join([f'\'{app}\'' for app in SUBMITTED_APPS_STATUSES])+ ") "
SUBMITTED_FOR_LOAN_COMMITMENT_FILTER = "AND AppStatus IN ( "+','.join([f'\'{app}\'' for app in SUBMITTED_FOR_LOAN_COMMITMENT])+ ") "

table = "[DigitalReport].[dbo].[Transactions]" # Table name
TABLE_NAME = "[DigitalReport].[dbo].[Transactions]"



consumerTransaction = "eCATrackingCode like 'C-%'"
businessTransaction = "ecaTrackingCode like 'B-%'"



#lending and deposit control 

applicationsApprovedAwaitingEntry = " AppStatus IN ('Deposit Approved Queue','Deposit Submitted','Loans Approved and Deposit Approved Queue','Loans Approved Queue','Post-Approval Customer Tasks','Post-BPM Entry Tasks')"
applicationsApprovedFundingOngoing = " AppStatus IN ('Approved Pending Microdeposits','Post-Approval Approved Tasks')"
applicationsApprovedInUnderwriting = " AppStatus IN ('LOS Submitted')"
applicationsApprovedOnboarded = " AppStatus IN ('Approve Application','Approve Application Complete','Approve Application Endpoint','Approved	BPM Submitted','Fiserv Failure and Retry Application Complete','Fiserv Failure and Retry Application Endpoint')"
applicationsDeclined = " AppStatus IN ('Decline Application','Decline Application Complete','Denied')"
applicationsExpired = " AppStatus IN ('Expired')"
applicationsInProgressAbandoned = " AppStatus IN ('Abandoned','Abandoned:existing_customer_verify_phone','Abandoned:funding','Abandoned:getting_started','Abandoned:id_and_citizenship','Abandoned:loading','Abandoned:personal_information','Abandoned:product_info_008_e5aa6d27-e609-4073-8bc9-6b4f749a9552','Abandoned:product_info_23602_cdc31647-22d3-409e-88e5-cb42a60bb4d3','Abandoned:prove_waiting','Abandoned:residence','Abandoned:vouched_trans')"
applicationsInProgressSaved = " AppStatus IN ('Pending	Saved')"
applicationsInProgressStarted = " AppStatus IN ('Address Add','Cancel Endpoint','Completed','Opened','Start','Started')"
applicationsMissing = " AppStatus IN ('Unknown')"
applicationsSubmittedError = " AppStatus IN ('Fiserv Failure and Retry','Onboarding Error','Onboarding Error Application Complete')"
applicationsSubmittedUnderReview = " AppStatus IN ('Review Application')"

#Bot data
excludeBotData = "PrimaryName IS NOT NULL AND PrimaryName != '' AND PrimaryName != 'TlVMTA==' AND PrimaryName IN (SELECT PrimaryName FROM [DigitalReport].[dbo].[Transactions] GROUP BY PrimaryName HAVING COUNT(*) <= 25)" # Filter for Bot data- PrimaryName with less than 500 transactions
includeBotData = "PrimaryName IS NOT NULL AND PrimaryName != '' AND PrimaryName != 'TlVMTA==' AND PrimaryName NOT IN (SELECT PrimaryName FROM [DigitalReport].[dbo].[Transactions] GROUP BY PrimaryName HAVING COUNT(*) <= 25)" # Filter for Bot data - PrimaryName with more than 500 transactions

#Loan, Deposit and Approved Apps
loanApprovedApps = "AppStatus IN ('Loans Approved and Deposit Approved Queue','Loans Approved Queue')" # Apps that are Loan Only and Approved
depositApprovedApps = "AppStatus IN ('Approve Application Endpoint','Approve Application','Approve Application Complete','Approved','Approved Pending Microdeposits','BPM Submitted','Deposit Approved Queue','Post Approval Customer Tasks','Fiserv Failure and Retry Appliation Complete','Fiserv Failure and Retry Application Endpoint')" # Apps that are Deposit Only and Approved  
mixedApprovedApps = "AppStatus IN ('Approve Application Endpoint','Approve Application','Approve Application Complete','Approved','Approved Pending Microdeposits','BPM Submitted','Deposit Approved Queue','Post Approval Customer Tasks','Fiserv Failure and Retry Appliation Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','LOS Submitted')" # Apps that are Mixed Applications and Approved
approvedApps = "AppStatus IN ('Approve Application Endpoint','Approve Application','Approve Application Complete','Approved','Approved Pending Microdeposits','BPM Submitted','Deposit Approved Queue','Post Approval Customer Tasks','Fiserv Failure and Retry Appliation Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue')" # Apps that are approved and completed
approvedAppsForBPMandCRIF = "AppStatus IN ('Approve Application Endpoint','Approve Application','Approve Application Complete','Approved','Approved Pending Microdeposits','BPM Submitted','Deposit Approved Queue','Post Approval Customer Tasks','Fiserv Failure and Retry Appliation Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','LOS Submitted')"
submittedApps = "AppStatus IN ('Decline Application Complete','Fiserv Failure and Retry','Onboarding Error','Onboarding Error Application Complete','Review Application','Approve Application Endpoint','Approve Application','Approve Application Complete','Approved','Approved Pending Microdeposits','BPM Submitted','Deposit Approved Queue','Post Approval Customer Tasks','Fiserv Failure and Retry Appliation Complete','Fiserv Failure and Retry Application Endpoint','Loans Approved and Deposit Approved Queue','Loans Approved Queue','LOS Submitted')" # apps that are submitted
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

#Zero Product Applications 
excludeZeroProductApps = 'NOT(NumLendingProducts = 0 AND NumDepositProducts =0)' # Apps that have at least one product
onlyZeroProductApps = '(NumLendingProducts = 0 AND NumDepositProducts =0)' #Apps that have no products

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
dataFromJanToPreviousMonth = "AppStartDate >= DATEFROMPARTS(YEAR(GETDATE()), 1, 1) AND AppStartDate < DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)"
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
countColumn = "Count(*) as data" # Count Column for SQL Queries
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

def get_date_filter(start_date, end_date):    
    return f" AppStartdate IS NOT NULL AND AppStartDate >= '{start_date}' AND AppStartDate <= '{end_date}' "

def bot_filter(primary_name_having_count_less_than = 25):
    return f"PrimaryName IS NOT NULL AND PrimaryName != '' AND PrimaryName != 'TlVMTA==' AND PrimaryName IN (SELECT PrimaryName FROM [DigitalReport].[dbo].[Transactions] GROUP BY PrimaryName HAVING COUNT(*) <= {primary_name_having_count_less_than})"

def application_type_filter(typeSelected):
    if typeSelected not in ALL_APPLICATION_TYPES:
        print("Invalid Application Type Passed")
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
            "Michael Delucia"
        ]
# Convert all names to lower case
PRIMARY_NAME_IGNORE = [name.lower() for name in PRIMARY_NAME_IGNORE]
# Split names and create combination of first name and last name
for first_name in [firstName.split()[0] for firstName in PRIMARY_NAME_IGNORE]:
    for last_name in [lastName.split()[1] for lastName in PRIMARY_NAME_IGNORE]:
        PRIMARY_NAME_IGNORE.append(f"{first_name} {last_name}")
        PRIMARY_NAME_IGNORE.append(f"{last_name} {first_name}")
# Remove duplicates
PRIMARY_NAME_IGNORE = list(set(PRIMARY_NAME_IGNORE))

ALL_PRODUCT_SET_ID = [
("1","Penguins® Cash Back Credit Card"),
("2","FNB SmartCash℠ Credit Card"),
("3","FNB SmartRate℠ Credit Card"),
("4","FNB SmartRewards℠ Credit Card"),
("5","Automobile Loan"),
("6","Recreational Vehicle Loan"),
("7","Boat/Yacht Loan"),
("8","Secured Installment Loan"),
("9","Unsecured Installment Loan"),
("10","Home Equity Line of Credit"),
("11","Home Equity Installment Loan"),
("12","Secured Line of Credit"),
("13","Unsecured Line of Credit"),
("14","Physicians Education Refinance Loan - Fixed Rate"),
("15","Home Equity Line of Credit Plus"),
("16","Home Equity Installment Loan Plus"),    
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
("22261","WauBank High-Yield Savings"),
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
("46203","WauBank CD Special - 13-Month Term"),
("46601","Certificate of Deposit - 18-Month Term"),
("46602","Special Certificate of Deposit - 19-Month Term"),
("46603","WauBank CD Special - 19-Month Term"),
("47001","Certificate of Deposit - 24-Month Term"),
("47003","Special Certificate of Deposit - 25-Month Term"),
("47006","WauBank CD Special - 25-Month Term"),
("47007","WauBank CD Special - 35-Month Term"),
("47008","Special Certificate of Deposit - 35-Month Term"),
("47401","Certificate of Deposit - 36-Month Term"),
("47801","Certificate of Deposit - 48-Month Term"),
("47802","Special Certificate of Deposit - 52-Month Term"),
("47803","WauBank CD Special - 52-Month Term"),
("48201","Certificate of Deposit - 60-Month Term"),
("48203","Special Certificate of Deposit - 61-Month Term"),
("48205","WauBank CD Special - 61-Month Term"),
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
  "EDW_APPID": "INT NULL",
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
            "Product Account Number": "AccountNumber"
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
    "Monthly Business Deposits Report",
    "Declined Report Table",
    "Declined Report Line",
    "New vs Existing Customers",
    "New vs Existing Customers Table"
]






