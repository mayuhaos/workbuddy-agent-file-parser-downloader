@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "VENV_PY=%PROJECT_ROOT%.venv\Scripts\python.exe"
set "OUT_DIR=%PROJECT_ROOT%outputs"

cd /d "%PROJECT_ROOT%"

if not exist "%VENV_PY%" (
  echo Creating virtual environment...
  python -m venv "%PROJECT_ROOT%.venv"
)

echo Installing/updating dependencies...
"%VENV_PY%" -m pip install -e "%PROJECT_ROOT%"
if errorlevel 1 goto failed

echo Starting FULL WorkBuddy sync...
"%VENV_PY%" -m workbuddy_agent_file_parser_downloader sync --out-dir "%OUT_DIR%" --concurrency 1 --delay-min 1 --delay-max 2
if errorlevel 1 goto failed

echo.
echo Done. Outputs:
echo %OUT_DIR%
pause
exit /b 0

:failed
echo.
echo Run failed. Please check the console output above.
pause
exit /b 1

