@echo off
chcp 65001 >nul
title VabHub 完整修复步骤
color 0B

echo.
echo ========================================
echo   VabHub 完整修复步骤
echo ========================================
echo.

REM 进入frontend目录
echo [步骤1] 进入frontend目录...
cd /d "%~dp0frontend"
if errorlevel 1 (
    echo [错误] 无法进入frontend目录
    echo 请确认脚本在VabHub根目录下运行
    pause
    exit /b 1
)
echo [成功] 当前目录: %CD%
echo.

REM 删除node_modules
echo [步骤2] 删除旧的node_modules目录...
if exist "node_modules" (
    echo 正在删除，请稍候...
    rmdir /s /q "node_modules"
    if errorlevel 1 (
        echo [警告] 删除node_modules时遇到问题，继续执行...
    ) else (
        echo [成功] node_modules已删除
    )
) else (
    echo [信息] node_modules不存在，跳过
)
echo.

REM 删除package-lock.json
echo [步骤3] 删除package-lock.json...
if exist "package-lock.json" (
    del /q "package-lock.json"
    echo [成功] package-lock.json已删除
) else (
    echo [信息] package-lock.json不存在，跳过
)
echo.

REM 重新安装依赖
echo [步骤4] 重新安装依赖（包含可选依赖）...
echo 这可能需要几分钟，请耐心等待...
echo.
npm install --legacy-peer-deps
if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败
    echo.
    echo 请尝试:
    echo   1. 检查网络连接
    echo   2. 使用国内镜像: npm config set registry https://registry.npmmirror.com
    echo   3. 重新运行此脚本
    echo.
    pause
    exit /b 1
)
echo.
echo [成功] 依赖安装完成
echo.

REM 验证esbuild安装
echo [步骤5] 验证esbuild安装...
if exist "node_modules\@esbuild\win32-x64\esbuild.exe" (
    echo [成功] esbuild已正确安装
) else (
    echo [警告] esbuild可能未正确安装，尝试手动安装...
    npm install esbuild --legacy-peer-deps
)
echo.

REM 启动服务
echo [步骤6] 启动前端服务...
echo.
echo ========================================
echo   前端服务将启动在:
echo   http://localhost:5173
echo   http://127.0.0.1:5173
echo.
echo   后端API地址:
echo   http://localhost:8000/docs
echo.
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

npm run dev

if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 启动失败
    echo ========================================
    echo.
    echo 请检查上面的错误信息
    echo.
)

pause

