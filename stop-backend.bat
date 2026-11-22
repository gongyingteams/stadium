@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title IBMS Backend Stopper

rem Auto-detect project root from this script's own location
set "PROJ=%~dp0"
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"
set "LOGDIR=%PROJ%\logs"

echo ==================================================
echo   IBMS Backend  -  stop
echo ==================================================
echo.

echo [1/3] killing processes listening on :8000 ...
set "KILLED=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
    echo       killing PID %%a
    taskkill /F /PID %%a >nul 2>&1
    set "KILLED=1"
)
if "%KILLED%"=="0" echo       nothing listening on 8000

echo [2/3] killing stray uvicorn processes ...
powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'uvicorn' } | ForEach-Object { Write-Host ('       killing PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

echo [3/3] verifying ...
timeout /t 2 >nul
set "STILL=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do set "STILL=1"

echo.
if "%STILL%"=="0" (
    echo ==================================================
    echo   Backend stopped. Port 8000 is free.
    echo ==================================================
) else (
    echo ==================================================
    echo   [WARN] port 8000 is STILL in use
    echo   Try running as administrator, or check task manager.
    echo ==================================================
)
echo.
timeout /t 5 >nul
exit /b 0
