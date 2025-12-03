@echo off
echo ========================================
echo VabHub 后端服务启动脚本
echo ========================================
echo.

cd backend

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH
    pause
    exit /b 1
)

echo.
echo [2/3] 检查依赖...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo 依赖未安装，正在安装...
    pip install -r ../requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo [3/3] 初始化数据库...
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
if errorlevel 1 (
    echo 警告: 数据库初始化可能失败，但继续启动...
)

echo.
echo ========================================
echo 启动后端服务...
echo ========================================
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python main.py

pause

