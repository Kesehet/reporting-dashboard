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

"%PYTHON_EXEC%" -m pip install -r requirements.txt || exit /b 1
"%PYTHON_EXEC%" -m pip install pyinstaller || exit /b 1
"%PYTHON_EXEC%" api-server\build\generate_build.py --check || exit /b 1
"%PYTHON_EXEC%" -m unittest discover -s tests -p test_*.py || exit /b 1
call npm install --package-lock-only --ignore-scripts --no-audit --no-fund || exit /b 1
call npm ci --no-audit --no-fund || exit /b 1
set "CI=true"
call npm run test:nocov -- --runInBand || exit /b 1
set "CI=false"
call npm run build || exit /b 1
"%PYTHON_EXEC%" api-server\build\generate_build.py || exit /b 1
if not exist dist mkdir dist
copy /Y exe_dist\*.exe dist\ >nul || exit /b 1
echo Build completed successfully.
