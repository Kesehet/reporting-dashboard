import os
import sys
import pyodbc
from getpass import getuser
from dotenv import load_dotenv

load_dotenv()

# This script tests SQL Server connection variants including Windows integrated auth and SQL auth.
# Run with runas /netonly for the domain account if Windows auth is needed:
#   runas /u:MYFNBOB1\svc_eCA_DEV_Report /netonly "python c:\Users\reddys\source\repos\eStore\api-server\test_conn_variations.py"

server = os.getenv("CORRILIAN_SQL_HOST", "vscorsqldev01.myfnbob1.loc")
database = os.getenv("CORRILIAN_SQL_DATABASE", "MobilitiFNBPA")
username = os.getenv("CORRILIAN_SQL_USER")
password = os.getenv("CORRILIAN_SQL_PASSWORD")


def try_conn(conn_str):
    print("Trying:", conn_str)
    try:
        conn = pyodbc.connect(conn_str, timeout=10)
        conn.close()
        print("  SUCCESS")
        return True
    except Exception as e:
        print("  FAILED ->", repr(e))
        return False


def build_conn_str(driver, attrs):
    parts = [f"DRIVER={{{driver}}}"]
    for k, v in attrs.items():
        parts.append(f"{k}={v}")
    return ";".join(parts) + ";"

installed_drivers = pyodbc.drivers()
current_user = getuser()
print("Installed ODBC drivers:", installed_drivers)
print(f"Current Windows user: {current_user}")
print(f"Current UID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
print(f"Server: {server}, Database: {database}")
if username:
    print(f"SQL User (from .env): {username}")

if current_user.lower() != "reddys":
    print(f"[OK] Running as service account: {current_user}")
else:
    print(f"[WARNING] Still running as {current_user}, not the service account!")
    print("  The runas /netonly delegation may not have worked.")
    print("  Try running without /netonly or check your password.")

print("Use runas /netonly for network Windows auth if your current user is not trusted.")
print(r"Example: runas /u:MYFNBOB1\svc_eCA_DEV_Report /netonly \"python c:\\Users\\reddys\\source\\repos\\eStore\\api-server\\test_conn_variations.py\"")
print()

# Prefer the newer Microsoft SQL Server drivers.
drivers = [d for d in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server Native Client 11.0", "SQL Server"] if d in installed_drivers]
if not drivers:
    drivers = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server Native Client 11.0", "SQL Server"]

servers = [server, f"tcp:{server},1433"]

variant_entries = []
for driver in drivers:
    for srv in servers:
        # Windows integrated auth variants
        variant_entries.append((driver, {
            "SERVER": srv,
            "DATABASE": database,
            "Trusted_Connection": "Yes",
            "Encrypt": "no",
            "TrustServerCertificate": "yes",
            "Connection Timeout": "10",
        }))
        variant_entries.append((driver, {
            "SERVER": srv,
            "DATABASE": database,
            "Integrated Security": "SSPI",
            "Encrypt": "no",
            "TrustServerCertificate": "yes",
            "Connection Timeout": "10",
        }))
        
        # SQL Server authentication variants (if credentials available)
        if username and password:
            variant_entries.append((driver, {
                "SERVER": srv,
                "DATABASE": database,
                "UID": username,
                "PWD": password,
                "Encrypt": "no",
                "TrustServerCertificate": "yes",
                "Connection Timeout": "10",
            }))
            variant_entries.append((driver, {
                "SERVER": srv,
                "DATABASE": database,
                "UID": username,
                "PWD": password,
                "Authentication": "SqlPassword",
                "Encrypt": "no",
                "TrustServerCertificate": "yes",
                "Connection Timeout": "10",
            }))

success = False
for driver, attrs in variant_entries:
    conn_str = build_conn_str(driver, attrs)
    if try_conn(conn_str):
        success = True
        break

if not success:
    print("No variants succeeded.")
else:
    print("At least one variant connected successfully.")