@echo off
chcp 65001 >nul
title VabHub 使用短路径启动
color 0B

echo.
echo ========================================
echo   VabHub 使用短路径启动前端服务
echo ========================================
echo.

REM 使用短路径名避免中文问题
for /f "tokens=*" %%I in ('forfiles /p "%~dp0" /m "frontend" /c "cmd /c echo @path" 2^>nul') do set "FRONTEND_DIR=%%I"

REM 如果上面的方法失败，尝试直接使用完整路径
if not defined FRONTEND_DIR (
    set "FRONTEND_DIR=%~dp0frontend"
)

REM 进入目录
cd /d "%FRONTEND_DIR%"
if errorlevel 1 (
    echo [错误] 无法进入frontend目录
    echo.
    echo 请尝试手动进入:
    echo   1. 打开文件资源管理器
    echo   2. 导航到: F:\VabHub项目\VabHub\frontend
    echo   3. 在地址栏输入: cmd
    echo   4. 按回车
    echo.
    pause
    exit /b 1
)

echo [成功] 当前目录: %CD%
echo.

REM 检查package.json
if not exist "package.json" (
    echo [错误] 找不到package.json文件
    echo 当前目录: %CD%
    pause
    exit /b 1
)

REM 检查依赖
if not exist "node_modules\vite" (
    echo [信息] vite未安装，正在安装依赖...
    echo 这可能需要几分钟，请耐心等待...
    echo.
    npm install --legacy-peer-deps
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo.
    echo [成功] 依赖安装完成
    echo.
)

REM 启动服务
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

pause

