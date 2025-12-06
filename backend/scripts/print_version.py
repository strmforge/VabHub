#!/usr/bin/env python3
"""
打印当前版本号（供 CI 调用）

DOCKER-RELEASE-1 实现

用法：
    python backend/scripts/print_version.py
"""

import sys
from pathlib import Path

# 确保可以导入 backend 模块
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.version import APP_VERSION

if __name__ == "__main__":
    print(APP_VERSION)
