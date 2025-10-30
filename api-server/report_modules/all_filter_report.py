from report_modules import condition_utils
from DB import Q

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
    all_filters = [condition_utils.get_date_filter(start_date,end_date), ecaFilter]
    available_filters = list(get_module_variables().keys())
    filters = filters.split(",")
    for f in filters:
        if f in available_filters:
            all_filters.append(get_module_variables().get(f))
    resp = Q(where=all_filters)
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

