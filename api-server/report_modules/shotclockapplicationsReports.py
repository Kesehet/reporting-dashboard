'''
Shot Clock Application Reports
'''
from DB import SQLConn, Transaction




def shot_clock_application_insights(start_date, end_date, params):
    query= '''
        SELECT
        s.*,
	    axp.*
		FROM [CustomerDocumentCenter].[dbo].[ShotClockApplications] AS s
		INNER JOIN [CustomerDocumentCenter].[dbo].[ApplicantXProduct] AS axp
		    ON axp.[ApplicantXProductId] = s.[ApplicantXProductId];
    '''
    sql = SQLConn(kind="CustomerDocumentCenter")
    sql.connect()
    txn = Transaction(sql)

    resp = txn.get_transactions_by_sql_query(query)
    if resp == 0:
        resp = []
    sql.disconnect()
    return {
        "Shot Clock Applications":len(resp),
        "_report_Shot Clock Applications": resp
    }