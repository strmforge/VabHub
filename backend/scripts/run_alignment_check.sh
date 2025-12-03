#!/bin/bash
# 前后端对齐检查脚本
# 需要先启动后端服务

echo "=========================================="
echo "前后端对齐检查"
echo "=========================================="

# 检查后端服务是否运行
echo "检查后端服务状态..."
if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务未运行，请先启动后端服务："
    echo "   cd backend && python main.py"
    exit 1
fi

# 运行对齐检查
echo ""
echo "运行对齐检查..."
cd "$(dirname "$0")/.."
python tools/check_ui_backend_alignment.py \
    --openapi http://localhost:8000/openapi.json \
    --expected tools/ui_expected_endpoints.txt \
    --output alignment_report.json

echo ""
echo "检查完成！报告已保存到: alignment_report.json"

