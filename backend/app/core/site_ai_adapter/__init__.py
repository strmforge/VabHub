"""
站点 AI 适配模块

提供站点适配配置的自动分析和缓存功能。
"""

from app.core.site_ai_adapter.service import (
    analyze_and_save_for_site,
    get_site_adapter_config,
    maybe_auto_analyze_site,
    load_parsed_config,  # Phase AI-2
)
from app.core.site_ai_adapter.status import (
    get_ai_adapter_status_for_site,  # Phase AI-3
    AISiteAdapterStatus,  # Phase AI-3
)
from app.core.site_ai_adapter.settings import update_site_ai_settings  # Phase AI-4
from app.core.site_ai_adapter.models import (
    AISiteAdapterConfig,
    SiteAIAdapterResult,
    ParsedAISiteAdapterConfig,  # Phase AI-2
    ParsedAISiteSearchConfig,  # Phase AI-2
    ParsedAISiteDetailConfig,  # Phase AI-2
    ParsedAISiteHRConfig,  # Phase AI-2
    ParsedAISiteAuthConfig,  # Phase AI-2
    ParsedAISiteCategoriesConfig,  # Phase AI-2
)

__all__ = [
    "analyze_and_save_for_site",
    "get_site_adapter_config",
    "maybe_auto_analyze_site",
    "load_parsed_config",  # Phase AI-2
    "get_ai_adapter_status_for_site",  # Phase AI-3
    "update_site_ai_settings",  # Phase AI-4
    "AISiteAdapterConfig",
    "SiteAIAdapterResult",
    "AISiteAdapterStatus",  # Phase AI-3
    "ParsedAISiteAdapterConfig",  # Phase AI-2
    "ParsedAISiteSearchConfig",  # Phase AI-2
    "ParsedAISiteDetailConfig",  # Phase AI-2
    "ParsedAISiteHRConfig",  # Phase AI-2
    "ParsedAISiteAuthConfig",  # Phase AI-2
    "ParsedAISiteCategoriesConfig",  # Phase AI-2
]

