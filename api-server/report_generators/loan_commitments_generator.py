from datetime import datetime
from dateutil.relativedelta import relativedelta
from DB import Q, SQLConn, Transaction
from report_modules.condition_utils import *
from report_modules.edw_condition_utils import *
import pandas as pd
import os
    


def get_opened_approved(start_date, end_date, params={}):
    common_filters = [get_date_filter(start_date,end_date), application_type_filter(params.get("application_type", ""))]
    

    submitted_conditions = [SUBMITTED_FOR_LOAN_COMMITMENT_FILTER] + common_filters
    submitted_query_all = Q(where=submitted_conditions, params=params)

    
    sql = SQLConn(kind="CRFEDW")
    sql.connect()
    txn = Transaction(sql_conn=sql)
    tids = []
    if submitted_query_all == 0:
        return []
    for row in submitted_query_all: #submitted_query_all:
        tids.append(row.get("eCATrackingCode"))
        
    tids = ','.join([f'\'{tid}\'' for tid in tids])
    Opened_Approved_query_all = f"""
            SELECT DISTINCT
                app.APPID,
                app.APPDETAILID,
                app.ApplicationStart,
                app.ProductShortName,
                app.ProductGrouping,
                app.DecisionStatusName,
                app.AmountRequested,
                app.AccountNumber,
                rc.Name as DecisionReason,
                temp.Temenos_ID
            FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR] AS app
            LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMFIELDS_CUR] as temp
                ON temp.APPID = app.APPID
            LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_DECLINES_CUR] AS dc
                ON app.APPID = dc.APPID
            LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_REASONMASTER_CUR] AS rc
                ON rc.ReasonID = dc.ReasonID
                where temp.Temenos_ID is not null and temp.Temenos_ID != '' and temp.Temenos_ID IN ({tids}) and app.DecisionStatusName = 'Approved'
            """
    resp = txn.get_transactions_by_sql_query(Opened_Approved_query_all)
    if resp == 0:
        Opened_Approved_query_all = []
    else:
        Opened_Approved_query_all = resp

    all_application_type_list =  Q(columns=["Application_Type", "eCATrackingCode"], where=[f"eCATrackingCode IN ({tids}) "], params=params)
    all_application_type_dict = {}
    for row in all_application_type_list:
        all_application_type_dict[row.get("eCATrackingCode")] = row.get("Application_Type")
    
    unique_query_by_tracking_code = {}
    for obj in Opened_Approved_query_all:
        if unique_query_by_tracking_code.get(obj["Temenos_ID"], None) == None:
            obj["ApplicationType"] = all_application_type_dict.get(obj["Temenos_ID"])
            unique_query_by_tracking_code[obj["Temenos_ID"]] = obj
        elif obj["DecisionReason"] != None and obj["DecisionReason"] != "":
            unique_query_by_tracking_code[obj["Temenos_ID"]]["DecisionReason"] += ", " + obj["DecisionReason"]

    
    Opened_Approved_query_all = list(unique_query_by_tracking_code.values())
        
    sql.disconnect()

    return Opened_Approved_query_all

def get_other_app_status(start_date, end_date, params={}):
    common_filters = [get_date_filter(start_date,end_date), application_type_filter(params.get("application_type", ""))]
    return Q(columns=[
        "eCATrackingCode",
        "AppStartDate",
        "AppStatus",
        "BranchID",
        "BranchContactPerson",
        "BranchContactPhone",
        "APPLICATION_TYPE",
        "EmployeeResponsibilityCode",
        "NMLS_Id",
        "AccountNumber",
        "EDW_APPID"
        ], where=[
                "AppStatus IN ('Loans Approved Queue','Loans and Deposits Approved Queue')", 
                  "AccountNumber IS NOT NULL AND AccountNumber NOT IN ('|','') "] + common_filters,
        debug=True,
        params=params
    ) 


def loan_commitments_reports_job(BASE_URL, API_KEY):    
    start_date = "2022-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    old_list = get_opened_approved(start_date, end_date, {"application_type": ""})
    new_list = get_other_app_status(start_date, end_date, {"application_type": ""})

    if new_list == 0:
        new_list = []
    if old_list == 0:
        old_list = []
    
    for app in new_list:
        old_list.append(
            {
                "Temenos_ID": app["eCATrackingCode"],
                "ApplicationStart": app["AppStartDate"],
                "DecisionStatusName": app["AppStatus"],
                "ApplicationType": app["APPLICATION_TYPE"],
                "AccountNumber": app["AccountNumber"],
                "APPID": app["EDW_APPID"],
                
            }
        )
    report_folder = "Loan Commiments Report"
    os.makedirs(report_folder,exist_ok=True)
    txt_destination = f"{report_folder}/Loan Report.txt"
    df = pd.DataFrame(old_list)
    # filter out duplicates based on Temenos_ID
    df = df.drop_duplicates(subset=["Temenos_ID"], keep="first")
    if os.path.exists(txt_destination):
        os.remove(txt_destination)
    df.to_csv(txt_destination, index=False, sep ="\t")
    