@echo off
chcp 65001 >nul
echo ============================================================
echo VabHub 快速启动服务
echo ============================================================
echo.

cd /d "%~dp0\backend"

echo 启动服务中...
echo 主机: 0.0.0.0
echo 端口: 8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ============================================================
echo.

python run_server.py

pause

