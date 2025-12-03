"""
存储处理链
统一处理存储相关操作
"""

from typing import List, Optional, Dict, Any, Tuple
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class StorageChain(ChainBase):
    """存储处理链"""
    
    def __init__(self):
        super().__init__()
    
    async def process(self, operation: str, storage_id: int, *args, **kwargs) -> Any:
        """
        处理存储操作
        
        Args:
            operation: 操作名称 (list_files, delete_file, mkdir, etc.)
            storage_id: 存储ID
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            操作结果
        """
        async with AsyncSessionLocal() as session:
            try:
                # 获取服务实例
                service = self._get_service(session)
                
                # 检查操作是否存在
                if not hasattr(service, operation):
                    raise ValueError(f"存储服务不支持操作: {operation}")
                
                # 执行操作
                method = getattr(service, operation)
                
                # 如果是存储相关操作，需要传入storage_id
                if operation in ['list_files', 'get_storage_usage', 'generate_qr_code', 
                                'check_qr_status', 'initialize_provider']:
                    return await method(storage_id, *args, **kwargs)
                else:
                    # 其他操作直接调用
                    return await method(*args, **kwargs)
            
            except Exception as e:
                logger.error(f"存储操作失败: {operation}, storage_id: {storage_id}, error: {e}")
                raise
    
    def _get_service(self, session):
        """
        获取云存储服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            CloudStorageService 实例
        """
        from app.modules.cloud_storage.service import CloudStorageService
        return CloudStorageService(session)
    
    # ========== 存储配置管理 ==========
    
    async def list_storages(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出云存储配置"""
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            storages = await service.list_storages(provider)
            return [self._storage_to_dict(storage) for storage in storages]
    
    async def get_storage(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """获取云存储配置"""
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            storage = await service.get_storage(storage_id)
            if storage:
                return self._storage_to_dict(storage)
            return None
    
    async def create_storage(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建云存储配置"""
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            storage = await service.create_storage(storage_data)
            return self._storage_to_dict(storage)
    
    async def update_storage(self, storage_id: int, storage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新云存储配置"""
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            storage = await service.update_storage(storage_id, storage_data)
            if storage:
                return self._storage_to_dict(storage)
            return None
    
    async def delete_storage(self, storage_id: int) -> bool:
        """删除云存储配置"""
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            return await service.delete_storage(storage_id)
    
    # ========== 文件操作 ==========
    
    async def list_files(self, storage_id: int, path: str = "/", recursive: bool = False) -> List[Dict[str, Any]]:
        """
        列出文件
        
        Args:
            storage_id: 存储ID
            path: 路径
            recursive: 是否递归
        
        Returns:
            文件列表
        """
        # 检查缓存
        cache_key = self._get_cache_key("list_files", storage_id, path, recursive)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取文件列表: storage_id={storage_id}, path={path}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            files = await service.list_files(storage_id, path, recursive)
            
            # 缓存结果（5分钟）
            await self._set_to_cache(cache_key, files, ttl=300)
            
            return files
    
    async def get_storage_usage(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        获取存储使用情况
        
        Args:
            storage_id: 存储ID
        
        Returns:
            存储使用情况
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_storage_usage", storage_id)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取存储使用情况: storage_id={storage_id}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            usage = await service.get_storage_usage(storage_id)
            
            # 缓存结果（1分钟）
            if usage:
                await self._set_to_cache(cache_key, usage, ttl=60)
            
            return usage
    
    # ========== 认证操作 ==========
    
    async def generate_qr_code(self, storage_id: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        生成二维码（115网盘）
        
        Args:
            storage_id: 存储ID
        
        Returns:
            (qr_content, qr_url, error_message)
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            return await service.generate_qr_code(storage_id)
    
    async def check_qr_status(self, storage_id: int) -> Tuple[Optional[int], Optional[str], Optional[Dict[str, Any]]]:
        """
        检查二维码登录状态（115网盘）
        
        Args:
            storage_id: 存储ID
        
        Returns:
            (status, message, token_data)
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            return await service.check_qr_status(storage_id)
    
    async def initialize_provider(self, storage_id: int) -> bool:
        """
        初始化provider
        
        Args:
            storage_id: 存储ID
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            return await service.initialize_provider(storage_id)
    
    # ========== 辅助方法 ==========
    
    def _storage_to_dict(self, storage) -> Dict[str, Any]:
        """将存储对象转换为字典"""
        return {
            "id": storage.id,
            "name": storage.name,
            "provider": storage.provider,
            "enabled": storage.enabled,
            "app_id": storage.app_id,
            "rclone_remote_name": storage.rclone_remote_name,
            "rclone_config_path": storage.rclone_config_path,
            "openlist_server_url": storage.openlist_server_url,
            "user_id": storage.user_id,
            "user_name": storage.user_name,
            "config": storage.config,
            "created_at": storage.created_at.isoformat() if storage.created_at else None,
            "updated_at": storage.updated_at.isoformat() if storage.updated_at else None,
        }
    
    async def clear_file_cache(self, storage_id: int, path: Optional[str] = None):
        """
        清除文件列表缓存
        
        Args:
            storage_id: 存储ID
            path: 路径（如果指定，只清除该路径的缓存；否则清除所有缓存）
        """
        if path:
            # 清除特定路径的缓存
            cache_key = self._get_cache_key("list_files", storage_id, path, False)
            if cache_key in self._cache:
                del self._cache[cache_key]
            
            cache_key_recursive = self._get_cache_key("list_files", storage_id, path, True)
            if cache_key_recursive in self._cache:
                del self._cache[cache_key_recursive]
        else:
            # 清除所有文件列表缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(self._get_cache_key("list_files", storage_id, "", False).split("_")[0])
            ]
            for key in keys_to_remove:
                del self._cache[key]
        
        logger.debug(f"已清除文件列表缓存: storage_id={storage_id}, path={path}")

