from DB import Q
from report_modules.condition_utils import *
from utils import *


PRODUCT_ID_FILTER = "ProductSetId like '%24501%'" #add product code for student checking
COMMON_CONDITION = [
    PRODUCT_ID_FILTER,
    approvedApps
]

def student_checking_report_insights():

    return {
        "StudentCheckingReport":Q(columns=[countColumn], where= COMMON_CONDITION),
        "_report_StudentCheckingReport":Q(where= COMMON_CONDITION)
    }

def student_checking_report_table(start_date,end_date):
    headers = []
    rows = [[]]
    intervals = get_list_of_months_between(start_date,end_date)

    for interv in intervals:
        headers.append(get_header(interv).get("label"))
        rows[0].append(Q(columns=[countColumn], where=[get_date_filter(
            interv.get("start_date"), interv.get("end_date")
        )] + COMMON_CONDITION))

    return {
        "headers": headers,
        "rows": rows
    }
