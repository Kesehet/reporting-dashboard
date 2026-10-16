from dateutil.relativedelta import relativedelta
from datetime import datetime
from decimal import Decimal
import re
from report_modules.condition_utils import CorBFilter

def params_to_condition_list(params):
    ret = [
        
    ]
    if CorBFilter(
        get_all_possible_spellings(
            params,
            ["eCATrackingCode", "eCaTrackingCode"]
        )
    ):
        ret.append(
            CorBFilter(
                get_all_possible_spellings(
                    params,
                    ["eCATrackingCode", "eCaTrackingCode"]
                )
            )
        )
    
    return ret

def get_all_possible_spellings(dictionary, word):
    for w in word:
        if dictionary.get(w):
            return dictionary.get(w)
    return None

def process_account_number(acc_num: str) -> list:
    if acc_num == None:
        return []
    if type(acc_num) == int or type(acc_num) == float or isinstance(acc_num, Decimal):
        return [try_int(acc_num)]
    ret = set(acc_num.split("|"))
    ret = [_ret for _ret in ret if _ret != "" and _ret != None ]
    for i in range(len(ret)):
        if try_int(ret[i]):
            ret[i] = try_int(ret[i])
        else:
            del ret[i]
    return ret

def process_product_id(product_id: str) -> list:
    product_id = str(product_id)
    ret = set(product_id.split("|"))
    ret = [_ret for _ret in ret if _ret != "" and _ret != None ]
    for i in range(len(ret)):
        if try_int(ret[i]):
            ret[i] = try_int(ret[i])
        else:
            del ret[i]
    return ret

def get_product_name(product_id):
    from report_modules.condition_utils import ALL_PRODUCT_SET_ID
    ret = ""
    if product_id:
        product_id = str(product_id).replace(".0", "")
    for id, name in ALL_PRODUCT_SET_ID:
        for p in process_product_id(product_id):
            if try_int(id) == try_int(p):
                ret = ret + " | " + name if ret != "" else name
    return ret if ret != "" else "Unknown Product"

def get_branch_name(branch_id):
    from report_modules.condition_utils import ALL_BRANCH_ID
    ret = ""
    if branch_id:
        branch_id = str(branch_id).replace(".0", "")
    for id, name in ALL_BRANCH_ID:
        for b in process_branch_id(branch_id):
            if try_int(id) == try_int(b):
                ret = ret + " | " + id + " - " + name if ret != "" else name
    return ret if ret != "" else "Unknown Branch"

def process_branch_id(branch_id: str) -> list:
    branch_id = str(branch_id)
    ret = set(branch_id.split("|"))
    ret = [_ret for _ret in ret if _ret != "" and _ret != None ]
    for i in range(len(ret)):
        if try_int(ret[i]):
            ret[i] = try_int(ret[i])
        else:
            del ret[i]
    return ret

def try_int(try_str:str) -> int:
    try:
        return int(try_str)
    except:
        return None

def get_numbers_from_string(try_str:str) -> int:
     all_chars = ""
     for char in try_str:
        if char.isdigit():
            all_chars += char
     return try_int(all_chars) if all_chars else None

def in_between_sql_condition(interval):
    return f" AppStartDate >= '{interval['start_date']}' AND AppStartDate <= '{interval['end_date']}'"

def get_header(interval):
    # Convert start date to format Jun-25
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%Y/%m - %b").upper()
    return {
        "field": start_date,
        "label": start_date
    }

def get_day_header(interval):
    # Convert start date to format 2025-06-05
    date_obj = datetime.strptime(interval['start_date'], "%Y-%m-%d")
    start_date = date_obj.strftime("%Y-%m-%d")
    return {
        "field": start_date,
        "label": start_date
    }


# Used for IN in SQL queries for batch fetching
def group_txns(txn_list, batch_size):
    grouped_txns = []
    for i in range(0, len(txn_list), batch_size):
        grouped_txns.append(txn_list[i:i + batch_size])
    return grouped_txns

def get_quarter_header(interval):
    date_obj = datetime.strptime(interval['start_date'], "%Y-%m-%d")
    year = date_obj.year
    month = date_obj.month
    quarter = (month - 1) // 3 + 1
    label = f"Q{quarter}-{year}"
    
    return {
        "field": label,
        "label": label,
        "Q": f"Q{quarter}",
        "Y": year
    }


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

def get_list_of_days_between(start_date, end_date):

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    days = []

    while start_date <= end_date:
        day_start = start_date.strftime("%Y-%m-%d")
        day_end = start_date.strftime("%Y-%m-%d")
        next_day = start_date + relativedelta(days=1)
        days.append({"start_date": day_start, "end_date": day_end}) 
        start_date = next_day

    return days



