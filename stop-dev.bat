@echo off
chcp 65001 >nul
setlocal

echo ============================================
echo   停止体育场馆 IBMS 开发服务
echo ============================================

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001 " ^| findstr LISTENING') do (
    echo   停止前端 PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
    echo   停止后端 PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
REM 清理残留的 uvicorn / vite 子进程
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%uvicorn app.main%%' or commandline like '%%node_modules\\vite\\bin\\vite.js%%'" get processid /format:value 2^>nul ^| findstr "="') do (
    set "pid=%%a"
)
timeout /t 1 >nul

echo.
echo   服务已停止
echo.
timeout /t 2 >nul
