<#
QAChatAgent 启动脚本
功能：一键启动前后端服务
#>

# 设置工作目录为脚本所在目录
$projectRoot = $PSScriptRoot
cd $projectRoot

# 启动后端服务
function Start-Backend {
    Write-Host "启动后端服务..."
    cd backend
    $env:PYTHONPATH = "$projectRoot"
    python main.py
}

# 启动前端服务
function Start-Frontend {
    Start-Sleep -Seconds 3
    Write-Host "启动前端开发服务器..."
    cd frontend
    npm run dev
}

# 并行启动服务
$backendJob = Start-Job -ScriptBlock ${function:Start-Backend}
$frontendJob = Start-Job -ScriptBlock ${function:Start-Frontend}

# 显示启动信息
Write-Host "===================================="
Write-Host "    QAChatAgent 服务已启动"
Write-Host "===================================="
Write-Host "后端: http://localhost:8000"
Write-Host "前端: http://localhost:5173"
Write-Host "按 Ctrl+C 停止所有服务"

# 等待用户输入以退出
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # 清理工作
    Get-Job | Remove-Job -Force
    Write-Host "服务已停止"
}