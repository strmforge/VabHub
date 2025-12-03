"""
Intel / Shared Intelligence 模块
提供统一的别名识别、发布索引查询能力
"""

from app.core.intel.service import (
    IntelService,
    LocalIntelService,
    CloudIntelService,
    HybridIntelService,
    get_intel_service,
    IntelResolveResult,
    IntelReleaseSitesResult,
)

__all__ = [
    "IntelService",
    "LocalIntelService",
    "CloudIntelService",
    "HybridIntelService",
    "get_intel_service",
    "IntelResolveResult",
    "IntelReleaseSitesResult",
]

