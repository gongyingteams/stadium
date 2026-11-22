@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title IBMS Backend (Silent)

rem Auto-detect project root from this script's own location
set "PROJ=%~dp0"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"

set "BK=%PROJ%\backend"
set "PY=%BK%\.venv\Scripts\python.exe"
set "LOGDIR=%PROJ%\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo ==================================================
echo   IBMS Backend  -  silent background start
echo ==================================================
echo   project : %PROJ%
echo.

if not exist "%BK%\app\main.py" (
    echo [ERR] backend not found: %BK%\app\main.py
    echo       Put this script in the project root next to "backend".
    pause & exit /b 1
)
if not exist "%PY%" (
    echo [ERR] venv python not found: %PY%
    pause & exit /b 1
)

echo [1/5] checking dependencies...
"%PY%" -c "import uvicorn, fastapi" >nul 2>&1
if errorlevel 1 (
    echo [ERR] missing deps: "%PY%" -m pip install -r "%BK%\requirements.txt"
    pause & exit /b 1
)
echo       ok

echo [2/5] import self-check (app.main)...
cd /d "%BK%"
"%PY%" -c "import app.main" >"%LOGDIR%\import-check.log" 2>&1
if errorlevel 1 (
    echo [ERR] import failed. See: %LOGDIR%\import-check.log
    type "%LOGDIR%\import-check.log"
    pause & exit /b 1
)
echo       ok

echo [3/5] freeing port 8000...
set "KILLED=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
    echo       killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
    set "KILLED=1"
)
if "%KILLED%"=="0" echo       nothing to kill
timeout /t 2 >nul

echo [4/5] launching detached (hidden window)...
rem Pass paths via environment variables to avoid quoting problems
set "IBMS_PY=%PY%"
set "IBMS_BK=%BK%"
set "IBMS_OUT=%LOGDIR%\backend-out.log"
set "IBMS_ERR=%LOGDIR%\backend-err.log"

powershell -NoProfile -Command ^
  "Start-Process -FilePath $env:IBMS_PY -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000' -WorkingDirectory $env:IBMS_BK -WindowStyle Hidden -RedirectStandardOutput $env:IBMS_OUT -RedirectStandardError $env:IBMS_ERR"

if errorlevel 1 (
    echo [ERR] Start-Process failed
    pause & exit /b 1
)

echo [5/5] waiting for readiness (max 40s)...
set /a N=0
:WAIT
timeout /t 2 >nul
set /a N+=2
powershell -NoProfile -Command "try{ $null=Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3 -UseBasicParsing; exit 0 }catch{ exit 1 }" >nul 2>&1
if not errorlevel 1 goto READY
if %N% LSS 40 goto WAIT

echo.
echo [WARN] not ready after 40s. Last 25 lines of err log:
powershell -NoProfile -Command "if(Test-Path $env:IBMS_ERR){Get-Content -LiteralPath $env:IBMS_ERR -Tail 25 -Encoding UTF8}"
echo.
pause
exit /b 1

:READY
echo.
echo ==================================================
echo   Backend is UP  (background, hidden window)
echo ==================================================
echo.
echo   Health  : http://127.0.0.1:8000/api/health
echo   Swagger : http://127.0.0.1:8000/docs
echo   Out log : %LOGDIR%\backend-out.log
echo   Err log : %LOGDIR%\backend-err.log
echo.
echo   Stop with: stop-backend.bat
echo ==================================================
echo.
timeout /t 8 >nul
exit /b 0
