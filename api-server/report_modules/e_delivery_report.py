from DB import  Transaction, SQLConn


def get_e_delivery_report_insights():
    myquery = '''
DECLARE @PrevBOM DATETIME SET @PrevBOM = DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0);
DECLARE @PrevEOM DATETIME SET @PrevEOM = DATEADD(SECOND, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0));
DECLARE @PrevMo VARCHAR(20) SET @PrevMo = CONCAT(DATENAME(MONTH, @PrevBOM), ' ', DATEPART(YEAR, @PrevBOM));


WITH eStore AS (
	SELECT
		[APPID], [APPDETAILID], [ProductGrouping], [DecisionStatusName]
	FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]
	WHERE [ApplicationStart] BETWEEN @PrevBOM AND @PrevEOM
	AND [SourceChannelName] = 'INTERNET'
)



SELECT 'OO32' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'eStore Common App Applications' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(DISTINCT APPID) AS [Value]
FROM eStore

UNION ALL

SELECT 'OO33' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'eStore Common App Products (Total)' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore

UNION ALL

SELECT 'OO34' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Direct Auto Loans' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Direct Auto In'

UNION ALL

SELECT 'OO35' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Home Equity Line of Credit' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] IN ('HELOC', 'Lock Option HELOC In')

UNION ALL

SELECT 'OO36' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Penguins Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] LIKE '%Penguins%'

UNION ALL

SELECT 'OO37' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'PERL Fixed' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] LIKE '%PERL%'

UNION ALL

SELECT 'OO38' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Home Equity Installment Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] IN ('HEIL', 'Real Estate Term Int')

UNION ALL

SELECT 'OO39' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'SmartCash Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'SmartCash Card'

UNION ALL

SELECT 'OO40' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'SmartRate Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'SmartRate Card'

UNION ALL

SELECT 'OO41' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'SmartRewards Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'SmartRewards Card'

UNION ALL

SELECT 'OO42' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'RV/Marine Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online RV/Marine Loa'

UNION ALL

SELECT 'OO43' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Secured LOC' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online SEC LOC'

UNION ALL

SELECT 'OO44' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Secured Term Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online SEC TERM'

UNION ALL

SELECT 'OO45' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Unsecured LOC' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online Unsec LOC'

UNION ALL

SELECT 'OO46' AS [ID]
	, 'Total Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Unsecured Term Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online Unsec Term Lo'

UNION ALL

SELECT 'OO48' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Direct Auto Loans' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Direct Auto In' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO49' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Home Equity Line of Credit' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] IN ('HELOC', 'Lock Option HELOC In') AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO50' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'RV/Marine Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online RV/Marine Loa' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO51' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Unsecured LOC' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online Unsec LOC' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO52' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Unsecured Term Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online Unsec Term Lo' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO53' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Penguins Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] LIKE '%Penguins%' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO54' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'PERL Fixed' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] LIKE '%PERL%' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO55' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Home Equity Installment Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] IN ('HEIL', 'Real Estate Term Int') AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO56' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'SmartCash Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'SmartCash Card' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO57' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'SmartRate Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'SmartRate Card' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO58' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'SmartRewards Credit Card' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'SmartRewards Card' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO61' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Secured LOC' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS "Value"
FROM eStore
WHERE [ProductGrouping] = 'Online SEC LOC' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

UNION ALL

SELECT 'OO62' AS [ID]
	, 'Approved Online Consumer Lending Apps (eStore Common App Stats)' AS [Table]
	, 'Secured Term Loan' AS [Key]
	, @PrevMo AS [Month]
	, COUNT(1) AS [Value]
FROM eStore
WHERE [ProductGrouping] = 'Online SEC TERM' AND [DecisionStatusName] IN ('Approved', 'Aprvd. Rejected by Applicant')

'''
    sql = SQLConn("CRFEDW")
    sql.connect()
    txn = Transaction(sql)
    resp = txn.get_transactions_by_sql_query(myquery)
    sql.disconnect()

    return {
        "E Delivery Report": len(resp),
        "_report_E Delivery Report": resp
    }