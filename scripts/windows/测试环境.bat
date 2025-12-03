@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   环境测试
echo ========================================
echo.

echo [测试1] 检查命令提示符是否工作...
echo 如果看到这行，说明批处理可以运行
echo.

echo [测试2] 检查当前目录...
cd
echo 当前目录: %CD%
echo.

echo [测试3] 检查Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo   [失败] Node.js未安装或未添加到PATH
    echo   这是导致闪退的主要原因！
) else (
    echo   [成功] Node.js已找到
    node --version
)
echo.

echo [测试4] 检查npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo   [失败] npm未找到
) else (
    echo   [成功] npm已找到
    npm --version
)
echo.

echo [测试5] 检查frontend目录...
if exist "frontend" (
    echo   [成功] frontend目录存在
) else (
    echo   [失败] frontend目录不存在
    echo   请确认脚本在VabHub根目录下运行
)
echo.

echo ========================================
echo   测试完成
echo ========================================
echo.
echo 如果看到"Node.js未安装"，请：
echo   1. 安装Node.js: https://nodejs.org/
echo   2. 安装时选择"Add to PATH"
echo   3. 重启命令提示符
echo.
pause

