@echo off
chcp 65001 >nul
title VabHub 前端服务
color 0A

echo.
echo ========================================
echo   VabHub 前端服务启动
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

echo [启动] 使用npx启动Vite开发服务器...
echo.
echo ========================================
echo   前端服务地址:
echo   http://localhost:5173
echo   http://127.0.0.1:5173
echo.
echo   后端服务地址:
echo   http://localhost:8000/docs
echo.
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

npx --yes vite --host 0.0.0.0 --port 5173

echo.
echo [信息] 服务已停止
pause

