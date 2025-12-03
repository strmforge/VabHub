@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 前端服务手动启动
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [1/3] 检查当前目录...
cd
echo 当前目录: %CD%
echo.

echo [2/3] 检查依赖...
if not exist "node_modules" (
    echo 依赖未安装，正在安装...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败！
        echo 请检查网络连接和Node.js安装
        pause
        exit /b 1
    )
) else (
    echo 依赖已存在
)
echo.

echo [3/3] 启动前端服务...
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

npm run dev

if errorlevel 1 (
    echo.
    echo [错误] 前端服务启动失败！
    echo.
    echo 可能的原因:
    echo   1. 端口5173被占用
    echo   2. 依赖未正确安装
    echo   3. Node.js版本不兼容
    echo.
    echo 请检查上面的错误信息
    pause
)

