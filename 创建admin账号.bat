@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 创建admin管理员账号
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/1] 创建admin账号...
python create_admin_only.py

echo.
pause

