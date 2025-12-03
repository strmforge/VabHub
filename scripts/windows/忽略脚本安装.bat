@echo off
chcp 65001 >nul
title VabHub 忽略脚本安装依赖
color 0B

echo.
echo ========================================
echo   VabHub 忽略脚本安装依赖
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "package.json" (
    echo [错误] 找不到package.json文件
    pause
    exit /b 1
)

echo [信息] 当前目录: %CD%
echo.

echo [安装] 正在安装依赖（忽略脚本）...
echo 这可以避免patch-package等脚本问题
echo 这可能需要几分钟，请耐心等待...
echo.

npm install --legacy-peer-deps --ignore-scripts

if errorlevel 1 (
    echo.
    echo [警告] 安装遇到问题，但继续尝试启动...
    echo.
) else (
    echo.
    echo [成功] 依赖安装完成
    echo.
)

echo [启动] 启动前端服务...
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

npm run dev

if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 启动失败
    echo ========================================
    echo.
    echo 如果esbuild相关错误，请尝试:
    echo   npm install esbuild --legacy-peer-deps
    echo.
)

pause

