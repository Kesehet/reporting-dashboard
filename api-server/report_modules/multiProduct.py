from DB import Transaction, SQLConn, Q
from report_modules.condition_utils import *
from utils import *



def get_multi_product_cross_sell_report_table(start_date, end_date, ecaTrackingCodeFilter):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
        f"""SELECT TOP 10
                ProductSetId,
                CrossSellProducts,
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS TransactionCount,
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
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    )
    top_10_list = []
    ctr = 1
    if top_10_dict == 0:
        return { 
            "rows": [],
            "headers": ["SNo", "ProductName", "CrossSellProducts", "TransactionCount", "Online/Banker Assisted"]
        }
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
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS TransactionCount
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
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    )
    labels = []
    top_10_list = []
    if top_10_dict == 0:
        return {
            "labels": [],
            "list": []
        }
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
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS TransactionCount
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
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    )
    labels = []
    top_10_list = []
    if top_10_dict == 0:
        return {
            "labels": [],
            "list": []
        }
    for listicle in top_10_dict:
        labels.append(pipe_swap(listicle.get("ProductSetId")))
        top_10_list.append(listicle.get("TransactionCount"))
    ret =  { 
        "labels": labels,
        "list": top_10_list
    }

    return ret


def get_single_product_cross_sell_report_table(start_date, end_date, ecaTrackingCodeFilter, limit="TOP 10", params={}):
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    stat_type = params.get("stat_type")
    additionalConditions = ""
    if stat_type == "Opened / Approved":
        additionalConditions = "AND " + approvedApps
    if stat_type == "Submitted":
        additionalConditions = "AND " + submittedApps
    top_10_query =f"""



            SELECT {limit}
                ProductSetId,
                CrossSellProducts,
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS TransactionCount,
                SUM(CASE WHEN APPLICATION_TYPE = 'Online' THEN 1 ELSE 0 END) AS OnlineCount,
                SUM(CASE WHEN APPLICATION_TYPE = 'Banker Assisted' THEN 1 ELSE 0 END) AS BankerAssistedCount
            FROM
                {table}
            WHERE
                ProductSetId NOT LIKE '%|%'
                AND {get_date_filter(start_date,end_date)}
                AND {ecaTrackingCodeFilter}
                AND {excludeBotData} AND {excludeZeroProductApps}
                {additionalConditions}
                
                AND CrossSellProducts IS NOT NULL
                AND LTRIM(RTRIM(CrossSellProducts)) <> ''
            GROUP BY
                ProductSetId, CrossSellProducts
            HAVING
                Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 10
            ORDER BY
                TransactionCount DESC;
        """ 
    top_10_dict = transaction.get_transactions_by_sql_query(
        top_10_query
    )
    top_10_list = []
    ctr = 1
    if top_10_dict == 0:
        return {
            "rows": [],
            "headers": ["SNo", "ProductName", "CrossSellProducts", "TransactionCount", "Online/Banker Assisted"]
        }
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


def get_monthly_multi_product_reports_line(start_date, end_date, ecaTrackingCodeFilter, params={}):
    from utils import try_int
    intervals = get_list_of_months_between(start_date, end_date)
    ret = {
        "labels": [],
        "datasetMap": {
            "Transaction Count " + params.get("stat_type") : []
        }
    }
    for interv in intervals:
        resp = get_single_product_cross_sell_report_table(interv.get("start_date"), interv.get("end_date"), ecaTrackingCodeFilter, limit="", params=params).get("rows")
        sum = 0
        for res in resp:
            sum = sum + try_int(res[3])
        ret["labels"].append(get_header(interv).get("label"))
        
        ret["datasetMap"]["Transaction Count " + params.get("stat_type") ].append(sum)

    return ret



def get_daily_multi_product_product_set_id_report_table(start_date, end_date, ecaTrackingCodeFilter):
    intervals = get_list_of_days_between(start_date, end_date)
    ret = {}
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)

    day_labels = {}
    for interv in intervals:
        day_label = get_day_header(interv).get("label")
        ret[day_label] = {}
        day_labels[interv.get("start_date")] = day_label

    if not intervals:
        return ret

    top_per_day = txn.get_transactions_by_sql_query(
        f"""
        WITH DailyProductCounts AS (
            SELECT
                CAST(AppStartDate AS DATE) AS AppDate,
                value AS ProductSetId,
                COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS product_count
            FROM
                {table}
            CROSS APPLY STRING_SPLIT(ProductSetId, '|')
            WHERE
                {get_date_filter(start_date, end_date)}
                AND {ecaTrackingCodeFilter}
                AND {excludeBotData}
                AND {excludeZeroProductApps}
                AND ProductSetId IS NOT NULL
                AND LTRIM(RTRIM(ProductSetId)) <> ''
            GROUP BY
                CAST(AppStartDate AS DATE),
                value
            HAVING
                COUNT(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 10
        ),
        RankedDailyProductCounts AS (
            SELECT
                AppDate,
                ProductSetId,
                product_count,
                ROW_NUMBER() OVER (
                    PARTITION BY AppDate
                    ORDER BY product_count DESC, ProductSetId
                ) AS rn
            FROM
                DailyProductCounts
        )
        SELECT
            AppDate,
            ProductSetId,
            product_count
        FROM
            RankedDailyProductCounts
        WHERE
            rn <= 10
        ORDER BY
            AppDate,
            product_count DESC,
            ProductSetId;
        """
    )

    if isinstance(top_per_day, list):
        for row in top_per_day:
            app_date = row.get("AppDate")
            product_set_id = row.get("ProductSetId")
            count_value = row.get("product_count")

            if not app_date or product_set_id is None or count_value is None:
                continue

            app_date_str = app_date.strftime("%Y-%m-%d") if hasattr(app_date, "strftime") else str(app_date)
            day_label = day_labels.get(app_date_str)
            if not day_label:
                continue

            try:
                ret[day_label][product_set_id] = int(count_value)
            except (TypeError, ValueError):
                ret[day_label][product_set_id] = count_value

    return ret


def get_multi_product_product_set_id_report_table(start_date, end_date, ecaTrackingCodeFilter):   
    sql = SQLConn()
    sql.connect()
    transaction = Transaction(sql)
    top_10_dict = transaction.get_transactions_by_sql_query(
            f"""SELECT TOP 10
                    ProductSetId,
                    Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS TransactionCount,
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
                    Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 10
                ORDER BY
                    TransactionCount DESC;
            """ 
        )
    top_10_list = []
    ctr = 1
    if top_10_dict == 0:
        return { 
            "rows":[],
            "headers": ["SNo","ProductCombinations", "TransactionCount", "Online/Banker Assisted"]
        }
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
                    Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) AS TransactionCount
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
                    Count(DISTINCT CONCAT(eCAID, '-', ecaTrackingCode)) > 10
                ORDER BY
                    TransactionCount DESC;
            """ 
        )
    labels = []
    top_10_list = []
    if top_10_list == 0:
        return {
            "labels": [],
            "list": []
        }
    for listicle in top_10_dict:
        labels.append(pipe_swap(listicle.get("ProductSetId")))
        top_10_list.append(listicle.get("TransactionCount"))
    ret =  { 
        "labels":labels,
        "list": top_10_list
    }

    return ret



