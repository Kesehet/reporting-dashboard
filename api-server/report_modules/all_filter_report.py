from report_modules.condition_utils import *
from report_modules import condition_utils
from DB import Q
from utils import get_list_of_months_between, get_header


def get_module_variables():
    # vars(module) gives you the modules __dict__
    all_items = vars(condition_utils)
        
    variables = {
        k: v for k, v in all_items.items()
        if isinstance(v, str)
        and not k.startswith("__")    # skip built-ins
        # and not callable(v)          # skip functions
        # and not isinstance(v, type)  # skip classes
        # and not isinstance(v, type(condition_utils))  # skip submodules
        # and not isinstance(v, list)
        # and not isinstance(v, dict)
        }
    return variables

def get_filters(start_date, end_date, ecaFilter, filters:str, return_format="json"):
    all_filters = [get_date_filter(start_date,end_date), ecaFilter]
    available_filters = list(get_module_variables().keys())
    filters = filters.split(",")
    for f in filters:
        if f in available_filters:
            all_filters.append(get_module_variables().get(f))
    resp = Q(where=all_filters)
    print(Q(where=all_filters, queryOnly=True))
    if resp == 0:
        return {"headers":[],"rows":[]}
    if return_format == "csv":
        headers = ','.join(list(resp[0].keys()))
        rows = ['{}'.format(','.join(map(str, row.values()))) for row in resp]
        return '\n'.join([headers] + rows)
    return {
        "headers": [header for header in list(resp[0].keys())],
        "rows": [list(row.values()) for row in resp], 
    }

def all_bot_deduped_data_monthly_insights(start_date, end_date, params):
    intervals = get_list_of_months_between(start_date, end_date)
    resp = {}
    for interval in intervals:
        month_label = get_header(interval)["label"].replace("-", " ")
        common_filters = [bot_filter(), CorBFilter(params.get("CorBFilter", "All")), get_date_filter(
                interval['start_date'],
                interval['end_date']
            ), excludeZeroProductApps]
        resp["Month " + month_label] = Q( columns=[countColumn], where=common_filters, params=params)
        
        resp["_report_Month " + month_label] = Q(columns=COMMON_EXPORT_COLUMNS,where=common_filters, params=params)
    
    return resp