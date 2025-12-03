"""
依赖注入简写入口
重新导出 dependencies.py 中的常用依赖
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

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

# 依赖别名，用于简化路由函数参数声明
DbSessionDep = Annotated[AsyncSession, Depends(get_database)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentAdminUserDep = Annotated[User, Depends(get_current_admin_user)]

__all__ = [
    "get_db",
    "get_database",
    "DbSessionDep",
    "CurrentUserDep",
    "CurrentAdminUserDep",
    "get_cache_manager",
    "get_current_user",
    "get_current_admin_user",
    "require_admin",
    "require_not_viewer",
    "oauth2_scheme",
    "register_service",
    "get_service",
]
