"""
STRM服务层
集成系统认证，提供STRM相关服务
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.cloud_storage import CloudStorage
from app.core.cloud_storage.providers.cloud_115_api import Cloud115API
from app.modules.cloud_storage.service import CloudStorageService


class STRMService:
    """STRM服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cloud_storage_service = CloudStorageService(db)
        self._115_api_cache: Optional[Cloud115API] = None
        self._115_storage_id: Optional[int] = None
    
    async def get_115_api_client(self, storage_id: Optional[int] = None) -> Optional[Cloud115API]:
        """
        获取115网盘API客户端（使用系统认证）
        
        Args:
            storage_id: 云存储ID，如果为None则自动查找第一个115网盘存储
        
        Returns:
            Cloud115API客户端实例，如果获取失败则返回None
        """
        try:
            # 如果指定了storage_id且与缓存一致，直接返回缓存的客户端
            if storage_id and storage_id == self._115_storage_id and self._115_api_cache:
                # 验证token是否仍然有效
                if await self._validate_token(self._115_api_cache):
                    return self._115_api_cache
            
            # 查找115网盘存储配置
            if not storage_id:
                result = await self.db.execute(
                    select(CloudStorage)
                    .where(CloudStorage.provider == "115")
                    .where(CloudStorage.enabled == True)
                    .limit(1)
                )
                storage = result.scalar_one_or_none()
            else:
                storage = await self.cloud_storage_service.get_storage(storage_id)
            
            if not storage:
                logger.warning("未找到启用的115网盘存储配置")
                return None
            
            if storage.provider != "115":
                logger.warning(f"存储配置不是115网盘: {storage.provider}")
                return None
            
            # 检查是否有access_token
            if not storage.access_token:
                logger.warning(f"115网盘存储配置未认证 (storage_id={storage.id})")
                return None
            
            # 创建Cloud115API客户端
            api_client = Cloud115API(access_token=storage.access_token)
            
            # 缓存客户端
            self._115_api_cache = api_client
            self._115_storage_id = storage.id
            
            logger.info(f"115网盘API客户端已创建 (storage_id={storage.id})")
            return api_client
            
        except Exception as e:
            logger.error(f"获取115网盘API客户端失败: {e}")
            return None
    
    async def _validate_token(self, api_client: Cloud115API) -> bool:
        """
        验证token是否有效
        
        Args:
            api_client: Cloud115API客户端
        
        Returns:
            token是否有效
        """
        try:
            # 尝试获取用户信息来验证token
            result = await api_client.get_user_info()
            if result and result.get("success"):
                return True
            # 如果获取用户信息失败，检查是否是401错误
            if result and "401" in str(result.get("error", "")):
                return False
            # 其他情况，假设token有效（可能是网络问题等）
            return True
        except Exception as e:
            logger.debug(f"Token验证失败: {e}")
            # 如果验证失败，假设token可能过期，返回False
            return False
    
    async def refresh_115_token(self, storage_id: Optional[int] = None) -> bool:
        """
        刷新115网盘token（如果需要）
        
        Args:
            storage_id: 云存储ID
        
        Returns:
            是否刷新成功
        """
        try:
            # 查找115网盘存储配置
            if not storage_id:
                result = await self.db.execute(
                    select(CloudStorage)
                    .where(CloudStorage.provider == "115")
                    .where(CloudStorage.enabled == True)
                    .limit(1)
                )
                storage = result.scalar_one_or_none()
            else:
                storage = await self.cloud_storage_service.get_storage(storage_id)
            
            if not storage or not storage.refresh_token:
                return False
            
            # 初始化provider并刷新token
            await self.cloud_storage_service.initialize_provider(storage.id)
            
            # 清除缓存，强制重新获取
            self._115_api_cache = None
            self._115_storage_id = None
            
            return True
        except Exception as e:
            logger.error(f"刷新115网盘token失败: {e}")
            return False

