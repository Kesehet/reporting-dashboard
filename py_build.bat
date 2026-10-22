@echo off
setlocal
cd /d "%~dp0" || exit /b 1

rem Use the project interpreter, not a Microsoft Store Python alias.
set "PYTHON_EXEC="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXEC=%CD%\.venv\Scripts\python.exe"
if not defined PYTHON_EXEC if exist "venv\Scripts\python.exe" set "PYTHON_EXEC=%CD%\venv\Scripts\python.exe"
if not defined PYTHON_EXEC (
    for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if not defined PYTHON_EXEC set "PYTHON_EXEC=%%P"
)
if not defined PYTHON_EXEC if exist "%ProgramFiles%\Python310\python.exe" set "PYTHON_EXEC=%ProgramFiles%\Python310\python.exe"
if not defined PYTHON_EXEC (
    for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do if not defined PYTHON_EXEC set "PYTHON_EXEC=%%P"
)
if not defined PYTHON_EXEC (
    echo ERROR: No working Python interpreter found. Install Python 3 or create .venv.
    exit /b 1
)
"%PYTHON_EXEC%" -c "import sys; assert sys.version_info.major == 3" >nul 2>nul || (
    echo ERROR: The selected Python interpreter is not working: "%PYTHON_EXEC%"
    exit /b 1
)
echo Using Python: "%PYTHON_EXEC%"

rem Build artifacts first. Do not let a failing test prevent binary delivery.
"%PYTHON_EXEC%" -m pip install -r requirements.txt || exit /b 1
"%PYTHON_EXEC%" -m pip install -r tests\contracts\requirements.txt || exit /b 1
"%PYTHON_EXEC%" -m pip install pyinstaller || exit /b 1
call npm ci --no-audit --no-fund || exit /b 1

set "BUILD_FAILED=0"
set "TEST_FAILED=0"
echo === Building React production assets ===
set "CI=false"
call npm run build
if errorlevel 1 set "BUILD_FAILED=1"

echo === Packaging standalone Python executables ===
"%PYTHON_EXEC%" api-server\build\generate_build.py
if errorlevel 1 set "BUILD_FAILED=1"
if not exist dist mkdir dist
if exist "exe_dist\*.exe" (
    copy /Y "exe_dist\*.exe" "dist" >nul
    if errorlevel 1 set "BUILD_FAILED=1"
) else (
    echo WARNING: No executable was produced in exe_dist.
    set "BUILD_FAILED=1"
)
echo === Builds are available in build\ and dist\ regardless of test results ===

echo === Generate real chart response test fixtures ===
"%PYTHON_EXEC%" scripts\run_chart_contracts.py
if errorlevel 1 set "TEST_FAILED=1"

echo === Run backend and chart regressions ===
"%PYTHON_EXEC%" -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 set "TEST_FAILED=1"
"%PYTHON_EXEC%" -m unittest discover -s tests\contracts -p "test_*.py" -v
if errorlevel 1 set "TEST_FAILED=1"

echo === Run full frontend suite with mandatory chart contracts ===
set "CI=true"
set "CHART_CONTRACTS_REQUIRED=1"
call npm run test:nocov -- --runInBand
if errorlevel 1 set "TEST_FAILED=1"
set "CHART_CONTRACTS_REQUIRED="

if "%BUILD_FAILED%"=="1" echo ERROR: One or more production builds failed.
if "%TEST_FAILED%"=="1" echo ERROR: Regression tests failed. Produced build files are retained.
if "%BUILD_FAILED%"=="1" exit /b 1
if "%TEST_FAILED%"=="1" exit /b 1
echo All builds and tests passed.
exit /b 0