def get_list_of_quarters_between(start_date, end_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    quarters = []

    # Align start_date to the beginning of its quarter
    start_month = ((start_date.month - 1) // 3) * 3 + 1
    start_date = datetime(start_date.year, start_month, 1)

    while start_date <= end_date:
        quarter_start = start_date.strftime("%Y-%m-%d")
        next_quarter = start_date + relativedelta(months=3)
        quarter_end = (next_quarter - relativedelta(days=1)).strftime("%Y-%m-%d")
        quarters.append({"start_date": quarter_start, "end_date": quarter_end})
        start_date = next_quarter

    return quarters

def get_start_date_and_end_date_of_given_quarter(year, quarter):
    # remove Q from quarter if present
    if isinstance(quarter, str) and quarter.startswith("Q"):
        quarter = int(quarter[1:])
    start_month = (quarter - 1) * 3 + 1
    start_date = datetime(year, start_month, 1)
    end_date = (start_date + relativedelta(months=3) - relativedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date
    }

def add_comma_to_long_numbers(num):
    try:
        return "{:,}".format(int(num))
    except:
        return num

def insight_report_to_csv_response(params, insight_report, txn=None):
    
    # Check return format
    return_format = params.get("return_format", "json")
    if return_format == "json":
        return 0
    
    block_name = "_report_" + params.get("report_name", "")
    
    
    # Check Key Name from insight_report that start with _report_
    report_keys = []
    for key in insight_report.keys():
        if key.startswith("_report_"):
            report_keys.append(key)
    if len(report_keys) == 0:
        return 0
    
    if block_name == "_report_":
        block_name = report_keys[0]
        print("Block name not provided, defaulting to first report block: ", block_name)
    
    print(f"Generating CSV for block: {block_name} with return format: {return_format} and block type: {type(insight_report.get(block_name))}")
    if type(insight_report.get(block_name)) == str:
        # Get data from sql query
        return  sql_response_to_csv(txn.get_transactions_by_sql_query(insight_report.get(block_name)))
    elif type(insight_report.get(block_name)) == dict:
        return insight_report_to_csv_response(params, insight_report.get(block_name), txn)
    elif type(insight_report.get(block_name)) == list:
        return sql_response_to_csv(insight_report.get(block_name))
    else:
        return 0

def table_fix_for_api_response(report):
    # Header order is positional: sorting or deduplicating it breaks the
    # association between each header and its value in the rows.
    return report

def sql_response_to_csv(sql_response):
    if type(sql_response) == list and len(sql_response) > 0 and type(sql_response[0]) == dict:
        headers = ','.join(list(sql_response[0].keys()))
        rows = ['{}'.format(','.join(map(str, row.values()))) for row in sql_response]
        return '\n'.join([headers] + rows)
    else:
        return 0


def get_all_product_set_ids(txn, CorB="C") -> list: 
    # Select Distinct value from [DigitalReport].[dbo].[Transactions] CROSS APPLY string_split(ProductSetId, '|') where eCATrackingCode like 'B-%'
    from report_modules.condition_utils import CorBFilter
    corb = CorBFilter(CorB)
    all_ = txn.get_transactions_by_sql_query(f'''
                                             Select Distinct value from [DigitalReport].[dbo].[Transactions] CROSS APPLY string_split(ProductSetId, '|') where {corb}
                                                ''')
    return [row['value'] for row in all_]

def get_all_branch_ids(txn, CorB="C") -> list:
    if txn.sql_conn.connection == None:
        print("No active connection")
    if CorB not in ["C", "B"]:
        return []
    q = f''' 
        Select Distinct BranchId from [DigitalReport].[dbo].[Transactions] where BranchId IS NOT NULL AND BranchId <> '' AND eCATrackingCode like '{CorB}-%'
                                                '''
    all_ = txn.get_transactions_by_sql_query(q)
    if all_ == 0:
        print("There is something wrong with the sql connection." + str(all_) + " " + str(CorB)+ " "+ q+ " "+ str(txn))
        return []
    return [row['BranchId'] for row in all_]


def format_number(value):
    """Format a numeric value with commas."""
    
    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        return f"{value:,.2f}".rstrip('0').rstrip('.')

    if isinstance(value, str):

        # remove commas temporarily to test numeric
        test = value.replace(",", "")

        # match integer or decimal numbers
        if re.fullmatch(r"-?\d+(\.\d+)?", test):
            if "." in test:
                num = float(test)
                return f"{num:,.2f}".rstrip('0').rstrip('.')
            else:
                num = int(test)
                return f"{num:,}"

    return value


def format_numbers_recursive(obj):
    """Recursively walk dict/list structures and format numbers."""
    
    if isinstance(obj, dict):
        return {k: format_numbers_recursive(v) if not ("account" in k.lower() or "id" in k.lower() or "promo" in k.lower()) else v for k, v in obj.items()}

    if isinstance(obj, list):
        return [format_numbers_recursive(v) for v in obj]

    if isinstance(obj, tuple):
        return tuple(format_numbers_recursive(v) for v in obj)
    
    if isinstance(obj, (int, float, str)):
        return format_number(obj)

    return format_number(obj)