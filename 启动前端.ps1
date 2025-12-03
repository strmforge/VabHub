# VabHub 前端服务启动脚本 (PowerShell版本)
# 如果批处理脚本闪退，请使用这个PowerShell脚本

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VabHub 前端服务启动 (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Node.js
Write-Host "[1/4] 检查Node.js环境..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [成功] Node.js已安装: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "  [失败] Node.js未安装或未添加到PATH" -ForegroundColor Red
        Write-Host "  请安装Node.js: https://nodejs.org/" -ForegroundColor Yellow
        Read-Host "按回车键退出"
        exit 1
    }
} catch {
    Write-Host "  [失败] Node.js未安装或未添加到PATH" -ForegroundColor Red
    Write-Host "  请安装Node.js: https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 检查npm
Write-Host "[2/4] 检查npm环境..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [成功] npm已安装: $npmVersion" -ForegroundColor Green
    } else {
        Write-Host "  [失败] npm未找到" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
} catch {
    Write-Host "  [失败] npm未找到" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 进入frontend目录
Write-Host "[3/4] 进入frontend目录..." -ForegroundColor Yellow
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Join-Path $scriptPath "frontend"

if (Test-Path $frontendPath) {
    Set-Location $frontendPath
    Write-Host "  [成功] 当前目录: $(Get-Location)" -ForegroundColor Green
} else {
    Write-Host "  [失败] frontend目录不存在: $frontendPath" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 启动服务
Write-Host "[4/4] 启动前端服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  前端服务将启动在:" -ForegroundColor White
Write-Host "  http://localhost:5173" -ForegroundColor Green
Write-Host "  http://127.0.0.1:5173" -ForegroundColor Green
Write-Host ""
Write-Host "  后端API地址:" -ForegroundColor White
Write-Host "  http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "  按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    npx --yes vite --host 0.0.0.0 --port 5173
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  [错误] 前端服务启动失败！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "错误信息: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请尝试:" -ForegroundColor Yellow
    Write-Host "  1. 检查网络连接" -ForegroundColor White
    Write-Host "  2. 检查端口5173是否被占用" -ForegroundColor White
    Write-Host "  3. 使用其他端口: npx vite --host 0.0.0.0 --port 5174" -ForegroundColor White
    Write-Host ""
    Read-Host "按回车键退出"
}

