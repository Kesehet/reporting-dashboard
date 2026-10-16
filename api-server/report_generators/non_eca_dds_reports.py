# Read XLSX file and extract necessary parameters
import os
import sys
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from DB import SQLConn, Transaction


file_path = "uploads/AtomicDDS Reports/tasks-export-2026-04-01.csv"

if not file_path or not os.path.exists(file_path):
    # Make the folder if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    raise ValueError(f"File path is invalid or does not exist: {file_path}")

df = pd.read_csv(file_path)


# Remove all rows where "userIdentifier" length is less than 9
df = df[df["userIdentifier"].str.len() > 9]



sql = SQLConn(kind="DGBEDW")
sql.connect()
txn = Transaction(sql)



batch_size = 1000
batches = [df[i:i+batch_size] for i in range(0, len(df), batch_size)]

responses = []
for batch in batches:
    query = f'''
        SELECT tma.ACCT_NUM as Account_Number,
        MAX(ccu.FirstName) as FirstName, 
        MAX(ccu.LastName) as LastName,
        MAX(ccu.TaxID) as TaxID,
        MAX(ccu.AuthRelationshipName) as AuthRelationshipName,
        MAX(ccu.email) as email,
        MAX(ccu.DayPhone) as DayPhone,
        MAX(ccu.EvePhone) as EvePhone,
        ccua.UserAgentGuid as UserAgentGuid,
        MAX(cud.SignonID) as SignonID,
        MAX(cud.DateFirstLogin) as DateFirstLogin,
        MAX(cud.DateLastSuccessfulLogin) as DateLastSuccessfulLogin
      FROM [DGBEDW].[DGB_EMPL_PII_V1].[ApplServices_TransMstrAcct_CUR] tma 
      LEFT JOIN [DGBEDW].[DGB_EMPL_PII_V1].[LNK_DGB_REG_USER_CRL_ACCT] tmalnk on tma.DGB_CRL_ACCT_SEQ_NUM=tmalnk.DGB_CRL_ACCT_SEQ_NUM
      LEFT JOIN [DGBEDW].[DGB_EMPL_PII_V1].[LNK_DGB_VOY_USER_REG_USER] reglnk on tmalnk.DGB_REG_USER_SEQ_NUM=reglnk.DGB_REG_USER_SEQ_NUM
      LEFT JOIN [DGBEDW].[DGB_EMPL_PII_V1].[Voyager_CCUser_CUR] ccu on reglnk.DGB_VOY_USER_SEQ_NUM=ccu.DGB_VOY_USER_SEQ_NUM
      LEFT JOIN DGBEDW.DGB_EMPL_PII_V1.Voyager_CCUserAgent_CUR ccua on reglnk.DGB_VOY_USER_SEQ_NUM=ccua.DGB_VOY_USER_SEQ_NUM
      LEFT JOIN [DGB_EMPL_PII_V1].[Corillian_IdUserDetails] as cud on reglnk.DGB_VOY_USER_SEQ_NUM=cud.[DGB_COR_USER_SEQ_NUM]
      WHERE ccua.UserAgentGuid IN ({','.join([f"'{user_id}'" for user_id in batch["userIdentifier"].tolist()])})
        GROUP BY tma.ACCT_NUM, ccua.UserAgentGuid
    '''
    response = txn.get_transactions_by_sql_query(query)
    if response == 0:
        raise ValueError("Query execution failed or returned no results.", response, query)
    responses.append(response)

final_response = pd.DataFrame([item for sublist in responses for item in sublist])




df["userIdentifier"] = (df["userIdentifier"].astype(str).str.lower().str.strip())
final_response["UserAgentGuid"] = (final_response["UserAgentGuid"].astype(str).str.lower().str.strip())


print(df.head())
print(final_response.head())

final_df = pd.merge(df, final_response, left_on="userIdentifier", right_on="UserAgentGuid", how="left")

print(final_df.head())

sql.disconnect()

# Save the final dataframe to a new CSV file
output_file_path = "uploads/AtomicDDS Reports/AtomicDDS_Enriched_Report.csv"
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
final_df.to_csv(output_file_path, index=False)

