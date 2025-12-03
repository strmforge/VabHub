@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 服务重启脚本（双宽带网络）
echo ========================================
echo.

echo [1/3] 检查后端服务...
cd backend
if exist "main.py" (
    echo 后端文件存在
) else (
    echo 错误: 找不到后端文件
    pause
    exit /b 1
)

echo.
echo [2/3] 检查前端服务...
cd ..\frontend
if exist "package.json" (
    echo 前端文件存在
) else (
    echo 错误: 找不到前端文件
    pause
    exit /b 1
)

echo.
echo [3/3] 启动服务...
echo ========================================
echo 前端服务将启动在:
echo   - http://localhost:5173
echo   - http://127.0.0.1:5173
echo   - http://192.168.51.101:5173
echo   - http://192.168.50.108:5173
echo.
echo 后端服务将启动在:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo   - http://192.168.51.101:8000
echo   - http://192.168.50.108:8000
echo.
echo 请确保后端服务已启动！
echo 按 Ctrl+C 停止前端服务
echo ========================================
echo.

npm run dev

pause

