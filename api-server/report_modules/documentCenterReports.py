from DB import SQLConn, Transaction
from dateutil.relativedelta import relativedelta
from datetime import datetime

def get_document_center_insights():
    sql = SQLConn(kind="CustomerDocumentCenter")
    sql.connect()
    txn = Transaction(sql)
    resp = txn.get_transactions_by_sql_query(f'''
        DECLARE @ThisYear int = YEAR(GETDATE());
        DECLARE @PrevYear int = @ThisYear - 1;

        WITH Docs AS (
        SELECT dc.UserId, YEAR(dc.CreatedDate) AS [Year]
        FROM [dbo].[DocumentCenter] dc
        WHERE dc.Status <> 'Deleted'
        -- OPTIONAL test-account exclusions (uncomment & adjust):
        -- AND dc.UserId NOT IN (SELECT u.Id FROM AspNetUsers u WHERE u.Email LIKE '%xfnbx%' OR u.Email LIKE '%joelegeisel@gmail.com%')
        ),
        DocCounts AS (
        SELECT [Year], COUNT(*) AS TotalDocs
        FROM Docs
        GROUP BY [Year]
        ),
        UploaderUsers AS (       -- use this CTE if counting "users"
        SELECT [Year], COUNT(DISTINCT UserId) AS TotalUploaders
        FROM Docs
        GROUP BY [Year]
        ),
        UploaderApps AS (        -- use this CTE if counting "applications"
        SELECT YEAR(dc.CreatedDate) AS [Year], COUNT(DISTINCT a.Id) AS TotalUploaders
        FROM [dbo].[DocumentCenter] dc
        JOIN Applications a ON a.UserId = dc.UserId
        WHERE dc.Status <> 'Deleted'
        GROUP BY YEAR(dc.CreatedDate)
        )
        SELECT 'Total number of documents uploaded last year (' + CAST(@PrevYear AS varchar(4)) + ')' AS [Doc Center Upload Stats],
            (SELECT TotalDocs FROM DocCounts WHERE [Year] = @PrevYear) AS [Count]
        UNION ALL
        SELECT 'Total number of users that uploaded documents or total number of applications that resulted in at least 1 upload (' + CAST(@PrevYear AS varchar(4)) + ')',
            -- switch which one you prefer:
            (SELECT TotalUploaders FROM UploaderApps  WHERE [Year] = @PrevYear)
            --(SELECT TotalUploaders FROM UploaderUsers WHERE [Year] = @PrevYear)
        UNION ALL
        SELECT 'Total number of documents uploaded YTD (' + CAST(@ThisYear AS varchar(4)) + ')',
            (SELECT TotalDocs FROM DocCounts WHERE [Year] = @ThisYear)
        UNION ALL
        SELECT 'Total number of users that uploaded documents or total number of applications that resulted in at least 1 upload (' + CAST(@ThisYear AS varchar(4)) + ')',
            -- switch which one you prefer:
            (SELECT TotalUploaders FROM UploaderApps  WHERE [Year] = @ThisYear);
            --(SELECT TotalUploaders FROM UploaderUsers WHERE [Year] = @ThisYear);



    ''')
    print(resp)
    if resp == 0:
        return {"error": "There are no insights available at the moment."}
    return {
        "headers": [keyer for keyer in resp[0].keys()],
        "rows": [[item for item in val.values()] for val in resp]
    }


def get_document_center_monthly_insights(start_date, end_date):
    intervals = get_list_of_months_between(start_date, end_date)
    headers = ["-"]
    rows = [
        ["Number Of Users"],
        ["Number of Documents"]
    ]
    for interval in intervals:
        sql = SQLConn(kind="CustomerDocumentCenter")
        sql.connect()
        txn = Transaction(sql)
        resp = txn.get_transactions_by_sql_query(f'''Select count(distinct(UserId)) as numofusers, count(UserId)as noofdocs from [dbo].[DocumentCenter] where UserId IS NOT NULL AND  {in_between_sql_condition(interval)}''')
        if resp == 0:
            continue
        rows[0].append(resp[0].get("numofusers"))
        rows[1].append(resp[0].get("noofdocs"))
        headers.append(get_header(interval).get("label", "0"))

    return {
        "rows": rows, "headers": headers
    }




# Created date - filter
# UserId - as key 
# get me monthly analysis table 





def get_header(interval):
    # Convert start date to format Jun-25
    start_date = datetime.strptime(interval['start_date'], "%Y-%m-%d").strftime("%b-%Y")
    return {
        "field": start_date,
        "label": start_date
    }
    

def in_between_sql_condition(interval):
    return f" CreatedDate >= '{interval['start_date']}' AND CreatedDate <= '{interval['end_date']}'"


def get_list_of_months_between(start_date, end_date):

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    months = []

    while start_date <= end_date:
        month_start = start_date.strftime("%Y-%m-01")  # July 1st
        next_month = datetime.strptime(month_start, "%Y-%m-%d") + relativedelta(months=1)  # Auguest 1st
        month_end = (next_month - relativedelta(days=1)).strftime("%Y-%m-%d") # Auguest 4th 
        months.append({"start_date": month_start, "end_date": month_end}) 
        start_date = next_month

    return months

