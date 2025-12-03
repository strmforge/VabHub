@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 前端服务启动（使用npx）
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: Node.js未安装或未添加到PATH
    pause
    exit /b 1
)
echo.

echo [2/2] 启动前端服务（使用npx vite）...
echo ========================================
echo 前端服务将启动在:
echo   http://localhost:5173
echo   http://127.0.0.1:5173
echo.
echo 请确保后端服务已启动在 http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

npx vite --host --port 5173 --config vite.config.ts

if errorlevel 1 (
    echo.
    echo [错误] 前端服务启动失败！
    echo.
    echo 尝试安装依赖...
    call npm install --legacy-peer-deps --ignore-scripts
    echo.
    echo 再次尝试启动...
    npx vite --host --port 5173 --config vite.config.ts
)

pause

