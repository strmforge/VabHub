#!/usr/bin/env bash
set -e

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "=== VabHub 前端自检脚本 ==="
echo "当前目录: $(pwd)"
echo ""

# 检查前端目录是否存在
if [ ! -d "frontend" ]; then
    echo "❌ 错误: frontend 目录不存在"
    exit 1
fi

echo "=== 前端: 代码检查 (ESLint) ==="
cd frontend

# 检查 pnpm 是否可用
if command -v pnpm >/dev/null 2>&1; then
    echo "使用 pnpm 执行检查..."
    
    # 检查 lint 脚本是否存在
    if pnpm run | grep -q "^  lint"; then
        pnpm lint
    else
        echo "⚠️ 警告: lint 脚本不存在，跳过代码检查"
    fi
    
    echo ""
    echo "=== 前端: 类型检查 (TypeScript) ==="
    
    # 检查 typecheck 脚本是否存在
    if pnpm run | grep -q "^  typecheck"; then
        pnpm typecheck
    else
        echo "⚠️ 警告: typecheck 脚本不存在，跳过类型检查"
    fi
    
    echo ""
    echo "=== 前端: 构建检查 ==="
    
    # 检查 build 脚本是否存在
    if pnpm run | grep -q "^  build"; then
        pnpm build
    else
        echo "⚠️ 警告: build 脚本不存在，跳过构建检查"
    fi
    
else
    echo "❌ 错误: pnpm 未安装"
    echo "请先安装 pnpm: npm install -g pnpm"
    exit 1
fi

echo ""
echo "=== 前端自检完成 ==="
echo ""

# 返回项目根目录
cd ..