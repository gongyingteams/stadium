@echo off
chcp 65001 >nul
setlocal

set "PROJ=E:\2026-体育场馆项目"
set "LOGDIR=%USERPROFILE%\venue-dev-logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo ============================================
echo   体育场馆 IBMS 开发服务启动
echo ============================================
echo.

REM --- 停止旧进程 ---
echo [1/4] 清理旧进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001 " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 >nul

REM --- 检测局域网 IP ---
set "LANIP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4" ^| findstr "192.168."') do (
    if not defined LANIP for /f "tokens=*" %%b in ("%%a") do set "LANIP=%%b"
)
if not defined LANIP set "LANIP=127.0.0.1"

REM --- 启动后端 ---
echo [2/4] 启动后端 FastAPI (8000)...
cd /d "%PROJ%\backend"
if exist ".venv\Scripts\python.exe" (
    start "IBMS-Backend" /min ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    start "IBMS-Backend" /min python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)

REM --- 启动前端 ---
echo [3/4] 启动前端 Vite (3001)...
cd /d "%PROJ%"
set "NODE_EXE=C:\Users\Administrator\.opencode-tools\node.exe"
if not exist "%NODE_EXE%" set "NODE_EXE=node"
start "IBMS-Frontend" /min "%NODE_EXE%" node_modules\vite\bin\vite.js --host 0.0.0.0 --port 3001

REM --- 等待就绪 ---
echo [4/4] 等待服务就绪...
set /a N=0
:WAIT
timeout /t 2 >nul
set /a N+=1
curl -s -o nul -w "" http://127.0.0.1:3001/ 2>nul && set "FOK=1"
curl -s -o nul -w "" http://127.0.0.1:8000/api/health 2>nul && set "BOK=1"
if not defined FOK if %N% LSS 20 goto WAIT
if not defined BOK if %N% LSS 20 goto WAIT

echo.
echo ============================================
echo   启动完成
echo ============================================
echo.
echo   本机访问:   http://localhost:3001
echo   局域网访问: http://%LANIP%:3001
echo.
echo   后端 API:   http://%LANIP%:8000/docs
echo.
echo   演示账号:   admin / admin123
echo               ops / ops123
echo               operator / operator123
echo               viewer / viewer123
echo.
echo   日志目录:   %LOGDIR%
echo.
echo   停止服务:   运行 stop-dev.bat
echo ============================================
echo.
pause
