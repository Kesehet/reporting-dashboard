from metrics import update_metrics, update_metrics_from_sql
from report_modules.condition_utils import *
from DB import get_EDW
import concurrent.futures
import sys


def post_process_txns(sql,txn):
    sql.execute(f'''UPDATE [DigitalReport].[dbo].[Transactions] SET APPLICATION_TYPE = 'Online' WHERE (APPLICATION_TYPE IS NULL OR TRIM(APPLICATION_TYPE) = '') AND AppStartDate < '2025-04-09';''')
    
    update_metrics_from_sql("bot_users", txn,
                '''     SELECT TOP 10
                            PrimaryName,
                            COUNT(*) AS SeenCount
                        FROM 
                            [DigitalReport].[dbo].[Transactions]
                        WHERE 
                            AppStartDate >= DATEADD(DAY, -15, GETDATE())
                        GROUP BY 
                            PrimaryName
                        HAVING 
                            COUNT(*) > 100
                        ORDER BY 
                            SeenCount DESC;
                '''
                            )


    all_app_status_filter = ','.join([f'\'{app}\'' for app in ALL_APP_STATUS])
    update_metrics_from_sql(
        "new_app_statuses",txn,
        f'''    Select DISTINCT AppStatus
                From [DigitalReport].[dbo].[Transactions]
                Where  AppStatus NOT IN ({all_app_status_filter});
        '''
    )


    product_set_ids = txn.get_transactions_by_sql_query('''
        select distinct(ProductSetId) from [DigitalReport].[dbo].[Transactions];
    ''')
    all_product_set_id = [int(psi) for psi, pss in ALL_PRODUCT_SET_ID]
    
    new_product_set_ids = []
    for psi in product_set_ids:
        psi = psi.get("ProductSetId")
        if psi is None:
            continue
        if psi.find("|"):
            psis  = psi.split('|')
            for psiB in psis:
                if psiB == "" or psiB is None:
                    continue
                psiB = int(float(psiB))
                if psiB not in new_product_set_ids and psiB not in all_product_set_id:
                    new_product_set_ids.append(psiB)
        else:
            if psi == "" or psi is None:
                continue
            psi = int(psi)
            if psi not in new_product_set_ids and psi not in all_product_set_id:
                new_product_set_ids.append(psi)
    new_product_set_ids = sorted(new_product_set_ids)

    update_metrics(
        "new_product_set_id",
        new_product_set_ids
    )


    
    promocodes  = txn.get_transactions_by_sql_query('''
        Select PromoCodes FROM [DigitalReport].[dbo].[Transactions] where PromoCodes is not NULL and PromoCodes != ''
    ''')
    new_promocodes = []
    for pc in promocodes:        
        pc = pc.get("PromoCodes")
        if pc is None:
            continue
        pc = pc.strip("|")
        
        if pc.find("|"):
            pcs  = pc.split('|')
            for pcB in pcs:
                pcB = pcB.strip()
                pcB = pcB.lstrip("|")
                if pcB == "" or pcB is None:
                    continue
                if pcB not in new_promocodes and pcB not in ALL_PROMOCODES:
                    new_promocodes.append(pcB)
        else:
            pc = pc.lstrip("|")
            if pc == "" or pc is None:
                continue
            if pc not in new_promocodes and pc not in ALL_PROMOCODES:
                new_promocodes.append(pc)
    new_promocodes = sorted(new_promocodes)

    update_metrics(
        "new_promocodes",
        new_promocodes
    )

    update_metrics_from_sql(
        "new_application_types",
        txn,
        ''' select distinct(APPLICATION_TYPE) from [DigitalReport].[dbo].[Transactions] 
            where APPLICATION_TYPE is not NULL and APPLICATION_TYPE != ''
            and APPLICATION_TYPE NOT IN ('''+ ','.join([f'\'{app}\'' for app in ALL_APPLICATION_TYPES]) +''');'''
    )

    # Post processing to get all account numbers from EDW
    all_ecatrackingCodes_with_null_accounts = txn.get_transactions_by_sql_query(f'''
        select eCATrackingCode from [DigitalReport].[dbo].[Transactions] where NumLendingProducts > 0 order by AppStartDate Desc
    ''')
    list_of_tc = [tc.get("eCATrackingCode") for tc in all_ecatrackingCodes_with_null_accounts]
    update_account_numbers(list_of_tc, sql)




def process_tc(tc, sql):
    accNoObj = get_EDW(tc, join_columns=["AccountNumber", "mt.APPID"])
    if accNoObj is None:
        return (tc, None)
    accNo = accNoObj.get("AccountNumber")
    appid = accNoObj.get("APPID")
    
    if accNo is None:
        return
    sql.execute(f'''
        UPDATE [DigitalReport].[dbo].[Transactions] SET EDW_APPID = '{appid}' WHERE eCATrackingCode = '{tc}'
    ''')
    sql.connection.commit()
    return (tc, accNo)

def update_account_numbers(list_of_tc, sql):
    print("Updating account numbers")
    ctr = 0
    runs = 0

    for tc in list_of_tc:
        runs += 1
        sys.stdout.write(f"\r{int((runs / len(list_of_tc)) * 100)}% - {ctr}/{len(list_of_tc)} account numbers pulled. - {runs}")
        sys.stdout.flush()
        resp = process_tc(tc, sql)
        if resp is None:
            continue
        tc, accNo = resp
        if accNo:
            ctr += 1
        


