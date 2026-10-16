from DB import Transaction, SQLConn, Q
from report_modules.condition_utils import *
from concurrent.futures import ThreadPoolExecutor
from utils import get_list_of_months_between, get_header

def get_lending_and_deposit_reports(start_date, end_date, params):
    intervals = get_list_of_months_between(start_date, end_date)

    PRODUCTS = "Products"
    APPLICATIONS = "Applications"

    CONSUMER_LOAN_APPLICATIONS_HEADERS, CONSUMER_LOAN_APPLICATIONS_ROWS = generate_report(
        intervals, 
        get_template_list([
            loanApps, # base
            singleLoanApps,# single
            multiLoanApps, # # multi
        ], countColumn, product_or_application=APPLICATIONS),
        params
        )
    
    sum_num_lending_products = f"SUM(NumlendingProducts) as data"
    CONSUMER_LOAN_PRODUCT_HEADERS, CONSUMER_LOAN_PRODUCT_ROWS = generate_report(
        intervals, 
        get_template_list([
            loanApps, # base
            singleLoanApps,# single
            multiLoanApps, # # multi
        ], sum_num_lending_products, product_or_application=PRODUCTS),
        params
    )
    
    CONSUMER_DEPOSIT_APPLICATIONS_HEADERS, CONSUMER_DEPOSIT_APPLICATIONS_ROWS = generate_report(
        intervals, 
        get_template_list([
            depositApps, # base
            singleDepositApps,# single
            multiDepositApps, # multi
        ], countColumn, product_or_application=APPLICATIONS),
        params
    )
    
    sum_num_deposit_products = f"SUM(NumDepositProducts) as data"    
    
    CONSUMER_DEPOSIT_PRODUCTS_HEADERS, CONSUMER_DEPOSIT_PRODUCTS_ROWS = generate_report(
        intervals, 
        get_template_list([
            depositApps, # base
            singleDepositApps,# single
            multiDepositApps, # multi
        ], sum_num_deposit_products, product_or_application=PRODUCTS),
        params
    )
    
    CONSUMER_MIXED_APPLICATIONS_HEADERS, CONSUMER_MIXED_APPLICATIONS_ROWS = generate_report(
        intervals, 
        get_template_list([
            mixedApps, # base
            mixedApps ,# single
            mixedApps, # multi
        ], countColumn, product_or_application=APPLICATIONS),
        params
        )
    

    CONSUMER_MIXED_PRODUCTS_HEADERS, CONSUMER_MIXED_PRODUCTS_ROWS = generate_report(
        intervals, 
        get_template_list([
            mixedApps, # base
            mixedApps ,# single
            mixedApps, # multi
        ], sum_num_deposit_products, product_or_application=PRODUCTS),
        params
            )    

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




