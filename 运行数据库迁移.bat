@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 订阅模型字段迁移
echo ========================================
echo.

cd /d "%~dp0backend"

echo [信息] 开始迁移订阅表，添加新字段...
echo.

python migrate_subscription.py

echo.
pause

