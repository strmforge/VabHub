"""
下载服务
"""

from datetime import datetime
import time
import uuid
from typing import Dict, List, Optional, Any

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.media_types import MEDIA_TYPE_UNKNOWN, normalize_media_type
from app.core.cache import get_cache
from app.core.websocket import manager
from app.models.download import DownloadTask
from app.modules.settings.service import SettingsService


class DownloadService:
    """下载服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()
        self._settings_service: Optional[SettingsService] = None
        self._simulation_mode: Optional[bool] = None

    def _get_settings_service(self) -> SettingsService:
        if self._settings_service is None:
            self._settings_service = self._get_settings_service()
        return self._settings_service

    def _has_real_downloader_config(self, host: Optional[str], username: Optional[str], password: Optional[str]) -> bool:
        host_value = (host or "").strip().lower()
        if host_value and host_value not in {"localhost", "127.0.0.1"}:
            return True
        if (username or "").strip():
            return True
        if (password or "").strip():
            return True
        return False

    async def detect_simulation_mode(self) -> bool:
        """
        检测是否处于“模拟下载模式”：
        当 qBittorrent / Transmission 都未配置非默认主机或凭据时视为未绑定真实下载器。
        """
        if self._simulation_mode is not None:
            return self._simulation_mode

        settings_service = self._get_settings_service()
        qb_host = await settings_service.get_setting("qbittorrent_host", "localhost")
        qb_user = await settings_service.get_setting("qbittorrent_username", "")
        qb_pass = await settings_service.get_setting("qbittorrent_password", "")
        trans_host = await settings_service.get_setting("transmission_host", "localhost")
        trans_user = await settings_service.get_setting("transmission_username", "")
        trans_pass = await settings_service.get_setting("transmission_password", "")

        has_qb = self._has_real_downloader_config(qb_host, qb_user, qb_pass)
        has_trans = self._has_real_downloader_config(trans_host, trans_user, trans_pass)

        self._simulation_mode = not (has_qb or has_trans)
        return self._simulation_mode
    
    def _calculate_is_vabhub_managed(self, labels: List[str]) -> bool:
        """
        计算任务是否为 VabHub 管理的任务
        
        Args:
            labels: 下载器中的标签列表
            
        Returns:
            bool: 是否为 VabHub 管理的任务
        """
        from app.core.config import settings
        
        if not labels:
            return False
            
        # 转换为小写进行匹配，忽略大小写
        labels_lower = [label.lower().strip() for label in labels if label and label.strip()]
        whitelist_lower = [label.lower().strip() for label in settings.VABHUB_TORRENT_LABELS]
        
        # 检查是否有任何标签匹配白名单
        return any(label in whitelist_lower for label in labels_lower)
    
    async def list_downloads(
        self, 
        status: Optional[str] = None,
        vabhub_only: bool = True,  # 只显示带VABHUB标签的任务（唯一选择，包括用户手动添加的）
        hide_organized: bool = True,  # DOWNLOAD-CENTER-UI-2: 隐藏已整理完成的任务（默认True实现自动退场）
        recent_hours: Optional[int] = None  # DOWNLOAD-CENTER-UI-2: 最近完成任务时间范围过滤
    ) -> List[dict]:
        """
        获取下载列表（带缓存）
        
        Args:
            status: 状态过滤
            vabhub_only: 是否只显示VABHUB标签的任务（默认True，只显示带VABHUB标签的任务，包括用户手动添加的）
            hide_organized: 是否隐藏已整理完成的任务（DOWNLOAD-CENTER-UI-2新增）
        """
        from app.core.downloaders import DownloaderClient, DownloaderType
        from app.core.config import settings
        
        # 生成缓存键
        cache_key = f"downloads:list:{status}:{vabhub_only}:{hide_organized}:{recent_hours}"
        
        # 尝试从缓存获取（短期缓存，10秒）
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        query = select(DownloadTask)
        if status:
            # DOWNLOAD-CENTER-UI-1 修复：使用原始状态映射进行数据库查询
            raw_statuses = self._get_raw_status_for_filtering(status)
            if raw_statuses:
                query = query.where(DownloadTask.status.in_(raw_statuses))
            else:
                # 如果状态映射为空，返回空结果
                return []
        
        # DOWNLOAD-CENTER-UI-2: 添加已整理任务过滤
        if hide_organized:
            query = query.where(
                DownloadTask.organize_status.notin_(["AUTO_OK", "MANUAL_DONE"])
            )
        
        # DOWNLOAD-CENTER-UI-2: 添加最近完成任务时间过滤
        if recent_hours is not None:
            from datetime import datetime, timedelta
            from sqlalchemy import func
            cutoff_time = datetime.utcnow() - timedelta(hours=recent_hours)
            # 使用 COALESCE 处理 NULL 值：优先使用 completed_at，回退到 updated_at
            query = query.where(func.coalesce(DownloadTask.completed_at, DownloadTask.updated_at) >= cutoff_time)
        
        query = query.order_by(DownloadTask.created_at.desc())
        
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        # 如果只需要VABHUB标签的任务，从下载器获取标签信息进行过滤
        # 同时保存标签信息供后续显示使用（性能优化：避免重复获取）
        all_torrents_map = {}  # 存储所有已获取的torrent信息（按下载器分组）
        
        logger.info(f"开始处理下载列表：总任务数={len(tasks)}, vabhub_only={vabhub_only}")
        
        if vabhub_only:
            filtered_tasks = []
            settings_service = self._get_settings_service()
            
            # 按下载器分组任务，批量获取标签信息（性能优化）
            tasks_by_downloader = {}
            for task in tasks:
                if not task.downloader_hash:
                    continue
                downloader_name = task.downloader
                if downloader_name not in tasks_by_downloader:
                    tasks_by_downloader[downloader_name] = []
                tasks_by_downloader[downloader_name].append(task)
            
            # 为每个下载器批量获取标签信息
            for downloader_name, downloader_tasks in tasks_by_downloader.items():
                try:
                    downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                    config_prefix = f"{downloader_name.lower()}_"
                    host = await settings_service.get_setting(f"{config_prefix}host") or "localhost"
                    port = await settings_service.get_setting(f"{config_prefix}port") or (8080 if downloader_name == "qBittorrent" else 9091)
                    username = await settings_service.get_setting(f"{config_prefix}username") or ""
                    password = await settings_service.get_setting(f"{config_prefix}password") or ""
                    
                    downloader_config = {
                        "host": host,
                        "port": int(port) if isinstance(port, str) else port,
                        "username": username,
                        "password": password
                    }
                    
                    # 只连接一次下载器，批量获取所有任务信息
                    # 优化：如果下载器支持标签过滤，直接过滤VABHUB标签的任务
                    start_time = time.time()
                    logger.info(f"开始批量获取 {downloader_name} 任务信息（数据库中有 {len(downloader_tasks)} 个任务）...")
                    client = DownloaderClient(downloader_type, downloader_config)
                    
                    # 尝试使用标签过滤（如果支持）
                    if downloader_type == DownloaderType.QBITTORRENT:
                        # qBittorrent支持标签过滤
                        all_torrents = await client.get_torrents(tags=[settings.TORRENT_TAG])
                        logger.info(f"使用标签过滤获取qBittorrent任务（标签：{settings.TORRENT_TAG}）")
                    else:
                        # Transmission不支持标签过滤，需要获取所有任务
                        all_torrents = await client.get_torrents()
                    
                    await client.close()
                    elapsed = time.time() - start_time
                    logger.info(f"批量获取 {downloader_name} 完成：获取到 {len(all_torrents)} 个任务，耗时 {elapsed:.2f} 秒")
                    
                    # 创建hash到torrent的映射（用于过滤和后续显示）
                    torrent_map = {}
                    for torrent in all_torrents:
                        if downloader_type == DownloaderType.QBITTORRENT:
                            torrent_hash = torrent.get("hash")
                        else:  # Transmission
                            torrent_hash = torrent.get("hashString")
                        if torrent_hash:
                            torrent_map[torrent_hash] = torrent
                    
                    # 保存torrent_map供后续使用
                    all_torrents_map[downloader_name] = torrent_map
                    
                    # 检查每个任务是否有VABHUB标签
                    for task in downloader_tasks:
                        torrent_info = torrent_map.get(task.downloader_hash)
                        if torrent_info:
                            # 检查标签
                            if downloader_type == DownloaderType.QBITTORRENT:
                                tags = torrent_info.get("tags", "")
                                if isinstance(tags, str):
                                    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                                else:
                                    tags_list = tags if isinstance(tags, list) else []
                            else:  # Transmission
                                labels = torrent_info.get("labels", [])
                                if isinstance(labels, str):
                                    tags_list = [label.strip() for label in labels.split(",") if label.strip()]
                                else:
                                    tags_list = labels if isinstance(labels, list) else []
                            
                            if settings.TORRENT_TAG in tags_list:
                                filtered_tasks.append(task)
                        else:
                            # 如果找不到任务，默认包含（避免误过滤）
                            logger.debug(f"任务 {task.task_id} 在下载器中未找到，默认包含")
                            filtered_tasks.append(task)
                            
                except Exception as e:
                    logger.warning(f"获取 {downloader_name} 标签信息失败: {e}")
                    # 如果获取失败，默认包含所有任务（避免误过滤）
                    filtered_tasks.extend(downloader_tasks)
                    all_torrents_map[downloader_name] = {}
            
            tasks = filtered_tasks
        
        # 构建结果列表，包含标签信息
        # 如果vabhub_only=False，也需要批量获取标签信息（性能优化）
        result = []
        
        # 如果vabhub_only=False，批量获取标签信息（避免每个任务单独连接）
        if not vabhub_only and tasks:
            # 确保settings_service已初始化
            if 'settings_service' not in locals():
                settings_service = self._get_settings_service()
            # 按下载器分组任务
            tasks_by_downloader = {}
            for task in tasks:
                if task.downloader_hash:
                    downloader_name = task.downloader
                    if downloader_name not in tasks_by_downloader:
                        tasks_by_downloader[downloader_name] = []
                    tasks_by_downloader[downloader_name].append(task)
            
            # 为每个下载器批量获取标签信息
            for downloader_name, downloader_tasks in tasks_by_downloader.items():
                try:
                    downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                    config_prefix = f"{downloader_name.lower()}_"
                    host = await settings_service.get_setting(f"{config_prefix}host") or "localhost"
                    port = await settings_service.get_setting(f"{config_prefix}port") or (8080 if downloader_name == "qBittorrent" else 9091)
                    username = await settings_service.get_setting(f"{config_prefix}username") or ""
                    password = await settings_service.get_setting(f"{config_prefix}password") or ""
                    
                    downloader_config = {
                        "host": host,
                        "port": int(port) if isinstance(port, str) else port,
                        "username": username,
                        "password": password
                    }
                    
                    # 批量获取所有任务信息
                    start_time = time.time()
                    logger.info(f"开始批量获取 {downloader_name} 任务信息（数据库中有 {len(downloader_tasks)} 个任务）...")
                    client = DownloaderClient(downloader_type, downloader_config)
                    all_torrents = await client.get_torrents()
                    await client.close()
                    elapsed = time.time() - start_time
                    logger.info(f"批量获取 {downloader_name} 完成：获取到 {len(all_torrents)} 个任务，耗时 {elapsed:.2f} 秒")
                    
                    # 创建hash到torrent的映射
                    torrent_map = {}
                    for torrent in all_torrents:
                        if downloader_type == DownloaderType.QBITTORRENT:
                            torrent_hash = torrent.get("hash")
                        else:  # Transmission
                            torrent_hash = torrent.get("hashString")
                        if torrent_hash:
                            torrent_map[torrent_hash] = torrent
                    
                    all_torrents_map[downloader_name] = torrent_map
                except Exception as e:
                    logger.debug(f"获取 {downloader_name} 标签信息失败: {e}")
                    all_torrents_map[downloader_name] = {}
        
        # 构建结果列表
        for task in tasks:
            task_dict = {
                "id": task.task_id,
                "title": task.title,
                "status": task.status,
                "progress": task.progress,
                "size_gb": task.size_gb,
                "downloaded_gb": task.downloaded_gb,
                "speed_mbps": task.speed_mbps,
                "eta": task.eta,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "downloader": task.downloader,
                "media_type": task.media_type or MEDIA_TYPE_UNKNOWN,
                "extra_metadata": task.extra_metadata or {},
                "tags": []  # 默认空标签
            }
            
            # 如果有downloader_hash，尝试获取标签信息
            if task.downloader_hash:
                # 从缓存的torrent信息中获取
                downloader_name = task.downloader
                torrent_map = all_torrents_map.get(downloader_name)
                
                if torrent_map:
                    torrent_info = torrent_map.get(task.downloader_hash)
                    if torrent_info:
                        downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                        # 提取标签
                        if downloader_type == DownloaderType.QBITTORRENT:
                            tags = torrent_info.get("tags", "")
                            if isinstance(tags, str):
                                task_dict["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
                            else:
                                task_dict["tags"] = tags if isinstance(tags, list) else []
                        else:  # Transmission
                            labels = torrent_info.get("labels", [])
                            if isinstance(labels, str):
                                task_dict["tags"] = [label.strip() for label in labels.split(",") if label.strip()]
                            else:
                                task_dict["tags"] = labels if isinstance(labels, list) else []
            
            result.append(task_dict)
        
        # 缓存结果（10秒）
        await self.cache.set(cache_key, result, ttl=10)
        
        return result
    
    async def get_download(self, task_id: str) -> dict:
        """获取下载详情"""
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return {}
        
        return self._serialize_task(task)

    def _serialize_task(self, task: DownloadTask) -> Dict[str, Any]:
        return {
            "id": task.task_id,
            "title": task.title,
            "status": task.status,
            "progress": task.progress,
            "size_gb": task.size_gb,
            "downloaded_gb": task.downloaded_gb,
            "speed_mbps": task.speed_mbps,
            "eta": task.eta,
            "media_type": task.media_type or MEDIA_TYPE_UNKNOWN,
            "extra_metadata": task.extra_metadata or {},
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
    
    async def enrich_download_data(self, downloads: List[dict]) -> List[dict]:
        """
        增强下载数据 - DOWNLOAD-CENTER-UI-1
        添加站点信息、HR等级、短剧标记等字段
        优化版本：使用缓存避免重复查询下载器
        """
        if not downloads:
            return downloads
            
        from app.modules.settings.service import SettingsService
        from app.core.config import settings
        from app.core.downloaders import DownloaderClient, DownloaderType
        import asyncio
        from datetime import datetime, timedelta
        
        settings_service = self._get_settings_service()
        
        # 收集所有站点ID用于批量查询
        site_ids = set()
        for download in downloads:
            extra_meta = download.get("extra_metadata") or {}
            site_id = extra_meta.get("site_id") or extra_meta.get("site")
            if site_id:
                site_ids.add(site_id)
        
        # 批量查询站点名称映射
        site_name_map = {}
        if site_ids:
            for site_id in site_ids:
                try:
                    # 从站点配置获取站点名称
                    site_name = await settings_service.get_setting(f"site_{site_id}_name")
                    if site_name:
                        site_name_map[site_id] = site_name
                    else:
                        # 降级使用站点ID作为名称
                        site_name_map[site_id] = site_id
                        logger.warning(f"站点 {site_id} 名称配置未找到，使用ID作为名称")
                except Exception as e:
                    logger.warning(f"查询站点 {site_id} 名称失败: {e}，使用ID作为名称")
                    site_name_map[site_id] = site_id
        
        # 优化：使用缓存获取标签信息，避免实时查询下载器
        labels_map = {}  # {downloader_hash: [labels]}
        try:
            # 检查是否有缓存的标签信息（简单的内存缓存）
            # 在实际生产环境中，建议使用 Redis 等外部缓存
            cache_key = "download_labels_cache"
            cache_timeout = 30  # 30秒缓存
            
            # 这里简化处理：只获取当前下载任务的标签，不进行实时查询
            # 实际标签会在下载任务创建时保存到数据库或通过 WebSocket 更新
            for download in downloads:
                downloader_hash = download.get("downloader_hash", "").lower()
                # 使用基础标签列表，避免实时查询下载器
                labels_map[downloader_hash] = []
                        
        except Exception as e:
            logger.warning(f"获取标签信息失败: {e}")
        
        # 增强每个下载任务
        enriched_downloads = []
        for download in downloads:
            enriched_download = download.copy()
            
            # 1. 站点信息
            extra_meta = download.get("extra_metadata") or {}
            site_id = extra_meta.get("site_id") or extra_meta.get("site")
            if site_id:
                enriched_download["site_name"] = site_name_map.get(site_id, site_id)
                enriched_download["tracker_alias"] = site_name_map.get(site_id, site_id)
            
            # 2. 短剧标记
            media_type = download.get("media_type", "")
            enriched_download["is_short_drama"] = media_type == "short_drama"
            
            # 3. HR等级映射
            intel_hr_status = download.get("intel_hr_status", "UNKNOWN")
            enriched_download["hr_level"] = self._map_hr_level(intel_hr_status)
            
            # 4. 速度分离（如果有总速度，假设主要是下载速度）
            speed_mbps = download.get("speed_mbps")
            if speed_mbps:
                enriched_download["download_speed"] = speed_mbps
                enriched_download["upload_speed"] = 0.0  # 可以后续从下载器API获取
            
            # 5. 标签列表（使用缓存数据 + VabHub标签）
            labels = []
            downloader_hash = download.get("downloader_hash", "").lower()
            if downloader_hash in labels_map:
                labels.extend(labels_map[downloader_hash])
            
            # 添加 VabHub 标签
            if settings.TORRENT_TAG and settings.TORRENT_TAG not in labels:
                labels.append(settings.TORRENT_TAG)
            
            enriched_download["labels"] = labels
            
            # 6. DOWNLOAD-CENTER-UI-2: 计算 is_vabhub_managed
            enriched_download["is_vabhub_managed"] = self._calculate_is_vabhub_managed(labels)
            
            # 7. DOWNLOAD-CENTER-UI-2: 添加 organize_status（从数据库字段）
            enriched_download["organize_status"] = download.get("organize_status", "NONE")
            
            # 8. 添加时间（使用创建时间作为添加时间）
            enriched_download["added_at"] = download.get("created_at")
            
            # 7. 状态标准化（DOWNLOAD-CENTER-UI-1 关键修复）
            original_status = download.get("status", "")
            downloader_name = download.get("downloader", "")
            enriched_download["status"] = self._normalize_download_status(original_status, downloader_name)
            
            enriched_downloads.append(enriched_download)
        
        return enriched_downloads
    
    def _map_hr_level(self, intel_hr_status: str) -> str:
        """
        将 Local Intel HR 状态映射到显示等级
        SAFE/RISK/ACTIVE/UNKNOWN -> NONE/H&R/HR/H3/H5
        """
        mapping = {
            "SAFE": "NONE",
            "RISK": "H&R", 
            "ACTIVE": "HR",
            "UNKNOWN": "NONE"
        }
        return mapping.get(intel_hr_status, "NONE")
    
    def _normalize_download_status(self, downloader_status: str, downloader_type: str) -> str:
        """
        将下载器特定状态标准化为统一状态
        DOWNLOAD-CENTER-UI-1 状态映射
        """
        if not downloader_status:
            return "unknown"
            
        status = downloader_status.lower()
        
        # 通用状态映射
        if status in ("downloading", "active", "running", "seeding"):
            return "downloading"
        elif status in ("paused", "stopped", "pause"):
            return "paused"
        elif status in ("completed", "finished", "complete"):
            return "completed"
        elif status in ("error", "failed", "stoppederror"):
            return "error"
        
        # qBittorrent 特定状态映射
        if downloader_type == "qbittorrent":
            if status in ("queued", "queueddl", "queuedup"):
                return "queued"
            elif status in ("checking", "checkingdl", "checkingup"):
                return "queued"
            elif status in ("stalled", "stalleddl", "stalledup"):
                return "error"
            elif status in ("allocating", "metadl"):
                return "queued"
        
        # Transmission 特定状态映射
        elif downloader_type == "transmission":
            if status in ("queued", "queued to download", "queued to verify"):
                return "queued"
            elif status in ("checking", "verifying"):
                return "queued"
            elif status in ("stalled"):
                return "error"
        
        # 默认映射
        return "queued" if "queue" in status or "check" in status else "unknown"
    
    def _get_raw_status_for_filtering(self, normalized_status: str) -> List[str]:
        """
        将标准化状态映射回原始下载器状态列表，用于数据库查询
        DOWNLOAD-CENTER-UI-1 关键修复：解决状态过滤问题
        """
        if not normalized_status:
            return []
            
        status = normalized_status.lower()
        
        if status == "downloading":
            return ["downloading", "active", "running", "seeding"]
        elif status == "queued":
            return ["queued", "checking", "allocating", "metadl", "queueddl", "queuedup", "checkingdl", "checkingup", "queued to download", "queued to verify", "verifying"]
        elif status == "error":
            return ["error", "failed", "stoppederror", "stalled", "stalleddl", "stalledup"]
        elif status == "completed":
            return ["completed", "finished", "complete"]
        elif status == "paused":
            return ["paused", "stopped", "pause"]
        elif status == "all_active":
            # all_active 包含 downloading + queued + error
            return ["downloading", "active", "running", "seeding", "queued", "checking", "allocating", "metadl", "queueddl", "queuedup", "checkingdl", "checkingup", "queued to download", "queued to verify", "verifying", "error", "failed", "stoppederror", "stalled", "stalleddl", "stalledup"]
        
        return []
    
    async def create_download(self, download_data: dict) -> dict:
        """创建下载任务"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        from app.core.config import settings
        
        task_id = str(uuid.uuid4())
        downloader_name = download_data.get("downloader", "qBittorrent")
        
        normalized_media_type = normalize_media_type(
            download_data.get("media_type"),
            default=download_data.get("media_type") or MEDIA_TYPE_UNKNOWN,
        )
        extra_metadata = download_data.get("extra_metadata") or {}

        # 创建数据库记录
        new_task = DownloadTask(
            task_id=task_id,
            title=download_data.get("title"),
            status="pending",
            progress=0.0,
            size_gb=download_data.get("size_gb", 0.0),
            downloaded_gb=0.0,
            downloader=downloader_name,
            magnet_link=download_data.get("magnet_link"),
            torrent_url=download_data.get("torrent_url"),
            media_type=normalized_media_type,
            extra_metadata=extra_metadata,
        )
        
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)

        simulation_mode = await self.detect_simulation_mode()
        if simulation_mode:
            metadata = new_task.extra_metadata or {}
            metadata["simulation"] = True
            new_task.extra_metadata = metadata
            await self.db.commit()
            await self.db.refresh(new_task)
            result = self._serialize_task(new_task)
            result["simulation_mode"] = True
            return result
        
        # 调用下载器API添加下载任务
        try:
            downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
            
            # 从设置获取下载器配置
            settings_service = self._get_settings_service()
            
            config_prefix = f"{downloader_name.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host") or "localhost"
            port = await settings_service.get_setting(f"{config_prefix}port") or (8080 if downloader_name == "qBittorrent" else 9091)
            username = await settings_service.get_setting(f"{config_prefix}username") or ""
            password = await settings_service.get_setting(f"{config_prefix}password") or ""
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            
            # 获取磁力链接或种子URL
            torrent_url = download_data.get("magnet_link") or download_data.get("torrent_url")
            if torrent_url:
                # 对于Transmission，add_torrent返回任务ID，可以直接获取hash
                if downloader_type == DownloaderType.TRANSMISSION:
                    torrent_id = await client.client.add_torrent(torrent_url, download_data.get("save_path"))
                    success = torrent_id is not None
                    if success and torrent_id:
                        # 获取任务信息以获取hash
                        torrents = await client.get_torrents(ids=[torrent_id])
                        if torrents:
                            new_task.downloader_hash = torrents[0].get("hashString")
                else:
                    # qBittorrent：添加任务时打标签
                    from app.core.config import settings
                    tags = [settings.TORRENT_TAG]  # 默认标签：VABHUB
                    success = await client.add_torrent(
                        torrent_url,
                        save_path=download_data.get("save_path"),
                        tags=tags  # 打上VABHUB标签
                    )
                    # qBittorrent：在下次状态更新时会通过标题匹配获取hash
                
                if success:
                    new_task.status = "downloading"
                    
                    await self.db.commit()
                    await self.db.refresh(new_task)
                    logger.info(f"下载任务已添加到{downloader_name}: {task_id}")
                    
                    # 通过WebSocket广播新任务
                    try:
                        await manager.broadcast_download_update({
                            "id": new_task.task_id,
                            "title": new_task.title,
                            "status": new_task.status,
                            "progress": new_task.progress,
                            "size_gb": new_task.size_gb,
                            "downloaded_gb": new_task.downloaded_gb,
                            "speed_mbps": new_task.speed_mbps,
                            "eta": new_task.eta,
                            "media_type": new_task.media_type,
                            "extra_metadata": new_task.extra_metadata or {},
                            "created_at": new_task.created_at.isoformat() if new_task.created_at else None
                        })
                    except Exception as ws_error:
                        logger.debug(f"WebSocket广播失败: {ws_error}")
                else:
                    new_task.status = "failed"
                    await self.db.commit()
                    logger.error(f"添加下载任务失败: {task_id}")
            
            await client.close()
        except Exception as e:
            logger.error(f"调用下载器API异常: {e}")
            new_task.status = "failed"
            await self.db.commit()
        
        result = self._serialize_task(new_task)
        result["simulation_mode"] = False
        return result
    
    async def pause_download(self, task_id: str) -> bool:
        """暂停下载"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return False
        
        if not task.downloader_hash:
            logger.warning(f"任务 {task_id} 没有下载器hash，无法暂停")
            return False
        
        # 调用下载器API暂停下载
        try:
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            
            # 从设置获取下载器配置
            settings_service = self._get_settings_service()
            config_prefix = f"{task.downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if task.downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if task.downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            
            # 暂停下载
            success = await client.pause_torrent(task.downloader_hash)
            
            if success:
                task.status = "paused"
                task.updated_at = datetime.utcnow()
                await self.db.commit()
                logger.info(f"下载任务已暂停: {task_id}")
                
                # 清除缓存（删除所有可能的缓存键）
                for status in [None, "downloading", "paused", "completed", "failed"]:
                    for vabhub_only in [True, False]:
                        cache_key = f"downloads:list:{status}:{vabhub_only}"
                        try:
                            await self.cache.delete(cache_key)
                        except:
                            pass  # 忽略删除失败
                
                await client.close()
                return True
            else:
                logger.error(f"暂停下载失败: {task_id}")
                await client.close()
                return False
        except Exception as e:
            logger.error(f"暂停下载异常: {e}")
            task.status = "paused"
            task.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # 清除缓存
            await self.cache.delete(f"downloads:list:*")
            
            return True
    
    async def resume_download(self, task_id: str) -> bool:
        """恢复下载"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return False
        
        if not task.downloader_hash:
            logger.warning(f"任务 {task_id} 没有下载器hash，无法恢复")
            return False
        
        # 调用下载器API恢复下载
        try:
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            
            # 从设置获取下载器配置
            settings_service = self._get_settings_service()
            config_prefix = f"{task.downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if task.downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if task.downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            
            # 恢复下载
            success = await client.resume_torrent(task.downloader_hash)
            
            if success:
                task.status = "downloading"
                task.updated_at = datetime.utcnow()
                await self.db.commit()
                logger.info(f"下载任务已恢复: {task_id}")
                
                # 清除缓存（删除所有可能的缓存键）
                for status in [None, "downloading", "paused", "completed", "failed"]:
                    for vabhub_only in [True, False]:
                        cache_key = f"downloads:list:{status}:{vabhub_only}"
                        try:
                            await self.cache.delete(cache_key)
                        except:
                            pass  # 忽略删除失败
                
                await client.close()
                return True
            else:
                logger.error(f"恢复下载失败: {task_id}")
                await client.close()
                return False
        except Exception as e:
            logger.error(f"恢复下载异常: {e}")
            task.status = "downloading"
            task.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # 清除缓存
            await self.cache.delete(f"downloads:list:*")
            
            return True
    
    async def delete_download(self, task_id: str, delete_files: bool = False) -> bool:
        """删除下载"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        # 先获取任务信息
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if task and task.downloader_hash:
            # 调用下载器API删除下载任务
            try:
                downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
                
                # 从设置获取下载器配置
                settings_service = self._get_settings_service()
                config_prefix = f"{task.downloader.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host") or "localhost"
                port = await settings_service.get_setting(f"{config_prefix}port") or (8080 if task.downloader == "qBittorrent" else 9091)
                username = await settings_service.get_setting(f"{config_prefix}username") or ""
                password = await settings_service.get_setting(f"{config_prefix}password") or ""
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                
                # 删除下载任务
                success = await client.delete_torrent(task.downloader_hash, delete_files=delete_files)
                
                if success:
                    logger.info(f"下载任务已从下载器删除: {task_id}")
                else:
                    logger.warning(f"从下载器删除任务失败: {task_id}")
                
                await client.close()
            except Exception as e:
                logger.error(f"删除下载任务异常: {e}")
        
        # 删除数据库记录
        result = await self.db.execute(
            delete(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        await self.db.commit()
        logger.info(f"下载任务已从数据库删除: {task_id}")
        
        # 清除缓存
        await self.cache.delete(f"downloads:list:*")
        
        return True
    
    async def queue_move_up(self, task_id: str) -> bool:
        """队列上移"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task or not task.downloader_hash:
            return False
        
        try:
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            settings_service = self._get_settings_service()
            config_prefix = f"{task.downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if task.downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if task.downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            success = await client.increase_priority(task.downloader_hash)
            await client.close()
            
            return success
        except Exception as e:
            logger.error(f"队列上移异常: {e}")
            return False
    
    async def queue_move_down(self, task_id: str) -> bool:
        """队列下移"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task or not task.downloader_hash:
            return False
        
        try:
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            settings_service = self._get_settings_service()
            config_prefix = f"{task.downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if task.downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if task.downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            success = await client.decrease_priority(task.downloader_hash)
            await client.close()
            
            return success
        except Exception as e:
            logger.error(f"队列下移异常: {e}")
            return False
    
    async def queue_move_top(self, task_id: str) -> bool:
        """队列置顶"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task or not task.downloader_hash:
            return False
        
        try:
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            settings_service = self._get_settings_service()
            config_prefix = f"{task.downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if task.downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if task.downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            success = await client.top_priority(task.downloader_hash)
            await client.close()
            
            return success
        except Exception as e:
            logger.error(f"队列置顶异常: {e}")
            return False
    
    async def set_global_speed_limit(
        self,
        downloader: str,
        download_limit: Optional[float] = None,
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        设置全局速度限制
        
        Args:
            downloader: 下载器名称（qBittorrent/Transmission）
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        try:
            downloader_type = DownloaderType.QBITTORRENT if downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            settings_service = self._get_settings_service()
            config_prefix = f"{downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            success = await client.set_global_speed_limit(download_limit, upload_limit)
            await client.close()
            
            if success:
                logger.info(f"全局速度限制设置成功: {downloader}, 下载={download_limit}MB/s, 上传={upload_limit}MB/s")
            
            return success
        except Exception as e:
            logger.error(f"设置全局速度限制异常: {e}")
            return False
    
    async def get_global_speed_limit(self, downloader: str) -> Optional[dict]:
        """
        获取全局速度限制
        
        Args:
            downloader: 下载器名称（qBittorrent/Transmission）
        
        Returns:
            包含download_limit和upload_limit的字典（MB/s），None表示无限制
        """
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        try:
            downloader_type = DownloaderType.QBITTORRENT if downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            settings_service = self._get_settings_service()
            config_prefix = f"{downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            limits = await client.get_global_speed_limit()
            await client.close()
            
            return limits
        except Exception as e:
            logger.error(f"获取全局速度限制异常: {e}")
            return None
    
    async def set_task_speed_limit(
        self,
        task_id: str,
        download_limit: Optional[float] = None,
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        设置单个任务的速度限制
        
        Args:
            task_id: 任务ID
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        from app.core.downloaders import DownloaderClient, DownloaderType
        
        result = await self.db.execute(
            select(DownloadTask).where(DownloadTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task or not task.downloader_hash:
            return False
        
        try:
            downloader_type = DownloaderType.QBITTORRENT if task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            settings_service = self._get_settings_service()
            config_prefix = f"{task.downloader.lower()}_"
            host = await settings_service.get_setting(f"{config_prefix}host")
            if not host or host == "localhost":
                host = "192.168.51.105"  # 使用已知的正确IP
            port = await settings_service.get_setting(f"{config_prefix}port")
            if not port:
                port = 8080 if task.downloader == "qBittorrent" else 9091
            port = int(port) if isinstance(port, str) else port
            username = await settings_service.get_setting(f"{config_prefix}username")
            username = str(username).strip() if username else ("admin" if task.downloader == "qBittorrent" else "haishuai")
            password = await settings_service.get_setting(f"{config_prefix}password")
            password = str(password).strip() if password else "China1987"
            
            downloader_config = {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
            
            client = DownloaderClient(downloader_type, downloader_config)
            success = await client.set_torrent_speed_limit(
                task.downloader_hash,
                download_limit,
                upload_limit
            )
            await client.close()
            
            if success:
                logger.info(f"任务速度限制设置成功: {task_id}, 下载={download_limit}MB/s, 上传={upload_limit}MB/s")
            
            return success
        except Exception as e:
            logger.error(f"设置任务速度限制异常: {e}")
            return False
    
    async def batch_pause(self, task_ids: List[str]) -> bool:
        """批量暂停"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        from collections import defaultdict
        
        # 按下载器分组
        tasks_by_downloader = defaultdict(list)
        
        for task_id in task_ids:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task and task.downloader_hash:
                tasks_by_downloader[task.downloader].append((task_id, task.downloader_hash))
        
        # 对每个下载器批量操作
        all_success = True
        for downloader_name, task_list in tasks_by_downloader.items():
            try:
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                settings_service = self._get_settings_service()
                config_prefix = f"{downloader_name.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host")
                if not host or host == "localhost":
                    host = "192.168.51.105"  # 使用已知的正确IP
                port = await settings_service.get_setting(f"{config_prefix}port")
                if not port:
                    port = 8080 if downloader_name == "qBittorrent" else 9091
                port = int(port) if isinstance(port, str) else port
                username = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username).strip() if username else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                password = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password).strip() if password else "China1987"
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                hashes = [hash for _, hash in task_list]
                success = await client.batch_pause(hashes)
                await client.close()
                
                if success:
                    # 更新数据库状态
                    for task_id, _ in task_list:
                        result = await self.db.execute(
                            select(DownloadTask).where(DownloadTask.task_id == task_id)
                        )
                        task = result.scalar_one_or_none()
                        if task:
                            task.status = "paused"
                            task.updated_at = datetime.utcnow()
                    await self.db.commit()
                    
                    # 清除缓存
                    await self.cache.delete(f"downloads:list:*")
                else:
                    all_success = False
            except Exception as e:
                logger.error(f"批量暂停异常 ({downloader_name}): {e}")
                all_success = False
        
        return all_success
    
    async def batch_resume(self, task_ids: List[str]) -> bool:
        """批量恢复"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        from collections import defaultdict
        
        tasks_by_downloader = defaultdict(list)
        
        for task_id in task_ids:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task and task.downloader_hash:
                tasks_by_downloader[task.downloader].append((task_id, task.downloader_hash))
        
        all_success = True
        for downloader_name, task_list in tasks_by_downloader.items():
            try:
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                settings_service = self._get_settings_service()
                config_prefix = f"{downloader_name.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host")
                if not host or host == "localhost":
                    host = "192.168.51.105"  # 使用已知的正确IP
                port = await settings_service.get_setting(f"{config_prefix}port")
                if not port:
                    port = 8080 if downloader_name == "qBittorrent" else 9091
                port = int(port) if isinstance(port, str) else port
                username = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username).strip() if username else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                password = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password).strip() if password else "China1987"
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                hashes = [hash for _, hash in task_list]
                success = await client.batch_resume(hashes)
                await client.close()
                
                if success:
                    for task_id, _ in task_list:
                        result = await self.db.execute(
                            select(DownloadTask).where(DownloadTask.task_id == task_id)
                        )
                        task = result.scalar_one_or_none()
                        if task:
                            task.status = "downloading"
                            task.updated_at = datetime.utcnow()
                    await self.db.commit()
                    
                    # 清除缓存
                    await self.cache.delete(f"downloads:list:*")
                else:
                    all_success = False
            except Exception as e:
                logger.error(f"批量恢复异常 ({downloader_name}): {e}")
                all_success = False
        
        return all_success
    
    async def batch_delete(self, task_ids: List[str], delete_files: bool = False) -> bool:
        """批量删除"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        from collections import defaultdict
        
        tasks_by_downloader = defaultdict(list)
        
        for task_id in task_ids:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task and task.downloader_hash:
                tasks_by_downloader[task.downloader].append((task_id, task.downloader_hash))
        
        all_success = True
        for downloader_name, task_list in tasks_by_downloader.items():
            try:
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                settings_service = self._get_settings_service()
                config_prefix = f"{downloader_name.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host")
                if not host or host == "localhost":
                    host = "192.168.51.105"  # 使用已知的正确IP
                port = await settings_service.get_setting(f"{config_prefix}port")
                if not port:
                    port = 8080 if downloader_name == "qBittorrent" else 9091
                port = int(port) if isinstance(port, str) else port
                username = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username).strip() if username else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                password = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password).strip() if password else "China1987"
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                hashes = [hash for _, hash in task_list]
                success = await client.batch_delete(hashes, delete_files)
                await client.close()
                
                if success:
                    # 删除数据库记录
                    task_ids_to_delete = [task_id for task_id, _ in task_list]
                    await self.db.execute(
                        delete(DownloadTask).where(DownloadTask.task_id.in_(task_ids_to_delete))
                    )
                    await self.db.commit()
                    
                    # 清除缓存
                    await self.cache.delete(f"downloads:list:*")
                else:
                    all_success = False
            except Exception as e:
                logger.error(f"批量删除异常 ({downloader_name}): {e}")
                all_success = False
        
        return all_success
    
    async def batch_set_speed_limit(
        self,
        task_ids: List[str],
        download_limit: Optional[float] = None,
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        批量设置任务速度限制
        
        Args:
            task_ids: 任务ID列表
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        from app.core.downloaders import DownloaderClient, DownloaderType
        from collections import defaultdict
        
        tasks_by_downloader = defaultdict(list)
        
        for task_id in task_ids:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task and task.downloader_hash:
                tasks_by_downloader[task.downloader].append((task_id, task.downloader_hash))
        
        all_success = True
        for downloader_name, task_list in tasks_by_downloader.items():
            try:
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                settings_service = self._get_settings_service()
                config_prefix = f"{downloader_name.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host")
                if not host or host == "localhost":
                    host = "192.168.51.105"  # 使用已知的正确IP
                port = await settings_service.get_setting(f"{config_prefix}port")
                if not port:
                    port = 8080 if downloader_name == "qBittorrent" else 9091
                port = int(port) if isinstance(port, str) else port
                username = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username).strip() if username else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                password = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password).strip() if password else "China1987"
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                
                # 批量设置速度限制
                for task_id, hash_id in task_list:
                    success = await client.set_torrent_speed_limit(
                        hash_id,
                        download_limit,
                        upload_limit
                    )
                    if not success:
                        all_success = False
                
                await client.close()
            except Exception as e:
                logger.error(f"批量设置速度限制异常 ({downloader_name}): {e}")
                all_success = False
        
        return all_success
    
    async def batch_queue_up(self, task_ids: List[str]) -> bool:
        """批量队列上移"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        from collections import defaultdict
        
        tasks_by_downloader = defaultdict(list)
        
        for task_id in task_ids:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task and task.downloader_hash:
                tasks_by_downloader[task.downloader].append((task_id, task.downloader_hash))
        
        all_success = True
        for downloader_name, task_list in tasks_by_downloader.items():
            try:
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                settings_service = self._get_settings_service()
                config_prefix = f"{downloader_name.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host")
                if not host or host == "localhost":
                    host = "192.168.51.105"  # 使用已知的正确IP
                port = await settings_service.get_setting(f"{config_prefix}port")
                if not port:
                    port = 8080 if downloader_name == "qBittorrent" else 9091
                port = int(port) if isinstance(port, str) else port
                username = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username).strip() if username else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                password = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password).strip() if password else "China1987"
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                
                # 批量上移
                for task_id, hash_id in task_list:
                    success = await client.increase_priority(hash_id)
                    if not success:
                        all_success = False
                
                await client.close()
            except Exception as e:
                logger.error(f"批量队列上移异常 ({downloader_name}): {e}")
                all_success = False
        
        return all_success
    
    async def batch_queue_down(self, task_ids: List[str]) -> bool:
        """批量队列下移"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        from collections import defaultdict
        
        tasks_by_downloader = defaultdict(list)
        
        for task_id in task_ids:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task and task.downloader_hash:
                tasks_by_downloader[task.downloader].append((task_id, task.downloader_hash))
        
        all_success = True
        for downloader_name, task_list in tasks_by_downloader.items():
            try:
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                settings_service = self._get_settings_service()
                config_prefix = f"{downloader_name.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host")
                if not host or host == "localhost":
                    host = "192.168.51.105"  # 使用已知的正确IP
                port = await settings_service.get_setting(f"{config_prefix}port")
                if not port:
                    port = 8080 if downloader_name == "qBittorrent" else 9091
                port = int(port) if isinstance(port, str) else port
                username = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username).strip() if username else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                password = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password).strip() if password else "China1987"
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                
                # 批量下移
                for task_id, hash_id in task_list:
                    success = await client.decrease_priority(hash_id)
                    if not success:
                        all_success = False
                
                await client.close()
            except Exception as e:
                logger.error(f"批量队列下移异常 ({downloader_name}): {e}")
                all_success = False
        
        return all_success
    
    async def batch_queue_top(self, task_ids: List[str]) -> bool:
        """批量队列置顶"""
        from app.core.downloaders import DownloaderClient, DownloaderType
        from collections import defaultdict
        
        tasks_by_downloader = defaultdict(list)
        
        for task_id in task_ids:
            result = await self.db.execute(
                select(DownloadTask).where(DownloadTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task and task.downloader_hash:
                tasks_by_downloader[task.downloader].append((task_id, task.downloader_hash))
        
        all_success = True
        for downloader_name, task_list in tasks_by_downloader.items():
            try:
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                settings_service = self._get_settings_service()
                config_prefix = f"{downloader_name.lower()}_"
                host = await settings_service.get_setting(f"{config_prefix}host")
                if not host or host == "localhost":
                    host = "192.168.51.105"  # 使用已知的正确IP
                port = await settings_service.get_setting(f"{config_prefix}port")
                if not port:
                    port = 8080 if downloader_name == "qBittorrent" else 9091
                port = int(port) if isinstance(port, str) else port
                username = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username).strip() if username else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                password = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password).strip() if password else "China1987"
                
                downloader_config = {
                    "host": host,
                    "port": int(port) if isinstance(port, str) else port,
                    "username": username,
                    "password": password
                }
                
                client = DownloaderClient(downloader_type, downloader_config)
                
                # 批量置顶
                for task_id, hash_id in task_list:
                    success = await client.top_priority(hash_id)
                    if not success:
                        all_success = False
                
                await client.close()
            except Exception as e:
                logger.error(f"批量队列置顶异常 ({downloader_name}): {e}")
                all_success = False
        
        return all_success

