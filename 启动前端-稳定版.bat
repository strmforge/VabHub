@echo off
chcp 65001 >nul
title VabHub 前端服务启动
color 0A

echo.
echo ========================================
echo   VabHub 前端服务启动（稳定版）
echo ========================================
echo.

cd /d "%~dp0frontend"
if errorlevel 1 (
    echo [错误] 无法进入frontend目录！
    echo 请确认脚本在VabHub根目录下运行
    pause
    exit /b 1
)

echo [1/4] 检查当前目录...
echo 当前目录: %CD%
echo.

echo [2/4] 检查Node.js环境...
where node >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js未安装或未添加到PATH！
    echo.
    echo 请：
    echo   1. 安装Node.js: https://nodejs.org/
    echo   2. 重启命令提示符
    echo   3. 验证安装: node --version
    echo.
    pause
    exit /b 1
)
node --version
echo.

echo [3/4] 检查npm环境...
where npm >nul 2>&1
if errorlevel 1 (
    echo [错误] npm未安装或未添加到PATH！
    pause
    exit /b 1
)
npm --version
echo.

echo [4/4] 启动前端服务...
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
echo [提示] 如果看到错误信息，请复制完整的错误内容
echo.

npx --yes vite --host 0.0.0.0 --port 5173

if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 前端服务启动失败！
    echo ========================================
    echo.
    echo 可能的原因:
    echo   1. 端口5173被占用
    echo   2. 网络连接问题
    echo   3. Node.js版本不兼容
    echo.
    echo 请尝试:
    echo   1. 检查端口占用: netstat -ano ^| findstr ":5173"
    echo   2. 使用其他端口: npx vite --host 0.0.0.0 --port 5174
    echo   3. 检查网络连接
    echo.
    echo 如果问题持续，请复制上面的错误信息
    echo.
)

echo.
echo [信息] 服务已停止
pause

