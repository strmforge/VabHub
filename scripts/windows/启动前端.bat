@echo off
echo ========================================
echo VabHub 前端服务启动脚本
echo ========================================
echo.

cd frontend

echo [1/3] 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: Node.js未安装或未添加到PATH
    pause
    exit /b 1
)

echo.
echo [2/3] 检查依赖...
if not exist "node_modules" (
    echo 依赖未安装，正在安装...
    call npm install
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo 依赖已安装
)

echo.
echo [3/3] 启动前端服务...
echo ========================================
echo 访问地址: http://localhost:5173
echo 后端API: http://localhost:8000
echo.
echo 请确保后端服务已启动！
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

npm run dev

pause

