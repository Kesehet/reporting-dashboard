@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
echo Running dependency, regression and visual pre-build checks...
"%PYTHON%" scripts\build_all.py %*
if errorlevel 1 (
  echo Build stopped: a pre-build check or frozen executable failed.
  exit /b 1
)
echo Release binaries are in exe_dist\.
exit /b 0
