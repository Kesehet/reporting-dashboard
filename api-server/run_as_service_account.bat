@echo off
REM Run the connection test as the service account (full context, not just /netonly)
REM This ensures the ODBC driver uses the service account's credentials

setlocal enabledelayedexpansion

set OUTPUT_FILE=%~dp0test_conn_variations_output.log

echo Running test as MYFNBOB1\svc_eCA_DEV_Report...
echo Output will be saved to: %OUTPUT_FILE%
echo.
echo You will be prompted for the service account password.
echo.

runas /user:MYFNBOB1\svc_eCA_DEV_Report "python %~dp0test_conn_variations.py > %OUTPUT_FILE% 2>&1"

if exist "%OUTPUT_FILE%" (
    echo.
    echo Connection test completed. Output:
    echo.
    type "%OUTPUT_FILE%"
) else (
    echo.
    echo [ERROR] Output file not created. Password may have been incorrect.
)

endlocal
pause
