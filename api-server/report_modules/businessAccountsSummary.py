from DB import Q, SQLConn, Transaction
from report_modules.condition_utils import *
from utils import *
from report_modules.edw_condition_utils import *
from DB import  Transaction, SQLConn


# Select * from Transactions where eCATrackingCode like 'B-%' 
# Select Initial_Deposit, Current_Balance from CAMEDW where DDA_ACCT_NUM IN (B-% accpunt numbers )


# table - 2 one user has mulitplt accounts - we have to display all the accounts of the user - sum up initila and curremt balance amounts for the same along with net amount - one table 
#table 1 - number of apps - with loan/deposits/multi/single product/multi-produtc and promocodes/cross sell - along with what proimo or  cross sell was provided to the user
# table - 3 - top 5 brances in terms of highets num of apps - along withbranch id, num of apps - and breakdown of apps in terms of product description
# table 4 - top 10 products along with product code , num of products and product description

# along with this we need a insight to export the whole data - b-% tracking code extract from transactions along with initial and final deposit amounts from EDW and product description column

def get_number_of_apps_by_product_type(start_date, end_date, extraConditions = [], label = None):    
    intervals = get_list_of_months_between(start_date, end_date)
    resp = {
        "headers": ["-"],
        "rows": [
            [f"{label} Promo Code"],
            [f"Single Product {label} Applications"],
            [f"Multi Product {label} Applications"],
            [f"Deposit Product {label} Applications"],
            [f"Lending Product {label} Applications"],
            [f"Mixed Product {label} Applications"],
            [f"Online {label} Applications"],
            [f"Banker Assisted {label} Applications"],
            [f"Total {label} Applications"]
        ]
    }
    for interval in intervals:
        resp["headers"].append(get_header(interval)["label"])
        common_conditions =[
            isBusinessTxn,
            in_between_sql_condition(interval),
            excludeBotData,
            excludeZeroProductApps
        ] + extraConditions
        # Promo Code count
        resp["rows"][0].append(
            Q(
                columns=[countColumn],                
                where= common_conditions + [                    
                    hasPromoCode
                ],
                queryOnly=True
            )
        )
        # Single Product Application
        resp["rows"][1].append(
            Q(
                columns=[countColumn],
                where= common_conditions + [                    
                    singleApps
                ],
                queryOnly=True
            )
        )
        # Multi Product Application
        resp["rows"][2].append(
            Q(
                columns=[countColumn],
                where= common_conditions + [                    
                    multiApps
                ],
                queryOnly=True
            )
        )
        # Deposit Product Application
        resp["rows"][3].append(
            Q(
                columns=[countColumn],
                where= common_conditions + [                    
                    depositApps
                ],
                queryOnly=True
            )
        )
        # Lending Product Application
        resp["rows"][4].append(
            Q(
                columns=[countColumn],
                where= common_conditions + [                    
                    loanApps
                ],
                queryOnly=True
            )
        )
        # Mixed Product Application
        resp["rows"][5].append(
            Q(
                columns=[countColumn],
                where= common_conditions + [                    
                    mixedApps
                ],
                queryOnly=True
            )
        )
        # Online Applications
        resp["rows"][6].append(
            Q(
                columns=[countColumn],
                where= common_conditions + [                    
                    application_type_filter("Online")
                ],
                queryOnly=True
            )
        )
        # Banker Assisted Applications
        resp["rows"][7].append(
            Q(
                columns=[countColumn],
                where= common_conditions + [                    
                    application_type_filter("Banker Assisted")
                ],
                queryOnly=True
            )
        )
        # Total Applications
        resp["rows"][8].append(
            """<b class='greyed_out'>"""+
            str(Q(
                columns=[countColumn],
                where= common_conditions,
                
            )) + """</b> 
            """
        )


    return resp

def get_number_of_apps_by_product_type_summarized(start_date, end_date, params=None):
    table_1 = get_number_of_apps_by_product_type(start_date, end_date, extraConditions=[startedApps], label="Started")
    table_2 = get_number_of_apps_by_product_type(start_date, end_date, extraConditions=[submittedApps], label="Submitted")
    table_3 = get_number_of_apps_by_product_type(start_date, end_date, extraConditions=[approvedApps], label="Opened/Approved")
    combined_rows = table_1["rows"] + table_2["rows"] + table_3["rows"]
    return {
        "headers": table_1["headers"],
        "rows": combined_rows
    }
    
