@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 服务状态诊断
echo ========================================
echo.

echo [1/4] 检查后端服务 (端口8000)...
netstat -ano | findstr ":8000" >nul
if %errorlevel%==0 (
    echo   [OK] 后端服务正在运行
    echo   测试访问: http://localhost:8000/health
) else (
    echo   [FAIL] 后端服务未运行
    echo   请运行: cd backend ^&^& python main.py
)
echo.

echo [2/4] 检查前端服务 (端口5173)...
netstat -ano | findstr ":5173" >nul
if %errorlevel%==0 (
    echo   [OK] 前端服务正在运行
    echo   访问地址: http://localhost:5173
) else (
    echo   [FAIL] 前端服务未运行
    echo   请运行: cd frontend ^&^& npm run dev
)
echo.

echo [3/4] 测试后端服务访问...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 (
    echo   [OK] 后端服务可以访问
) else (
    echo   [FAIL] 后端服务无法访问
    echo   可能原因: 防火墙阻止或服务未正确启动
)
echo.

echo [4/4] 测试前端服务访问...
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel%==0 (
    echo   [OK] 前端服务可以访问
) else (
    echo   [FAIL] 前端服务无法访问
    echo   可能原因: 服务未启动或端口被占用
)
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.
echo 如果服务未运行，请：
echo   1. 启动后端: cd backend ^&^& python main.py
echo   2. 启动前端: cd frontend ^&^& npm run dev
echo.
pause

