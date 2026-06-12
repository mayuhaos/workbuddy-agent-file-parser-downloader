@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "VENV_PY=%PROJECT_ROOT%.venv\Scripts\python.exe"
set "OUT_DIR=%PROJECT_ROOT%outputs-test-3"

cd /d "%PROJECT_ROOT%"

if not exist "%VENV_PY%" (
  echo Creating virtual environment...
  python -m venv "%PROJECT_ROOT%.venv"
)

echo Installing/updating dependencies...
"%VENV_PY%" -m pip install -e "%PROJECT_ROOT%"
if errorlevel 1 goto failed

echo Starting TEST WorkBuddy run: 2 experts + 1 expert team...
"%VENV_PY%" -m workbuddy_agent_file_parser_downloader run --out-dir "%OUT_DIR%" --sample-agents 2 --sample-teams 1 --concurrency 1 --delay-min 1 --delay-max 2
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
