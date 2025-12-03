@echo off
chcp 65001 >nul
title VabHub 修复依赖并启动
color 0B

echo.
echo ========================================
echo   VabHub 修复依赖并启动前端服务
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "package.json" (
    echo [错误] 找不到package.json文件
    pause
    exit /b 1
)

echo [1/4] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js未安装
    pause
    exit /b 1
)
node --version
echo.

echo [2/4] 重新安装依赖（包含可选依赖）...
echo 这可能需要几分钟，请耐心等待...
echo.
echo [提示] 正在安装esbuild的可选依赖...
npm install --legacy-peer-deps
if errorlevel 1 (
    echo.
    echo [警告] 安装遇到问题，尝试清理后重新安装...
    echo.
    echo [清理] 删除node_modules和package-lock.json...
    if exist "node_modules" (
        rmdir /s /q "node_modules" 2>nul
    )
    if exist "package-lock.json" (
        del /q "package-lock.json" 2>nul
    )
    echo.
    echo [重新安装] 正在重新安装所有依赖...
    npm install --legacy-peer-deps
)
echo.

echo [3/4] 验证esbuild安装...
if exist "node_modules\@esbuild\win32-x64" (
    echo [成功] esbuild平台依赖已安装
) else (
    echo [警告] esbuild平台依赖可能未正确安装
    echo 尝试手动安装esbuild...
    npm install esbuild --legacy-peer-deps
)
echo.

echo [4/4] 启动前端服务...
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
    echo 请尝试以下方法:
    echo.
    echo 方法1: 清理后重新安装
    echo   cd F:\VabHub项目\VabHub\frontend
    echo   rmdir /s /q node_modules
    echo   del package-lock.json
    echo   npm install --legacy-peer-deps
    echo   npm run dev
    echo.
    echo 方法2: 手动安装esbuild
    echo   cd F:\VabHub项目\VabHub\frontend
    echo   npm install esbuild --legacy-peer-deps
    echo   npm run dev
    echo.
)

pause

