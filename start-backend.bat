@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title IBMS Backend Launcher

rem ============================================================
rem  Auto-detect project root from this script's own location.
rem  No hard-coded Chinese path -> avoids codepage breakage.
rem ============================================================
set "PROJ=%~dp0"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"

set "BK=%PROJ%\backend"
set "PY=%BK%\.venv\Scripts\python.exe"
set "LOGDIR=%PROJ%\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo ==================================================
echo   IBMS Backend Launcher  (port 8000)
echo ==================================================
echo   project : %PROJ%
echo.

if not exist "%BK%\app\main.py" (
    echo [ERR] backend not found:
    echo       %BK%\app\main.py
    echo       Put this script in the project root next to "backend".
    echo.
    pause
    exit /b 1
)
if not exist "%PY%" (
    echo [ERR] venv python not found:
    echo       %PY%
    echo.
    echo Create it with:
    echo       cd /d "%BK%"
    echo       python -m venv .venv
    echo       .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [1/5] checking dependencies...
"%PY%" -c "import uvicorn, fastapi" >nul 2>&1
if errorlevel 1 (
    echo [ERR] missing deps. Run:
    echo       "%PY%" -m pip install -r "%BK%\requirements.txt"
    echo.
    pause
    exit /b 1
)
echo       ok

echo [2/5] import self-check (app.main)...
cd /d "%BK%"
"%PY%" -c "import app.main" >"%LOGDIR%\import-check.log" 2>&1
if errorlevel 1 (
    echo [ERR] import failed. Details:
    echo.
    type "%LOGDIR%\import-check.log"
    echo.
    echo Full log: %LOGDIR%\import-check.log
    pause
    exit /b 1
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

echo [4/5] starting backend in a new window...
start "IBMS-Backend" cmd /k ""%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [5/5] waiting for readiness (max 40s)...
set /a N=0
:WAIT
timeout /t 2 >nul
set /a N+=2
powershell -NoProfile -Command "try{ $null=Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3 -UseBasicParsing; exit 0 }catch{ exit 1 }" >nul 2>&1
if not errorlevel 1 goto READY
if %N% LSS 40 goto WAIT

echo.
echo [WARN] not ready after 40s.
echo        Check the window titled "IBMS-Backend".
echo.
pause
exit /b 1

:READY
echo.
echo ==================================================
echo   Backend is UP
echo ==================================================
echo.
echo   Health   : http://127.0.0.1:8000/api/health
echo   Swagger  : http://127.0.0.1:8000/docs
echo   Flag API : http://127.0.0.1:8000/api/flag/health
echo.
echo   A new window "IBMS-Backend" is running.
echo   Close it, or run stop-backend.bat, to stop.
echo ==================================================
echo.
timeout /t 8 >nul
exit /b 0
