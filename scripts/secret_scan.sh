#!/bin/bash
# VabHub Secret Scanner
# 扫描代码中可能的敏感信息泄露
#
# 用法: ./scripts/secret_scan.sh [--strict]
#   --strict: 严格模式，发现问题时返回非零退出码

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 参数解析
STRICT_MODE=false
if [[ "$1" == "--strict" ]]; then
    STRICT_MODE=true
fi

echo "========================================"
echo "  VabHub Secret Scanner"
echo "========================================"
echo ""

cd "$PROJECT_ROOT"

# 计数器
WARNINGS=0
ERRORS=0

# 检查是否安装了 ripgrep
if command -v rg &> /dev/null; then
    GREP_CMD="rg"
else
    GREP_CMD="grep -rn"
fi

# 定义敏感模式
PATTERNS=(
    # 硬编码密码
    "password.*=.*['\"][^${}][^'\"]{4,}['\"]"
    "passwd.*=.*['\"][^${}][^'\"]{4,}['\"]"
    # API Keys
    "api_key.*=.*['\"][^${}][^'\"]{10,}['\"]"
    "apikey.*=.*['\"][^${}][^'\"]{10,}['\"]"
    # AWS
    "AKIA[0-9A-Z]{16}"
    # Private Keys
    "BEGIN.*PRIVATE KEY"
    # JWT/Secret
    "secret.*=.*['\"][^${}change][^'\"]{10,}['\"]"
    # Bearer tokens
    "bearer.*['\"][^${}][^'\"]{20,}['\"]"
)

# 白名单路径（允许包含示例密码的文件）
WHITELIST_PATHS=(
    "docs/SECURITY"
    "scripts/secret_scan.sh"
    "*.md"  # markdown 文档中的示例代码允许
)

# 构建排除参数
EXCLUDE_ARGS=""
if [[ "$GREP_CMD" == "rg" ]]; then
    EXCLUDE_ARGS="--glob '!.git' --glob '!node_modules' --glob '!*.pyc' --glob '!dist' --glob '!.venv' --glob '!venv'"
    for path in "${WHITELIST_PATHS[@]}"; do
        EXCLUDE_ARGS="$EXCLUDE_ARGS --glob '!$path'"
    done
fi

echo "🔍 扫描敏感信息模式..."
echo ""

# 扫描函数
scan_pattern() {
    local pattern=$1
    local description=$2
    
    if [[ "$GREP_CMD" == "rg" ]]; then
        results=$(rg -i --glob '!.git' --glob '!node_modules' --glob '!*.pyc' --glob '!dist' --glob '!.venv' --glob '!venv' --glob '!docs/SECURITY*' --glob '!scripts/secret_scan.sh' -l "$pattern" 2>/dev/null || true)
    else
        results=$(grep -rln --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.venv --exclude-dir=venv -E "$pattern" . 2>/dev/null || true)
    fi
    
    if [[ -n "$results" ]]; then
        echo -e "${YELLOW}⚠️  可能的敏感信息: $description${NC}"
        echo "   文件:"
        echo "$results" | while read -r file; do
            echo "   - $file"
        done
        echo ""
        return 1
    fi
    return 0
}

# 特定检查：硬编码的 vabhub_password（应该已被清理）
echo "📋 检查 1: 硬编码默认密码"
if $GREP_CMD -l "vabhub_password" --glob '!docs/SECURITY*' --glob '!scripts/secret_scan.sh' --glob '!*.md' . 2>/dev/null | grep -v "CHANGE-ME" > /dev/null 2>&1; then
    echo -e "${RED}❌ 发现硬编码的 vabhub_password！${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ 未发现硬编码的 vabhub_password${NC}"
fi
echo ""

# 特定检查：docker-compose 中的明文密码
echo "📋 检查 2: Docker Compose 配置"
if $GREP_CMD -l "PASSWORD:.*['\"].*['\"]" docker-compose*.yml 2>/dev/null | head -1 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  docker-compose 中可能存在明文密码${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ Docker Compose 配置安全${NC}"
fi
echo ""

# 特定检查：.env 文件是否被 gitignore
echo "📋 检查 3: .env 文件保护"
if grep -q "^\.env$" .gitignore 2>/dev/null && grep -q "^\.env\.docker$" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ .env 和 .env.docker 已在 .gitignore 中${NC}"
else
    echo -e "${RED}❌ .env 文件可能未被 .gitignore 保护！${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 特定检查：.env.example 中是否有真实密码
echo "📋 检查 4: 模板文件占位符"
if grep -E "PASSWORD=.*[^CHANGE].*[^-]$" .env*.example 2>/dev/null | grep -v "CHANGE-ME" | grep -v "change-" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  .env.example 中可能存在非占位符密码${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ 模板文件使用了占位符密码${NC}"
fi
echo ""

# 总结
echo "========================================"
echo "  扫描结果"
echo "========================================"
echo ""
echo "错误: $ERRORS"
echo "警告: $WARNINGS"
echo ""

if [[ $ERRORS -gt 0 ]]; then
    echo -e "${RED}❌ 发现 $ERRORS 个严重问题，请修复后再提交！${NC}"
    if [[ "$STRICT_MODE" == true ]]; then
        exit 1
    fi
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  发现 $WARNINGS 个警告，请检查确认${NC}"
else
    echo -e "${GREEN}✅ 未发现敏感信息泄露风险${NC}"
fi

echo ""
echo "提示: 如需跳过某些文件，请编辑脚本中的 WHITELIST_PATHS"
