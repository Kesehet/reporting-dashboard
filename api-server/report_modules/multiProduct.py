from DB import Transaction, SQLConn
from report_modules.condition_utils import *




def get_multi_product_cross_sell_report_table(start_date, end_date, ecaTrackingCodeFilter):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
        f"""SELECT TOP 10
                ProductSetId,
                CrossSellProducts,
                COUNT(*) AS TransactionCount,
                SUM(CASE WHEN APPLICATION_TYPE = 'Online' THEN 1 ELSE 0 END) AS OnlineCount,
                SUM(CASE WHEN APPLICATION_TYPE = 'Banker Assisted' THEN 1 ELSE 0 END) AS BankerAssistedCount
            FROM
                {table}
            WHERE
                ProductSetId LIKE '%|%'
                AND {get_date_filter(start_date,end_date)}
                AND {ecaTrackingCodeFilter}
                AND {excludeBotData} AND {excludeZeroProductApps}
                AND CrossSellProducts IS NOT NULL
                AND LTRIM(RTRIM(CrossSellProducts)) <> ''
            GROUP BY
                ProductSetId, CrossSellProducts
            HAVING
                COUNT(*) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    )
    top_10_list = []
    ctr = 1
    for listicle in top_10_dict:
        onlineVsbanker_assisted = str(listicle.get("OnlineCount")) + " / " + str(listicle.get("BankerAssistedCount"))
        top_10_list.append([
            ctr,
            pipe_swap(listicle.get("ProductSetId")), 
            listicle.get("CrossSellProducts"),
            listicle.get("TransactionCount"),
            onlineVsbanker_assisted
        ])
        ctr += 1
    ret =  { 
        "rows": top_10_list,
        "headers": ["SNo", "ProductName", "CrossSellProducts", "TransactionCount", "Online/Banker Assisted"]
    }

    return ret


def get_multi_product_cross_sell_report_bar(start_date, end_date, ecaTrackingCodeFilter):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
        f"""SELECT TOP 10
                ProductSetId,
                CrossSellProducts,
                COUNT(*) AS TransactionCount
            FROM
                {table}
            WHERE
                ProductSetId LIKE '%|%'
                AND {get_date_filter(start_date,end_date)}
                AND {ecaTrackingCodeFilter}
                AND {excludeBotData} AND {excludeZeroProductApps}
                AND CrossSellProducts IS NOT NULL
                AND LTRIM(RTRIM(CrossSellProducts)) <> ''
            GROUP BY
                ProductSetId, CrossSellProducts
            HAVING
                COUNT(*) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    )
    labels = []
    top_10_list = []
    for listicle in top_10_dict:
        labels.append(pipe_swap(listicle.get("ProductSetId")))
        top_10_list.append(listicle.get("TransactionCount"))
    ret =  { 
        "labels": labels,
        "list": top_10_list
    }

    return ret

# Top 10 Single product with Cross Sell Products
def get_single_product_cross_sell_report_bar(start_date, end_date, ecaTrackingCodeFilter):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
        f"""
                

            SELECT TOP 10
                ProductSetId,
                CrossSellProducts,
                COUNT(*) AS TransactionCount
            FROM
                {table}
            WHERE
                ProductSetId NOT LIKE '%|%'
                AND {get_date_filter(start_date,end_date)}
                AND {ecaTrackingCodeFilter}
                AND {excludeBotData} AND {excludeZeroProductApps}
                
                AND CrossSellProducts IS NOT NULL
                AND LTRIM(RTRIM(CrossSellProducts)) <> ''
            GROUP BY
                ProductSetId, CrossSellProducts
            HAVING
                COUNT(*) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    )
    labels = []
    top_10_list = []
    for listicle in top_10_dict:
        labels.append(pipe_swap(listicle.get("ProductSetId")))
        top_10_list.append(listicle.get("TransactionCount"))
    ret =  { 
        "labels": labels,
        "list": top_10_list
    }

    return ret


def get_single_product_cross_sell_report_table(start_date, end_date, ecaTrackingCodeFilter):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
        f"""



            SELECT TOP 10
                ProductSetId,
                CrossSellProducts,
                COUNT(*) AS TransactionCount,
                SUM(CASE WHEN APPLICATION_TYPE = 'Online' THEN 1 ELSE 0 END) AS OnlineCount,
                SUM(CASE WHEN APPLICATION_TYPE = 'Banker Assisted' THEN 1 ELSE 0 END) AS BankerAssistedCount
            FROM
                {table}
            WHERE
                ProductSetId NOT LIKE '%|%'
                AND {get_date_filter(start_date,end_date)}
                AND {ecaTrackingCodeFilter}
                AND {excludeBotData} AND {excludeZeroProductApps}
                
                AND CrossSellProducts IS NOT NULL
                AND LTRIM(RTRIM(CrossSellProducts)) <> ''
            GROUP BY
                ProductSetId, CrossSellProducts
            HAVING
                COUNT(*) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    )
    top_10_list = []
    ctr = 1
    for listicle in top_10_dict:
        onlineVsbanker_assisted = str(listicle.get("OnlineCount")) + " / " + str(listicle.get("BankerAssistedCount"))
        top_10_list.append([
            ctr,
            pipe_swap(listicle.get("ProductSetId")), 
            listicle.get("CrossSellProducts"),
            listicle.get("TransactionCount"),
            onlineVsbanker_assisted
        ])
        ctr += 1
    ret =  { 
        "rows": top_10_list,
        "headers": ["SNo", "ProductName", "CrossSellProducts", "TransactionCount", "Online/Banker Assisted"]
    }

    return ret




