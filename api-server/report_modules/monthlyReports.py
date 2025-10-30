from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *
from DB import query_maker, Q




def get_monthly_in_branch_report(start_date, end_date, params={"monthlyReportProductTypeSelector":"All"}): 
    base_filters = [get_date_filter(start_date,end_date), excludeZeroProductApps, consumerTransaction, application_type_filter("Banker Assisted"), bot_filter(25)]
    intervals = get_list_of_months_between(start_date, end_date)
    return generate_report_variants_by_filters(base_filters, intervals, params.get("monthlyReportProductTypeSelector"))

def get_monthly_consumer_facing_report(start_date, end_date, params={"monthlyReportProductTypeSelector":"All"}): 
    base_filters = [get_date_filter(start_date,end_date), excludeZeroProductApps, consumerTransaction, application_type_filter("Online"), bot_filter(25)]
    intervals = get_list_of_months_between(start_date, end_date)
    return generate_report_variants_by_filters(base_filters, intervals, params.get("monthlyReportProductTypeSelector"))

def get_monthly_business_deposits_report(start_date, end_date, params={"monthlyReportProductTypeSelector":"All"}): 
    base_filters = [get_date_filter(start_date,end_date), excludeZeroProductApps, businessTransaction, bot_filter(25)]
    intervals = get_list_of_months_between(start_date, end_date)
    return generate_report_variants_by_filters(base_filters, intervals, params.get("monthlyReportProductTypeSelector"))

def get_monthly_bpm_and_crif_report(start_date, end_date):
    base_filters = [excludeZeroProductApps, bot_filter(25), 'AccountNumber is not Null']
    intervals = get_list_of_months_between(start_date, end_date)
    return generate_report_variants_by_EDW_filters(base_filters, intervals)

def get_in_branch_vs_bpm_crif_report(start_date,end_date):
    intervals = get_list_of_months_between(start_date, end_date)
    bpm_crif_report = get_monthly_bpm_and_crif_report(start_date, end_date)['rows'][2][1:(len(intervals)*2)]
    in_branch_report = get_monthly_in_branch_report(start_date, end_date)['rows'][2][1:(len(intervals)*2)]
    
    

    bpm_crif_pct = []
    in_branch_pct = []
    total_bpm_crif_in_branch_merge = []
    prev_in_branch_pct = 0
    prev_bpm_crif_pct = 0
    prev_total_bpm_crif_in_branch_change_merge_pct = 0
    for i in range((len(intervals)*2 )-1 ):
        if i % 2 == 0:
            total = (bpm_crif_report[i] + in_branch_report[i])
            if total == 0:
                bpm_crif_pct.append(0.0)
                in_branch_pct.append(0.0)
                continue
            bpm_crif_pct.append(
                round(bpm_crif_report[i] / total * 100, 2)
            )
            in_branch_pct.append(
                round(in_branch_report[i] / total * 100, 2)
            )
            total_bpm_crif_in_branch_merge.append(
                total
            )
        else:
            current_total_bpm_crif = bpm_crif_pct[i-1]
            current_total_in_branch = in_branch_pct[i-1]
            current_total_bpm_crif_in_branch_change_merge_pct = total_bpm_crif_in_branch_merge[i-1]


            if prev_bpm_crif_pct != 0:
                bpm_crif_pct.append(
                    round((current_total_bpm_crif - prev_bpm_crif_pct)/prev_bpm_crif_pct * 100, 2)
                )
            else:
                bpm_crif_pct.append(0.0)

            if prev_total_bpm_crif_in_branch_change_merge_pct != 0:
                total_bpm_crif_in_branch_merge.append(
                    round((current_total_bpm_crif_in_branch_change_merge_pct - prev_total_bpm_crif_in_branch_change_merge_pct)/prev_total_bpm_crif_in_branch_change_merge_pct * 100, 2)
                )
            else:
                total_bpm_crif_in_branch_merge.append(0.0)
            

            if prev_in_branch_pct != 0:
                in_branch_pct.append(
                    round((current_total_in_branch - prev_in_branch_pct)/prev_in_branch_pct * 100, 2)
                )
            else:
                in_branch_pct.append(0.0)

            prev_in_branch_pct = current_total_in_branch
            prev_bpm_crif_pct = current_total_bpm_crif
            prev_total_bpm_crif_in_branch_change_merge_pct = current_total_bpm_crif_in_branch_change_merge_pct


    print("__________________________________________________________________")
    print("In Branch Report", in_branch_report)
    print("BPM & CRIF Report", bpm_crif_report)

    print("In Branch Report", in_branch_pct)
    print("BPM & CRIF Report", bpm_crif_pct)
    print("__________________________________________________________________")


    return {
        "headers": ["-"] + [get_header(header)['field'] for header in intervals] + [get_header(header)['field'] for header in intervals],
        "rows": [
            ["Total In-Branch Account Openings"] + total_bpm_crif_in_branch_merge,
            # ["BPM/CRIF Numbers (Debugging)"] + bpm_crif_report,
            # ["In Branch Numbers (Debugging)"] + in_branch_report,
            ["% Via BPM & CRIF App"] +  [f"{pct} %" for pct in bpm_crif_pct],
            ["% Via eStore Common App"] + [f"{pct} %" for pct in in_branch_pct],
        ]
    }

