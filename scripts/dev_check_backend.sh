#!/usr/bin/env bash
set -euo pipefail

# 切换到项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PY_BIN=""
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PY_BIN="$ROOT_DIR/.venv/bin/python"
elif [ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]; then
  PY_BIN="$ROOT_DIR/.venv/Scripts/python.exe"
elif command -v python >/dev/null 2>&1; then
  PY_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
else
  echo "❌ 错误: 未找到 Python 解释器，请先安装环境"
  exit 1
fi

echo "============ dev_check_backend: start ============"
echo "当前目录: $ROOT_DIR"
echo ""

# 检查后端目录是否存在
if [ ! -d "$ROOT_DIR/backend" ]; then
    echo "❌ 错误: backend 目录不存在"
    exit 1
fi

echo "=== 后端: 测试 (lint/mypy/pytest) ==="
cd "$ROOT_DIR/backend"

echo "============ dev_check_backend: start ============"
echo "[info] CWD: $(pwd)"
echo "[info] Python: $($PY_BIN --version 2>&1)"

if $PY_BIN -m pip show ruff >/dev/null 2>&1; then
  echo "[step] ruff check (app + alembic + scripts + tools) ..."
  $PY_BIN -m ruff check app alembic scripts tools
else
  echo "[warn] ruff 未安装，跳过 ruff check"
fi

if $PY_BIN -m pip show mypy >/dev/null 2>&1; then
  echo "[step] mypy ..."
  $PY_BIN -m mypy .
else
  echo "[warn] mypy 未安装，跳过 mypy"
fi

if $PY_BIN -m pip show pytest >/dev/null 2>&1; then
  if [ "${1:-}" = "full" ]; then
    echo "[step] pytest (FULL mode - including all tests) ..."
    $PY_BIN -m pytest
  else
    echo "[step] pytest (excluding integration and slow tests) ..."
    $PY_BIN -m pytest -m "not integration and not slow"
  fi
else
  echo "[warn] pytest 未安装，无法运行测试"
  exit 1
fi

echo "============ dev_check_backend: done ============"

echo ""
echo "=== 后端自检完成 ==="
echo ""

# 返回项目根目录
cd ..