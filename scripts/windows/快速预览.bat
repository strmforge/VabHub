@echo off
chcp 65001 >nul
title VabHub 快速预览
color 0A

echo.
echo ========================================
echo   VabHub 快速预览 (开发模式)
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [启动] 使用npx启动Vite开发服务器...
echo.
echo ========================================
echo   预览地址:
echo   http://localhost:5173
echo   http://127.0.0.1:5173
echo.
echo   后端API:
echo   http://localhost:8000/docs
echo.
echo   按 Ctrl+C 停止
echo ========================================
echo.

npx --yes vite --host 0.0.0.0 --port 5173

pause

