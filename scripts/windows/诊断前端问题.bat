@echo off
chcp 65001 >nul
title VabHub 前端问题诊断
color 0E

echo.
echo ========================================
echo   VabHub 前端问题诊断工具
echo ========================================
echo.

echo [1/6] 检查Node.js安装...
where node >nul 2>&1
if errorlevel 1 (
    echo   [失败] Node.js未安装或未添加到PATH
    echo   请安装Node.js: https://nodejs.org/
) else (
    echo   [成功] Node.js已安装
    node --version
)
echo.

echo [2/6] 检查npm安装...
where npm >nul 2>&1
if errorlevel 1 (
    echo   [失败] npm未安装或未添加到PATH
) else (
    echo   [成功] npm已安装
    npm --version
)
echo.

echo [3/6] 检查frontend目录...
cd /d "%~dp0frontend"
if errorlevel 1 (
    echo   [失败] frontend目录不存在
) else (
    echo   [成功] frontend目录存在
    echo   当前目录: %CD%
)
echo.

echo [4/6] 检查package.json...
if exist "package.json" (
    echo   [成功] package.json存在
) else (
    echo   [失败] package.json不存在
)
echo.

echo [5/6] 检查端口5173占用...
netstat -ano | findstr ":5173" >nul 2>&1
if errorlevel 1 (
    echo   [成功] 端口5173未被占用
) else (
    echo   [警告] 端口5173已被占用
    echo   占用进程:
    netstat -ano | findstr ":5173"
)
echo.

echo [6/6] 测试npx命令...
npx --version >nul 2>&1
if errorlevel 1 (
    echo   [失败] npx命令不可用
) else (
    echo   [成功] npx命令可用
    npx --version
)
echo.

echo ========================================
echo   诊断完成
echo ========================================
echo.
echo 如果所有检查都通过，请尝试手动启动:
echo   cd frontend
echo   npx vite --host 0.0.0.0 --port 5173
echo.
pause

