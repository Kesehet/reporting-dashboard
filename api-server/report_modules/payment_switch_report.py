from DB import Q
from report_modules.condition_utils import *

def get_payment_switch_insight(start_date, end_date, params):
    common_filters = [
        get_date_filter(start_date, end_date),
        excludeZeroProductApps,
        bot_filter(25),
        paymentSwitchFilter
    ]
    return { 
        "Total Payment Switches": Q(columns=[countColumn], where=common_filters, queryOnly=True, params=params),
        "_report_Total Payment Switches": Q(columns=["AccountNumber","PaymentSwitchStatus","PaymentSwitchMethod"]+COMMON_EXPORT_COLUMNS, where=common_filters, queryOnly=True, params=params),
    }