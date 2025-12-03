@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 检查现有用户
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/1] 检查用户...
python check_users.py

echo.
pause

