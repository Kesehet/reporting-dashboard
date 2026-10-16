from DB import Transaction, SQLConn
from datetime import datetime
from dateutil.relativedelta import relativedelta
from report_modules.condition_utils import *
from DB import query_maker, Q
import math
from typing import Any, Union
from utils import *



def get_monthly_all_report(start_date, end_date, params=None, transactions=None):
    params = params or {"monthlyReportProductTypeSelector": "All"}
    base_filters = [
        get_date_filter(start_date, end_date),
        excludeZeroProductApps,
        CorBFilter(params.get("eCATrackingCode", "C")),
        bot_filter(25),
    ]
    intervals = get_list_of_months_between(start_date, end_date)
    report = generate_report_variants_by_filters(
        base_filters,
        intervals,
        params.get("monthlyReportProductTypeSelector", "All"),
        transactions=transactions,
    )
    return table_fix_for_api_response(report)

def get_monthly_in_branch_report(start_date, end_date, params={"monthlyReportProductTypeSelector":"All"}):
    base_filters = [get_date_filter(start_date,end_date), excludeZeroProductApps, consumerTransaction, application_type_filter("Banker Assisted"), bot_filter(25)]
    intervals = get_list_of_months_between(start_date, end_date)
    report = generate_report_variants_by_filters(base_filters, intervals, params.get("monthlyReportProductTypeSelector"))
    return table_fix_for_api_response(report)

def get_monthly_consumer_facing_report(start_date, end_date, params={"monthlyReportProductTypeSelector":"All"}): 
    base_filters = [get_date_filter(start_date,end_date), excludeZeroProductApps, consumerTransaction, application_type_filter("Online"), bot_filter(25)]
    intervals = get_list_of_months_between(start_date, end_date)
    report = generate_report_variants_by_filters(base_filters, intervals, params.get("monthlyReportProductTypeSelector"))
    return table_fix_for_api_response(report)


def get_monthly_business_deposits_report(start_date, end_date, params={"monthlyReportProductTypeSelector":"All"}): 
    base_filters = [get_date_filter(start_date,end_date), excludeZeroProductApps, businessTransaction, bot_filter(25)]
    intervals = get_list_of_months_between(start_date, end_date)
    report = generate_report_variants_by_filters(base_filters, intervals, params.get("monthlyReportProductTypeSelector"))
    return table_fix_for_api_response(report)

def get_monthly_bpm_and_crif_report(start_date, end_date, params):
    base_filters = [excludeZeroProductApps, bot_filter(25), 'AccountNumber is not Null']
    intervals = get_list_of_months_between(start_date, end_date)
    report = generate_report_variants_by_EDW_filters(base_filters, intervals, params)
    return table_fix_for_api_response(report)

def get_in_branch_vs_bpm_crif_report(start_date,end_date, params):
    intervals = get_list_of_months_between(start_date, end_date)
    expected_length = len(intervals) * 2

    def _extract_report_values(report):
        rows = report.get('rows', []) if isinstance(report, dict) else []
        if len(rows) <= 2 or not isinstance(rows[2], list):
            return [0] * expected_length
        values = rows[2][1:expected_length]
        return values + [0] * max(0, expected_length - len(values))

    bpm_crif_report = _extract_report_values(get_monthly_bpm_and_crif_report(start_date, end_date, params))
    in_branch_report = _extract_report_values(get_monthly_in_branch_report(start_date, end_date))
    
    

    bpm_crif_pct = []
    in_branch_pct = []
    total_bpm_crif_in_branch_merge = []
    prev_in_branch_pct = 0
    prev_bpm_crif_pct = 0
    prev_total_bpm_crif_in_branch_change_merge_pct = 0
    current_total_in_branch = 0
    for i in range((len(intervals)*2 )-1 ):
        if i % 2 == 0: # The number part
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
        else: # The Change % calculation part
            if i-1 < 0:
                continue


            if len(bpm_crif_pct) > 0 and (bpm_crif_pct[i-1] == 0 or bpm_crif_pct[i-1] == None):
                bpm_crif_pct.append(0.0)
            else:
                current_total_bpm_crif = bpm_crif_pct[i-1]

            if len(in_branch_pct) > 0 and (in_branch_pct[i-1] == 0 or in_branch_pct[i-1] == None):
                in_branch_pct.append(0.0)
            else:
                current_total_in_branch = in_branch_pct[i-1]
            if len(total_bpm_crif_in_branch_merge) > 0 and ((total_bpm_crif_in_branch_merge[i-1] == 0 or total_bpm_crif_in_branch_merge[i-1] == None)):
                total_bpm_crif_in_branch_merge.append(0.0)
            else:
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


    report = {
        "headers": ["-"] + [get_header(header)['field'] for header in intervals] + [get_header(header)['field'] for header in intervals],
        "rows": [
            ["Total In-Branch Account Openings"] + total_bpm_crif_in_branch_merge,
            ["BPM/CRIF Numbers (Debugging)"] + bpm_crif_report,
            ["In Branch Numbers (Debugging)"] + in_branch_report,
            ["% Via BPM & CRIF App"] +  [f"{pct} %" for pct in bpm_crif_pct],
            ["% Via eStore Common App"] + [f"{pct} %" for pct in in_branch_pct],
        ]
    }
    return table_fix_for_api_response(report)

