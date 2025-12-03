@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 重置测试账号密码
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/1] 重置测试账号密码...
python reset_test_passwords.py

echo.
pause

