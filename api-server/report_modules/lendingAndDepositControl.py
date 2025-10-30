from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *

def get_lending_and_deposit_reports(start_date, end_date):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    intervals = get_list_of_months_between(start_date, end_date)

    CONSUMER_LOAN_APPLICATIONS_HEADERS, CONSUMER_LOAN_APPLICATIONS_ROWS = generate_report(
        intervals, 
        [
            #----------------------------------------------------------------------CONSUMER LOAN APPLICATIONS---------------------------------------------------------------------------------------------------------------------------------------,
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressAbandoned}",
                "label": "Applications In Progress (Abandoned)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsSubmittedError}",
                "label": "Applications Submitted (Error)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsDeclined}",
                "label":"Applications Declined",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsExpired}",
                "label":"Applications Expired",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "label":"Total Unsuccessful Applications",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressStarted}", 
                "label":"Applications In Progress (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressSaved}",
                "label":"Applications In Progress (Saved)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsSubmittedUnderReview}", 
                "label":"Applications Submitted(Under Review)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedAwaitingEntry}",
                "label":"Applications Approved(Awaiting Entry)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedInUnderwriting}",
                "label":"Applications Approved(In Underwriting)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedFundingOngoing}",
                "label":"Applications Approved(Funding Ongoing)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedOnboarded}",
                "label":"Applications Approved(Onboarded)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Successful Applications",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsMissing}",
                "label":"Applications Missing", 
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Total Applications Started",
            },
            {
                "sql": f"",
                "label": "Change in Applicatons Started",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiLoanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Multi Product Applications (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleLoanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Single Product Applications (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Total Applications Submitted",
            },
            {
                "sql": f"",
                "label": "Change in Applications Submitted",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiLoanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Multi Product Applications (Submitted)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleLoanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Single Product Applictaions (Submitted)",
            },
        ]) 
    CONSUMER_LOAN_PRODUCT_HEADERS, CONSUMER_LOAN_PRODUCT_ROWS = generate_report(
        intervals, 
        [
            #----------------------------------------------------------------------CONSUMER LOAN PRODUCTS---------------------------------------------------------------------------------------------------------------------------------------
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressAbandoned}",
                "label": "Applications In Progress (Abandoned)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsSubmittedError}",
                "label": "Applications Submitted (Error)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsDeclined}",
                "label":"Applications Declined",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsExpired}",
                "label":"Applications Expired",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "label":"Total Unsuccessful Applications",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressStarted}", 
                "label":"Applications In Progress (Started)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressSaved}",
                "label":"Applications In Progress (Saved)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsSubmittedUnderReview}", 
                "label":"Applications Submitted(Under Review)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedAwaitingEntry}",
                "label":"Applications Approved(Awaiting Entry)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedInUnderwriting}",
                "label":"Applications Approved(In Underwriting)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedFundingOngoing}",
                "label":"Applications Approved(Funding Ongoing)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedOnboarded}",
                "label":"Applications Approved(Onboarded)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Successful Applications",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsMissing}",
                "label":"Applications Missing", 
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Total Applications Started",
            },
            {
                "sql": f"",
                "label": "Change in Products Started",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiLoanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Multi Product Applications (Started)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleLoanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Single Product Applications (Started)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Total Applications Submitted",
            },
            {
                "sql": f"",
                "label": "Change in Products Submitted",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiLoanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Multi Product Applications (Submitted)",
            },
            {
                "sql": f"Select SUM(NumlendingProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleLoanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Single Product Applictaions (Submitted)",
            },
        ])
    CONSUMER_DEPOSIT_APPLICATIONS_HEADERS, CONSUMER_DEPOSIT_APPLICATIONS_ROWS = generate_report(
        intervals, 
        [
            #----------------------------------------------------------------------CONSUMER DEPOSIT APPLICATIONS---------------------------------------------------------------------------------------------------------------------------------------,
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsInProgressAbandoned}",
                "label": "Applications In Progress (Abandoned)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsSubmittedError}",
                "label": "Applications Submitted (Error)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsDeclined}",
                "label":"Applications Declined",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsExpired}",
                "label":"Applications Expired",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "label":"Total Unsuccessful Applications",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsInProgressStarted}", 
                "label":"Applications In Progress (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsInProgressSaved}",
                "label":"Applications In Progress (Saved)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsSubmittedUnderReview}", 
                "label":"Applications Submitted(Under Review)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedAwaitingEntry}",
                "label":"Applications Approved(Awaiting Entry)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedInUnderwriting}",
                "label":"Applications Approved(In Underwriting)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedFundingOngoing}",
                "label":"Applications Approved(Funding Ongoing)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedOnboarded}",
                "label":"Applications Approved(Onboarded)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Successful Applications",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsMissing}",
                "label":"Applications Missing", 
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Total Applications Started",
            },
            {
                "sql": f"",
                "label": "Change in Applicatons Started",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiDepositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Multi Product Applications (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleDepositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Single Product Applications (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Total Applications Submitted",
            },
            {
                "sql": f"",
                "label": "Change in Applications Submitted",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiDepositApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Multi Product Applications (Submitted)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleDepositApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Single Product Applictaions (Submitted)",
            },
        ]) 
    CONSUMER_DEPOSIT_PRODUCTS_HEADERS, CONSUMER_DEPOSIT_PRODUCTS_ROWS = generate_report(
        intervals, 
        [
            #----------------------------------------------------------------------CONSUMER DEPOSIT PRODUCTS---------------------------------------------------------------------------------------------------------------------------------------
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsInProgressAbandoned}",
                "label": "Applications In Progress (Abandoned)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsSubmittedError}",
                "label": "Applications Submitted (Error)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsDeclined}",
                "label":"Applications Declined",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsExpired}",
                "label":"Applications Expired",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "label":"Total Unsuccessful Applications",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsInProgressStarted}", 
                "label":"Applications In Progress (Started)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsInProgressSaved}",
                "label":"Applications In Progress (Saved)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsSubmittedUnderReview}", 
                "label":"Applications Submitted(Under Review)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedAwaitingEntry}",
                "label":"Applications Approved(Awaiting Entry)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedInUnderwriting}",
                "label":"Applications Approved(In Underwriting)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedFundingOngoing}",
                "label":"Applications Approved(Funding Ongoing)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsApprovedOnboarded}",
                "label":"Applications Approved(Onboarded)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Successful Applications",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND {applicationsMissing}",
                "label":"Applications Missing", 
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Total Applications Started",
            },
            {
                "sql": f"",
                "label": "Change in Products Started",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiDepositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Multi Product Applications (Started)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleDepositApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Single Product Applications (Started)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {depositApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Total Applications Submitted",
            },
            {
                "sql": f"",
                "label": "Change in Products Submitted",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiDepositApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Multi Product Applications (Submitted)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleDepositApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Single Product Applictaions (Submitted)",
            },
        ])
    
    CONSUMER_MIXED_APPLICATIONS_HEADERS, CONSUMER_MIXED_APPLICATIONS_ROWS = generate_report(
        intervals, 
        [
            #----------------------------------------------------------------------CONSUMER MIXED APPLICATIONS---------------------------------------------------------------------------------------------------------------------------------------
            
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsInProgressAbandoned}",
                "label": "Applications In Progress (Abandoned)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsSubmittedError}",
                "label": "Applications Submitted (Error)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsDeclined}",
                "label":"Applications Declined",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsExpired}",
                "label":"Applications Expired",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "label":"Total Unsuccessful Applications",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsInProgressStarted}", 
                "label":"Applications In Progress (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsInProgressSaved}",
                "label":"Applications In Progress (Saved)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsSubmittedUnderReview}", 
                "label":"Applications Submitted(Under Review)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedAwaitingEntry}",
                "label":"Applications Approved(Awaiting Entry)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedInUnderwriting}",
                "label":"Applications Approved(In Underwriting)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedFundingOngoing}",
                "label":"Applications Approved(Funding Ongoing)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedOnboarded}",
                "label":"Applications Approved(Onboarded)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Successful Applications",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsMissing}",
                "label":"Applications Missing", 
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Total Applications Started",
            },
            {
                "sql": f"",
                "label": "Change in Applicatons Started",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Multi Product Applications (Started)",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Total Applications Submitted",
            },
            {
                "sql": f"",
                "label": "Change in Applications Submitted",
            },
            {
                "sql": f"Select Count(*) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Multi Product Applications (Submitted)",
            },
        ])
    CONSUMER_MIXED_PRODUCTS_HEADERS, CONSUMER_MIXED_PRODUCTS_ROWS = generate_report(
        intervals, 
        [
            #----------------------------------------------------------------------CONSUMER MIXED PRODUCTS---------------------------------------------------------------------------------------------------------------------------------------
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsInProgressAbandoned}",
                "label": "Applications In Progress (Abandoned)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsSubmittedError}",
                "label": "Applications Submitted (Error)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsDeclined}",
                "label":"Applications Declined",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsExpired}",
                "label":"Applications Expired",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "label":"Total Unsuccessful Applications",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsInProgressStarted}", 
                "label":"Applications In Progress (Started)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsInProgressSaved}",
                "label":"Applications In Progress (Saved)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsSubmittedUnderReview}", 
                "label":"Applications Submitted(Under Review)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedAwaitingEntry}",
                "label":"Applications Approved(Awaiting Entry)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedInUnderwriting}",
                "label":"Applications Approved(In Underwriting)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedFundingOngoing}",
                "label":"Applications Approved(Funding Ongoing)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsApprovedOnboarded}",
                "label":"Applications Approved(Onboarded)",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Successful Applications",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND {applicationsMissing}",
                "label":"Applications Missing", 
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Total Applications Started",
            },
            {
                "sql": f"",
                "label": "Change in Products Started",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing} OR {applicationsMissing})",
                "label":"Multi Product Applications (Started)",
            },
            
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Total Applications Submitted",
            },
            {
                "sql": f"",
                "label": "Change in Products Submitted",
            },
            {
                "sql": f"Select SUM(NumDepositProducts) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {mixedApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedFundingOngoing})",
                "label":"Multi Product Applications (Submitted)",
            },
            
        ])    

    sql.disconnect()
    return {
                "headers": CONSUMER_LOAN_APPLICATIONS_HEADERS,
                "rowSets": {
                    "Consumer Loan Applications":CONSUMER_LOAN_APPLICATIONS_ROWS,
                    "Consumer Loan Products":CONSUMER_LOAN_PRODUCT_ROWS,
                    "Consumer Deposit Applications": CONSUMER_DEPOSIT_APPLICATIONS_ROWS,
                    "Consumer Deposit Products": CONSUMER_DEPOSIT_PRODUCTS_ROWS,
                    "Consumer Mixed Applications": CONSUMER_MIXED_APPLICATIONS_ROWS,
                    "Consumer Mixed Products": CONSUMER_MIXED_PRODUCTS_ROWS,
                    }
            }
