#!/bin/bash
# 启动后端服务并运行前后端对齐检查

echo "=========================================="
echo "启动后端服务并运行前后端对齐检查"
echo "=========================================="

# 切换到后端目录
cd "$(dirname "$0")/.."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python"
    exit 1
fi

# 启动后端服务（后台运行）
echo "启动后端服务..."
python main.py &
BACKEND_PID=$!

# 等待服务启动
echo "等待服务启动（最多30秒）..."
for i in {1..30}; do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "后端服务已启动"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "错误: 后端服务启动超时"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# 运行对齐检查
echo ""
echo "运行前后端对齐检查..."
python tools/check_ui_backend_alignment.py \
    --openapi http://localhost:8000/openapi.json \
    --expected tools/ui_expected_endpoints.txt \
    --output alignment_report.json

CHECK_EXIT_CODE=$?

# 保存报告
if [ -f alignment_report.json ]; then
    echo ""
    echo "对齐检查报告已保存到: alignment_report.json"
    cat alignment_report.json | python -m json.tool
fi

# 停止后端服务
echo ""
echo "停止后端服务..."
kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null

# 返回检查结果
exit $CHECK_EXIT_CODE

