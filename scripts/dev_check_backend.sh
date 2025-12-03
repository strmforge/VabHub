#!/usr/bin/env bash
set -e

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "=== VabHub 后端自检脚本 ==="
echo "当前目录: $(pwd)"
echo ""

# 检查后端目录是否存在
if [ ! -d "backend" ]; then
    echo "❌ 错误: backend 目录不存在"
    exit 1
fi

echo "=== 后端: 测试 (pytest) ==="
cd backend

# 检查 pytest 是否可用
if command -v pytest >/dev/null 2>&1; then
    pytest -v
else
    if [ "${GITHUB_ACTIONS:-}" = "true" ] || [ "${VABHUB_CI:-0}" = "1" ]; then
        echo "❌ 错误: pytest 未安装，CI 环境必须安装测试依赖"
        echo "请运行: pip install -r requirements-dev.txt"
        exit 1
    else
        echo "⚠️ 警告: pytest 未安装，本地环境跳过测试"
        echo "请运行: pip install -r requirements-dev.txt"
    fi
fi

echo ""
echo "=== 后端自检完成 ==="
echo ""

# 返回项目根目录
cd ..