@echo off
chcp 65001 >nul
echo ============================================================
echo VabHub API序列化修复 - 启动并测试
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH
    echo 请先安装Python并添加到系统PATH
    pause
    exit /b 1
)
echo [OK] Python环境正常
echo.

echo [2/3] 启动后端服务...
echo 注意: 服务将在后台启动，请在新窗口中运行测试
echo.
start "VabHub后端服务" cmd /k "python backend\run_server.py"
echo [OK] 后端服务已启动（新窗口）
echo.

echo [3/3] 等待服务启动（10秒）...
timeout /t 10 /nobreak >nul
echo.

echo ============================================================
echo 服务已启动，现在可以运行测试
echo ============================================================
echo.
echo 运行测试的方法:
echo   1. 打开新的终端窗口
echo   2. 运行: python backend\scripts\quick_test.py
echo   3. 或运行: python backend\scripts\test_functional.py
echo.
echo 或者按任意键自动运行快速测试...
pause >nul

echo.
echo 运行快速测试...
python backend\scripts\quick_test.py

echo.
echo ============================================================
echo 测试完成
echo ============================================================
pause
