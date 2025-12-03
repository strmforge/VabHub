@echo off
chcp 65001 >nul
title VabHub 前端预览服务
color 0B

echo.
echo ========================================
echo   VabHub 前端预览服务
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [检查] Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js未安装！
    echo 请先安装Node.js: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

echo [选项] 选择预览方式:
echo   1. 开发模式预览 (推荐，支持热更新)
echo   2. 构建后预览 (需要先构建)
echo.
set /p choice="请输入选项 (1 或 2): "

if "%choice%"=="1" (
    echo.
    echo [启动] 开发模式预览...
    echo.
    echo ========================================
    echo   前端预览地址:
    echo   http://localhost:5173
    echo   http://127.0.0.1:5173
    echo.
    echo   后端API地址:
    echo   http://localhost:8000/docs
    echo.
    echo   按 Ctrl+C 停止服务
    echo ========================================
    echo.
    npx --yes vite --host 0.0.0.0 --port 5173
) else if "%choice%"=="2" (
    echo.
    echo [步骤1] 构建生产版本...
    npx --yes vite build
    if errorlevel 1 (
        echo [错误] 构建失败！
        pause
        exit /b 1
    )
    echo.
    echo [步骤2] 启动预览服务...
    echo.
    echo ========================================
    echo   预览地址:
    echo   http://localhost:4173
    echo   http://127.0.0.1:4173
    echo.
    echo   按 Ctrl+C 停止服务
    echo ========================================
    echo.
    npx --yes vite preview --host 0.0.0.0 --port 4173
) else (
    echo [错误] 无效的选项！
    pause
    exit /b 1
)

echo.
echo [信息] 服务已停止
pause

