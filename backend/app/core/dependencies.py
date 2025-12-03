"""
依赖注入系统
提供统一的依赖注入和服务注册
"""

from typing import Dict, Type, TypeVar, Optional, Any
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger

from app.core.database import get_db
from app.core.cache import get_cache, CacheManager
from app.core.config import settings
from app.models.user import User
from app.core.security import decode_access_token
from app.core.schemas import UnauthorizedResponse, error_response

T = TypeVar('T')

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


class ServiceRegistry:
    """服务注册表"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, name: str, service: Any, singleton: bool = False):
        """注册服务"""
        if singleton:
            self._singletons[name] = service
        else:
            self._services[name] = service
        logger.debug(f"服务已注册: {name} (singleton={singleton})")
    
    def get(self, name: str) -> Optional[Any]:
        """获取服务"""
        if name in self._singletons:
            return self._singletons[name]
        if name in self._services:
            return self._services[name]
        return None
    
    def is_registered(self, name: str) -> bool:
        """检查服务是否已注册"""
        return name in self._services or name in self._singletons


# 全局服务注册表
_service_registry = ServiceRegistry()


def register_service(name: str, service: Any, singleton: bool = False):
    """注册服务到全局注册表"""
    _service_registry.register(name, service, singleton)


def get_service(name: str) -> Optional[Any]:
    """从全局注册表获取服务"""
    return _service_registry.get(name)


# 常用依赖项

async def get_database() -> AsyncSession:
    """获取数据库会话依赖"""
    async for session in get_db():
        yield session


@lru_cache()
def get_cache_manager() -> CacheManager:
    """获取缓存管理器依赖（单例）"""
    return get_cache()


def get_service_dependency(service_name: str):
    """获取服务依赖的工厂函数"""
    def dependency():
        service = get_service(service_name)
        if service is None:
            raise ValueError(f"服务未注册: {service_name}")
        return service
    return dependency


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户依赖"""
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UnauthorizedResponse(
                    error_code="INVALID_TOKEN",
                    error_message="无效的认证凭据"
                ).model_dump()
            )
        
        user = await User.get_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UnauthorizedResponse(
                    error_code="USER_NOT_FOUND",
                    error_message="用户不存在"
                ).model_dump()
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    error_code="USER_DISABLED",
                    error_message="用户已被禁用"
                ).model_dump()
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UnauthorizedResponse(
                error_code="INVALID_TOKEN",
                error_message="无效的认证凭据"
            ).model_dump()
        )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户（需要 admin 角色或 is_superuser）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_admin(user: User) -> User:
    """
    要求管理员权限的辅助函数
    LAUNCH-1 L3-2 实现
    
    用法：
        @router.get("/admin/something")
        async def admin_endpoint(current_user: User = Depends(get_current_user)):
            require_admin(current_user)
            ...
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


def require_not_viewer(user: User) -> User:
    """
    要求非只读用户的辅助函数
    LAUNCH-1 L3-2 实现
    """
    if user.is_viewer_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只读用户无法执行此操作"
        )
    return user
