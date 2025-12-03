@echo off
chcp 65001 >nul
title VabHub 前端服务启动
color 0A

echo.
echo ========================================
echo   VabHub 前端服务启动（直接方式）
echo ========================================
echo.

REM 直接进入frontend目录并启动
cd /d "%~dp0frontend"

if not exist "package.json" (
    echo [错误] 找不到package.json文件
    echo 请确认脚本在VabHub根目录下运行
    pause
    exit /b 1
)

echo [信息] 当前目录: %CD%
echo.

echo [启动] 使用npx启动Vite...
echo.
echo ========================================
echo   前端服务将启动在:
echo   http://localhost:5173
echo   http://127.0.0.1:5173
echo.
echo   后端API地址:
echo   http://localhost:8000/docs
echo.
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

REM 直接调用npx，不依赖其他脚本
npx --yes vite --host 0.0.0.0 --port 5173

if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 启动失败
    echo ========================================
    echo.
    echo 请尝试手动启动:
    echo   1. 打开命令提示符或PowerShell
    echo   2. 运行: cd F:\VabHub项目\VabHub\frontend
    echo   3. 运行: npx vite --host 0.0.0.0 --port 5173
    echo.
)

pause

