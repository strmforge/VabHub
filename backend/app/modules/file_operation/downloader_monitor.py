"""
下载器监控服务
定时扫描下载器中的已完成任务（只处理打了标签的任务）
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.downloaders import DownloaderClient, DownloaderType
from app.models.directory import Directory
from app.models.download import DownloadTask
from app.schemas.directory import DirectoryConfig
from app.modules.file_operation.transfer_service import TransferService
from app.modules.settings.service import SettingsService


class DownloaderMonitor:
    """下载器监控服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start(self, interval: int = 1800):
        """
        启动下载器监控（兜底机制）
        
        Args:
            interval: 监控间隔（秒），默认30分钟（作为事件驱动的兜底机制）
        """
        if self._running:
            logger.warning("下载器监控已在运行")
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info(f"下载器监控已启动，间隔: {interval}秒")
    
    async def stop(self):
        """停止下载器监控"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("下载器监控已停止")
    
    async def _monitor_loop(self, interval: int):
        """监控循环"""
        while self._running:
            try:
                await self.process_completed_torrents()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"下载器监控异常: {e}", exc_info=True)
                await asyncio.sleep(interval)
    
    async def process_completed_torrents(self):
        """
        处理已完成的下载任务
        
        工作流程：
        1. 获取下载器监控目录配置
        2. 查询下载器中的已完成任务（只查询打了标签的任务）
        3. 检查任务是否在下载器监控目录中
        4. 查询下载历史记录（获取媒体信息）
        5. 调用文件整理服务
        """
        try:
            # 1. 获取下载器监控目录配置
            download_dirs = await self._get_downloader_monitor_dirs()
            if not download_dirs:
                logger.debug("没有配置下载器监控目录，跳过处理")
                return
            
            logger.info(f"开始处理下载器中的已完成任务，监控目录数: {len(download_dirs)}")
            
            # 2. 获取所有启用的下载器配置
            downloaders = await self._get_enabled_downloaders()
            if not downloaders:
                logger.debug("没有启用的下载器，跳过处理")
                return
            
            # 3. 遍历每个下载器
            for downloader_config in downloaders:
                try:
                    await self._process_downloader(downloader_config, download_dirs)
                except Exception as e:
                    logger.error(f"处理下载器 {downloader_config['name']} 失败: {e}", exc_info=True)
            
            logger.info("下载器监控处理完成")
            
        except Exception as e:
            logger.error(f"处理已完成任务异常: {e}", exc_info=True)
    
    async def _process_downloader(
        self,
        downloader_config: Dict[str, Any],
        download_dirs: List[DirectoryConfig]
    ):
        """处理单个下载器的已完成任务"""
        try:
            # 创建下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if downloader_config['type'] == 'qBittorrent' else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloader_config['config'])
            
            # 查询已完成的种子（只查询打了标签的任务）
            tags = [settings.TORRENT_TAG]
            completed_torrents = await client.get_completed_torrents(tags=tags)
            
            if not completed_torrents:
                logger.debug(f"下载器 {downloader_config['name']} 没有已完成的带标签任务")
                return
            
            logger.info(f"下载器 {downloader_config['name']} 找到 {len(completed_torrents)} 个已完成的带标签任务")
            
            # 处理每个已完成的任务
            for torrent in completed_torrents:
                try:
                    await self._process_torrent(torrent, downloader_config, download_dirs, client)
                except Exception as e:
                    logger.error(f"处理任务失败: {torrent.get('name', 'unknown')} - {e}", exc_info=True)
            
        except Exception as e:
            logger.error(f"处理下载器 {downloader_config['name']} 异常: {e}", exc_info=True)
    
    async def _process_torrent(
        self,
        torrent: Dict[str, Any],
        downloader_config: Dict[str, Any],
        download_dirs: List[DirectoryConfig],
        client: DownloaderClient
    ):
        """处理单个种子任务"""
        try:
            torrent_hash = torrent.get("hash") or torrent.get("hashString")
            torrent_path = torrent.get("content_path") or torrent.get("downloadDir")
            torrent_name = torrent.get("name", "")
            
            if not torrent_path:
                logger.warning(f"任务 {torrent_name} 没有路径信息，跳过")
                return
            
            file_path = Path(torrent_path)
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return
            
            # 检查是否为下载器监控目录中的文件
            matched_dir = None
            for dir_config in download_dirs:
                if not dir_config.download_path:
                    continue
                if file_path.is_relative_to(Path(dir_config.download_path)):
                    matched_dir = dir_config
                    break
            
            if not matched_dir:
                logger.debug(f"文件 {file_path} 不在下载器监控目录中，跳过")
                return
            
            # 查询下载历史记录（从DownloadTask表查询）
            media_info = None
            if torrent_hash:
                download_task = await self._get_download_task_by_hash(torrent_hash)
                if download_task:
                    # 构建媒体信息（简化版，实际应该从媒体识别服务获取）
                    media_info = {
                        "title": download_task.title,
                        "type": "unknown",  # TODO: 从下载任务或媒体识别服务获取
                    }
                    # 从 extra_metadata 中提取 site_id 和 torrent_id（用于 Local Intel HR 保护）
                    if download_task.extra_metadata:
                        extra_meta = download_task.extra_metadata
                        # 尝试从不同位置获取 site_id
                        site_id = (
                            extra_meta.get("site_id") or
                            extra_meta.get("site") or
                            (extra_meta.get("decision", {}).get("site") if isinstance(extra_meta.get("decision"), dict) else None)
                        )
                        # 尝试从不同位置获取 torrent_id
                        torrent_id = (
                            extra_meta.get("torrent_id") or
                            extra_meta.get("torrentId") or
                            (extra_meta.get("decision", {}).get("torrent_id") if isinstance(extra_meta.get("decision"), dict) else None)
                        )
                        if site_id:
                            media_info["site_id"] = site_id
                            media_info["site"] = site_id  # 兼容两种字段名
                        if torrent_id:
                            media_info["torrent_id"] = str(torrent_id)
            
            # 调用文件整理服务
            transfer_service = TransferService(self.db)
            result = await transfer_service.transfer_directory(
                source_dir=str(file_path),
                directory_config=matched_dir,
                media_info=media_info,
                overwrite_mode="never"  # 默认不覆盖
            )
            
            if result.get("success"):
                logger.info(f"文件整理成功: {file_path}")
                # TODO: 标记任务为已整理（在下载器中添加"已整理"标签或更新数据库状态）
            else:
                logger.error(f"文件整理失败: {file_path} - {result.get('error')}")
            
        except Exception as e:
            logger.error(f"处理任务异常: {e}", exc_info=True)
    
    async def _get_downloader_monitor_dirs(self) -> List[DirectoryConfig]:
        """获取下载器监控目录配置"""
        try:
            result = await self.db.execute(
                select(Directory).where(
                    Directory.monitor_type == "downloader",
                    Directory.enabled == True,
                    Directory.storage == "local"
                ).order_by(Directory.priority)
            )
            directories = result.scalars().all()
            
            return [
                DirectoryConfig(
                    download_path=dir.download_path,
                    library_path=dir.library_path,
                    storage=dir.storage,
                    library_storage=dir.library_storage,
                    monitor_type=dir.monitor_type,
                    transfer_type=dir.transfer_type,
                    media_type=dir.media_type,
                    media_category=dir.media_category,
                    priority=dir.priority,
                    enabled=dir.enabled
                )
                for dir in directories
            ]
        except Exception as e:
            logger.error(f"获取下载器监控目录失败: {e}")
            return []
    
    async def _get_enabled_downloaders(self) -> List[Dict[str, Any]]:
        """获取所有启用的下载器配置"""
        try:
            settings_service = SettingsService(self.db)
            downloaders = []
            
            # 检查qBittorrent
            qb_host = await settings_service.get_setting("qbittorrent_host")
            if qb_host:
                qb_port = await settings_service.get_setting("qbittorrent_port") or 8080
                qb_username = await settings_service.get_setting("qbittorrent_username") or ""
                qb_password = await settings_service.get_setting("qbittorrent_password") or ""
                
                downloaders.append({
                    "name": "qBittorrent",
                    "type": "qBittorrent",
                    "config": {
                        "host": qb_host,
                        "port": int(qb_port) if isinstance(qb_port, str) else qb_port,
                        "username": qb_username,
                        "password": qb_password
                    }
                })
            
            # 检查Transmission
            tr_host = await settings_service.get_setting("transmission_host")
            if tr_host:
                tr_port = await settings_service.get_setting("transmission_port") or 9091
                tr_username = await settings_service.get_setting("transmission_username") or ""
                tr_password = await settings_service.get_setting("transmission_password") or ""
                
                downloaders.append({
                    "name": "Transmission",
                    "type": "Transmission",
                    "config": {
                        "host": tr_host,
                        "port": int(tr_port) if isinstance(tr_port, str) else tr_port,
                        "username": tr_username,
                        "password": tr_password
                    }
                })
            
            return downloaders
        except Exception as e:
            logger.error(f"获取下载器配置失败: {e}")
            return []
    
    async def _get_download_task_by_hash(self, torrent_hash: str) -> Optional[DownloadTask]:
        """根据hash查询下载任务"""
        try:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.downloader_hash == torrent_hash)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"查询下载任务失败: {e}")
            return None

