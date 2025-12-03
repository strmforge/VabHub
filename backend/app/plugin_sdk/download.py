"""
插件下载服务客户端

PLUGIN-SDK-2 实现
PLUGIN-SAFETY-1 扩展：细粒度权限 + 审计日志

提供下载任务的创建和查询能力。
"""

from typing import Any, Optional, TYPE_CHECKING
from loguru import logger

from app.plugin_sdk.types import PluginCapability

if TYPE_CHECKING:
    from app.plugin_sdk.api import VabHubSDK


class DownloadClient:
    """
    下载服务客户端
    
    封装主系统的下载能力，允许插件创建和查询下载任务。
    
    权限要求（PLUGIN-SAFETY-1 细粒度）：
    - download.read: 查询任务状态
    - download.add: 创建下载任务（替代 download.write）
    
    Example:
        # 创建 HTTP 下载任务
        task_id = await sdk.download.add_task(
            url="https://example.com/file.zip",
            title="My Download",
            media_type="other"
        )
        
        # 查询任务状态
        task = await sdk.download.get_task(task_id)
        print(f"Progress: {task['progress']}%")
    """
    
    def __init__(self, sdk: "VabHubSDK") -> None:
        """
        初始化下载客户端
        
        Args:
            sdk: VabHub SDK 实例
        """
        self._sdk = sdk
    
    async def add_task(
        self,
        url: str,
        *,
        title: Optional[str] = None,
        media_type: str = "other",
        save_path: Optional[str] = None,
        extra_metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        创建下载任务
        
        支持 HTTP 链接、磁力链接、种子 URL。
        
        Args:
            url: 下载链接（HTTP/磁力/种子）
            title: 任务标题（可选，默认从 URL 推断）
            media_type: 媒体类型（movie/tv/music/other）
            save_path: 保存路径（可选，使用默认路径）
            extra_metadata: 额外元数据
            
        Returns:
            任务 ID，失败返回 None
            
        Raises:
            PermissionError: 未声明 download.add 权限
        """
        # PLUGIN-SAFETY-1: 使用细粒度权限并记录审计日志
        self._sdk._require_capability(PluginCapability.DOWNLOAD_ADD)
        self._sdk._audit("download.add_task", {
            "url": url[:200] if len(url) > 200 else url,  # 限制长度避免过大
            "title": title,
            "media_type": media_type
        })
        
        try:
            from app.core.database import get_session
            from app.models.download import DownloadTask
            import uuid
            
            # 生成任务 ID
            task_id = f"plugin_{self._sdk.context.plugin_id}_{uuid.uuid4().hex[:8]}"
            
            # 推断任务标题
            if not title:
                title = url.split("/")[-1].split("?")[0] or "Download Task"
            
            # 判断链接类型
            is_magnet = url.startswith("magnet:")
            is_torrent = url.endswith(".torrent") or "torrent" in url.lower()
            
            async for session in get_session():
                task = DownloadTask(
                    task_id=task_id,
                    title=title,
                    status="pending",
                    progress=0.0,
                    size_gb=0.0,
                    downloaded_gb=0.0,
                    downloader="pending",  # 待分配下载器
                    magnet_link=url if is_magnet else None,
                    torrent_url=url if (is_torrent and not is_magnet) else None,
                    media_type=media_type,
                    extra_metadata={
                        **(extra_metadata or {}),
                        "_source_plugin": self._sdk.context.plugin_id,
                        "_original_url": url,
                        "_save_path": save_path,
                    },
                )
                session.add(task)
                await session.commit()
                
                self._sdk.log.info(f"Created download task: {task_id}")
                return task_id
                
        except Exception as e:
            self._sdk.log.error(f"Failed to create download task: {e}")
            return None
    
    async def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """
        查询下载任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务信息字典，不存在返回 None
            
        Raises:
            PermissionError: 未声明 download.read 权限
        """
        self._sdk._require_capability(PluginCapability.DOWNLOAD_READ)
        
        try:
            from app.core.database import get_session
            from app.models.download import DownloadTask
            from sqlalchemy import select
            
            async for session in get_session():
                stmt = select(DownloadTask).where(DownloadTask.task_id == task_id)
                result = await session.execute(stmt)
                task = result.scalar_one_or_none()
                
                if not task:
                    return None
                
                return {
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status,
                    "progress": task.progress,
                    "size_gb": task.size_gb,
                    "downloaded_gb": task.downloaded_gb,
                    "speed_mbps": task.speed_mbps,
                    "eta": task.eta,
                    "downloader": task.downloader,
                    "media_type": task.media_type,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
                
        except Exception as e:
            self._sdk.log.error(f"Failed to get download task: {e}")
            return None
    
    async def list_tasks(
        self,
        *,
        status: Optional[str] = None,
        media_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        列出下载任务
        
        Args:
            status: 状态过滤（downloading/paused/completed/failed）
            media_type: 媒体类型过滤
            limit: 返回数量限制
            
        Returns:
            任务列表
            
        Raises:
            PermissionError: 未声明 download.read 权限
        """
        self._sdk._require_capability(PluginCapability.DOWNLOAD_READ)
        
        try:
            from app.core.database import get_session
            from app.models.download import DownloadTask
            from sqlalchemy import select, desc
            
            async for session in get_session():
                stmt = select(DownloadTask).order_by(desc(DownloadTask.created_at)).limit(limit)
                
                if status:
                    stmt = stmt.where(DownloadTask.status == status)
                if media_type:
                    stmt = stmt.where(DownloadTask.media_type == media_type)
                
                result = await session.execute(stmt)
                tasks = result.scalars().all()
                
                return [
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "status": task.status,
                        "progress": task.progress,
                        "size_gb": task.size_gb,
                        "media_type": task.media_type,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                    }
                    for task in tasks
                ]
                
        except Exception as e:
            self._sdk.log.error(f"Failed to list download tasks: {e}")
            return []
