"""
云存储Provider管理器
统一管理所有存储Provider的注册、初始化和选择
"""

from typing import Dict, Optional, Type, List
from loguru import logger

from app.core.cloud_storage.providers.base import CloudStorageProvider


class StorageProviderManager:
    """存储Provider管理器"""
    
    _instance: Optional['StorageProviderManager'] = None
    _providers: Dict[str, Type[CloudStorageProvider]] = {}
    _instances: Dict[str, CloudStorageProvider] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._register_builtin_providers()
            self._initialized = True
    
    def _register_builtin_providers(self):
        """注册内置Provider"""
        try:
            from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
            self.register("115", Cloud115Provider)
            logger.info("已注册115网盘Provider")
        except ImportError as e:
            logger.warning(f"无法导入115网盘Provider: {e}")
        
        try:
            from app.core.cloud_storage.providers.rclone import RCloneProvider
            self.register("rclone", RCloneProvider)
            logger.info("已注册RClone Provider")
        except ImportError as e:
            logger.warning(f"无法导入RClone Provider: {e}")
        
        try:
            from app.core.cloud_storage.providers.openlist import OpenListProvider
            self.register("openlist", OpenListProvider)
            logger.info("已注册OpenList Provider")
        except ImportError as e:
            logger.warning(f"无法导入OpenList Provider: {e}")
    
    def register(self, name: str, provider_class: Type[CloudStorageProvider]):
        """
        注册Provider
        
        Args:
            name: Provider名称
            provider_class: Provider类
        """
        if not issubclass(provider_class, CloudStorageProvider):
            raise TypeError(f"{provider_class} 必须是 CloudStorageProvider 的子类")
        
        self._providers[name.lower()] = provider_class
        logger.info(f"已注册存储Provider: {name}")
    
    def get_provider_class(self, name: str) -> Optional[Type[CloudStorageProvider]]:
        """
        获取Provider类
        
        Args:
            name: Provider名称
        
        Returns:
            Provider类或None
        """
        return self._providers.get(name.lower())
    
    def create_provider(self, name: str, credentials: Dict) -> Optional[CloudStorageProvider]:
        """
        创建Provider实例
        
        Args:
            name: Provider名称
            credentials: 认证信息
        
        Returns:
            Provider实例或None
        """
        provider_class = self.get_provider_class(name)
        if not provider_class:
            logger.error(f"未找到Provider: {name}")
            return None
        
        try:
            provider = provider_class()
            # 初始化Provider
            # 注意：这里不直接调用initialize，由调用者决定何时初始化
            return provider
        except Exception as e:
            logger.error(f"创建Provider实例失败: {name}, error: {e}")
            return None
    
    def get_or_create_provider(self, name: str, storage_id: Optional[int] = None) -> Optional[CloudStorageProvider]:
        """
        获取或创建Provider实例（带缓存）
        
        Args:
            name: Provider名称
            storage_id: 存储配置ID（用于缓存）
        
        Returns:
            Provider实例或None
        """
        cache_key = f"{name}_{storage_id}" if storage_id else name
        
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        provider_class = self.get_provider_class(name)
        if not provider_class:
            return None
        
        try:
            provider = provider_class()
            if storage_id:
                self._instances[cache_key] = provider
            return provider
        except Exception as e:
            logger.error(f"创建Provider实例失败: {name}, error: {e}")
            return None
    
    def list_providers(self) -> List[str]:
        """
        列出所有已注册的Provider
        
        Returns:
            Provider名称列表
        """
        return list(self._providers.keys())
    
    def is_provider_registered(self, name: str) -> bool:
        """
        检查Provider是否已注册
        
        Args:
            name: Provider名称
        
        Returns:
            是否已注册
        """
        return name.lower() in self._providers
    
    def unregister(self, name: str):
        """
        取消注册Provider
        
        Args:
            name: Provider名称
        """
        name_lower = name.lower()
        if name_lower in self._providers:
            del self._providers[name_lower]
            logger.info(f"已取消注册存储Provider: {name}")
        
        # 清除相关实例缓存
        keys_to_remove = [key for key in self._instances.keys() if key.startswith(name_lower)]
        for key in keys_to_remove:
            del self._instances[key]
    
    def clear_instances(self, name: Optional[str] = None):
        """
        清除Provider实例缓存
        
        Args:
            name: Provider名称（如果指定，只清除该Provider的实例；否则清除所有）
        """
        if name:
            keys_to_remove = [key for key in self._instances.keys() if key.startswith(name.lower())]
            for key in keys_to_remove:
                del self._instances[key]
            logger.info(f"已清除Provider实例缓存: {name}")
        else:
            self._instances.clear()
            logger.info("已清除所有Provider实例缓存")


# 全局管理器实例
_manager: Optional[StorageProviderManager] = None


def get_storage_provider_manager() -> StorageProviderManager:
    """获取存储Provider管理器实例"""
    global _manager
    if _manager is None:
        _manager = StorageProviderManager()
    return _manager


def register_storage_provider(name: str, provider_class: Type[CloudStorageProvider]):
    """注册存储Provider"""
    get_storage_provider_manager().register(name, provider_class)


def get_storage_provider(name: str, credentials: Optional[Dict] = None) -> Optional[CloudStorageProvider]:
    """
    获取存储Provider实例
    
    Args:
        name: Provider名称
        credentials: 认证信息（可选）
    
    Returns:
        Provider实例或None
    """
    manager = get_storage_provider_manager()
    
    if credentials:
        return manager.create_provider(name, credentials)
    else:
        return manager.get_or_create_provider(name)


def list_storage_providers() -> List[str]:
    """列出所有已注册的存储Provider"""
    return get_storage_provider_manager().list_providers()

