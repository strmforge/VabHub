"""
Chain 基类
提供统一的处理链接口
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import hashlib
import json
from loguru import logger

# 尝试导入统一缓存系统，如果失败则使用内存缓存
try:
    from app.core.cache import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("统一缓存系统不可用，将仅使用内存缓存")


class ChainBase(ABC):
    """Chain 基类"""
    
    def __init__(self):
        # L1: 内存缓存（快速访问）
        self._memory_cache: dict = {}
        
        # L2/L3: 统一缓存系统（如果可用）
        if CACHE_AVAILABLE:
            try:
                self._cache_backend = get_cache()
                self._use_unified_cache = True
            except Exception as e:
                logger.warning(f"初始化统一缓存系统失败: {e}，将仅使用内存缓存")
                self._cache_backend = None
                self._use_unified_cache = False
        else:
            self._cache_backend = None
            self._use_unified_cache = False
        
        logger.debug(f"{self.__class__.__name__} 初始化（统一缓存: {self._use_unified_cache}）")
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """处理请求"""
        pass
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "class": self.__class__.__name__,
            "args": str(args),
            "kwargs": json.dumps(kwargs, sort_keys=True, default=str)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        从缓存获取值（三级缓存）
        1. 先检查L1内存缓存
        2. 如果未命中，检查L2/L3缓存
        """
        # L1: 内存缓存（最快）
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # L2/L3: 统一缓存系统（如果可用）
        if self._use_unified_cache and self._cache_backend:
            try:
                cached_value = await self._cache_backend.get(key)
                if cached_value is not None:
                    # 回填到L1内存缓存
                    self._memory_cache[key] = cached_value
                    return cached_value
            except Exception as e:
                logger.debug(f"从统一缓存获取值失败: {e}")
        
        return None
    
    async def _set_to_cache(self, key: str, value: Any, ttl: int = 3600):
        """
        设置缓存值（三级缓存）
        1. 设置L1内存缓存
        2. 设置L2/L3缓存
        """
        # L1: 内存缓存
        self._memory_cache[key] = value
        
        # L2/L3: 统一缓存系统（如果可用）
        if self._use_unified_cache and self._cache_backend:
            try:
                await self._cache_backend.set(key, value, ttl=ttl)
            except Exception as e:
                logger.debug(f"设置统一缓存值失败: {e}")
    
    def _clear_cache(self):
        """清空缓存"""
        self._memory_cache.clear()
    
    @property
    def _cache(self):
        """
        兼容性属性：返回内存缓存
        注意：这仅用于清除缓存等操作，实际缓存使用三级缓存系统
        """
        return self._memory_cache

