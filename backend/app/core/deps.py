"""
依赖注入简写入口
重新导出 dependencies.py 中的常用依赖
"""

from app.core.dependencies import (
    get_db,
    get_database,
    get_cache_manager,
    get_current_user,
    get_current_admin_user,
    require_admin,
    require_not_viewer,
    oauth2_scheme,
    register_service,
    get_service,
)
from app.core.database import get_db

__all__ = [
    "get_db",
    "get_database",
    "get_cache_manager",
    "get_current_user",
    "get_current_admin_user",
    "require_admin",
    "require_not_viewer",
    "oauth2_scheme",
    "register_service",
    "get_service",
]
