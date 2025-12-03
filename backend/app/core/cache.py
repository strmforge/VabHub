"""
统一缓存系统
支持三级缓存：L1内存 + L2 Redis + L3数据库
"""

from typing import Optional, Any, Union
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis未安装，将仅使用内存缓存")

from app.core.config import settings
from app.core.database import AsyncSessionLocal

REDIS_ENABLED = getattr(settings, "REDIS_ENABLED", True)
_redis_warning_logged = False


class CacheBackend:
    """缓存后端接口"""
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        raise NotImplementedError
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: dict = {}
        self._timestamps: dict = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._timestamps:
            ttl = self._timestamps[key].get('ttl', self.default_ttl)
            created_at = self._timestamps[key]['created_at']
            if datetime.now() - created_at > timedelta(seconds=ttl):
                await self.delete(key)
                return None
        
        return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        # 如果超过最大大小，删除最旧的项
        if len(self._cache) >= self.max_size and key not in self._cache:
            # 删除最旧的项
            oldest_key = min(self._timestamps.keys(), 
                           key=lambda k: self._timestamps[k]['created_at'])
            await self.delete(oldest_key)
        
        self._cache[key] = value
        self._timestamps[key] = {
            'created_at': datetime.now(),
            'ttl': ttl or self.default_ttl
        }
        return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        return True
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if key not in self._cache:
            return False
        # 检查是否过期
        if key in self._timestamps:
            ttl = self._timestamps[key].get('ttl', self.default_ttl)
            created_at = self._timestamps[key]['created_at']
            if datetime.now() - created_at > timedelta(seconds=ttl):
                await self.delete(key)
                return False
        return True
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        self._cache.clear()
        self._timestamps.clear()
        return True


