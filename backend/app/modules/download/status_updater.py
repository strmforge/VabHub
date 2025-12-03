"""
下载状态更新服务
定期从下载器获取状态并更新数据库
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.download import DownloadTask
from app.core.downloaders import DownloaderClient, DownloaderType
from app.core.websocket import manager
from pathlib import Path


class DownloadStatusUpdater:
    """下载状态更新器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.running = False
        self.update_interval = 5  # 更新间隔（秒）
    
    async def start(self):
        """启动状态更新服务"""
        self.running = True
        logger.info("下载状态更新服务已启动")
        
        while self.running:
            try:
                await self.update_all_downloads()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"更新下载状态异常: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def stop(self):
        """停止状态更新服务"""
        self.running = False
        logger.info("下载状态更新服务已停止")
    
    async def update_all_downloads(self):
        """更新所有下载任务的状态"""
        try:
            # 获取所有活跃的下载任务
            query = select(DownloadTask).where(
                DownloadTask.status.in_(["downloading", "paused", "pending"])
            )
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            if not tasks:
                return
            
            # 按下载器分组
            tasks_by_downloader: dict = {}
            for task in tasks:
                downloader = task.downloader
                if downloader not in tasks_by_downloader:
                    tasks_by_downloader[downloader] = []
                tasks_by_downloader[downloader].append(task)
            
            # 更新每个下载器的任务
            for downloader_name, downloader_tasks in tasks_by_downloader.items():
                await self.update_downloader_tasks(downloader_name, downloader_tasks)
        
        except Exception as e:
            logger.error(f"更新所有下载任务状态失败: {e}")
    
    async def update_downloader_tasks(self, downloader_name: str, tasks: List[DownloadTask]):
        """更新指定下载器的任务状态"""
        try:
            # 从设置中获取下载器配置
            from app.modules.settings.service import SettingsService
            settings_service = SettingsService(self.db)
            
            # 获取下载器配置
            downloader_config = await self._get_downloader_config(downloader_name, settings_service)
            
            if not downloader_config:
                logger.warning(f"下载器 {downloader_name} 配置未找到，跳过更新")
                return
            
            # 创建下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
            
            client = DownloaderClient(downloader_type, downloader_config)
            
            # 获取下载器中的所有任务
            try:
                torrents = await client.get_torrents()
                
                # 创建hash到torrent的映射
                torrent_map = {}
                for torrent in torrents:
                    if downloader_type == DownloaderType.QBITTORRENT:
                        torrent_hash = torrent.get("hash")
                    else:
                        torrent_hash = torrent.get("hashString")
                    
                    if torrent_hash:
                        torrent_map[torrent_hash] = torrent
                
                # 更新每个任务
                for task in tasks:
                    if task.downloader_hash:
                        # 从映射中获取任务信息
                        torrent_info = torrent_map.get(task.downloader_hash)
                        if torrent_info:
                            await self.update_task_status(task, torrent_info, downloader_type)
                        else:
                            # 如果下载器中找不到，可能已被删除
                            if task.status not in ["completed", "failed"]:
                                task.status = "failed"
                                self.db.add(task)
                                await self.db.commit()
                                logger.warning(f"下载任务 {task.title} 在下载器中未找到，标记为失败")
                    else:
                        # 如果没有hash，尝试通过标题匹配
                        await self._match_task_by_title(task, torrents, downloader_type, client)
                
                await client.close()
            except Exception as e:
                logger.error(f"从下载器获取任务状态失败: {e}")
                try:
                    await client.close()
                except:
                    pass
        
        except Exception as e:
            logger.error(f"更新下载器任务状态失败: {e}")
    
    async def _get_downloader_config(self, downloader_name: str, settings_service) -> Optional[Dict]:
        """获取下载器配置"""
        try:
            # 从设置中获取下载器配置
            config_prefix = f"{downloader_name.lower()}_"
            
            host = await settings_service.get_setting(f"{config_prefix}host")
            port = await settings_service.get_setting(f"{config_prefix}port")
            username = await settings_service.get_setting(f"{config_prefix}username")
            password = await settings_service.get_setting(f"{config_prefix}password")
            
            # 如果设置中没有，使用默认值
            if not host:
                host = "localhost"
            if not port:
                port = 8080 if downloader_name == "qBittorrent" else 9091
            
            return {
                "host": host or "localhost",
                "port": int(port) if port else (8080 if downloader_name == "qBittorrent" else 9091),
                "username": username or "",
                "password": password or ""
            }
        except Exception as e:
            logger.error(f"获取下载器配置失败: {e}")
            # 返回默认配置
            return {
                "host": "localhost",
                "port": 8080 if downloader_name == "qBittorrent" else 9091,
                "username": "",
                "password": ""
            }
    
    async def _match_task_by_title(self, task: DownloadTask, torrents: List[Dict], downloader_type: DownloaderType, client: DownloaderClient):
        """通过标题匹配任务"""
        try:
            task_title = task.title.lower()
            
            for torrent in torrents:
                torrent_name = torrent.get("name", "").lower()
                
                # 简单的标题匹配
                if task_title in torrent_name or torrent_name in task_title:
                    # 找到匹配的任务，更新hash
                    if downloader_type == DownloaderType.QBITTORRENT:
                        task.downloader_hash = torrent.get("hash")
                    else:
                        task.downloader_hash = torrent.get("hashString")
                    
                    self.db.add(task)
                    await self.db.commit()
                    
                    # 更新任务状态
                    await self.update_task_status(task, torrent, downloader_type)
                    break
        except Exception as e:
            logger.error(f"匹配任务失败: {e}")
    
    async def update_task_status(self, task: DownloadTask, torrent_info: dict, downloader_type: DownloaderType):
        """更新单个任务的状态"""
        try:
            # 保存旧值用于比较
            old_progress = task.progress
            old_status = task.status
            
            # 根据下载器类型解析状态
            if downloader_type == DownloaderType.QBITTORRENT:
                # qBittorrent状态映射
                qb_state = torrent_info.get("state", "")
                if qb_state in ["uploading", "stalledUP"]:
                    task.status = "completed"
                elif qb_state in ["downloading", "stalledDL"]:
                    task.status = "downloading"
                elif qb_state == "pausedDL":
                    task.status = "paused"
                elif qb_state == "queuedDL":
                    task.status = "pending"
                else:
                    task.status = "downloading"
                
                # 更新进度
                progress = torrent_info.get("progress", 0)  # 0-1之间的小数
                task.progress = progress * 100  # 转换为百分比
                
                # 更新大小和下载量
                total_size = torrent_info.get("total_size", 0)
                downloaded = torrent_info.get("downloaded", 0)
                task.size_gb = total_size / (1024 ** 3)
                task.downloaded_gb = downloaded / (1024 ** 3)
                
                # 更新速度
                dl_speed = torrent_info.get("dlspeed", 0)  # bytes/s
                task.speed_mbps = dl_speed / (1024 ** 2)  # MB/s
                
                # 更新ETA
                eta = torrent_info.get("eta", -1)
                task.eta = eta if eta > 0 else None
                
            else:
                # Transmission状态映射
                trans_status = torrent_info.get("status", 0)
                # Transmission状态: 0=stopped, 4=downloading, 6=seeding
                if trans_status == 6:
                    task.status = "completed"
                elif trans_status == 4:
                    task.status = "downloading"
                elif trans_status == 0:
                    task.status = "paused"
                else:
                    task.status = "downloading"
                
                # 更新进度
                percent_done = torrent_info.get("percentDone", 0)  # 0-1之间的小数
                task.progress = percent_done * 100  # 转换为百分比
                
                # 更新大小和下载量
                total_size = torrent_info.get("totalSize", 0)
                downloaded = torrent_info.get("downloadedEver", 0)
                task.size_gb = total_size / (1024 ** 3)
                task.downloaded_gb = downloaded / (1024 ** 3)
                
                # 更新速度
                dl_speed = torrent_info.get("rateDownload", 0)  # bytes/s
                task.speed_mbps = dl_speed / (1024 ** 2)  # MB/s
                
                # 更新ETA
                eta = torrent_info.get("eta", -1)
                task.eta = eta if eta > 0 else None
            
            # 更新更新时间
            task.updated_at = datetime.utcnow()
            
            # 如果状态改变为完成，更新完成时间
            if task.status == "completed" and old_status != "completed":
                task.completed_at = datetime.utcnow()
                
                # P2: 发送下载完成通知
                try:
                    from app.services.notification_service import notify_download_task_completed_for_user
                    from app.schemas.notification_download import DownloadTaskCompletedPayload
                    
                    # 计算下载耗时
                    download_duration = None
                    if task.created_at:
                        duration = task.completed_at - task.created_at
                        download_duration = int(duration.total_seconds() / 60)  # 转换为分钟
                    
                    # 构建通知 payload
                    notification_payload = DownloadTaskCompletedPayload(
                        title=task.title,
                        site_name=None,  # 可以从 extra_metadata 中获取
                        category_label=task.media_type or "unknown",
                        resolution=None,  # 可以从 extra_metadata 中获取
                        source_label="下载引擎",
                        route_name="download-tasks",
                        route_params={"task_id": task.id},
                        task_id=task.id,
                        success=True,  # 这里假设完成就是成功，后续可以根据文件整理结果调整
                        media_type=task.media_type,
                        season_number=None,  # 可以从 extra_metadata 中解析
                        episode_number=None,  # 可以从 extra_metadata 中解析
                        library_path=None,   # 文件整理后的路径
                        file_size_gb=task.size_gb,
                        download_duration_minutes=download_duration
                    ).dict()
                    
                    # 获取用户ID - 从 extra_metadata 获取
                    user_id = 1  # 默认值
                    if task.extra_metadata:
                        user_id = task.extra_metadata.get("user_id", 1)
                    
                    await notify_download_task_completed_for_user(
                        session=self.db,
                        user_id=user_id,
                        payload=notification_payload
                    )
                    
                    logger.info(f"下载完成通知已发送: 任务={task.id}, 标题={task.title}")
                except Exception as e:
                    logger.warning(f"发送下载完成通知失败: {e}")
                    # 通知失败不影响下载流程
                
                # 事件驱动：任务完成时立即触发文件整理
                # 异步触发，不阻塞状态更新
                asyncio.create_task(self._on_task_completed(task))
            
            # 保存到数据库
            self.db.add(task)
            await self.db.commit()
            
            # 如果进度或状态有变化，通过WebSocket广播
            if abs(task.progress - old_progress) > 0.1 or task.status != old_status:
                try:
                    await manager.broadcast_download_progress(
                        task_id=task.task_id,
                        progress=task.progress,
                        status=task.status,
                        downloaded_gb=task.downloaded_gb,
                        speed_mbps=task.speed_mbps,
                        eta=task.eta
                    )
                except Exception as ws_error:
                    logger.debug(f"WebSocket广播失败: {ws_error}")
        
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
    
    async def _on_task_completed(self, task: DownloadTask):
        """
        任务完成时的处理（事件驱动）
        检查是否有VABHUB标签，如果有则立即触发文件整理
        """
        try:
            # 检查任务是否有VABHUB标签
            has_tag = await self._has_vabhub_tag(task)
            
            if not has_tag:
                logger.debug(f"任务 {task.task_id} 没有VABHUB标签，跳过文件整理")
                return
            
            logger.info(f"任务 {task.task_id} ({task.title}) 已完成，开始触发文件整理")
            
            # 通过WebSocket通知前端：开始整理
            try:
                await manager.broadcast({
                    "type": "transfer_started",
                    "data": {
                        "task_id": task.task_id,
                        "title": task.title,
                        "status": "transferring",
                        "message": "下载完成，开始整理文件..."
                    }
                })
            except Exception as ws_error:
                logger.debug(f"WebSocket广播失败: {ws_error}")
            
            # 触发文件整理（异步执行，不阻塞）
            asyncio.create_task(self._trigger_transfer(task))
            
            # 如果是电子书或有声书，触发入库（异步执行，不阻塞）
            if task.media_type:
                from app.constants.media_types import normalize_media_type, MEDIA_TYPE_EBOOK, MEDIA_TYPE_AUDIOBOOK
                normalized_type = normalize_media_type(task.media_type)
                if normalized_type == MEDIA_TYPE_EBOOK:
                    asyncio.create_task(self._import_ebook(task))
                elif normalized_type == MEDIA_TYPE_AUDIOBOOK:
                    asyncio.create_task(self._import_audiobook(task))
            
        except Exception as e:
            logger.error(f"任务完成处理异常: {e}", exc_info=True)
    
    async def _has_vabhub_tag(self, task: DownloadTask) -> bool:
        """
        检查任务是否有VABHUB标签
        通过查询下载器中的任务标签来判断
        """
        try:
            from app.core.config import settings
            from app.modules.settings.service import SettingsService
            
            # 获取下载器配置
            settings_service = SettingsService(self.db)
            downloader_config = await self._get_downloader_config(task.downloader, settings_service)
            
            if not downloader_config:
                return False
            
            # 创建下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloader_config)
            
            try:
                # 获取任务信息（包含标签）
                if task.downloader_hash:
                    torrent_info = await client.get_torrent_info(task.downloader_hash)
                    if torrent_info:
                        # 检查标签
                        tags = torrent_info.get("tags", [])
                        if isinstance(tags, str):
                            tags = [tag.strip() for tag in tags.split(",")]
                        
                        has_tag = settings.TORRENT_TAG in tags
                        await client.close()
                        return has_tag
                
                await client.close()
                return False
            except Exception as e:
                logger.debug(f"检查任务标签失败: {e}")
                try:
                    await client.close()
                except:
                    pass
                return False
        except Exception as e:
            logger.error(f"检查VABHUB标签异常: {e}")
            return False
    
    async def _trigger_transfer(self, task: DownloadTask):
        """
        触发文件整理
        查询目录配置，调用文件整理服务
        """
        try:
            from app.modules.file_operation.transfer_service import TransferService
            from app.models.directory import Directory
            from app.schemas.directory import DirectoryConfig
            from app.core.config import settings
            
            # 获取下载器监控目录配置
            result = await self.db.execute(
                select(Directory).where(
                    Directory.monitor_type == "downloader",
                    Directory.enabled == True,
                    Directory.storage == "local"
                ).order_by(Directory.priority)
            )
            directories = result.scalars().all()
            
            if not directories:
                logger.debug(f"没有配置下载器监控目录，跳过文件整理")
                return
            
            # 获取任务的文件路径（从下载器获取）
            from app.modules.settings.service import SettingsService
            settings_service = SettingsService(self.db)
            downloader_config = await self._get_downloader_config(task.downloader, settings_service)
            
            if not downloader_config:
                logger.warning(f"无法获取下载器配置，跳过文件整理")
                return
            
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloader_config)
            
            try:
                # 获取任务信息
                if task.downloader_hash:
                    torrent_info = await client.get_torrent_info(task.downloader_hash)
                    if not torrent_info:
                        logger.warning(f"无法获取任务信息，跳过文件整理")
                        await client.close()
                        return
                    
                    # 获取文件路径
                    file_path = torrent_info.get("content_path") or torrent_info.get("downloadDir")
                    if not file_path:
                        logger.warning(f"任务没有文件路径，跳过文件整理")
                        await client.close()
                        return
                    
                    file_path_obj = Path(file_path)
                    if not file_path_obj.exists():
                        logger.warning(f"文件不存在: {file_path}")
                        await client.close()
                        return
                    
                    # 检查是否为下载器监控目录中的文件
                    matched_dir = None
                    for dir in directories:
                        if not dir.download_path:
                            continue
                        if file_path_obj.is_relative_to(Path(dir.download_path)):
                            matched_dir = DirectoryConfig(
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
                            break
                    
                    if not matched_dir:
                        logger.debug(f"文件 {file_path} 不在下载器监控目录中，跳过文件整理")
                        await client.close()
                        return
                    
                    # 调用文件整理服务
                    transfer_service = TransferService(self.db)
                    result = await transfer_service.transfer_directory(
                        source_dir=str(file_path_obj.parent if file_path_obj.is_file() else file_path_obj),
                        directory_config=matched_dir,
                        media_info=None,  # 可以从任务中获取媒体信息
                        overwrite_mode="never"
                    )
                    
                    # 通过WebSocket通知前端：整理完成
                    try:
                        if result.get("success"):
                            await manager.broadcast({
                                "type": "transfer_completed",
                                "data": {
                                    "task_id": task.task_id,
                                    "title": task.title,
                                    "status": "completed",
                                    "message": "文件整理完成",
                                    "result": result
                                }
                            })
                        else:
                            await manager.broadcast({
                                "type": "transfer_failed",
                                "data": {
                                    "task_id": task.task_id,
                                    "title": task.title,
                                    "status": "failed",
                                    "message": f"文件整理失败: {result.get('error')}",
                                    "error": result.get("error")
                                }
                            })
                    except Exception as ws_error:
                        logger.debug(f"WebSocket广播失败: {ws_error}")
                    
                    if result.get("success"):
                        logger.info(f"文件整理成功: {file_path}")
                    else:
                        logger.error(f"文件整理失败: {file_path} - {result.get('error')}")
                    
                    await client.close()
            except Exception as e:
                logger.error(f"触发文件整理异常: {e}", exc_info=True)
                try:
                    await client.close()
                except:
                    pass
        except Exception as e:
            logger.error(f"触发文件整理异常: {e}", exc_info=True)
    
    async def _import_ebook(self, task: DownloadTask):
        """
        导入电子书（当下载任务完成且媒体类型为 ebook 时）
        """
        try:
            from app.modules.ebook.importer import EBookImporter
            from app.modules.settings.service import SettingsService
            from app.modules.download.client import DownloaderClient, DownloaderType
            import os
            
            logger.info(f"开始导入电子书: {task.task_id} ({task.title})")
            
            # 获取下载器配置以获取文件路径
            settings_service = SettingsService(self.db)
            downloader_config = await self._get_downloader_config(task.downloader, settings_service)
            
            if not downloader_config:
                logger.warning(f"无法获取下载器配置，跳过电子书入库")
                return
            
            # 获取下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloader_config)
            
            try:
                # 获取任务的文件路径
                if task.downloader_hash:
                    torrent_info = await client.get_torrent_info(task.downloader_hash)
                    if torrent_info:
                        content_path = torrent_info.get("content_path") or torrent_info.get("save_path")
                        if content_path:
                            # 从 extra_metadata 中提取 site_id 和 torrent_id
                            extra_meta = task.extra_metadata or {}
                            site_id = extra_meta.get("site_id") or extra_meta.get("site")
                            torrent_id = extra_meta.get("torrent_id")
                            
                            # 创建电子书导入器
                            importer = EBookImporter(self.db)
                            
                            # 判断是文件还是目录
                            if os.path.isfile(content_path):
                                # 单个文件
                                await importer.import_ebook_from_file(
                                    file_path=content_path,
                                    source_site_id=site_id,
                                    source_torrent_id=torrent_id,
                                    download_task_id=task.id,
                                    media_type=task.media_type
                                )
                            elif os.path.isdir(content_path):
                                # 目录（可能包含多个文件）
                                await importer.import_ebooks_from_directory(
                                    directory_path=content_path,
                                    source_site_id=site_id,
                                    source_torrent_id=torrent_id,
                                    download_task_id=task.id,
                                    media_type=task.media_type
                                )
                            
                            logger.info(f"电子书入库完成: {task.task_id}")
                
                await client.close()
            except Exception as e:
                logger.error(f"电子书导入流程失败: {task.task_id}, 错误: {e}", exc_info=True)
                try:
                    await client.close()
                except:
                    pass
        except Exception as e:
            logger.error(f"导入电子书失败: {task.task_id}, 错误: {e}", exc_info=True)
    
    async def _import_audiobook(self, task: DownloadTask):
        """
        导入有声书（当下载任务完成且媒体类型为 audiobook 时）
        """
        try:
            from app.modules.audiobook.importer import AudiobookImporter
            from app.modules.settings.service import SettingsService
            from app.modules.download.client import DownloaderClient, DownloaderType
            import os
            
            logger.info(f"开始导入有声书: {task.task_id} ({task.title})")
            
            # 获取下载器配置以获取文件路径
            settings_service = SettingsService(self.db)
            downloader_config = await self._get_downloader_config(task.downloader, settings_service)
            
            if not downloader_config:
                logger.warning(f"无法获取下载器配置，跳过高声书入库")
                return
            
            # 获取下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloader_config)
            
            try:
                # 获取任务的文件路径
                if task.downloader_hash:
                    torrent_info = await client.get_torrent_info(task.downloader_hash)
                    if torrent_info:
                        content_path = torrent_info.get("content_path") or torrent_info.get("save_path")
                        if content_path:
                            # 从 extra_metadata 中提取 site_id 和 torrent_id
                            extra_meta = task.extra_metadata or {}
                            site_id = extra_meta.get("site_id") or extra_meta.get("site")
                            torrent_id = extra_meta.get("torrent_id")
                            
                            # 创建有声书导入器
                            importer = AudiobookImporter(self.db)
                            
                            # 判断是文件还是目录
                            if os.path.isfile(content_path):
                                # 单个文件
                                await importer.import_audiobook_from_file(
                                    file_path=content_path,
                                    source_site_id=site_id,
                                    source_torrent_id=torrent_id,
                                    download_task_id=task.id,
                                    media_type=task.media_type
                                )
                            elif os.path.isdir(content_path):
                                # 目录（可能包含多个文件）
                                imported_count = 0
                                for file_path in Path(content_path).rglob("*"):
                                    if file_path.is_file() and importer.is_audiobook_file(str(file_path)):
                                        await importer.import_audiobook_from_file(
                                            file_path=str(file_path),
                                            source_site_id=site_id,
                                            source_torrent_id=torrent_id,
                                            download_task_id=task.id,
                                            media_type=task.media_type
                                        )
                                        imported_count += 1
                                
                                if imported_count > 0:
                                    logger.info(f"有声书批量入库完成: {task.task_id}，共导入 {imported_count} 个文件")
                            
                            logger.info(f"有声书入库完成: {task.task_id}")
                
                await client.close()
            except Exception as e:
                logger.error(f"导入有声书失败: {task.task_id}, 错误: {e}", exc_info=True)
                try:
                    await client.close()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"导入有声书失败: {task.task_id}, 错误: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"电子书入库处理异常: {e}", exc_info=True)


# 全局状态更新器实例（将由后台任务使用）
_status_updater: DownloadStatusUpdater = None


async def start_status_updater(db: AsyncSession):
    """启动状态更新器"""
    global _status_updater
    if _status_updater is None:
        _status_updater = DownloadStatusUpdater(db)
        # 在后台任务中运行
        asyncio.create_task(_status_updater.start())


async def stop_status_updater():
    """停止状态更新器"""
    global _status_updater
    if _status_updater:
        await _status_updater.stop()
        _status_updater = None