def get_cross_sell_products_presented_and_accepted_table(start_date, end_date, params):
    intervals = get_list_of_months_between(start_date, end_date)
    common_filters = [excludeBotData, excludeZeroProductApps]
    ret = {
        "rows":[["CrossSell Presented"],["CrossSell Accepted"], ["Acceptance %age"]],
        "headers":["Month"]
    }
    filters = [
                "CrossSellProducts IS NOT NULL AND CrossSellProducts != ''",
            ] + common_filters
    if params.get("type") == "submitted":
        filters.append(submittedApps)
    if params.get("type") == "opened/approved":
        filters.append(approvedApps)
    for interv in intervals:
        pres = Q(columns=[countColumn], where=filters+[
            get_date_filter(interv.get("start_date"), interv.get("end_date")), 
            ], params=params)
        accept = Q(columns=[countColumn], where=filters+[
            get_date_filter(interv.get("start_date"), interv.get("end_date")), 
            "Opted = 'Y'"
            ], params=params)
        ret['headers'].append(get_header(interv)["label"])
        ret["rows"][0].append(pres)
        ret["rows"][1].append(accept)
        if pres != 0:
            ret["rows"][2].append(round((accept/pres)*100, 2))
        else:
            ret["rows"][2].append(0)
        


    return ret


def get_cross_sell_products_presented_and_accepted_line(start_date, end_date, params):
    ret = get_cross_sell_products_presented_and_accepted_table(start_date, end_date, params)
    return {
            "labels": ret['headers'][1:],
            "list": [
                {
                    "name": "CrossSell Presented",
                    "type": "bar",
                    "data": ret["rows"][0][1:]
                },
                {
                    "name": "CrossSell Accepted",
                    "type": "line",
                    "data": ret["rows"][1][1:]
                }
        ]
        }



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