class RedisCacheBackend(CacheBackend):
    """Redis缓存后端（L2）"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
        self._disabled: bool = False
    
    async def _get_client(self) -> Optional[redis.Redis]:
        """获取Redis客户端（带错误处理）"""
        global _redis_warning_logged

        if not REDIS_AVAILABLE:
            return None

        if not REDIS_ENABLED:
            if not _redis_warning_logged:
                logger.info("Redis缓存已被禁用，使用内存/L3缓存")
                _redis_warning_logged = True
            return None

        if self._disabled:
            return None
        
        if self._client is None:
            try:
                self._client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,  # 2秒连接超时
                    socket_timeout=2,  # 2秒操作超时
                    retry_on_timeout=False,  # 不重试
                    health_check_interval=30  # 30秒健康检查
                )
                # 测试连接
                await self._client.ping()
            except Exception as e:
                if not _redis_warning_logged:
                    logger.warning(f"Redis连接失败，将仅使用内存缓存: {e}")
                    _redis_warning_logged = True
                else:
                    logger.debug(f"Redis连接失败（已降级）: {e}")
                self._client = None
                self._disabled = True
                return None
        
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            client = await self._get_client()
            if client is None:
                return None  # Redis不可用，返回None让上层使用其他缓存层
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.debug(f"Redis获取缓存失败（已降级）: {e}")
            return None  # 失败时返回None，让上层使用其他缓存层
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            client = await self._get_client()
            if client is None:
                return False  # Redis不可用，返回False让上层使用其他缓存层
            value_str = json.dumps(value, ensure_ascii=False, default=str)
            ttl = ttl or self.default_ttl
            await client.setex(key, ttl, value_str)
            return True
        except Exception as e:
            logger.debug(f"Redis设置缓存失败（已降级）: {e}")
            return False  # 失败时返回False，让上层使用其他缓存层
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            client = await self._get_client()
            if client is None:
                return False  # Redis不可用
            await client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Redis删除缓存失败（已降级）: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            client = await self._get_client()
            if client is None:
                return False  # Redis不可用
            return await client.exists(key) > 0
        except Exception as e:
            logger.debug(f"Redis检查缓存失败（已降级）: {e}")
            return False
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        try:
            client = await self._get_client()
            if client is None:
                return False  # Redis不可用
            await client.flushdb()
            return True
        except Exception as e:
            logger.debug(f"Redis清空缓存失败（已降级）: {e}")
            return False
    
    async def close(self):
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None


class DatabaseCacheBackend(CacheBackend):
    """数据库缓存后端（L3）"""
    
    def __init__(self, default_ttl: int = 86400):
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            from app.models.cache import CacheEntry
            
            # 检查键是否太长
            cache_key = key
            if len(key) > 500:
                key_hash = hashlib.md5(key.encode()).hexdigest()
                cache_key = f"hash:{key_hash}"
            
            async with AsyncSessionLocal() as session:
                # 查询缓存条目
                result = await session.execute(
                    select(CacheEntry).where(CacheEntry.key == cache_key)
                )
                entry = result.scalar_one_or_none()
                
                if entry is None:
                    return None
                
                # 检查是否过期
                if entry.is_expired():
                    # 删除过期条目
                    await session.delete(entry)
                    await session.commit()
                    return None
                
                # 反序列化值
                try:
                    return json.loads(entry.value)
                except json.JSONDecodeError:
                    logger.warning(f"数据库缓存值反序列化失败: {key}")
                    return None
                
        except Exception as e:
            # 如果是表不存在错误，记录警告但不报错（表会在数据库初始化时创建）
            error_str = str(e).lower()
            if "no such table" in error_str or "does not exist" in error_str:
                logger.debug(f"缓存表不存在，将在数据库初始化时创建: {key}")
            else:
                logger.debug(f"数据库获取缓存失败（已降级）: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            from app.models.cache import CacheEntry
            
            # 序列化值
            try:
                value_str = json.dumps(value, ensure_ascii=False, default=str)
            except (TypeError, ValueError) as e:
                logger.warning(f"缓存值序列化失败: {e}")
                return False
            
            # 检查键是否太长
            cache_key = key
            if len(key) > 500:
                # 键太长，使用哈希
                key_hash = hashlib.md5(key.encode()).hexdigest()
                cache_key = f"hash:{key_hash}"
            
            ttl = ttl or self.default_ttl
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            async with AsyncSessionLocal() as session:
                # 查询是否已存在
                result = await session.execute(
                    select(CacheEntry).where(CacheEntry.key == cache_key)
                )
                entry = result.scalar_one_or_none()
                
                if entry:
                    # 更新现有条目
                    entry.value = value_str
                    entry.ttl = ttl
                    entry.expires_at = expires_at
                    entry.updated_at = datetime.utcnow()
                else:
                    # 创建新条目
                    entry = CacheEntry(
                        key=cache_key,
                        value=value_str,
                        ttl=ttl,
                        expires_at=expires_at
                    )
                    session.add(entry)
                
                await session.commit()
                return True
            
        except Exception as e:
            # 如果是表不存在错误，记录警告但不报错（表会在数据库初始化时创建）
            error_str = str(e).lower()
            if "no such table" in error_str or "does not exist" in error_str:
                logger.debug(f"缓存表不存在，将在数据库初始化时创建: {key}")
            else:
                logger.debug(f"数据库设置缓存失败（已降级）: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            from app.models.cache import CacheEntry
            
            # 检查键是否太长
            cache_key = key
            if len(key) > 500:
                key_hash = hashlib.md5(key.encode()).hexdigest()
                cache_key = f"hash:{key_hash}"
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    delete(CacheEntry).where(CacheEntry.key == cache_key)
                )
                await session.commit()
                return result.rowcount > 0
            
        except Exception as e:
            # 如果是表不存在错误，记录警告但不报错
            error_str = str(e).lower()
            if "no such table" in error_str or "does not exist" in error_str:
                logger.debug(f"缓存表不存在，将在数据库初始化时创建")
            else:
                logger.debug(f"数据库删除缓存失败（已降级）: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            from app.models.cache import CacheEntry
            
            # 检查键是否太长
            cache_key = key
            if len(key) > 500:
                key_hash = hashlib.md5(key.encode()).hexdigest()
                cache_key = f"hash:{key_hash}"
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(CacheEntry).where(CacheEntry.key == cache_key)
                )
                entry = result.scalar_one_or_none()
                
                if entry is None:
                    return False
                
                # 检查是否过期
                if entry.is_expired():
                    await session.delete(entry)
                    await session.commit()
                    return False
                
                return True
            
        except Exception as e:
            # 如果是表不存在错误，记录警告但不报错
            error_str = str(e).lower()
            if "no such table" in error_str or "does not exist" in error_str:
                logger.debug(f"缓存表不存在，将在数据库初始化时创建")
            else:
                logger.debug(f"数据库检查缓存失败（已降级）: {e}")
            return False
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        try:
            from app.models.cache import CacheEntry
            
            async with AsyncSessionLocal() as session:
                await session.execute(delete(CacheEntry))
                await session.commit()
                return True
            
        except Exception as e:
            # 如果是表不存在错误，记录警告但不报错
            error_str = str(e).lower()
            if "no such table" in error_str or "does not exist" in error_str:
                logger.debug(f"缓存表不存在，将在数据库初始化时创建")
            else:
                logger.debug(f"数据库清空缓存失败（已降级）: {e}")
            return False
    
    async def cleanup_expired(self) -> int:
        """清理过期缓存"""
        try:
            from app.models.cache import CacheEntry
            
            now = datetime.utcnow()
            async with AsyncSessionLocal() as session:
                # 注意：需要处理时区问题
                result = await session.execute(
                    delete(CacheEntry).where(CacheEntry.expires_at < now)
                )
                await session.commit()
                return result.rowcount
            
        except Exception as e:
            # 如果是表不存在错误，记录警告但不报错
            error_str = str(e).lower()
            if "no such table" in error_str or "does not exist" in error_str:
                logger.debug(f"缓存表不存在，将在数据库初始化时创建")
            else:
                logger.debug(f"清理过期缓存失败（已降级）: {e}")
            return 0
    
    async def close(self):
        """关闭数据库缓存后端（L3使用会话上下文管理器，无需手动关闭）"""
        pass


class CacheManager:
    """统一缓存管理器（三级缓存）"""
    
    def __init__(self, enable_l3: bool = True):
        self.backends: list[CacheBackend] = []
        self.enable_l3 = enable_l3
        self._init_backends()
    
    def _init_backends(self):
        """初始化缓存后端"""
        # L1: 总是添加内存缓存（最快，但容量小）
        self.backends.append(MemoryCacheBackend(max_size=1000, default_ttl=300))
        logger.info("L1内存缓存后端已初始化")
        
        # L2: 如果Redis可用，添加Redis缓存（较快，容量中等，可共享）
        if REDIS_AVAILABLE and settings.REDIS_URL:
            try:
                self.backends.append(RedisCacheBackend(
                    redis_url=settings.REDIS_URL,
                    default_ttl=3600
                ))
                logger.info("L2 Redis缓存后端已初始化")
            except Exception as e:
                logger.warning(f"L2 Redis缓存后端初始化失败: {e}")
        else:
            logger.info("Redis不可用，跳过L2缓存")
        
        # L3: 数据库缓存（较慢，但容量大，持久化）
        if self.enable_l3:
            try:
                self.backends.append(DatabaseCacheBackend(default_ttl=86400))
                logger.info("L3数据库缓存后端已初始化")
            except Exception as e:
                logger.warning(f"L3数据库缓存后端初始化失败: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """三级缓存获取（L1 → L2 → L3）"""
        # 从L1到L3依次查找
        for i, backend in enumerate(self.backends):
            value = await backend.get(key)
            if value is not None:
                # 记录缓存命中
                try:
                    from app.core.performance import record_cache_hit
                    record_cache_hit()
                except ImportError:
                    pass
                
                # 回填到更高级缓存（提升后续访问速度）
                # 例如：如果在L3找到，回填到L2和L1
                for j in range(i):
                    try:
                        await self.backends[j].set(key, value)
                    except Exception as e:
                        logger.debug(f"回填缓存到L{j+1}失败: {e}")
                return value
        
        # 记录缓存未命中
        try:
            from app.core.performance import record_cache_miss
            record_cache_miss()
        except ImportError:
            pass
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """多级缓存设置"""
        success = True
        for backend in self.backends:
            result = await backend.set(key, value, ttl)
            success = success and result
        return success
    
    async def delete(self, key: str) -> bool:
        """多级缓存删除"""
        success = True
        for backend in self.backends:
            result = await backend.delete(key)
            success = success and result
        return success
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        for backend in self.backends:
            if await backend.exists(key):
                return True
        return False
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        success = True
        for backend in self.backends:
            result = await backend.clear()
            success = success and result
        return success
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        parts = [prefix]
        if args:
            parts.extend(str(arg) for arg in args)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
        
        key_str = ":".join(parts)
        # 如果键太长，使用哈希
        if len(key_str) > 200:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        return key_str
    
    async def cleanup_expired(self) -> int:
        """清理所有后端的过期缓存"""
        total_cleaned = 0
        for backend in self.backends:
            if isinstance(backend, DatabaseCacheBackend):
                cleaned = await backend.cleanup_expired()
                total_cleaned += cleaned
        return total_cleaned
    
    async def close(self):
        """关闭缓存管理器"""
        for backend in self.backends:
            if hasattr(backend, 'close'):
                try:
                    await backend.close()
                except Exception as e:
                    logger.warning(f"关闭缓存后端失败: {e}")


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """获取缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            # 生成缓存键
            cache_key = cache.generate_key(
                key_prefix,
                func.__name__,
                *args,
                **kwargs
            )
            
            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

