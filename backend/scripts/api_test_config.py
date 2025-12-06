"""
测试脚本公共配置
统一维护 API 基础地址与前缀，避免各脚本重复写死 /api/v1
"""

from __future__ import annotations

import os

DEFAULT_BASE_URL = "http://127.0.0.1:8000"

# 允许通过环境变量覆盖，保持向后兼容
# 注意：后端 API_PREFIX 为 /api（见 app/core/config.py）
API_BASE_URL = os.environ.get("API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
API_PREFIX = os.environ.get("API_PREFIX", "/api")


def api_url(path: str) -> str:
    """
    生成完整的 API 地址
    Args:
        path: 以 / 开头或不带 / 的 API 路径（例如 "auth/login" 或 "/auth/login"）
    """
    if not path.startswith("/"):
        path = f"/{path}"

    prefix = API_PREFIX or ""
    if prefix.endswith("/"):
        prefix = prefix.rstrip("/")

    return f"{API_BASE_URL}{prefix}{path}"


