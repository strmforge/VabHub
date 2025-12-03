@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 测试订阅管理API
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/1] 测试订阅管理API...
echo.
echo 请确保后端服务已启动 (http://localhost:8000)
echo.
python test_subscription.py

echo.
pause

