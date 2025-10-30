applicationcurtable = "[CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR]"
customfieldscurtable = "[CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMFIELDS_CUR]"
declinescurtable = "[CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_DECLINES_CUR]"
reasonmastercurtable = "[CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_REASONMASTER_CUR]"
openedorapprovedappsreport = "SELECT DISTINCT app.APPID,app.APPDETAILID,app.ApplicationStart,app.ProductShortName,app.ProductGrouping,app.DecisionStatusName,app.AmountRequested,app.AccountNumber,rc.Name as DecisionReason,temp.Temenos_ID FROM [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_APPLICATION_CUR] AS app LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_CUSTOMFIELDS_CUR] as temp ON temp.APPID = app.APPID LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_ACTION_DECLINES_CUR] AS dc ON app.APPID = dc.APPID LEFT JOIN [CRFEDW].[CRF_EMPL_PII_V1].[CRF_APP_REASONMASTER_CUR] AS rc ON rc.ReasonID = dc.ReasonID  "
# bar + line graph for the loan commitment amounts 
# clustered bar graph for Quarterly analysis 
# stacked bar for Unsecured and Secured Laons 

lendingApps = "NumLendingProducts > 0"
SECURED_PRODUCT_GROUPINGS = [
    'Auto',
    'Direct Auto In',
    'HEIL',
    'HELOC',
    'Online RV/Marine Loa',
    'Online SEC LOC',
    'Online SEC TERM',
    'Other Secured',
    'Secured Credit Card',
    'Small Business Other Secured LOC',
    'Small Business Other Secured Term',
    'Small Business Real Estate LOC'
]
UNSECURED_PRODUCT_GROUPINGS = [
    'CapEx Draw',
    'CapEx Master Line',
    'COVID Deferral',
    'Credit Card',
    'Letter of Credit',
    'Online Unsec LOC',
    'Online Unsec Term Lo',
    'Paynet Review',
    'Penguins CC',
    'PERL Fixed',
    'PERL Variable',
    'Pgh Penguins Card',
    'Small Business Credit Card',
    'Small Business Mods',
    'Small Business Unsecured',
    'SmartCash Card',
    'SmartRate Card',
    'SmartRewards Card',
    'Unsecured LOC',
    'Unsecured Term'
]