def generate_report_variants_by_EDW_filters(base_filters, intervals):
    camedw_sql = SQLConn(kind="CRFEDW")
    camedw_sql.connect()
    camedw_txn = Transaction(camedw_sql)
    n_sql = SQLConn()    
    n_sql.connect()
    rows = {
        "BPM" :[],
        "CRIF" :[],
        "TOTAL" :[],
    }

    def flatten_pipe_separated_strings(input_list):
        return [item for string in input_list for item in string.split('|')]
    
    for idx, interval in enumerate(intervals, start=1):
        


        account_numbers_from_txns_table_req = Q(
            where=[approvedAppsForBPMandCRIF, in_between_sql_condition(interval), 'AccountNumber Not like \'%n\' '] + base_filters,
            sql=n_sql
        )

        


        if account_numbers_from_txns_table_req == 0:
            rows["BPM"].append(0.0)
            rows["CRIF"].append(0.0)
            rows["TOTAL"].append(0.0)
            rows["BPM"].append(0.0)
            rows["CRIF"].append(0.0)
            rows["TOTAL"].append(0.0)
            
            continue
        
        
        
        account_numbers_from_txns_table = [
            accNo.get("AccountNumber") for accNo in account_numbers_from_txns_table_req
            if accNo.get("AccountNumber") not in [None, 'None', '']
        ]

        account_numbers_from_txns_table =  flatten_pipe_separated_strings(account_numbers_from_txns_table)


        acc_app_filter = '''( ''' + ','.join([f'\'{int(app)}\'' for app in account_numbers_from_txns_table]) + ''')'''

        dda_total = camedw_txn.get_transactions_by_sql_query(
            f"""SELECT COUNT(*) AS data FROM [CAMEDW].[CAM_EMPL_PII_V1].[CAM_DDA_ACCT_CUR]
                WHERE Date_Opened >= '{interval['start_date']}' AND Date_Opened <= '{interval['end_date']}' AND  DDA_ACCT_NUM NOT IN {acc_app_filter}"""
        )

        sav_total = camedw_txn.get_transactions_by_sql_query(
            f"""SELECT COUNT(*) AS data FROM [CAMEDW].[CAM_EMPL_PII_V1].[CAM_SAV_ACCT_CUR]
                WHERE Date_Opened >= '{interval['start_date']}' AND Date_Opened <= '{interval['end_date']}' AND  SAV_ACCT_NUM NOT IN {acc_app_filter}"""
        )

        cod_total = camedw_txn.get_transactions_by_sql_query(
            f"""SELECT COUNT(*) AS data FROM [CAMEDW].[CAM_EMPL_PII_V1].[CAM_COD_ACCT_CUR]
                WHERE Date_Opened >= '{interval['start_date']}' AND Date_Opened <= '{interval['end_date']}' AND  COD_ACCT_NUM NOT IN {acc_app_filter}"""
        )

        temp_table_sql = "WITH FilteredAccounts AS (SELECT value AS AccountNumber FROM (VALUES " + \
                        ",".join([f"('{acc}')" for acc in account_numbers_from_txns_table if acc != None]) + \
                        ") AS V(value))"

        NOTE_TABLE = "CAM_NOTE_ACCT_CUR"
        NOTE_COLUMN = "NOTE_ACCT_NUM"

        long_sql = f"""
        {temp_table_sql}
        SELECT COUNT(*) AS data
        FROM [CAMEDW].[CAM_EMPL_PII_V1].[{NOTE_TABLE}] n
        WHERE  Date_Opened >= '{interval['start_date']}' AND Date_Opened <= '{interval['end_date']}' AND NOT EXISTS (
            SELECT 1
            FROM FilteredAccounts f
            WHERE f.AccountNumber = n.{NOTE_COLUMN}
        )
        """

        note_total = camedw_txn.get_transactions_by_sql_query(long_sql)

        for variant in rows.keys():
            if variant == "BPM":
                current_total = int(dda_total + sav_total + cod_total)
                rows["BPM"].append(current_total)
                if len(rows["BPM"]) > 1:
                    prev = rows["BPM"][-3]
                    pct_change = ((current_total - prev) / prev * 100) if prev != 0 else 0
                else:
                    pct_change = 0
                rows["BPM"].append(round(pct_change, 2))

            elif variant == "CRIF":
                current_total = int(note_total)
                rows["CRIF"].append(current_total)
                if len(rows["CRIF"]) > 1:
                    prev = rows["CRIF"][-3]
                    pct_change = ((current_total - prev) / prev * 100) if prev != 0 else 0
                else:
                    pct_change = 0
                rows["CRIF"].append(round(pct_change, 2))

            elif variant == "TOTAL":
                current_total = int(note_total + dda_total + cod_total + sav_total)
                rows["TOTAL"].append(current_total)
                if len(rows["TOTAL"]) > 1:
                    prev = rows["TOTAL"][-3]
                    pct_change = ((current_total - prev) / prev * 100) if prev != 0 else 0
                else:
                    pct_change = 0
                rows["TOTAL"].append(round(pct_change, 2))


    camedw_sql.disconnect()
    n_sql.disconnect()
    
    
    
    for i in range(len(intervals)*2):
        if i % 2 != 0:
            rows["BPM"][i]  = str(rows["BPM"][i])+ " %"
            rows["CRIF"][i]  = str(rows["CRIF"][i])+ " %"
            rows["TOTAL"][i]  = str(rows["TOTAL"][i])+ " %"

    
    return {
                "headers": ["-"] + [get_header(header)['field'] for header in intervals] + [get_header(header)['field'] for header in intervals],
                "rows": [
                    ["BPM"] + rows["BPM"] ,
                    ["CRIF"] + rows["CRIF"],
                    ["TOTAL"] + rows["TOTAL"],
                ]
            }





