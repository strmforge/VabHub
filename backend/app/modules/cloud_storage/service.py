"""
云存储服务层
统一管理115网盘、RClone和OpenList
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
from loguru import logger

from app.models.cloud_storage import CloudStorage, CloudStorageAuth
from app.core.cloud_key_manager import get_key_manager
from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
from app.core.cloud_storage.providers.rclone import RCloneProvider
from app.core.cloud_storage.providers.openlist import OpenListProvider


class CloudStorageService:
    """云存储服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.key_manager = get_key_manager()
        self._providers: Dict[int, Any] = {}  # 缓存provider实例
    
    async def create_storage(self, storage_data: Dict[str, Any]) -> CloudStorage:
        """创建云存储配置"""
        try:
            provider = storage_data.get("provider")
            
            # 创建存储配置
            storage = CloudStorage(
                name=storage_data.get("name"),
                provider=provider,
                enabled=storage_data.get("enabled", True),
                config=storage_data.get("config", {})
            )
            
            # 根据提供商设置特定配置
            if provider == "115":
                # 115网盘：从密钥管理器获取密钥（只需要AppID和AppKey）
                keys = self.key_manager.get_115_keys()
                if keys and keys.get("app_id") and keys.get("app_key"):
                    storage.app_id = keys.get("app_id")
                else:
                    raise ValueError("115网盘密钥未配置，请先运行 setup_115_keys.py 初始化密钥（需要AppID和AppKey）")
            
            elif provider == "rclone":
                storage.rclone_remote_name = storage_data.get("rclone_remote_name", "VabHub")
                storage.rclone_config_path = storage_data.get("rclone_config_path")
            
            elif provider == "openlist":
                storage.openlist_server_url = storage_data.get("openlist_server_url", "https://api.oplist.org.cn")
            
            self.db.add(storage)
            await self.db.commit()
            await self.db.refresh(storage)
            
            logger.info(f"云存储配置已创建: {storage.name} ({provider})")
            return storage
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建云存储配置失败: {e}")
            raise
    
    async def get_storage(self, storage_id: int) -> Optional[CloudStorage]:
        """获取云存储配置"""
        try:
            result = await self.db.execute(
                select(CloudStorage).where(CloudStorage.id == storage_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取云存储配置失败: {e}")
            return None
    
    async def list_storages(self, provider: Optional[str] = None) -> List[CloudStorage]:
        """列出云存储配置"""
        try:
            query = select(CloudStorage)
            if provider:
                query = query.where(CloudStorage.provider == provider)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"列出云存储配置失败: {e}")
            return []
    
    async def list_enabled_storages(self) -> List[CloudStorage]:
        """获取所有已启用的云存储配置"""
        try:
            query = select(CloudStorage).where(CloudStorage.enabled == True)
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取已启用云存储配置失败: {e}")
            return []
    
    async def update_storage(self, storage_id: int, storage_data: Dict[str, Any]) -> Optional[CloudStorage]:
        """更新云存储配置"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage:
                return None
            
            # 更新字段
            if "name" in storage_data:
                storage.name = storage_data["name"]
            if "enabled" in storage_data:
                storage.enabled = storage_data["enabled"]
            if "config" in storage_data:
                storage.config = storage_data["config"]
            
            # 根据提供商更新特定配置
            if storage.provider == "rclone":
                if "rclone_remote_name" in storage_data:
                    storage.rclone_remote_name = storage_data["rclone_remote_name"]
                if "rclone_config_path" in storage_data:
                    storage.rclone_config_path = storage_data["rclone_config_path"]
            
            elif storage.provider == "openlist":
                if "openlist_server_url" in storage_data:
                    storage.openlist_server_url = storage_data["openlist_server_url"]
            
            storage.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(storage)
            
            # 清除缓存的provider
            if storage_id in self._providers:
                del self._providers[storage_id]
            
            logger.info(f"云存储配置已更新: {storage.name}")
            return storage
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新云存储配置失败: {e}")
            return None
    
    async def _save_storage_tokens(
        self,
        storage_id: int,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None
    ):
        """保存云存储token到数据库（内部方法，供provider回调使用）"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage:
                logger.warning(f"无法保存token：存储配置不存在 (storage_id={storage_id})")
                return
            
            # 更新token信息
            if access_token is not None:
                storage.access_token = access_token
            if refresh_token is not None:
                storage.refresh_token = refresh_token
            if expires_at is not None:
                storage.expires_at = expires_at
            if user_id is not None:
                storage.user_id = user_id
            if user_name is not None:
                storage.user_name = user_name
            
            storage.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(storage)
            
            logger.info(f"Token已保存到数据库: {storage.name} (storage_id={storage_id})")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"保存token到数据库失败: {e}")
            raise
    
    async def delete_storage(self, storage_id: int) -> bool:
        """删除云存储配置"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage:
                return False
            
            storage_name = storage.name
            
            # 清除缓存的provider
            await self._cleanup_provider(storage_id)
            
            # 删除存储配置
            await self.db.execute(delete(CloudStorage).where(CloudStorage.id == storage_id))
            await self.db.commit()
            
            logger.info(f"云存储配置已删除: {storage_name}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除云存储配置失败: {e}")
            return False
    
    def _get_provider(self, storage: CloudStorage):
        """获取provider实例（带缓存）"""
        if storage.id in self._providers:
            return self._providers[storage.id]
        
        provider = None
        
        if storage.provider == "115":
            # 115网盘
            keys = self.key_manager.get_115_keys()
            if not keys:
                raise ValueError("115网盘密钥未配置")
            
            provider = Cloud115Provider()
            # 初始化provider（异步，需要在外部调用）
            self._providers[storage.id] = provider
            return provider
        
        elif storage.provider == "rclone":
            # RClone
            provider = RCloneProvider()
            self._providers[storage.id] = provider
            return provider
        
        elif storage.provider == "openlist":
            # OpenList
            provider = OpenListProvider()
            self._providers[storage.id] = provider
            return provider
        
        raise ValueError(f"不支持的云存储提供商: {storage.provider}")
    
    async def _cleanup_provider(self, storage_id: int):
        """清理provider实例"""
        if storage_id in self._providers:
            provider = self._providers[storage_id]
            if hasattr(provider, 'close'):
                try:
                    await provider.close()
                except:
                    pass
            del self._providers[storage_id]
    
    async def initialize_provider(self, storage_id: int) -> bool:
        """初始化provider"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage:
                return False
            
            provider = self._get_provider(storage)
            
            # 准备凭证
            credentials = {}
            
            if storage.provider == "115":
                # 从密钥管理器获取密钥（加密存储）
                keys = self.key_manager.get_115_keys()
                if not keys:
                    # 尝试从环境变量获取（备用方案）
                    import os
                    app_id = os.getenv("CLOUD115_APP_ID") or os.getenv("VABHUB_115_APP_ID")
                    app_key = os.getenv("CLOUD115_APP_KEY") or os.getenv("VABHUB_115_APP_KEY")
                    app_secret = os.getenv("CLOUD115_APP_SECRET") or os.getenv("VABHUB_115_APP_SECRET")
                    
                    # 115网盘API只需要AppID和AppKey，AppSecret是可选的
                    if app_id and app_key:
                        credentials = {
                            "app_id": app_id,
                            "app_key": app_key,
                            "app_secret": app_secret  # 可选
                        }
                        logger.info("从环境变量读取115网盘密钥")
                    else:
                        raise ValueError("115网盘密钥未配置，请先运行 setup_115_keys.py 初始化密钥或设置环境变量（需要AppID和AppKey）")
                else:
                    credentials = {
                        "app_id": keys.get("app_id"),
                        "app_key": keys.get("app_key"),
                        "app_secret": keys.get("app_secret")  # 可选
                    }
                    logger.debug("从加密存储读取115网盘密钥")
                
                # 从数据库加载已保存的token（如果存在）
                if storage.access_token:
                    credentials["access_token"] = storage.access_token
                if storage.refresh_token:
                    credentials["refresh_token"] = storage.refresh_token
                if storage.expires_at:
                    credentials["expires_at"] = storage.expires_at
                if storage.user_id:
                    credentials["user_id"] = storage.user_id
                if storage.user_name:
                    credentials["user_name"] = storage.user_name
                
                # 设置存储ID和token保存回调（用于token持久化）
                credentials["storage_id"] = storage_id
                credentials["token_save_callback"] = self._save_storage_tokens
            
            elif storage.provider == "rclone":
                credentials = {
                    "remote_name": storage.rclone_remote_name or "VabHub",
                    "config_path": storage.rclone_config_path
                }
            
            elif storage.provider == "openlist":
                credentials = {
                    "server_url": storage.openlist_server_url or "https://api.oplist.org.cn",
                    "app_id": None,
                    "app_secret": None
                }
            
            # 初始化provider
            success = await provider.initialize(credentials)
            
            # 如果已有token，设置token
            if success and storage.access_token:
                if hasattr(provider, 'set_token'):
                    await provider.set_token(
                        storage.access_token,
                        storage.refresh_token,
                        int((storage.expires_at - datetime.utcnow()).total_seconds()) if storage.expires_at else 604800
                    )
            
            return success
        except Exception as e:
            logger.error(f"初始化provider失败: {e}")
            return False
    
    async def generate_qr_code(self, storage_id: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """生成二维码（115网盘）"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage or storage.provider != "115":
                return None, None, "不支持的提供商或存储不存在"
            
            # 初始化provider
            if not await self.initialize_provider(storage_id):
                return None, None, "初始化provider失败"
            
            provider = self._get_provider(storage)
            
            if not hasattr(provider, 'generate_qr_code'):
                return None, None, "提供商不支持二维码登录"
            
            qr_content, qr_url = await provider.generate_qr_code()
            
            # 保存认证状态
            auth = CloudStorageAuth(
                storage_id=storage_id,
                provider=storage.provider,
                auth_type="qrcode",
                auth_data={"qr_content": qr_content, "qr_url": qr_url},
                status="pending"
            )
            self.db.add(auth)
            await self.db.commit()
            
            return qr_content, qr_url, None
        except Exception as e:
            logger.error(f"生成二维码失败: {e}")
            return None, None, str(e)
    
    async def check_qr_status(self, storage_id: int) -> Tuple[Optional[int], Optional[str], Optional[Dict[str, Any]]]:
        """检查二维码登录状态（115网盘）"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage or storage.provider != "115":
                return None, "不支持的提供商或存储不存在", None
            
            # 初始化provider
            if not await self.initialize_provider(storage_id):
                return None, "初始化provider失败", None
            
            provider = self._get_provider(storage)
            
            if not hasattr(provider, 'check_qr_status'):
                return None, "提供商不支持二维码登录", None
            
            status, message, token_data = await provider.check_qr_status()
            
            # 如果登录成功，token已经通过provider的回调函数保存到数据库
            # 这里只需要更新认证状态记录
            if status == 2:
                # 更新认证状态
                result = await self.db.execute(
                    select(CloudStorageAuth)
                    .where(CloudStorageAuth.storage_id == storage_id)
                    .order_by(CloudStorageAuth.created_at.desc())
                    .limit(1)
                )
                auth = result.scalar_one_or_none()
                if auth:
                    auth.status = "confirmed"
                    auth.updated_at = datetime.utcnow()
                    await self.db.commit()
            
            return status, message, token_data
        except Exception as e:
            logger.error(f"检查二维码状态失败: {e}")
            return None, str(e), None
    
    async def list_files(self, storage_id: int, path: str = "/", recursive: bool = False) -> List[Dict[str, Any]]:
        """列出文件"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage:
                return []
            
            # 初始化provider
            if not await self.initialize_provider(storage_id):
                return []
            
            provider = self._get_provider(storage)
            files = await provider.list_files(path, recursive)
            
            # 转换为字典
            return [{
                "id": file.id,
                "name": file.name,
                "path": file.path,
                "size": file.size,
                "type": file.type,
                "parent_id": file.parent_id,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "modified_at": file.modified_at.isoformat() if file.modified_at else None,
                "thumbnail": file.thumbnail,
                "download_url": file.download_url,
                "metadata": file.metadata
            } for file in files]
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    async def get_storage_usage(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """获取存储使用情况"""
        try:
            storage = await self.get_storage(storage_id)
            if not storage:
                return None
            
            # 初始化provider
            if not await self.initialize_provider(storage_id):
                return None
            
            provider = self._get_provider(storage)
            usage = await provider.get_storage_usage()
            
            if not usage:
                return None
            
            return {
                "total": usage.total,
                "used": usage.used,
                "available": usage.available,
                "percentage": usage.percentage
            }
        except Exception as e:
            logger.error(f"获取存储使用情况失败: {e}")
            return None

