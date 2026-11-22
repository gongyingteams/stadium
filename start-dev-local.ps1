# 本地一键启动脚本（体育场馆应用集成管理系统）
# 用法: 在项目根目录右键“使用 PowerShell 运行”或执行 powershell -ExecutionPolicy Bypass -File .\start-dev-local.ps1
# 启动为独立后台进程，关闭本窗口或终端不影响服务运行。

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$node = 'C:\Users\Administrator\.opencode-tools\node.exe'
$py   = Join-Path $root 'backend\.venv\Scripts\python.exe'

function Test-Port($port) {
    return $null -ne (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

$backendRunning  = Test-Port 8000
$frontendRunning = Test-Port 3001

if ($backendRunning -and $frontendRunning) {
    Write-Host '两个服务都已在运行：' -ForegroundColor Green
    Write-Host '  前端 http://localhost:3001'
    Write-Host '  后端 http://localhost:8000'
    exit 0
}

if (-not $backendRunning) {
    if (-not (Test-Path $py)) {
        Write-Host "未找到后端虚拟环境: $py" -ForegroundColor Red
        Write-Host '请先创建: cd backend; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt'
        exit 1
    }
    Start-Process -FilePath $py `
        -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000' `
        -WorkingDirectory (Join-Path $root 'backend') `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $root 'dev-local-backend.out.log') `
        -RedirectStandardError  (Join-Path $root 'dev-local-backend.err.log')
    Write-Host '后端已启动: http://localhost:8000  (Swagger 文档 /docs)' -ForegroundColor Cyan
} else {
    Write-Host '后端已在运行 (8000)，跳过' -ForegroundColor DarkGray
}

if (-not $frontendRunning) {
    if (-not (Test-Path $node)) { $node = 'node' }   # 退回 PATH 中的 node
    Start-Process -FilePath $node `
        -ArgumentList (Join-Path $root 'node_modules\vite\bin\vite.js'),'--host','0.0.0.0','--port','3001' `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $root 'dev-local-frontend.out.log') `
        -RedirectStandardError  (Join-Path $root 'dev-local-frontend.err.log')
    Write-Host '前端已启动: http://localhost:3001' -ForegroundColor Cyan
} else {
    Write-Host '前端已在运行 (3001)，跳过' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '演示账号: admin / admin123' -ForegroundColor Yellow
Write-Host '停止服务: 在任务管理器结束 python.exe 与 node.exe，或执行 Stop-Process -Name python,node -ErrorAction SilentlyContinue'
