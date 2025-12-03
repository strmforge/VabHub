@echo off
chcp 65001 >nul
echo ============================================================
echo VabHub API序列化修复 - 运行测试
echo ============================================================
echo.

cd /d "%~dp0"

echo 检查服务状态...
python backend\scripts\check_service_status.py
if errorlevel 1 (
    echo.
    echo [警告] 服务未运行
    echo 请先启动服务: python backend\run_server.py
    echo 或运行: 启动并测试.bat
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 选择测试类型
echo ============================================================
echo.
echo 1. 快速测试（推荐）
echo 2. 功能测试
echo 3. 基础测试
echo 4. API端点测试
echo 5. 全部测试
echo.
set /p choice=请选择 (1-5): 

if "%choice%"=="1" (
    echo.
    echo 运行快速测试...
    python backend\scripts\quick_test.py
) else if "%choice%"=="2" (
    echo.
    echo 运行功能测试...
    python backend\scripts\test_functional.py
) else if "%choice%"=="3" (
    echo.
    echo 运行基础测试...
    python backend\scripts\test_simple.py
) else if "%choice%"=="4" (
    echo.
    echo 运行API端点测试...
    python backend\scripts\test_api_endpoints.py
) else if "%choice%"=="5" (
    echo.
    echo 运行全部测试...
    python backend\scripts\run_tests.py
) else (
    echo.
    echo [错误] 无效选择
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 测试完成
echo ============================================================
pause

