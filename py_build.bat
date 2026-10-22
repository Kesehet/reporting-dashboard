@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PYTHON_EXEC=.venv\Scripts\python.exe") else (set "PYTHON_EXEC=python")
%PYTHON_EXEC% -m pip install -r requirements.txt || exit /b 1
%PYTHON_EXEC% -m pip install pyinstaller || exit /b 1
%PYTHON_EXEC% api-server\build\generate_build.py --check || exit /b 1
%PYTHON_EXEC% -m unittest discover -s tests -p test_*.py || exit /b 1
call npm install --package-lock-only --ignore-scripts --no-audit --no-fund || exit /b 1
call npm ci --no-audit --no-fund || exit /b 1
set "CI=true"
call npm run test:nocov -- --runInBand || exit /b 1
set "CI=false"
call npm run build || exit /b 1
%PYTHON_EXEC% api-server\build\generate_build.py || exit /b 1
if not exist dist mkdir dist
copy /Y exe_dist\*.exe dist\ >nul || exit /b 1
echo Build completed successfully.
