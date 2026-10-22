from DB import Q, SQLConn, Transaction
from report_modules.condition_utils import countColumn, get_date_filter, DDS_SUCCESSFUL, DDS_FAILED, ddsFilter, DDS_BACKFILL_SuccessfulSwitch, COMMON_EXPORT_COLUMNS
from utils import get_list_of_months_between, get_header, process_account_number, try_int


def direct_deposit_switch_report_table(start_date, end_date, params):
    intervals = get_list_of_months_between(start_date, end_date)
    resp = {
        "headers": ["-"],
        "rows": [["Successful Switches"],["Failed Switches"],["Conversion Rate"],["Initial Deposits $ Received"], ["Avg Paycheck Amount"], ["Running Total"]]
    }
    running_total = 0
    for interv in intervals:
        isBefore2026 = try_int(interv.get("end_date")[0:4]) < 2026
        if isBefore2026:
            resp_succ = Q(columns=[countColumn], where=[get_date_filter(interv.get("start_date"),interv.get("end_date")), DDS_BACKFILL_SuccessfulSwitch ], params=params)
        else:
            resp_succ = Q(columns=[countColumn], where=[get_date_filter(interv.get("start_date"),interv.get("end_date")), DDS_SUCCESSFUL ], params=params)

        
        resp_fail = Q(columns=[countColumn], where=[get_date_filter(interv.get("start_date"),interv.get("end_date")), DDS_FAILED ], params=params)

        initial_deposits = Q(columns=["SUM(DDSTranAmount) as data"], where=[get_date_filter(interv.get("start_date"),interv.get("end_date")), DDS_SUCCESSFUL], params=params)
        running_total = running_total + initial_deposits
        avg = initial_deposits/resp_succ if resp_succ !=0 else 0
        avg = round(avg,2)
        
        resp["headers"].append(get_header(interv).get("label"))

        resp["rows"][0].append(resp_succ)
        resp["rows"][1].append(resp_fail)
        if (resp_fail+resp_succ) != 0:
            _perc_ = (resp_succ/(resp_fail+resp_succ))*100
        else:
            _perc_ = 0

        resp["rows"][2].append(str(round(_perc_, 2)) + " %")

        resp["rows"][3].append("$ " + format(initial_deposits, ",.2f"))
        resp["rows"][4].append("$ " + format(avg, ",.2f"))
        resp["rows"][5].append("$ " + format(running_total, ",.2f"))


    return resp

def current_total_dds_amount(start_date, end_date, params):
    resp = direct_deposit_switch_report_table(start_date, end_date, params)
    total_number_of_swithces = 0
    current_total_dds_amount = resp["rows"][5][-1]
    for i in range(1, len(resp["headers"])):
        total_number_of_swithces += resp["rows"][0][i]


    
    return {
        "Current Total DDS Amount": current_total_dds_amount,
        "Total Number of Successful Switches": total_number_of_swithces
    }



# Base_URL/charts/Direct%20Deposit%20Switch%20Reports%20Insights?start_date=2025-11-14&end_date=2026-02-12&eCATrackingCode=%25&return_format=csv  (send X-API-KEY in the request header)
def direct_deposit_switch_report_insights(start_date, end_date, params):
    resp = Q(columns=["AccountNumber","DDSAccountLast4","DDSAccountName","DDSAccountType","DDSStatus","DDSTranAmount"]+COMMON_EXPORT_COLUMNS, where=[get_date_filter(start_date, end_date), ddsFilter ], params=params)
    if resp == 0:
        return {"headers":[],"rows":[]}

    
    # Get All Account numbers
    for i in range(len(resp)):
        r = resp[i]
        numbers = process_account_number(r.get("AccountNumber"))
        status = ""
        # Post processing to get all new status'
        if len(numbers) > 0:
            comma_separated = ','.join([str(n) for n in numbers])
            q = f'''
                SELECT Status_Code_Desc as data FROM [CAMEDW].[CAM_EMPL_PII_V1].[CAM_DDA_CODES_CUR] WHERE [DDA_ACCT_NUM] in ({comma_separated})
            '''
            sql = SQLConn("CAMEDW")
            sql.connect()
            txn = Transaction(sql)
            status = txn.get_transactions_by_sql_query(q)
            sql.disconnect()
        resp[i]["Status_Code_Desc"] = status if status != 0 else "Unavailable"
    


    return {
        "Direct Deposit Report": len(resp),
        "_report_Direct Deposit Report": resp
    }