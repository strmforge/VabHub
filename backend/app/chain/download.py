"""
下载处理链
统一处理下载相关操作
"""

from typing import List, Optional, Dict, Any
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class DownloadChain(ChainBase):
    """下载处理链"""
    
    def __init__(self):
        super().__init__()
    
    def _get_service(self, session):
        """
        获取下载服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            DownloadService 实例
        """
        from app.modules.download.service import DownloadService
        return DownloadService(session)
    
    # ========== 下载任务管理 ==========
    
    async def list_downloads(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出下载任务
        
        Args:
            status: 状态（downloading, paused, completed, failed）
        
        Returns:
            下载任务列表
        """
        # 检查缓存
        cache_key = self._get_cache_key("list_downloads", status)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取下载列表: status={status}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            downloads = await service.list_downloads(status)
            
            # 服务已经返回字典列表，直接使用
            # 如果需要过滤下载器，可以在这里添加过滤逻辑
            result = downloads
            
            # 缓存结果（30秒，因为下载状态变化较快）
            await self._set_to_cache(cache_key, result, ttl=30)
            
            return result
    
    async def get_download(self, download_id: str) -> Optional[Dict[str, Any]]:
        """
        获取下载任务详情
        
        Args:
            download_id: 下载任务ID
        
        Returns:
            下载任务详情
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_download", download_id)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取下载详情: download_id={download_id}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            download = await service.get_download(download_id)
            
            if download:
                # 服务已经返回字典，直接使用
                result = download
                # 缓存结果（30秒）
                await self._set_to_cache(cache_key, result, ttl=30)
                return result
            
            return None
    
    async def create_download(self, download_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建下载任务
        
        Args:
            download_data: 下载数据
        
        Returns:
            创建的下载任务
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            download = await service.create_download(download_data)
            
            # 清除下载列表缓存
            await self._clear_download_cache()
            
            return download
    
    async def pause_download(self, download_id: str) -> bool:
        """
        暂停下载
        
        Args:
            download_id: 下载任务ID
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            await service.pause_download(download_id)
            
            # 清除相关缓存
            await self._clear_download_cache(download_id)
            
            return True
    
    async def resume_download(self, download_id: str) -> bool:
        """
        恢复下载
        
        Args:
            download_id: 下载任务ID
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            await service.resume_download(download_id)
            
            # 清除相关缓存
            await self._clear_download_cache(download_id)
            
            return True
    
    async def delete_download(self, download_id: str, delete_files: bool = False) -> bool:
        """
        删除下载任务
        
        Args:
            download_id: 下载任务ID
            delete_files: 是否删除文件
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            await service.delete_download(download_id, delete_files)
            
            # 清除相关缓存
            await self._clear_download_cache(download_id)
            
            return True
    
    # ========== 辅助方法 ==========
    
    # 注意：DownloadService 已经返回字典，不需要转换
    # 但为了兼容性，保留此方法以备将来使用
    
    async def _clear_download_cache(self, download_id: Optional[str] = None):
        """
        清除下载缓存
        
        Args:
            download_id: 下载任务ID（如果指定，只清除该任务的缓存；否则清除所有缓存）
        """
        if download_id:
            # 清除特定下载任务的缓存
            cache_key = self._get_cache_key("get_download", download_id)
            if cache_key in self._cache:
                del self._cache[cache_key]
        else:
            # 清除所有下载相关缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if "list_downloads" in key or "get_download" in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
        
        logger.debug(f"已清除下载缓存: download_id={download_id}")