def generate_report_variants_by_filters(base_filters, intervals, variant):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    
    intervals = intervals + intervals
    
    test_report_header, test_report_rows = generate_report(
        intervals, transaction,
        [
            {
                "sql": {
                    # Started Applications
                    "Apps" : query_maker(columns=[countColumn], where=base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Started Applications" # Red
            },
            {
                "sql": {
                    # Started Applications
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Started Products" # Red
            },
            {
                "sql": {
                    # Started Applications
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[loanApps] + base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Started Loan Products" # Red
            }, 
            {
                "sql": {
                    # Started Applications
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[depositApps] + base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Started Deposit Products" # Red
            },
            {
                "sql": {
                    # Started Applications
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[mixedApps] + base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Started Mixed Products" # Red
            },            
            {
                "sql": {
                    "Apps" : query_maker(columns=[countColumn], where=[submittedApps] + base_filters ), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Submitted Applications" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[submittedApps] + base_filters ), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Submitted Products" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[submittedApps] + [loanApps] + base_filters ), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Submitted Loan Products" # Red
            },{
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[submittedApps] + [depositApps] + base_filters ), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Submitted Deposit Products" # Red
            },{
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[submittedApps] + [mixedApps] + base_filters ), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Submitted Mixed Products" # Red
            },
            
            {
                "sql": {
                    "Apps" : query_maker(columns=[countColumn], where=[approvedApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Applications" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[approvedApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Products" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[loanApprovedApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Loan Products" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[depositApprovedApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Deposit Products" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[mixedApprovedApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Mixed Products" # Red
            },
            
            
        ]
    )

    final_rows = []
    for row in test_report_rows:
        test_str_for_variant = str(row)
        variant_found = False
        v = variant.split(" ")[0]
        if test_str_for_variant.find(v) != -1 or test_str_for_variant.find("Application")  != -1:
            variant_found = True
        if variant_found:
            final_rows.append(row)
    

        


    sql.disconnect()
    return {
                "headers": test_report_header,
                "rows": final_rows
            }


def generate_report(intervals, transaction, query_list):
    headers = ["-"] 
    # Generate headers for each interval
    for interval in intervals:
        if interval['start_date'] != interval['end_date']:
            label = get_header(interval)["label"]
            headers.append(f"{label}")

    rows = []
    # Initialize rows with labels only
    for red in query_list:
        row = []
        row.append(
            red["label"]
        )
        for i in range(len(intervals)):
            pink = intervals[i]
            queryNowA = red["sql"]["Apps"] + f" AND {in_between_sql_condition(pink)}"
            numA = transaction.get_transactions_by_sql_query(queryNowA)
            row.append(
                int(numA)
                )
            if i != 0:
                ponk = intervals[i-1]
                queryBeforeThis = red["sql"]["Apps"] + f" AND {in_between_sql_condition(ponk)}"
                numB = transaction.get_transactions_by_sql_query(queryBeforeThis)
                if numB != 0:
                    change = ((numA-numB)/numB) * 100
                else:
                    change = 0
                row.append(
                    str(
                            "{:,}".format(round(change, 2))
                        ) + '%'
                )
            else:
                row.append("-")  
            

        rows.append(row)

    return headers, rows




def get_header(interval):
    # Convert start date to format Jun-25
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%b-%Y")
    return {
        "field": start_date,
        "label": start_date
    }
    

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"


def get_list_of_months_between(start_date, end_date):

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    months = []

    while start_date <= end_date:
        month_start = start_date.strftime("%Y-%m-01")  # July 1st
        next_month = datetime.strptime(month_start, "%Y-%m-%d") + relativedelta(months=1)  # Auguest 1st
        month_end = (next_month - relativedelta(days=1)).strftime("%Y-%m-%d") # Auguest 4th 
        months.append({"start_date": month_start, "end_date": month_end}) 
        start_date = next_month

    return months

