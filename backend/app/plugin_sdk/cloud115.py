"""
插件 115 云存储客户端

PLUGIN-SDK-2 实现
PLUGIN-SAFETY-1 扩展：细粒度权限 + 审计日志

提供 115 网盘的离线任务和目录查询能力。
"""

from typing import Any, Optional, TYPE_CHECKING
from loguru import logger

from app.plugin_sdk.types import PluginCapability

if TYPE_CHECKING:
    from app.plugin_sdk.api import VabHubSDK


class Cloud115Client:
    """
    115 云存储客户端
    
    封装主系统的 115 网盘能力，允许插件创建离线任务和查询目录。
    
    权限要求（PLUGIN-SAFETY-1 细粒度）：
    - cloud115.add_offline: 创建离线任务（替代 cloud115.task）
    - cloud115.read: 读取目录信息
    
    Example:
        # 检查 115 是否可用
        if await sdk.cloud115.is_available():
            # 添加离线任务
            task_id = await sdk.cloud115.add_offline_task(
                "magnet:?xt=urn:btih:..."
            )
    """
    
    def __init__(self, sdk: "VabHubSDK") -> None:
        """
        初始化 115 客户端
        
        Args:
            sdk: VabHub SDK 实例
        """
        self._sdk = sdk
    
    async def is_available(self) -> bool:
        """
        检查 115 集成是否可用
        
        不需要权限，仅检查配置状态。
        
        Returns:
            是否可用
        """
        try:
            from app.core.database import get_session
            from app.models.cloud_storage import CloudStorage
            from sqlalchemy import select
            
            async for session in get_session():
                # 查找 115 类型的存储配置
                stmt = select(CloudStorage).where(
                    CloudStorage.provider == "115",
                    CloudStorage.enabled == True
                ).limit(1)
                result = await session.execute(stmt)
                storage = result.scalar_one_or_none()
                
                return storage is not None
                
        except Exception as e:
            self._sdk.log.debug(f"115 availability check failed: {e}")
            return False
    
    async def add_offline_task(
        self,
        url: str,
        *,
        save_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        添加 115 离线下载任务
        
        支持磁力链接、HTTP 链接等。
        
        Args:
            url: 下载链接（磁力/HTTP）
            save_path: 保存路径（115 网盘内路径，可选）
            
        Returns:
            任务标识，失败返回 None
            
        Raises:
            PermissionError: 未声明 cloud115.add_offline 权限
        """
        # PLUGIN-SAFETY-1: 使用细粒度权限并记录审计日志
        self._sdk._require_capability(PluginCapability.CLOUD115_ADD_OFFLINE)
        self._sdk._audit("cloud115.add_offline_task", {
            "url": url[:200] if len(url) > 200 else url,  # 限制长度避免过大
            "save_path": save_path
        })
        
        try:
            from app.core.database import get_session
            from app.models.cloud_storage import CloudStorage
            from app.modules.cloud_storage.service import CloudStorageService
            from sqlalchemy import select
            
            async for session in get_session():
                # 获取 115 存储配置
                stmt = select(CloudStorage).where(
                    CloudStorage.provider == "115",
                    CloudStorage.enabled == True
                ).limit(1)
                result = await session.execute(stmt)
                storage = result.scalar_one_or_none()
                
                if not storage:
                    self._sdk.log.error("No enabled 115 storage found")
                    return None
                
                # 使用云存储服务
                service = CloudStorageService(session)
                provider = await service.get_provider(storage.id)
                
                if not provider:
                    self._sdk.log.error("Failed to get 115 provider")
                    return None
                
                # 调用离线下载 API
                # 注意：具体实现取决于 Cloud115Provider 的 API
                if hasattr(provider, 'add_offline_task'):
                    task_info = await provider.add_offline_task(url, save_path=save_path)
                    if task_info:
                        self._sdk.log.info(f"115 offline task created: {url[:50]}...")
                        return str(task_info.get('task_id', task_info.get('info_hash', 'unknown')))
                else:
                    self._sdk.log.warning("115 provider does not support offline tasks")
                
                return None
                
        except Exception as e:
            self._sdk.log.error(f"Failed to add 115 offline task: {e}")
            return None
    
    async def list_dir(
        self,
        path: str = "/",
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        列出 115 网盘目录内容
        
        Args:
            path: 目录路径（默认根目录）
            limit: 返回数量限制
            
        Returns:
            文件/目录列表
            
        Raises:
            PermissionError: 未声明 cloud115.read 权限
        """
        self._sdk._require_capability(PluginCapability.CLOUD115_READ)
        
        try:
            from app.core.database import get_session
            from app.models.cloud_storage import CloudStorage
            from app.modules.cloud_storage.service import CloudStorageService
            from sqlalchemy import select
            
            async for session in get_session():
                # 获取 115 存储配置
                stmt = select(CloudStorage).where(
                    CloudStorage.provider == "115",
                    CloudStorage.enabled == True
                ).limit(1)
                result = await session.execute(stmt)
                storage = result.scalar_one_or_none()
                
                if not storage:
                    return []
                
                service = CloudStorageService(session)
                provider = await service.get_provider(storage.id)
                
                if not provider:
                    return []
                
                # 调用目录列表 API
                if hasattr(provider, 'list_files'):
                    files = await provider.list_files(path, limit=limit)
                    return [
                        {
                            "name": f.name if hasattr(f, 'name') else str(f),
                            "path": f.path if hasattr(f, 'path') else path,
                            "is_dir": f.is_dir if hasattr(f, 'is_dir') else False,
                            "size": f.size if hasattr(f, 'size') else 0,
                        }
                        for f in (files or [])
                    ][:limit]
                
                return []
                
        except Exception as e:
            self._sdk.log.error(f"Failed to list 115 directory: {e}")
            return []
    
    async def get_storage_info(self) -> Optional[dict[str, Any]]:
        """
        获取 115 存储空间信息
        
        Returns:
            存储信息（已用/总量等），不可用返回 None
            
        Raises:
            PermissionError: 未声明 cloud115.read 权限
        """
        self._sdk._require_capability(PluginCapability.CLOUD115_READ)
        
        try:
            from app.core.database import get_session
            from app.models.cloud_storage import CloudStorage
            from app.modules.cloud_storage.service import CloudStorageService
            from sqlalchemy import select
            
            async for session in get_session():
                stmt = select(CloudStorage).where(
                    CloudStorage.provider == "115",
                    CloudStorage.enabled == True
                ).limit(1)
                result = await session.execute(stmt)
                storage = result.scalar_one_or_none()
                
                if not storage:
                    return None
                
                service = CloudStorageService(session)
                provider = await service.get_provider(storage.id)
                
                if not provider:
                    return None
                
                if hasattr(provider, 'get_storage_usage'):
                    usage = await provider.get_storage_usage()
                    if usage:
                        return {
                            "used_bytes": usage.used_bytes if hasattr(usage, 'used_bytes') else 0,
                            "total_bytes": usage.total_bytes if hasattr(usage, 'total_bytes') else 0,
                            "free_bytes": usage.free_bytes if hasattr(usage, 'free_bytes') else 0,
                        }
                
                return None
                
        except Exception as e:
            self._sdk.log.error(f"Failed to get 115 storage info: {e}")
            return None