def get_template_list(app_type, column_type, product_or_application="Application", skipSingle=False, params={}):
    common_filters = [excludeBotData, excludeZeroProductApps]
    template_list = [
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressAbandoned}",
                "special_condition":  applicationsInProgressAbandoned,
                "label": "Applications In Progress (Abandoned)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsSubmittedError}",
                "special_condition":  applicationsSubmittedError,
                "label": "Applications Submitted (Error)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsDeclined}",
                "special_condition":  applicationsDeclined,
                "label":"Applications Declined",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsExpired}",
                "special_condition":  applicationsExpired,
                "label":"Applications Expired",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({abandonedApps} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "special_condition":  f"({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired})",
                "label":"Total Unsuccessful Applications",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressStarted}",
                "special_condition":  applicationsInProgressStarted,
                "label":"Applications In Progress (Started)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsInProgressSaved}",
                "special_condition":  applicationsInProgressSaved,
                "label":"Applications In Progress (Saved)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsSubmittedUnderReview}", 
                "special_condition":  applicationsSubmittedUnderReview,
                "label":"Applications Submitted(Under Review)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedAwaitingEntry}",
                "special_condition":  applicationsApprovedAwaitingEntry,
                "label":"Applications Approved(Awaiting Entry)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedInUnderwriting}",
                "special_condition":  applicationsApprovedInUnderwriting,
                "label":"Applications Approved(In Underwriting)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedFundingOngoing}",
                "special_condition":  applicationsApprovedFundingOngoing,
                "label":"Applications Approved(Funding Ongoing)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsApprovedOnboarded}",
                "special_condition":  applicationsApprovedOnboarded,
                "label":"Applications Approved(Onboarded)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "special_condition":  f"({applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Successful Applications",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND {applicationsMissing}",
                "special_condition":  applicationsMissing,
                "label":"Applications Missing", 
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing}  OR {applicationsMissing})",
                "special_condition":  f"({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing}  OR {applicationsMissing} OR {applicationsApprovedOnboarded})",
                "label":"Total Applications Started",
            },
            {
                # "sql": f"",
                "special_condition": "",
                "label": "Change in Applicatons Started",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiLoanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing}  OR {applicationsMissing})",
                "special_condition":f"({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing}  OR {applicationsMissing} OR {applicationsApprovedOnboarded})",
                "label":"Multi Product Applications (Started)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleLoanApps} AND ({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing}  OR {applicationsMissing})",
                "special_condition": f"({applicationsInProgressAbandoned} OR {applicationsSubmittedError} OR {applicationsDeclined} OR {applicationsExpired} OR {applicationsInProgressStarted} OR {applicationsInProgressSaved} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing}  OR {applicationsMissing} OR {applicationsApprovedOnboarded})",
                "label":"Single Product Applications (Started)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} )",
                "special_condition":  f"({applicationsSubmitted} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded} OR {applicationsDeclined} OR {applicationsSubmittedError})",
                "label":"Total Applications Submitted",
            },
            {
                # "sql": f"",
                "special_condition": "",
                "label": "Change in Applications Submitted",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiLoanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} )",
                "special_condition": f"({applicationsSubmitted} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded} OR {applicationsDeclined} OR {applicationsSubmittedError})",
                "label":"Multi Product Applications (Submitted)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleLoanApps} AND ({applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} )",
                "special_condition": f"({applicationsSubmitted} OR {applicationsSubmittedUnderReview} OR {applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded} OR {applicationsDeclined} OR {applicationsSubmittedError})",
                "label":"Single Product Applictaions (Submitted)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {loanApps} AND ({applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} )",
                "special_condition":  f"({applicationsApprovedAwaitingEntry} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded})",
                "label":"Total Applications Approved",
            },
            {
                # "sql": f"",
                "special_condition": "",
                "label": "Change in Applications Approved",
            },
            {
               # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {multiLoanApps} AND ({applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} )",
                "special_condition": f"({applicationsApprovedAwaitingEntry} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded} )",
                "label":"Multi Product Applications (Approved)",
            },
            {
                # "sql": f"Select Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) as data from {table} where {excludeBotData} AND {excludeZeroProductApps} AND {singleLoanApps} AND ({applicationsApprovedAwaitingEntry} OR {applicationsApprovedInUnderwriting} OR {applicationsApprovedFundingOngoing} )",
                "special_condition": f"({applicationsApprovedAwaitingEntry} OR {applicationsApprovedFundingOngoing} OR {applicationsApprovedOnboarded} )",
                "label":"Single Product Applications (Approved)",
            },
            
        ]
    
    for i in range(len(template_list)):
        if product_or_application == "Products":
            template_list[i]["label"] = template_list[i]["label"].replace("Applications","Products")
        if template_list[i].get("label").startswith("Single"):
            if skipSingle:
                del template_list[i]
            template_list[i]["sql"] = Q(
                where=[template_list[i].get("special_condition"), app_type[1]] + common_filters,
                columns=[column_type],
                queryOnly=True,
                params=params
            )
        elif template_list[i].get("label").startswith("Multi"):
            template_list[i]["sql"] = Q(
                where=[template_list[i].get("special_condition"), app_type[2]] + common_filters,
                columns=[column_type],
                queryOnly=True,
                params=params
            )
        elif template_list[i].get("label").startswith("Change"):
            template_list[i]["sql"] = ""
        else:
            template_list[i]["sql"] = Q(
                where=[template_list[i].get("special_condition"), app_type[0]] + common_filters,
                columns=[column_type],
                queryOnly=True,
                params=params
            )

    return template_list

def generate_report(intervals,  query_list, params):
    
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
            elif is_same_label(query["label"], "Change in Applications Approved"):
                num = get_change("Total Applications Approved", query_list, intervals, transaction, interv)
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

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"