def generate_report_variants_by_EDW_filters(base_filters, intervals, params):
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
            sql=n_sql,
            params=params
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


        acc_app_filter = '''( ''' + ','.join([f'\'{to_number(app)}\'' for app in account_numbers_from_txns_table]) + ''')'''

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

        valid_accounts = []
        for acc in account_numbers_from_txns_table:
            if acc and acc.isdigit():  # ensures numeric only
                valid_accounts.append(acc)

        temp_table_sql = "WITH FilteredAccounts AS (SELECT CAST(value AS BIGINT) AS AccountNumber FROM (VALUES " + \
            ",".join([f"('{acc}')" for acc in valid_accounts]) + \
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

        dda_total = to_number(dda_total)
        sav_total = to_number(sav_total)
        cod_total = to_number(cod_total)
        note_total = to_number(note_total)


        for variant in rows.keys():
            if variant == "BPM":
                current_total = to_number(dda_total + sav_total + cod_total)
                rows["BPM"].append(current_total)
                if len(rows["BPM"]) > 1:
                    prev = to_number(rows["BPM"][-3])
                    pct_change = ((current_total - prev) / prev * 100) if prev != 0 else 0
                else:
                    pct_change = 0
                rows["BPM"].append(round(pct_change, 2))

            elif variant == "CRIF":
                current_total = to_number(note_total)
                rows["CRIF"].append(current_total)
                if len(rows["CRIF"]) > 1:
                    prev = to_number(rows["CRIF"][-3])
                    pct_change = ((current_total - prev) / prev * 100) if prev != 0 else 0
                else:
                    pct_change = 0
                rows["CRIF"].append(round(pct_change, 2))

            elif variant == "TOTAL":
                current_total = to_number(note_total + dda_total + cod_total + sav_total)
                rows["TOTAL"].append(current_total)
                if len(rows["TOTAL"]) > 1:
                    prev = to_number(rows["TOTAL"][-3])
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





def generate_report_variants_by_filters(base_filters, intervals, variant, transactions=None):
    variant = variant or "All"
    if variant == "All":
        variant = "Applications"
    
    test_report_header, test_report_rows = generate_report(
        intervals, 
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
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[approvedApps,loanApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Loan Products" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[approvedApps,depositApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Deposit Products" # Red
            },
            {
                "sql": {
                    "Apps" : query_maker(columns=[sumColumn("NumLendingProducts+NumDepositProducts")], where=[approvedApps,mixedApps]+base_filters), # Yellow
                    "%Change" : "", # Green
                },
                "label": "Opened/Approved Mixed Products" # Red
            },
        ],
        transaction=transactions,
        variant=variant,
    )

    return {
                "headers": test_report_header,
                "rows": test_report_rows
            }


def generate_report(intervals, query_list, transaction=None, variant="All"):
    headers = ["-"]
    owned_sql = None
    if transaction is None:
        owned_sql = SQLConn()
        owned_sql.connect()
        transaction = Transaction(owned_sql)

    try:
        # Generate headers for each interval
        for interval in intervals:
            if interval['start_date'] != interval['end_date']:
                label = get_header(interval)["label"]
                headers.append(f"{label}")

        rows = []
        selected_variant = (variant or "All").split(" ")[0]
        for report_row in query_list:
            if selected_variant not in report_row["label"]:
                continue

            row = [report_row["label"]]
            for interval in intervals:
                query = report_row["sql"]["Apps"] + f" AND {in_between_sql_condition(interval)}  "
                row.append(transaction.get_transactions_by_sql_query(query))
            rows.append(row)
    finally:
        if owned_sql is not None:
            owned_sql.disconnect()

    return headers, rows



    

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"




def to_number(value: Any, *, default: Union[int, float, str] = 0, as_str: bool = False):
    """
    Clean and convert `value` to a number:
      - Removes everything not digit or '.' (preserves a single leading sign; supports '(...)' as negative)
      - Rounds to 2 decimal places
      - If the rounded value is integral (e.g., 12.00), returns/prints as an int (e.g., '12' or 12)
      - Otherwise shows up to 2 decimals (trim trailing zeros)
    
    Args:
      value: Any messy input (e.g., '$ (1,234.50) USD')
      default: Fallback value (type should align with as_str)
      as_str: If True -> return a display string; if False -> return int or float

    Returns:
      If as_str=True: a string like '123', '123.4', '123.46'
      If as_str=False: an int (for integral results) or float (rounded to 2 dp)
    """
    # Fast paths for simple numerics and edge cases
    if value is None or isinstance(value, bool):
        return str(default) if as_str else default
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return str(default) if as_str else default
        num = round(float(value), 2)
        if num.is_integer():
            return str(int(num)) if as_str else int(num)
        return (f"{num:.2f}".rstrip("0").rstrip(".")) if as_str else num

    # Convert to string and strip outer whitespace
    s = str(value).strip()
    if not s:
        return str(default) if as_str else default

    # Handle parentheses for negatives: "(...)" -> negative
    is_paren_negative = s.startswith("(") and s.endswith(")")
    if is_paren_negative:
        s = s[1:-1].strip()

    # Capture a single leading sign
    sign = ''
    if s and s[0] in '+-':
        sign = s[0]
        s = s[1:]

    # Remove everything except digits and '.'
    cleaned = ''.join(ch for ch in s if ch.isdigit() or ch == '.')

    # Normalize edge cases like ".5" or "12."
    if cleaned == '' or cleaned == '.':
        return str(default) if as_str else default
    if cleaned.startswith('.'):
        cleaned = '0' + cleaned
    if cleaned.endswith('.'):
        cleaned = cleaned + '0'

    # Parentheses imply negative and override '+'
    final_sign = '-' if is_paren_negative else (sign if sign in '+-' else '')
    token = final_sign + cleaned

    # Parse, round, and format
    try:
        num = round(float(token), 2)
        if num.is_integer():
            return str(int(num)) if as_str else int(num)
        # format with up to 2 decimals (no trailing zeros)
        txt = f"{num:.2f}".rstrip("0").rstrip(".")
        return txt if as_str else num
    except Exception:
        return str(default) if as_str else default