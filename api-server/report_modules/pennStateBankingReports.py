'''
PennState Branch Reports

date filter applicable , consumer/business filter applicable 


'''

from report_modules.condition_utils import *
from DB import Q
from utils import get_list_of_months_between, get_header

COMMON_FILTERS = [excludeZeroProductApps, excludeBotData, '''
appStartDate > '2026-07-01'
''', '''branchID IN (2037,
2041,
2047,
2075,
2087,
2098,
2099,
2099,
2106,
2218,
2302,
2304,
2428,
2511,
2851,
2855,
2874,
2876,
2881,
2889,
2889,
2894,
2897)''']

'''
PennState Branch Reports - Insights 
'''

def pennStateBranchReportsInsights(params, start_date, end_date):
    filters = [
        CorBFilter(params.get("CorBFilter", "All")),
        get_date_filter(start_date,end_date)
    ] + COMMON_FILTERS
    return {
        "Started": Q(columns=[countColumn], where=[startedApps] + filters),
        "_report_Started": Q(where=[startedApps] + filters),
        "Submitted": Q(columns=[countColumn], where=[submittedApps] + filters),
        "_report_Submitted": Q(where=[submittedApps] + filters),
        "Opened/Approved": Q(columns=[countColumn], where=[approvedApps] + filters),
        "_report_Opened/Approved": Q(where=[approvedApps] + filters)
    }

'''
PennState Student Banking Reports - Insights
'''
def pennStateStudentBankingReportsInsights(params,start_date,end_date):
    filters = [
        CorBFilter(params.get("CorBFilter", "All")),
        "ProductSetId like '%24501%'",
        get_date_filter(start_date,end_date)
    ] + COMMON_FILTERS
    return {
            "Started": Q(columns=[countColumn], where=[startedApps] + filters),
            "_report_Started": Q(where=[startedApps] + filters),
            "Submitted": Q(columns=[countColumn], where=[submittedApps] + filters),
            "_report_Submitted": Q(where=[submittedApps]+ filters),
            "Opened/Approved": Q(columns=[countColumn], where=[approvedApps]+ filters),
            "_report_Opened/Approved": Q(where=[approvedApps]+ filters)
        }

'''
PennState Student Banking Reports - Line
'''
def pennStateStudentBankingReportsLine(params,start_date,end_date):
    intervals = get_list_of_months_between(start_date, end_date)
    variant = params.get("variant", "Started")
    ret = {
        "labels": [],
        "datasetMap": {
            f"{variant}": []
        }
    }
    
    

    for interval in intervals:
        month_label = get_header(interval)["label"].replace("-", " ")
        filters = [CorBFilter(params.get("CorBFilter", "All")), get_date_filter(
                interval['start_date'],
                interval['end_date']
            )] + COMMON_FILTERS

        if variant == "Started":
            filters = filters + [startedApps]
            
        if variant == "Submitted":
            filters = filters + [submittedApps]
            
        if variant == "Opened/Approved":
            filters = filters + [approvedApps]

        ret["labels"].append(month_label)
        ret["datasetMap"][variant].append(Q(columns=[countColumn], where=filters))
    
    return ret
            
            