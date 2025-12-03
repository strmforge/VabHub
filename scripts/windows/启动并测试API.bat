@echo off
echo ========================================
echo VabHub 启动并测试API
echo ========================================
echo.

cd backend

echo [1/3] 检查后端服务是否运行...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% == 0 (
    echo 后端服务已在运行
    goto :test
)

echo [2/3] 启动后端服务...
start "VabHub Backend" cmd /k "python main.py"
echo 等待服务启动...
timeout /t 5 /nobreak >nul 2>&1

:test
echo [3/3] 运行API测试...
python test_api_direct.py

echo.
echo ========================================
pause