def get_multi_product_product_set_id_report_table(start_date, end_date, ecaTrackingCodeFilter):   
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
            f"""SELECT TOP 10
                    ProductSetId,
                    COUNT(*) AS TransactionCount,
                    SUM(CASE WHEN APPLICATION_TYPE = 'Online' THEN 1 ELSE 0 END) AS OnlineCount,
                    SUM(CASE WHEN APPLICATION_TYPE = 'Banker Assisted' THEN 1 ELSE 0 END) AS BankerAssistedCount
                FROM
                    {table}
                WHERE
                    ProductSetId LIKE '%|%'
                    And {get_date_filter(start_date,end_date)}
                    And {ecaTrackingCodeFilter}
                    AND {excludeBotData} AND {excludeZeroProductApps}
                GROUP BY
                    ProductSetId
                HAVING
                    COUNT(*) > 10
                ORDER BY
                    TransactionCount DESC;
            """ 
        )
    top_10_list = []
    ctr = 1
    for listicle in top_10_dict:
        onlineVsbanker_assisted = str(listicle.get("OnlineCount")) + " / " + str(listicle.get("BankerAssistedCount"))
        top_10_list.append([
            ctr, 
            pipe_swap(listicle.get("ProductSetId")), 
            listicle.get("TransactionCount"),
            onlineVsbanker_assisted
            ])
        ctr += 1
    ret =  { 
        "rows":top_10_list,
        "headers": ["SNo","ProductCombinations", "TransactionCount", "Online/Banker Assisted"]
    }

    return ret

def get_multi_product_product_set_id_report_bar(start_date, end_date, ecaTrackingCodeFilter):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
            f"""SELECT TOP 10
                    ProductSetId,
                    COUNT(*) AS TransactionCount
                FROM
                    {table}
                WHERE
                    ProductSetId LIKE '%|%'
                    And {get_date_filter(start_date,end_date)}
                    And {ecaTrackingCodeFilter}
                    AND {excludeBotData} AND {excludeZeroProductApps}
                GROUP BY
                    ProductSetId
                HAVING
                    COUNT(*) > 10
                ORDER BY
                    TransactionCount DESC;
            """ 
        )
    labels = []
    top_10_list = []
    for listicle in top_10_dict:
        labels.append(pipe_swap(listicle.get("ProductSetId")))
        top_10_list.append(listicle.get("TransactionCount"))
    ret =  { 
        "labels":labels,
        "list": top_10_list
    }

    return ret



def pipe_swap(val):
    val = str(val)
    product_ids = val.split('|')  # Split into individual IDs
    swapped_ids = []

    for pid in product_ids:
        matched = False
        for id, name in ALL_PRODUCT_SET_ID:
            if pid == id:  # Match full ID only
                swapped_ids.append(f"{id}: {name}")
                matched = True
                break
        if not matched:
            swapped_ids.append(pid)  # Keep original if no match

    return ' | '.join(swapped_ids)


