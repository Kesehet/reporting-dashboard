from DB import Q
from report_modules.condition_utils import *
from utils import *

def application_volume_by_product_current_quarter_all_submitted_apps_pie(start_date,end_date,params):
    ecaTrackingCodeFilter = CorBFilter(params.get("eCATrackingCode", "All"))
    common_filters = [excludeBotData,submittedApps,currentQuarter, startedApps, ecaTrackingCodeFilter]
    return {
            "labels": [
                "Loan Product Apps",
                "Deposit Product Apps",
                "Mixed product Apps",
            ],
            "list": [
                Q(columns=[countColumn], where=[loanApps]+common_filters, params=params),
                Q(columns=[countColumn], where=[depositApps]+common_filters, params=params),
                Q(columns=[countColumn], where=[mixedApps]+common_filters,params=params)                
            ]
        }

def get_custom_quarterly_analytics_common_app_table(start_date, end_date, params):
    quarters = params.get("quarters", [])
    
    # Sort quarters by year and quarter
    quarters.sort(key=lambda x: (x['year'], x['quarter']))


    productColumn = " SUM(NumLendingProducts + NumDepositProducts) as data"
    ecaTrackingCodeFilter = CorBFilter(params.get("eCATrackingCode", "All"))
    common_filters = [excludeBotData, startedApps, ecaTrackingCodeFilter]
    resp = {
        "headers": ["Overall Common App Metrics"],
        "rows": [

                ["Common App Started applications"],
                ["Common App Started Deposits | Loans | Mixed products"],
                ["Common App Submitted applications"],  
                ["Common App Submitted Deposits | Loans | Mixed products"],
                ["Common App approved/opened applications"],
                ["Common App approved/opened Deposits | Loans | Mixed products"],
                
                ["Common App Started multi product applications | Single Product Applications"],
                ["Common App Submitted multi product applications | Single Product Applications"],
                ["Common App Opened/Approved multi product applications | Single Product Applications"],
                ["CrossSell Started Presented | Accepted | Acceptance Rate "],
                ["CrossSell Submitted Presented | Accepted | Acceptance Rate "],
                ["CrossSell Opened/Approved Presented | Accepted | Acceptance Rate "]

            ]
    }
    for quarter in quarters:
        quarter_dates = get_start_date_and_end_date_of_given_quarter(quarter['year'], quarter['quarter'])
        date_filter = get_date_filter(quarter_dates['start_date'], quarter_dates['end_date'])

        resp["rows"][0].append(Q(columns=[countColumn], where=common_filters+[date_filter, startedApps]))
        resp["rows"][1].append(
            f"""
            {format_number(try_int(Q(columns=["SUM(NumDepositProducts) as data"], where=common_filters+[date_filter, depositApps])))}  |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts) as data"], where=common_filters+[date_filter, loanApps])))} |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, mixedApps])))} 
            """
            )
        resp["rows"][2].append(Q(columns=[countColumn], where=common_filters+[date_filter, submittedApps]))
        resp["rows"][3].append(
            f"""
            {format_number(try_int(Q(columns=["SUM(NumDepositProducts) as data"], where=common_filters+[date_filter, depositApps, depositSubmittedApps])))}  |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts) as data"], where=common_filters+[date_filter, loanApps, loanSubmittedApps])))} |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, mixedApps, submittedApps ])))} 
            """
            )
        resp["rows"][4].append(Q(columns=[countColumn], where=common_filters+[date_filter, approvedApps]))
        resp["rows"][5].append(
            f"""
            {format_number(try_int(Q(columns=["SUM(NumDepositProducts) as data"], where=common_filters+[date_filter, depositApps, approvedApps])))}  |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts) as data"], where=common_filters+[date_filter, loanApps, approvedApps])))} |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, mixedApps, approvedApps])))} 
            """
            )
        
        resp["rows"][6].append(
            f"""
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, multiApps])))}  |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, singleApps])))}
            """
            )
        resp["rows"][7].append(
            f"""
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, multiApps, submittedApps])))}  |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, singleApps, submittedApps])))}
            """
            )
        resp["rows"][8].append(
            f"""
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, multiApps, approvedApps])))}  |
            {format_number(try_int(Q(columns=["SUM(NumLendingProducts+NumDepositProducts) as data"], where=common_filters+[date_filter, singleApps, approvedApps])))}
            """
            )
        
        resp["rows"][9].append(
            f"""
            {format_number(try_int(Q(columns=[countColumn], where=common_filters+[date_filter, crossSellPresented])))}  |
            {format_number(try_int(Q(columns=[countColumn], where=common_filters+[date_filter, crossSellAccepted])))} |
            {format_number(Q(columns=[crossSellAcceptanceRateColumn], where=common_filters+[date_filter, crossSellPresented]))} %
            """
        )

        resp["rows"][10].append(
             f"""
            {format_number(try_int(Q(columns=[countColumn], where=common_filters+[date_filter, crossSellPresented, submittedApps])))}  |
            {format_number(try_int(Q(columns=[countColumn], where=common_filters+[date_filter, crossSellAccepted, submittedApps])))} |
            {format_number(Q(columns=[crossSellAcceptanceRateColumn], where=common_filters+[date_filter, crossSellPresented, submittedApps ]))} %
            """
            )
        
        resp["rows"][11].append(
             f"""
            {format_number(try_int(Q(columns=[countColumn], where=common_filters+[date_filter, crossSellPresented, approvedApps])))}  |
            {format_number(try_int(Q(columns=[countColumn], where=common_filters+[date_filter, crossSellAccepted, approvedApps])))} |
            {format_number(Q(columns=[crossSellAcceptanceRateColumn], where=common_filters+[date_filter, crossSellPresented, submittedApps ]))} %
            """
        )

        resp["headers"].append(f"{quarter['quarter']}-{quarter['year']}")

    # b-a/a
    # for i in range(len(resp["rows"])):
    #     r = resp["rows"][i]
    #     for j in range(1, len(r)):
    #         a = try_int(r[j-1])
    #         b = try_int(r[j])
    #         if a == 0 or a == None or type(a) == str or type(b) == str or b == None or b == 0:
    #             continue
    #         else:
    #             resp["rows"][i].append(str(round((b - a)/a * 100, 2)) + " %")
    # resp["headers"].append(f"% Change")
 
    return resp


