@echo off
chcp 65001 >nul
title VabHub 安装依赖并启动
color 0B

echo.
echo ========================================
echo   VabHub 安装依赖并启动前端服务
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "package.json" (
    echo [错误] 找不到package.json文件
    echo 请确认脚本在VabHub根目录下运行
    pause
    exit /b 1
)

echo [1/3] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js未安装或未添加到PATH
    echo 请安装Node.js: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

echo [2/3] 检查依赖...
if exist "node_modules\vite" (
    echo [信息] vite已安装，跳过安装步骤
) else (
    echo [信息] vite未安装，正在安装依赖...
    echo 这可能需要几分钟，请耐心等待...
    echo.
    npm install --legacy-peer-deps --ignore-scripts
    if errorlevel 1 (
        echo.
        echo [警告] 依赖安装遇到问题，但继续尝试启动...
        echo.
    ) else (
        echo.
        echo [成功] 依赖安装完成
        echo.
    )
)
echo.

echo [3/3] 启动前端服务...
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

REM 尝试使用本地安装的vite
if exist "node_modules\.bin\vite.cmd" (
    echo [信息] 使用本地安装的vite...
    call node_modules\.bin\vite.cmd --host 0.0.0.0 --port 5173
) else (
    echo [信息] 使用npx下载并运行vite...
    npx --yes vite --host 0.0.0.0 --port 5173
)

if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 启动失败
    echo ========================================
    echo.
    echo 请尝试手动安装依赖:
    echo   cd F:\VabHub项目\VabHub\frontend
    echo   npm install --legacy-peer-deps
    echo   npm run dev
    echo.
)

pause

