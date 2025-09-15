# QAChatAgent 一键启动脚本
# 此脚本用于同时启动前端和后端服务

# 设置控制台编码为 UTF-8，解决乱码问题
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 设置控制台颜色
$host.UI.RawUI.BackgroundColor = "Black"
$host.UI.RawUI.ForegroundColor = "Green"
Clear-Host

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "    QAChatAgent 一键启动脚本" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 创建一个新的作业来运行后端
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    
    # 检查是否存在虚拟环境
    if (Test-Path ".venv\Scripts\activate.ps1") {
        Write-Host "激活 Python 虚拟环境..."
        & .\.venv\Scripts\activate.ps1
    } else {
        Write-Host "警告: 未找到虚拟环境，尝试直接运行..."
    }
    
    # 运行后端服务
    Write-Host "启动后端服务..."
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

Write-Host "正在启动后端服务，请稍候..." -ForegroundColor Yellow
Write-Host ""
Write-Host "后端服务日志:" -ForegroundColor Magenta
Write-Host "-----------------------------------" -ForegroundColor DarkGray

# 等待后端服务启动
$backendStarted = $false
$startTime = Get-Date
$timeout = New-TimeSpan -Seconds 2

while (-not $backendStarted -and ((Get-Date) - $startTime) -lt $timeout) {
    $backendOutput = Receive-Job -Job $backendJob
    if ($backendOutput) {
        Write-Host $backendOutput -ForegroundColor Green
        
        # 检查后端是否已启动完成
        if ($backendOutput -match "Application startup complete" -or $backendOutput -match "Uvicorn running on") {
            $backendStarted = $true
            Write-Host "后端服务已成功启动!" -ForegroundColor Green
            Write-Host "-----------------------------------" -ForegroundColor DarkGray
            Write-Host ""
        }
    }
    
    # 检查作业是否失败
    if ($backendJob.State -eq "Failed") {
        Write-Host "错误: 后端服务启动失败!" -ForegroundColor Red
        exit 1
    }
}

# 延迟 3 秒后启动前端
Write-Host "等待 3 秒后启动前端服务..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 直接在当前窗口启动前端，而不是在作业中
Write-Host "前端服务日志:" -ForegroundColor Magenta
Write-Host "-----------------------------------" -ForegroundColor DarkGray
Write-Host "启动前端开发服务器..." -ForegroundColor Cyan

# 创建一个新的进程来运行前端，而不是作业
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd $PWD\frontend && npm run dev" -PassThru -NoNewWindow

try {
    # 只显示后端的输出，前端直接在控制台显示
    while ($true) {
        # 获取并显示后端作业的输出
        $backendOutput = Receive-Job -Job $backendJob
        if ($backendOutput) {
            Write-Host "[ backend ] $backendOutput" -ForegroundColor Green
        }
        
        # 检查后端作业是否仍在运行
        if ($backendJob.State -eq "Failed") {
            Write-Host "错误: 后端服务启动失败!" -ForegroundColor Red
            break
        }
        
        # 检查前端进程是否仍在运行
        if ($frontendProcess.HasExited) {
            Write-Host "错误: 前端服务已停止运行!" -ForegroundColor Red
            break
        }
        
        # 暂停一下再检查新输出
        Start-Sleep -Milliseconds 500
    }
}
finally {
    # 按 Ctrl+C 时清理作业和进程
    Write-Host "`n正在关闭服务..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob
    Remove-Job -Job $backendJob
    
    if (-not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}