def get_top_10_products(start_date, end_date, params=None):
    resp = {
        "headers": ["Product Description", "Product Code", "Number of Applications"],
        "rows": []
    }

    all_counts = {}
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    for product_set_ids in get_all_product_set_ids(txn, "B"):
        product_id = product_set_ids
        count = get_product_count(product_id, start_date, end_date)
        all_counts[product_id] = count
    sql.disconnect()
    # remove duplicates and sort by count and get top 10
    sorted_products = sorted(all_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for product_id, count in sorted_products:
        product_id = str(product_id)
        if product_id.endswith(".0"):
            product_id = product_id[:-2]
        resp["rows"].append(
            [
                get_product_name(product_id),
                product_id,
                count
            ]
        )
    return resp

def get_top_10_branches(start_date, end_date, params=None):
    resp = {
        "headers": ["Branch ID", "Number of Applications", "Product Description Breakdown"],
        "rows": [
            
        ]
    }
    # Get top 10 branches by number of applications
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    common_conditions = [
        in_between_sql_condition({
            "start_date": start_date,
            "end_date": end_date
        }),
        excludeBotData,
        excludeZeroProductApps,
        isBusinessTxn
    ]
    # sql_query = f'''        
    # SELECT TOP 10
    #        BranchId AS BranchId,
    #        COUNT(DISTINCT eCATrackingCode) AS DistinctECACount
    # FROM [DigitalReport].[dbo].[Transactions]
    # WHERE 
    #     BranchId IS NOT NULL
    #     AND BranchId <> ''
    #     AND {" AND ".join(common_conditions)}
    # GROUP BY BranchId
    # ORDER BY COUNT(DISTINCT eCATrackingCode) DESC;
    # '''
    # Get all branch ids and then get counts for each branch and sort in python 
    # since number of branches are not that high and it will give us the flexibility to do 
    # product breakdown for each branch without having to do complex SQL queries
    all_branches = get_all_branch_ids(txn, 'B')
    top_10_branches = []
    for branch in all_branches:
        all_product_count = 0
        for product_set_ids in get_all_product_set_ids(txn, "B"):
            product_id = product_set_ids
            count = get_product_count(product_id, start_date, end_date, extraConditions=[f"BranchId = '{branch}'"])
            all_product_count += count
        top_10_branches.append({
            "BranchId": branch,
            "DistinctECACount": all_product_count
        })
    top_10_branches = sorted(top_10_branches, key=lambda x: x["DistinctECACount"], reverse=True)[:10]

    
    countColumn = "DistinctECACount"
    for branch in top_10_branches:
        branch_id = branch["BranchId"]
        app_count = branch[countColumn]
        product_breakdown = get_product_breakdown_by_branch(branch_id, start_date, end_date, txn)
        breakdown_str = " <hr/> ".join([f"(<b>{product_id}</b>) {get_product_name(product_id)}: {count}" for product_id, count in product_breakdown.items()])
        resp["rows"].append([branch_id, app_count, breakdown_str])
    sql.disconnect()
    return resp

def get_product_breakdown_by_branch(branch_id, start_date, end_date, txn):
    ret = {}
    for product_set_ids in get_all_product_set_ids(txn, "B"):
        product_id = product_set_ids
        count = get_product_count(product_id, start_date, end_date, extraConditions=[f"BranchId = '{branch_id}'"])
        if count > 0:
            ret[product_id] = count
    # Sort by count
    ret = dict(sorted(ret.items(), key=lambda x: x[1], reverse=True))
    return ret

def get_current_balance_and_initial_deposit(start_date, end_date, params=None):
    resp = {
        "headers": ["-"],
        "rows": [
            ["<h4>Deposit</h4>"], # 0
            ["Initial Deposit"], # 1
            ["Current Balance"], # 2
            ["Net Amount (Current Balance - Initial Deposit)"], # 3
            ["<h4>Loan</h4>"], # 4
            ["Number of Loan Applications"], # 5
            ["Amount Financed"], # 6
            ["Number of Secured Loan Applications"], # 7
            ["Amount Financed for Secured Loans"], # 8
            ["Number of Unsecured Loan Applications"], # 9
            ["Amount Financed for Unsecured Loans"], # 10
            
        ]
    }
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    crf_edw_sql = SQLConn('CRFEDW')
    crf_edw_sql.connect()
    txn_crf_edw = Transaction(crf_edw_sql)
    pty_edw_sql = SQLConn('PTYEDW')
    pty_edw_sql.connect()
    txn_pty_edw = Transaction(pty_edw_sql)
    cam_edw_sql = SQLConn('CAMEDW')
    cam_edw_sql.connect()
    txn_cam_edw = Transaction(cam_edw_sql)

    

    intervals = get_list_of_months_between(start_date, end_date)
    for interval in intervals:
        initial_deposit_current_balance_sums_response = []
        amt_financed = []

        resp["headers"].append(get_header(interval)["label"])
        tax_numbers_or_ssn_loan_apps = Q(columns=['PrimarySSN'], where=[
            isBusinessTxn,
            approvedApps,
            excludeBotData,
            excludeZeroProductApps,
            loanApps,
            in_between_sql_condition({"start_date": interval["start_date"], "end_date": interval["end_date"]})
        ])
        if tax_numbers_or_ssn_loan_apps == 0:
            tax_numbers_or_ssn_loan_apps = []

        tax_numbers_or_ssn_deposit_apps = Q(columns=['PrimarySSN'], where=[
            isBusinessTxn,
            approvedApps,
            excludeBotData, 
            excludeZeroProductApps,
            depositApps,
            in_between_sql_condition({"start_date": interval["start_date"], "end_date": interval["end_date"]})
        ])
        if tax_numbers_or_ssn_deposit_apps == 0:
            tax_numbers_or_ssn_deposit_apps = []
        # SELECT ACCT_NUM FROM [PTYEDW].[PTY_EMPL_PII_V2].[PTYMSTR_DDA] where TAX_ID IN ()
        # SELECT APPID, SSN FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMER_CUR] where SSN IN ()

        # Group tax numbers  or ssn to minimize the number of queries to EDW batch size is 500 for IN clause - we can optimize further by doing a join in EDW but for now we will do it in batches of 500
        loan_apps_tax_numbers_or_ssn = group_txns(tax_numbers_or_ssn_loan_apps, 500)
        deposit_apps_tax_numbers_or_ssn = group_txns(tax_numbers_or_ssn_deposit_apps, 500)
                

        
        for group in loan_apps_tax_numbers_or_ssn:
            
            sql_query_2 = f'''
            SELECT APPID FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMER_CUR] where SSN IN ({','.join(["'{}'".format(s['PrimarySSN'].replace('-','')) for s in group])})
            '''
            app_results = txn_crf_edw.get_transactions_by_sql_query(sql_query_2)
            if app_results == 0:
                app_results = []
            
            amt_financed_ = f'''
                SELECT TOP (1000) [APPID], [AmountFinanced], ProductGrouping as name FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR] Where 
                APPID in ({','.join(["'{}'".format(app["APPID"]) for app in app_results])})
                '''
            amt_financed = txn_crf_edw.get_transactions_by_sql_query(amt_financed_)
            if amt_financed == 0:
                amt_financed = []
            

            

            
            
        for group in deposit_apps_tax_numbers_or_ssn:
            
            sql_query_2 = f'''
            SELECT ACCT_NUM FROM [PTYEDW].[PTY_EMPL_PII_V2].[PTYMSTR_DDA] where TAX_ID IN  ({','.join(["'{}'".format(s['PrimarySSN'].replace('-','')) for s in group])})
            '''
            app_results = txn_pty_edw.get_transactions_by_sql_query(sql_query_2)
            if app_results == 0:
                app_results = []
            
            initial_deposit_current_balance_sums_ = f'''
                SELECT SUM([Initial_Deposit]) as Initial_Deposit, SUM([Current_Balance]) as Current_Balance FROM [CAMEDW].[CAM_EMPL_PII_V1].[CAM_DDA_ACCT_CUR] where DDA_ACCT_NUM IN ({','.join(["'{}'".format(acct["ACCT_NUM"]) for acct in app_results])})
                '''
            initial_deposit_current_balance_sums_response = txn_cam_edw.get_transactions_by_sql_query(initial_deposit_current_balance_sums_)
            if initial_deposit_current_balance_sums_response == 0:
                initial_deposit_current_balance_sums_response = []
            
        initial_deposit = 0
        current_balance = 0
        for res in initial_deposit_current_balance_sums_response:
            initial_deposit += res["Initial_Deposit"] if res["Initial_Deposit"] is not None else 0
            current_balance += res["Current_Balance"] if res["Current_Balance"] is not None else 0
            
        resp["rows"][1].append(DOLLAR_SIGN + f"{initial_deposit:,.2f}")
        resp["rows"][2].append(DOLLAR_SIGN + f"{current_balance:,.2f}")
        resp["rows"][3].append(DOLLAR_SIGN + f"{current_balance - initial_deposit:,.2f}")

        amt_financed_sum = 0
        unsecured_amt_financed_sum = 0
        secured_amt_financed_sum = 0
        ctr_all = 0
        ctr_secured = 0
        ctr_unsecured = 0
        for res in amt_financed:
            amt_financed_sum += res["AmountFinanced"] if res["AmountFinanced"] is not None else 0
            ctr_all += 1
            if res["name"] in SECURED_PRODUCT_GROUPINGS:
                secured_amt_financed_sum += res["AmountFinanced"] if res["AmountFinanced"] is not None else 0
                ctr_secured += 1
            elif res["name"] in UNSECURED_PRODUCT_GROUPINGS:
                unsecured_amt_financed_sum += res["AmountFinanced"] if res["AmountFinanced"] is not None else 0
                ctr_unsecured += 1

        resp["rows"][5].append(ctr_all)
        resp["rows"][6].append(DOLLAR_SIGN + f"{amt_financed_sum:,.2f}")
        resp["rows"][7].append(ctr_secured)
        resp["rows"][8].append(DOLLAR_SIGN + f"{secured_amt_financed_sum:,.2f}")
        resp["rows"][9].append(ctr_unsecured)
        resp["rows"][10].append(DOLLAR_SIGN + f"{unsecured_amt_financed_sum:,.2f}")



    sql.disconnect()
    crf_edw_sql.disconnect()
    pty_edw_sql.disconnect()
    cam_edw_sql.disconnect()
    return resp




def get_product_count(product_id, start_date = None, end_date = None, extraConditions = []):
    ret = 0
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    product_id = product_id.replace(".0", "") 

    common_conditions = [
        in_between_sql_condition({
            "start_date": start_date,
            "end_date": end_date
        }),
        excludeBotData,
        excludeZeroProductApps,
        isBusinessTxn
    ] + extraConditions

    sql_query = f'''SELECT 
       ProductSetId as ProductId,
       COUNT(DISTINCT eCATrackingCode) AS DistinctECATrackingCodeCount
        FROM [DigitalReport].[dbo].[Transactions]
        WHERE ProductSetId IS NOT NULL
        AND ProductSetId <> ''
        AND (ProductSetId = '{product_id}'
        OR ProductSetId = '{product_id}.0')
        AND {" AND ".join(common_conditions)}
        GROUP BY ProductSetId
        ORDER BY COUNT(DISTINCT eCATrackingCode) DESC;
    '''
    # remove repeated AND if any ..
    sql_query = sql_query.replace(" AND  AND ", " AND ")
    result = txn.get_transactions_by_sql_query(sql_query)
    if result == 0:
        return 0
    for row in result:        
        
        for all_products in process_product_id(row["ProductId"]):
            if try_int(all_products) == try_int(product_id):
                print(f"Product ID: {product_id}, Count: {row['DistinctECATrackingCodeCount']}, ret: {ret}")
                ret = ret + try_int(row["DistinctECATrackingCodeCount"])
                
    sql.disconnect()
    return ret