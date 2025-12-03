@echo off
chcp 65001 >nul
echo ========================================
echo VabHub 服务启动和测试脚本
echo ========================================
echo.

echo [1/4] 检查后端服务状态...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ 后端服务未运行
    echo.
    echo 正在启动后端服务...
    start "VabHub Backend" cmd /k "cd /d F:\VabHub项目\VabHub\backend && python main.py"
    echo 等待后端服务启动...
    timeout /t 5 /nobreak >nul
) else (
    echo ✅ 后端服务正在运行
)

echo.
echo [2/4] 检查前端依赖...
cd /d F:\VabHub项目\VabHub\frontend
if not exist "node_modules" (
    echo 依赖未安装，正在安装...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo ✅ 依赖已安装
)

echo.
echo [3/4] 启动前端服务...
echo ========================================
echo 前端地址: http://localhost:5173
echo 后端API: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 测试地址:
echo - 推荐设置: http://localhost:5173/recommendations
echo - 媒体识别: http://localhost:5173/media-identification
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

start "VabHub Frontend" cmd /k "cd /d F:\VabHub项目\VabHub\frontend && npm run dev"

echo.
echo [4/4] 等待服务启动...
timeout /t 3 /nobreak >nul

echo.
echo ✅ 服务启动完成！
echo.
echo 📋 下一步操作:
echo 1. 打开浏览器访问 http://localhost:5173
echo 2. 测试推荐设置功能
echo 3. 测试文件上传功能
echo 4. 查看 API 文档 http://localhost:8000/docs
echo.
pause

