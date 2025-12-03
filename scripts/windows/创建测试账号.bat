@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 创建测试账号
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/2] 检查Python环境...
python --version
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

echo.
echo [2/2] 创建测试账号...
python create_test_user.py

echo.
echo ========================================
echo 完成！
echo ========================================
echo.
echo 测试账号信息：
echo   用户名: admin    密码: admin123  (管理员)
echo   用户名: test     密码: test123   (普通用户)
echo   用户名: demo     密码: demo123   (普通用户)
echo.
pause

