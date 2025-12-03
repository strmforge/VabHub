"""
插件配置客户端
PLUGIN-UX-3 实现

允许插件在运行时读取自己的配置
"""

from typing import Any, Optional, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from app.plugin_sdk.context import PluginContext


class ConfigClient:
    """
    插件配置客户端
    
    提供插件配置的读取能力。
    
    Example:
        # 获取完整配置
        config = await sdk.config.get()
        api_key = config.get("api_key", "")
        
        # 获取单个配置项
        max_items = await sdk.config.get_value("max_items", default=10)
    """
    
    def __init__(self, ctx: "PluginContext") -> None:
        """
        初始化配置客户端
        
        Args:
            ctx: 插件上下文
        """
        self._ctx = ctx
        self._cache: Optional[dict[str, Any]] = None
    
    async def get(self, use_cache: bool = True) -> dict[str, Any]:
        """
        获取插件完整配置
        
        Args:
            use_cache: 是否使用缓存（默认 True）
            
        Returns:
            配置字典
        """
        if use_cache and self._cache is not None:
            return self._cache.copy()
        
        try:
            from app.core.database import get_session
            from app.models.plugin_config import PluginConfig
            from sqlalchemy import select
            
            async for session in get_session():
                stmt = select(PluginConfig).where(
                    PluginConfig.plugin_id == self._ctx.plugin_id
                )
                result = await session.execute(stmt)
                config_record = result.scalar_one_or_none()
                
                if config_record:
                    self._cache = config_record.config or {}
                else:
                    self._cache = {}
                
                return self._cache.copy()
        
        except Exception as e:
            logger.error(f"[plugin-config] Failed to get config for {self._ctx.plugin_id}: {e}")
            return {}
    
    async def get_value(
        self,
        key: str,
        default: Any = None,
        use_cache: bool = True,
    ) -> Any:
        """
        获取单个配置项
        
        Args:
            key: 配置键
            default: 默认值
            use_cache: 是否使用缓存
            
        Returns:
            配置值
        """
        config = await self.get(use_cache=use_cache)
        return config.get(key, default)
    
    def invalidate_cache(self) -> None:
        """
        清除配置缓存
        
        当配置被外部更新时调用，强制下次读取从数据库获取
        """
        self._cache = None
    
    async def reload(self) -> dict[str, Any]:
        """
        强制重新加载配置
        
        Returns:
            最新配置
        """
        self.invalidate_cache()
        return await self.get(use_cache=False)
