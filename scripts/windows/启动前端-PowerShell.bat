@echo off
REM 这个脚本用于启动PowerShell版本的启动脚本
REM 如果批处理脚本都闪退，这个脚本会尝试使用PowerShell

echo.
echo ========================================
echo   使用PowerShell启动前端服务
echo ========================================
echo.

REM 检查PowerShell是否可用
where powershell >nul 2>&1
if errorlevel 1 (
    echo [错误] PowerShell未找到
    echo 请使用手动启动方法
    pause
    exit /b 1
)

REM 获取脚本所在目录（使用短路径避免中文问题）
set "SCRIPT_DIR=%~dp0"

REM 使用PowerShell执行启动脚本（使用短路径）
for %%I in ("%SCRIPT_DIR%启动前端.ps1") do set "PS_SCRIPT=%%~fI"
powershell -ExecutionPolicy Bypass -File "!PS_SCRIPT!"

REM 如果上面的方法失败，尝试直接使用完整路径
if errorlevel 1 (
    powershell -ExecutionPolicy Bypass -File "F:\VabHub项目\VabHub\启动前端.ps1"
)

if errorlevel 1 (
    echo.
    echo [错误] PowerShell脚本执行失败
    echo.
    echo 请尝试手动启动:
    echo   1. 打开PowerShell
    echo   2. 运行: cd F:\VabHub项目\VabHub\frontend
    echo   3. 运行: npx vite --host 0.0.0.0 --port 5173
    echo.
)

pause

