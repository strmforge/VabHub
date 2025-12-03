"""
仪表盘服务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional, Dict, List
import psutil
import platform
import os
import logging

try:
    from loguru import logger as loguru_logger  # type: ignore
except ImportError:  # pragma: no cover
    loguru_logger = logging.getLogger("app.modules.dashboard.service")

logger = getattr(loguru_logger, "bind", lambda **_: loguru_logger)(module="dashboard_service")

from app.models.media import Media, MediaFile
from app.models.download import DownloadTask
from app.models.subscription import Subscription
from app.models.tts_job import TTSJob
from app.models.plugin import Plugin
from app.models.user_novel_reading_progress import UserNovelReadingProgress
from app.models.user_audiobook_progress import UserAudiobookProgress
from app.models.manga_reading_progress import MangaReadingProgress
from app.services.reading_hub_service import get_reading_stats
from app.core.cache import get_cache


class DashboardService:
    """仪表盘服务"""
    
    def __init__(self, db: Optional[AsyncSession]):
        self.db = db
        self.cache = get_cache()  # 使用统一缓存系统
    
    async def get_dashboard_data(self) -> Dict:
        """获取仪表盘数据（带缓存）"""
        # 生成缓存键
        cache_key = self.cache.generate_key("dashboard_data")
        
        # 尝试从缓存获取（短期缓存，30秒）
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        system_stats = await self.get_system_stats()
        media_stats = await self.get_media_stats()
        download_stats = await self.get_download_stats()
        downloader_status = await self.get_downloader_status()
        music_stats = await self.get_music_stats()
        
        # 新增的统计功能
        tts_stats = await self.get_tts_stats()
        plugin_stats = await self.get_plugin_stats()
        reading_stats = await self.get_reading_stats()
        recent_events = await self.get_recent_events()
        
        result = {
            "system_stats": system_stats,
            "media_stats": media_stats,
            "download_stats": download_stats,
            "downloader_status": downloader_status,
            "music_stats": music_stats,
            "active_downloads": download_stats.get("active", 0),
            "active_subscriptions": await self.get_active_subscriptions_count(),
            # 新增字段
            "tts_stats": tts_stats,
            "plugin_stats": plugin_stats,
            "reading_stats": reading_stats,
            "recent_events": recent_events
        }
        
        # 缓存结果（30秒，仪表盘数据更新频繁）
        await self.cache.set(cache_key, result, ttl=30)
        
        return result
    
    async def get_system_stats(self) -> Dict:
        """获取系统统计"""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # 获取磁盘使用情况（Windows使用C:，Linux使用/）
            if platform.system() == "Windows":
                disk = psutil.disk_usage('C:')
            else:
                disk = psutil.disk_usage('/')
            
            network = psutil.net_io_counters()
            
            return {
                "cpu_usage": round(cpu_usage, 2),
                "memory_usage": round(memory.percent, 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "disk_usage": round(disk.percent, 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_sent": network.bytes_sent,
                "network_recv": network.bytes_recv
            }
        except Exception as e:
            # 如果psutil不可用，返回默认值
            return {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "memory_total_gb": 0.0,
                "memory_used_gb": 0.0,
                "disk_usage": 0.0,
                "disk_total_gb": 0.0,
                "disk_used_gb": 0.0,
                "disk_free_gb": 0.0,
                "network_sent": 0,
                "network_recv": 0
            }
    
    async def get_media_stats(self) -> Dict:
        """获取媒体统计"""
        if not self.db:
            return {
                "total_movies": 0,
                "total_tv_shows": 0,
                "total_anime": 0,
                "total_episodes": 0,
                "total_size_gb": 0.0,
                "by_quality": {}
            }
        
        try:
            # 统计电影数量
            movies_result = await self.db.execute(
                select(func.count(Media.id)).where(Media.media_type == "movie")
            )
            total_movies = movies_result.scalar() or 0
            
            # 统计电视剧数量
            tv_shows_result = await self.db.execute(
                select(func.count(Media.id)).where(Media.media_type == "tv")
            )
            total_tv_shows = tv_shows_result.scalar() or 0

            short_drama_result = await self.db.execute(
                select(func.count(Media.id)).where(Media.media_type == "short_drama")
            )
            total_short_drama = short_drama_result.scalar() or 0
            
            # 统计动漫数量
            anime_result = await self.db.execute(
                select(func.count(Media.id)).where(Media.media_type == "anime")
            )
            total_anime = anime_result.scalar() or 0
            
            # 统计总大小
            size_result = await self.db.execute(
                select(func.sum(MediaFile.file_size_gb))
            )
            total_size_gb = size_result.scalar() or 0.0
            
            # 按质量统计
            quality_result = await self.db.execute(
                select(MediaFile.quality, func.count(MediaFile.id))
                .group_by(MediaFile.quality)
            )
            by_quality = {row[0] or "unknown": row[1] for row in quality_result.all()}
            
            return {
                "total_movies": total_movies,
                "total_tv_shows": total_tv_shows,
                "total_short_drama": total_short_drama,
                "total_anime": total_anime,
                "total_episodes": 0,  # TODO: 实现剧集统计
                "total_size_gb": round(total_size_gb, 2),
                "by_quality": by_quality
            }
        except Exception as e:
            return {
                "total_movies": 0,
                "total_tv_shows": 0,
                "total_short_drama": 0,
                "total_anime": 0,
                "total_episodes": 0,
                "total_size_gb": 0.0,
                "by_quality": {}
            }
    
    async def get_download_stats(self) -> Dict:
        """获取下载统计"""
        if not self.db:
            return {
                "active": 0,
                "paused": 0,
                "completed": 0,
                "failed": 0,
                "total_speed_mbps": 0.0,
                "total_size_gb": 0.0,
                "downloaded_gb": 0.0
            }
        
        try:
            # 统计各状态下载数
            active_result = await self.db.execute(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == "downloading")
            )
            active = active_result.scalar() or 0
            
            paused_result = await self.db.execute(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == "paused")
            )
            paused = paused_result.scalar() or 0
            
            completed_result = await self.db.execute(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == "completed")
            )
            completed = completed_result.scalar() or 0
            
            failed_result = await self.db.execute(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == "failed")
            )
            failed = failed_result.scalar() or 0
            
            # 计算总速度（活跃下载）
            speed_result = await self.db.execute(
                select(func.sum(DownloadTask.speed_mbps))
                .where(DownloadTask.status == "downloading")
            )
            total_speed_mbps = speed_result.scalar() or 0.0
            
            # 计算总大小和已下载
            size_result = await self.db.execute(
                select(
                    func.sum(DownloadTask.size_gb),
                    func.sum(DownloadTask.downloaded_gb)
                )
            )
            size_data = size_result.first()
            total_size_gb = size_data[0] or 0.0 if size_data else 0.0
            downloaded_gb = size_data[1] or 0.0 if size_data else 0.0
            
            return {
                "active": active,
                "paused": paused,
                "completed": completed,
                "failed": failed,
                "total_speed_mbps": round(total_speed_mbps, 2),
                "total_size_gb": round(total_size_gb, 2),
                "downloaded_gb": round(downloaded_gb, 2)
            }
        except Exception as e:
            return {
                "active": 0,
                "paused": 0,
                "completed": 0,
                "failed": 0,
                "total_speed_mbps": 0.0,
                "total_size_gb": 0.0,
                "downloaded_gb": 0.0
            }
    
    async def get_active_subscriptions_count(self) -> int:
        """获取活跃订阅数量"""
        if not self.db:
            return 0
        
        try:
            result = await self.db.execute(
                select(func.count(Subscription.id)).where(Subscription.status == "active")
            )
            return result.scalar() or 0
        except Exception:
            return 0
    
    async def get_storage_stats(self) -> Dict:
        """获取存储统计"""
        system_stats = await self.get_system_stats()
        media_stats = await self.get_media_stats()
        
        return {
            "disk_usage": system_stats.get("disk_usage", 0),
            "disk_total_gb": system_stats.get("disk_total_gb", 0),
            "disk_used_gb": system_stats.get("disk_used_gb", 0),
            "disk_free_gb": system_stats.get("disk_free_gb", 0),
            "media_size_gb": media_stats.get("total_size_gb", 0)
        }
    
    async def get_downloader_status(self) -> Dict:
        """获取下载器状态"""
        try:
            from app.modules.settings.service import SettingsService
            
            if not self.db:
                return {
                    "qBittorrent": {"connected": False, "status": "unknown"},
                    "Transmission": {"connected": False, "status": "unknown"}
                }
            
            settings_service = SettingsService(self.db)
            
            # 检查qBittorrent
            qb_host = await settings_service.get_setting("qbittorrent_host", category="downloader")
            qb_port = await settings_service.get_setting("qbittorrent_port", category="downloader")
            qb_username = await settings_service.get_setting("qbittorrent_username", category="downloader")
            qb_password = await settings_service.get_setting("qbittorrent_password", category="downloader")
            
            qb_status = {"connected": False, "status": "unknown", "error": None}
            if qb_host and qb_port:
                try:
                    from app.core.downloaders.qbittorrent import QBittorrentClient
                    client = QBittorrentClient(
                        host=qb_host,
                        port=int(qb_port) if qb_port else 8080,
                        username=qb_username or "",
                        password=qb_password or ""
                    )
                    connected = await client.login()
                    if connected:
                        # 获取传输信息
                        try:
                            response = await client.session.get(f"{client.base_url}/api/v2/transfer/info")
                            if response.status_code == 200:
                                info = response.json()
                                qb_status = {
                                    "connected": True,
                                    "status": "online",
                                    "dl_info_speed": info.get("dl_info_speed", 0),  # 下载速度（bytes/s）
                                    "up_info_speed": info.get("up_info_speed", 0),  # 上传速度（bytes/s）
                                    "dl_info_data": info.get("dl_info_data", 0),  # 总下载量（bytes）
                                    "up_info_data": info.get("up_info_data", 0)  # 总上传量（bytes）
                                }
                            else:
                                qb_status = {"connected": True, "status": "online", "error": "无法获取传输信息"}
                        except Exception as e:
                            qb_status = {"connected": True, "status": "online", "error": str(e)}
                    else:
                        qb_status = {"connected": False, "status": "offline", "error": "登录失败"}
                except Exception as e:
                    qb_status = {"connected": False, "status": "error", "error": str(e)}
            
            # 检查Transmission
            tr_host = await settings_service.get_setting("transmission_host", category="downloader")
            tr_port = await settings_service.get_setting("transmission_port", category="downloader")
            tr_username = await settings_service.get_setting("transmission_username", category="downloader")
            tr_password = await settings_service.get_setting("transmission_password", category="downloader")
            
            tr_status = {"connected": False, "status": "unknown", "error": None}
            if tr_host and tr_port:
                try:
                    from app.core.downloaders.transmission import TransmissionClient
                    client = TransmissionClient(
                        host=tr_host,
                        port=int(tr_port) if tr_port else 9091,
                        username=tr_username or "",
                        password=tr_password or ""
                    )
                    # 尝试获取会话ID（测试连接）
                    session_id = await client._get_session_id()
                    if session_id:
                        # 尝试获取统计信息
                        try:
                            result = await client._request("session-stats")
                            if result:
                                tr_status = {
                                    "connected": True,
                                    "status": "online",
                                    "downloadSpeed": result.get("downloadSpeed", 0),  # 下载速度（bytes/s）
                                    "uploadSpeed": result.get("uploadSpeed", 0),  # 上传速度（bytes/s）
                                    "downloadedEver": result.get("downloadedEver", 0),  # 总下载量（bytes）
                                    "uploadedEver": result.get("uploadedEver", 0)  # 总上传量（bytes）
                                }
                            else:
                                tr_status = {"connected": True, "status": "online", "error": "无法获取统计信息"}
                        except Exception as e:
                            tr_status = {"connected": True, "status": "online", "error": str(e)}
                    else:
                        tr_status = {"connected": False, "status": "offline", "error": "无法获取会话ID"}
                except Exception as e:
                    tr_status = {"connected": False, "status": "error", "error": str(e)}
            
            return {
                "qBittorrent": qb_status,
                "Transmission": tr_status
            }
        except Exception as e:
            logger.error(f"获取下载器状态失败: {e}")
            return {
                "qBittorrent": {"connected": False, "status": "error", "error": str(e)},
                "Transmission": {"connected": False, "status": "error", "error": str(e)}
            }
    
    async def get_music_stats(self) -> Dict:
        """获取音乐统计"""
        if not self.db:
            return {
                "total_tracks": 0,
                "total_albums": 0,
                "total_artists": 0,
                "total_playlists": 0,
                "total_size_gb": 0.0
            }
        
        try:
            from app.models.music import MusicTrack, MusicPlaylist, MusicLibrary
            
            # 统计曲目数量
            tracks_result = await self.db.execute(select(func.count(MusicTrack.id)))
            total_tracks = tracks_result.scalar() or 0
            
            # 统计专辑数量（通过曲目去重）
            albums_result = await self.db.execute(
                select(func.count(func.distinct(MusicTrack.album)))
            )
            total_albums = albums_result.scalar() or 0
            
            # 统计艺术家数量（通过曲目去重）
            artists_result = await self.db.execute(
                select(func.count(func.distinct(MusicTrack.artist)))
            )
            total_artists = artists_result.scalar() or 0
            
            # 统计播放列表数量
            playlists_result = await self.db.execute(select(func.count(MusicPlaylist.id)))
            total_playlists = playlists_result.scalar() or 0
            
            # 统计总大小
            size_result = await self.db.execute(
                select(func.sum(MusicTrack.file_size_mb))
            )
            total_size_mb = size_result.scalar() or 0.0
            total_size_gb = total_size_mb / 1024.0  # 转换为GB
            
            return {
                "total_tracks": total_tracks,
                "total_albums": total_albums,
                "total_artists": total_artists,
                "total_playlists": total_playlists,
                "total_size_gb": round(total_size_gb, 2)
            }
        except Exception as e:
            logger.error(f"获取音乐统计失败: {e}")
            return {
                "total_tracks": 0,
                "total_albums": 0,
                "total_artists": 0,
                "total_playlists": 0,
                "total_size_gb": 0.0
            }
    
    async def get_system_resources_history(
        self,
        hours: int = 24,
        interval_minutes: int = 5
    ) -> Dict:
        """
        获取系统资源历史数据（用于图表）
        
        Args:
            hours: 查询最近N小时的数据
            interval_minutes: 数据点间隔（分钟）
        
        Returns:
            历史数据字典
        """
        try:
            # 这里可以从数据库或缓存中获取历史数据
            # 目前返回实时数据作为示例
            # TODO: 实现历史数据存储和查询
            
            current_stats = await self.get_system_stats()
            
            # 生成时间序列数据（模拟，实际应从数据库获取）
            from datetime import datetime, timedelta
            import random
            
            data_points = []
            now = datetime.utcnow()
            points_count = (hours * 60) // interval_minutes
            
            for i in range(points_count):
                timestamp = now - timedelta(minutes=interval_minutes * (points_count - i))
                # 模拟数据（实际应从历史记录中获取）
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "cpu_usage": max(0, min(100, current_stats.get("cpu_usage", 0) + random.uniform(-5, 5))),
                    "memory_usage": max(0, min(100, current_stats.get("memory_usage", 0) + random.uniform(-2, 2))),
                    "disk_usage": max(0, min(100, current_stats.get("disk_usage", 0) + random.uniform(-1, 1)))
                })
            
            return {
                "cpu": [{"timestamp": p["timestamp"], "value": p["cpu_usage"]} for p in data_points],
                "memory": [{"timestamp": p["timestamp"], "value": p["memory_usage"]} for p in data_points],
                "disk": [{"timestamp": p["timestamp"], "value": p["disk_usage"]} for p in data_points]
            }
        except Exception as e:
            logger.error(f"获取系统资源历史数据失败: {e}")
            return {
                "cpu": [],
                "memory": [],
                "disk": []
            }
    
    async def get_tts_stats(self) -> Dict:
        """获取TTS统计"""
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("tts_stats")
            
            # 尝试从缓存获取（30秒TTL）
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            if not self.db:
                return {
                    "pending_jobs": 0,
                    "running_jobs": 0,
                    "completed_last_24h": 0
                }
            
            # 计算24小时前的时间
            from datetime import datetime, timedelta
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            # 统计待处理任务
            pending_stmt = select(func.count(TTSJob.id)).where(TTSJob.status == "queued")
            pending_result = await self.db.execute(pending_stmt)
            pending_jobs = pending_result.scalar() or 0
            
            # 统计运行中任务
            running_stmt = select(func.count(TTSJob.id)).where(TTSJob.status == "running")
            running_result = await self.db.execute(running_stmt)
            running_jobs = running_result.scalar() or 0
            
            # 统计最近24小时完成的任务
            completed_stmt = select(func.count(TTSJob.id)).where(
                and_(
                    TTSJob.status.in_(["success", "partial"]),
                    TTSJob.finished_at >= twenty_four_hours_ago
                )
            )
            completed_result = await self.db.execute(completed_stmt)
            completed_last_24h = completed_result.scalar() or 0
            
            result = {
                "pending_jobs": pending_jobs,
                "running_jobs": running_jobs,
                "completed_last_24h": completed_last_24h
            }
            
            # 缓存结果（30秒）
            await self.cache.set(cache_key, result, ttl=30)
            
            return result
        except Exception as e:
            logger.error(f"获取TTS统计失败: {e}")
            return {
                "pending_jobs": 0,
                "running_jobs": 0,
                "completed_last_24h": 0
            }
    
    async def get_plugin_stats(self) -> Dict:
        """获取插件统计"""
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("plugin_stats")
            
            # 尝试从缓存获取（30秒TTL）
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            if not self.db:
                return {
                    "total_plugins": 0,
                    "active_plugins": 0,
                    "quarantined_plugins": 0
                }
            
            # 统计总插件数
            total_stmt = select(func.count(Plugin.id))
            total_result = await self.db.execute(total_stmt)
            total_plugins = total_result.scalar() or 0
            
            # 统计活跃插件数（ENABLED状态且未被隔离）
            active_stmt = select(func.count(Plugin.id)).where(
                and_(
                    Plugin.status == "ENABLED",
                    Plugin.is_quarantined.is_(False)
                )
            )
            active_result = await self.db.execute(active_stmt)
            active_plugins = active_result.scalar() or 0
            
            # 统计被隔离的插件数
            quarantined_stmt = select(func.count(Plugin.id)).where(Plugin.is_quarantined == True)
            quarantined_result = await self.db.execute(quarantined_stmt)
            quarantined_plugins = quarantined_result.scalar() or 0
            
            result = {
                "total_plugins": total_plugins,
                "active_plugins": active_plugins,
                "quarantined_plugins": quarantined_plugins
            }
            
            # 缓存结果（30秒）
            await self.cache.set(cache_key, result, ttl=30)
            
            return result
        except Exception as e:
            logger.error(f"获取插件统计失败: {e}")
            return {
                "total_plugins": 0,
                "active_plugins": 0,
                "quarantined_plugins": 0
            }
    
    async def get_reading_stats(self) -> Dict:
        """获取阅读统计（系统级）"""
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("reading_stats")
            
            # 尝试从缓存获取（30秒TTL）
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            if not self.db:
                return {
                    "active_novels": 0,
                    "active_audiobooks": 0,
                    "active_manga": 0
                }
            
            # 统计活跃小说数（未读完）
            novels_stmt = select(func.count(UserNovelReadingProgress.id)).where(
                UserNovelReadingProgress.is_finished == False
            )
            novels_result = await self.db.execute(novels_stmt)
            active_novels = novels_result.scalar() or 0
            
            # 统计活跃有声书数（未听完）
            audiobooks_stmt = select(func.count(UserAudiobookProgress.id)).where(
                UserAudiobookProgress.is_finished == False
            )
            audiobooks_result = await self.db.execute(audiobooks_stmt)
            active_audiobooks = audiobooks_result.scalar() or 0
            
            # 统计活跃漫画数（有阅读进度）
            manga_stmt = select(func.count(MangaReadingProgress.id))
            manga_result = await self.db.execute(manga_stmt)
            active_manga = manga_result.scalar() or 0
            
            result = {
                "active_novels": active_novels,
                "active_audiobooks": active_audiobooks,
                "active_manga": active_manga
            }
            
            # 缓存结果（30秒）
            await self.cache.set(cache_key, result, ttl=30)
            
            return result
        except Exception as e:
            logger.error(f"获取阅读统计失败: {e}")
            return {
                "active_novels": 0,
                "active_audiobooks": 0,
                "active_manga": 0
            }
    
    async def get_recent_events(self, limit: int = 20) -> List[Dict]:
        """获取最近活动事件"""
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key(f"recent_events_{limit}")
            
            # 尝试从缓存获取（10秒TTL，需要较实时）
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            if not self.db:
                return []
            
            events = []
            from datetime import datetime, timedelta
            
            # 1. 获取最近完成的下载任务
            download_stmt = select(
                DownloadTask.id,
                DownloadTask.title,
                DownloadTask.status,
                DownloadTask.completed_at,
                DownloadTask.media_type
            ).where(
                and_(
                    DownloadTask.status == "completed",
                    DownloadTask.completed_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(desc(DownloadTask.completed_at)).limit(limit)
            
            download_result = await self.db.execute(download_stmt)
            for row in download_result.all():
                events.append({
                    "type": "download_completed",
                    "title": f"下载完成: {row.title}",
                    "time": row.completed_at.isoformat() if row.completed_at else None,
                    "message": f"媒体类型: {row.media_type or 'unknown'}",
                    "media_type": row.media_type
                })
            
            # 2. 获取最近完成的TTS任务
            tts_stmt = select(
                TTSJob.id,
                TTSJob.status,
                TTSJob.finished_at,
                TTSJob.ebook_id
            ).where(
                and_(
                    TTSJob.status.in_(["success", "partial"]),
                    TTSJob.finished_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(desc(TTSJob.finished_at)).limit(limit)
            
            tts_result = await self.db.execute(tts_stmt)
            for row in tts_result.all():
                events.append({
                    "type": "tts_completed",
                    "title": f"TTS任务完成",
                    "time": row.finished_at.isoformat() if row.finished_at else None,
                    "message": f"电子书ID: {row.ebook_id}",
                    "ebook_id": row.ebook_id
                })
            
            # 3. 获取最近的插件错误事件
            plugin_error_stmt = select(
                Plugin.id,
                Plugin.name,
                Plugin.display_name,
                Plugin.last_error,
                Plugin.last_error_at
            ).where(
                and_(
                    Plugin.last_error.isnot(None),
                    Plugin.last_error_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(desc(Plugin.last_error_at)).limit(limit)
            
            plugin_result = await self.db.execute(plugin_error_stmt)
            for row in plugin_result.all():
                events.append({
                    "type": "plugin_error",
                    "title": f"插件错误: {row.display_name or row.name}",
                    "time": row.last_error_at.isoformat() if row.last_error_at else None,
                    "message": row.last_error[:100] + "..." if row.last_error and len(row.last_error) > 100 else row.last_error,
                    "plugin_name": row.name
                })
            
            # 按时间排序并限制数量
            events.sort(key=lambda x: x.get("time", ""), reverse=True)
            events = events[:limit]
            
            # 缓存结果（10秒）
            await self.cache.set(cache_key, events, ttl=10)
            
            return events
        except Exception as e:
            logger.error(f"获取最近活动失败: {e}")
            return []

