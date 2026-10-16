from datetime import datetime
from dateutil.relativedelta import relativedelta

from DB import Q
from report_modules.condition_utils import *
from utils import get_header, get_list_of_months_between, in_between_sql_condition


def _normalize_condition(condition):
    if not condition:
        return ""
    condition = condition.strip()
    if condition.upper().startswith("AND "):
        return condition[4:].strip()
    return condition


def _zero_product_filters(date_filter=None, application_type_condition=""):
    filters = [onlyZeroProductApps, excludeBotData]
    if date_filter:
        filters.append(date_filter)

    normalized_condition = _normalize_condition(application_type_condition)
    if normalized_condition:
        filters.append(normalized_condition)
    return filters


def get_zero_product_apps_bar(application_type_condition="", params=None):
    params = params or {}
    labels = []
    values = []
    current_month = datetime.now().replace(day=1)

    for month_offset in range(-11, 1):
        month_start = current_month + relativedelta(months=month_offset)
        month_end = month_start + relativedelta(months=1, days=-1)
        labels.append(month_start.strftime("%b %Y"))

        date_filter = f"AppStartDate >= '{month_start.strftime('%Y-%m-%d')}' AND AppStartDate <= '{month_end.strftime('%Y-%m-%d')}'"
        values.append(Q(columns=[countColumn], where=_zero_product_filters(date_filter, application_type_condition), params=params))

    return {
        "labels": labels,
        "list": values,
    }


def get_zero_product_apps_reports(start_date, end_date, application_type_condition="", params=None):
    params = params or {}
    intervals = get_list_of_months_between(start_date, end_date)
    headers = ["-"] + [get_header(interval)["label"] for interval in intervals if interval["start_date"] != interval["end_date"]]

    rows = []
    row_definitions = [{
        "label": "No Of Apps",
        "base_filters": [onlyZeroProductApps, excludeBotData],
    }]

    for row in row_definitions:
        current_row = [row["label"]]
        for interval in intervals:
            filters = row["base_filters"] + [in_between_sql_condition(interval)]
            normalized_condition = _normalize_condition(application_type_condition)
            if normalized_condition:
                filters.append(normalized_condition)
            current_row.append(Q(columns=[countColumn], where=filters, params=params))
        rows.append(current_row)

    return {
        "headers": headers,
        "rows": rows,
    }

