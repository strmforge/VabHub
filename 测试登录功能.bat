@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 测试登录功能
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/1] 测试登录功能...
echo.
echo 请确保后端服务已启动 (http://localhost:8000)
echo.
python test_login.py

echo.
pause