from concurrent.futures import ThreadPoolExecutor

def generate_report(intervals,  query_list):
    
    headers = ["-"] + [get_header(interval)["label"] for interval in intervals if interval['start_date'] != interval['end_date']]
    headers.append("Grand-Total")
    rows = []

    def process_query(query):
        sql = SQLConn()
        sql.connect()
        transaction = Transaction(sql)
        total = 0
        row_now = [query["label"]]
        for interv in range(len(intervals)):
            if is_same_label(query["label"], "Change in Applicatons Started"):
                num = get_change("Total Applications Started", query_list, intervals, transaction, interv)
            elif is_same_label(query["label"], "Change in Applications Submitted"):
                num = get_change("Total Applications Submitted", query_list, intervals, transaction, interv)
            else:
                num = get_query_from_list(query["label"], query_list, intervals[interv - 1], transaction)

            if isinstance(num, (int, float)):
                total += num

            row_now.append(round(num, 2))
        row_now.append(round(total, 2))
        sql.disconnect()
        return row_now

    with ThreadPoolExecutor(200) as executor:
        rows = list(executor.map(process_query, query_list))

    return headers, rows

def is_same_label(a,b):
    return a.lower().strip() == b.lower().strip()

def get_change(label,query_list,intervals,transaction, interv):
    a = get_query_from_list(label,query_list,intervals[interv-1],transaction)
    b = get_query_from_list(label,query_list,intervals[interv],transaction)
    if a == 0:
        num = 0
    else:
        num = (b-a)/a
    return num
                

def get_query_from_list(name,queries,interval,transaction):
    for query in queries:
        if is_same_label(name,query["label"]):
            if query["sql"] != "":
                queryNow =  query["sql"] + f" AND {in_between_sql_condition(interval)}"
                num = transaction.get_transactions_by_sql_query(queryNow)
                return num
            
    return 0


def get_list_of_months_between(start_date, end_date):

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    months = []

    while start_date <= end_date:
        month_start = start_date.strftime("%Y-%m-01")
        next_month = start_date + relativedelta(months=1)
        month_end = (next_month - relativedelta(days=1)).strftime("%Y-%m-%d")
        months.append({"start_date": month_start, "end_date": month_end})
        start_date = next_month

    return months

def get_header(interval):
    # Convert start date to format Jun-25
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%b-%Y")
    return {
        "field": start_date,
        "label": start_date
    }
    

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"