def get_custom_quarterly_analytics_customer_eCA_table(start_date, end_date, params):
    quarters = params.get("quarters", [])
    
    # Sort quarters by year and quarter
    quarters.sort(key=lambda x: (x['year'], x['quarter']))

    ecaTrackingCodeFilter = CorBFilter(params.get("eCATrackingCode", "All"))
    common_filters = [excludeBotData, startedApps, ecaTrackingCodeFilter, application_type_filter("Online") ]
    resp = {
        "headers": ["Online Customer-Facing Common App Metrics"],
        "rows": [
                ["Customer eCA Common App submitted applications"],
                ["Customer eCA Common App approved/opened applications"],
            ]
    }
    for quarter in quarters:
        quarter_dates = get_start_date_and_end_date_of_given_quarter(quarter['year'], quarter['quarter'])
        date_filter = get_date_filter(quarter_dates['start_date'], quarter_dates['end_date'])
        
        resp["rows"][0].append(Q(columns=[countColumn], where=common_filters+[date_filter, submittedApps]))
        resp["rows"][1].append(Q(columns=[countColumn], where=common_filters+[date_filter, approvedApps]))


        resp["headers"].append(f"{quarter['quarter']}-{quarter['year']}")

    # b-a/a
    # for i in range(len(resp["rows"])):
    #     r = resp["rows"][i]
    #     for j in range(1, len(r)):
    #         a = try_int(r[j-1])
    #         b = try_int(r[j])
    #         if a == 0 or a == None or type(a) == str or type(b) == str or b == None or b == 0:
    #             continue
    #         else:
    #             resp["rows"][i].append(str(round((b - a)/a * 100, 2)) + " %")
    # resp["headers"].append(f"% Change")

    return resp

def get_custom_quarterly_analytics_inBranch_common_app_table(start_date, end_date, params):
    quarters = params.get("quarters", [])
    
    # Sort quarters by year and quarter
    quarters.sort(key=lambda x: (x['year'], x['quarter']))

    ecaTrackingCodeFilter = CorBFilter(params.get("eCATrackingCode", "All"))
    common_filters = [excludeBotData, startedApps, ecaTrackingCodeFilter, application_type_filter("Banker Assisted") ]
    resp = {
        "headers": ["In-Branch Common App Metrics"],
        "rows": [
                ["In-Branch Common App submitted applications"],
                ["In-Branch Common App approved/opened applications"],
            ]
    }
    for quarter in quarters:
        quarter_dates = get_start_date_and_end_date_of_given_quarter(quarter['year'], quarter['quarter'])
        date_filter = get_date_filter(quarter_dates['start_date'], quarter_dates['end_date'])

        resp["rows"][0].append(Q(columns=[countColumn], where=common_filters+[date_filter, submittedApps]))
        resp["rows"][1].append(Q(columns=[countColumn], where=common_filters+[date_filter, approvedApps]))

        resp["headers"].append(f"{quarter['quarter']}-{quarter['year']}")

    # b-a/a
    # for i in range(len(resp["rows"])):
    #     r = resp["rows"][i]
    #     for j in range(1, len(r)):
    #         a = try_int(r[j-1])
    #         b = try_int(r[j])
    #         if a == 0 or a == None or type(a) == str or type(b) == str or b == None or b == 0:
    #             continue
    #         else:
    #             resp["rows"][i].append(str(round((b - a)/a * 100, 2)) + " %")
    # resp["headers"].append(f"% Change")

    return resp