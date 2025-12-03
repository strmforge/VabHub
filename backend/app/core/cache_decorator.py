"""
缓存装饰器
用于简化API和服务的缓存使用
"""

from functools import wraps
from typing import Callable, Optional, Any
import hashlib
import json
from loguru import logger

from app.core.cache import get_cache


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_func: Optional[Callable] = None,
    exclude_params: Optional[list] = None
):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        key_func: 自定义键生成函数
        exclude_params: 排除的参数列表（不参与键生成）
    
    Example:
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认键生成：基于函数名和参数
                key_data = {
                    "func": func.__name__,
                    "args": str(args),
                    "kwargs": {k: v for k, v in kwargs.items() 
                              if exclude_params is None or k not in exclude_params}
                }
                key_str = json.dumps(key_data, sort_keys=True, default=str)
                key_hash = hashlib.md5(key_str.encode()).hexdigest()
                cache_key = f"{key_prefix}:{func.__name__}:{key_hash}" if key_prefix else f"{func.__name__}:{key_hash}"
            
            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存储到缓存
            await cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"缓存存储: {cache_key} (TTL: {ttl}s)")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函数包装（需要手动处理）
            import asyncio
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # 判断是异步还是同步函数
        if hasattr(func, '__code__'):
            co_flags = func.__code__.co_flags
            if co_flags & 0x80:  # CO_COROUTINE
                return async_wrapper
            else:
                return sync_wrapper
        else:
            # 可能是类方法，尝试异步
            return async_wrapper
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def cache_key_builder(prefix: str, *key_parts: Any) -> str:
    """
    构建缓存键
    
    Args:
        prefix: 键前缀
        *key_parts: 键部分
    
    Returns:
        缓存键字符串
    """
    parts = [prefix] + [str(part) for part in key_parts]
    key_str = ":".join(parts)
    # 如果键太长，使用哈希
    if len(key_str) > 200:
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:hash:{key_hash}"
    return key_str

