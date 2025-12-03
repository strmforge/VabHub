"""
做种管理服务
提供做种统计、做种管理、自动做种等功能
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from app.core.cache import get_cache

from app.models.download import DownloadTask
from app.core.downloaders import DownloaderClient, DownloaderType
from .statistics import SeedingStatistics


class SeedingService:
    """做种管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()
        self.statistics = SeedingStatistics(db)
    
    async def get_seeding_tasks(
        self,
        downloader: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取做种任务列表
        
        Args:
            downloader: 下载器名称（可选）
            status: 状态（可选）
            limit: 限制数量（可选）
            
        Returns:
            做种任务列表
        """
        try:
            # 从下载器获取做种任务
            seeding_tasks = []
            
            # 获取所有下载器配置
            from app.modules.settings.service import SettingsService
            settings_service = SettingsService(self.db)
            
            # 获取下载器列表
            downloaders = await self._get_downloaders(settings_service)
            
            # 并发获取所有下载器的做种任务
            import asyncio
            
            async def get_downloader_seeding_tasks(downloader_name: str, config: Dict) -> List[Dict]:
                try:
                    downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                    client = DownloaderClient(downloader_type, config)
                    
                    # 获取所有种子
                    torrents = await client.get_torrents()
                    
                    # 筛选做种中的种子
                    seeding_torrents = []
                    for torrent in torrents:
                        torrent_status = torrent.get("state", torrent.get("status", ""))
                        
                        # 判断是否为做种状态
                        is_seeding = False
                        if downloader_type == DownloaderType.QBITTORRENT:
                            # qBittorrent: uploading, stalledUP, queuedUP
                            is_seeding = torrent_status in ["uploading", "stalledUP", "queuedUP"]
                        else:
                            # Transmission: status == 6 (seeding) 或 status字段为6
                            status_value = torrent.get("status", torrent_status)
                            is_seeding = (isinstance(status_value, int) and status_value == 6) or \
                                       (isinstance(status_value, str) and "seeding" in status_value.lower()) or \
                                       (isinstance(torrent_status, str) and "seeding" in torrent_status.lower())
                        
                        if is_seeding:
                            seeding_torrents.append({
                                "hash": torrent.get("hash", torrent.get("hashString", "")),
                                "title": torrent.get("name", ""),
                                "downloader": downloader_name,
                                "size": torrent.get("total_size", torrent.get("size", 0)),
                                "uploaded": torrent.get("uploaded", torrent.get("uploadedEver", 0)),
                                "downloaded": torrent.get("downloaded", torrent.get("downloadedEver", 0)),
                                "ratio": torrent.get("ratio", torrent.get("uploadRatio", 0.0)),
                                "upload_speed": torrent.get("upspeed", torrent.get("rateUpload", 0)),
                                "download_speed": torrent.get("dlspeed", torrent.get("rateDownload", 0)),
                                "peers": torrent.get("num_leechs", torrent.get("peersGettingFromUs", 0)),
                                "seeds": torrent.get("num_seeds", torrent.get("seeders", 0)),
                                "added_date": torrent.get("added_on", torrent.get("addedDate", 0)),
                                "completion_date": torrent.get("completion_on", torrent.get("doneDate", 0)),
                                "status": "seeding"
                            })
                    
                    return seeding_torrents
                except Exception as e:
                    logger.error(f"获取{downloader_name}做种任务失败: {e}")
                    return []
            
            # 并发获取所有下载器的做种任务
            tasks = [get_downloader_seeding_tasks(name, config) for name, config in downloaders.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"获取做种任务异常: {result}")
                    continue
                if isinstance(result, list):
                    seeding_tasks.extend(result)
            
            # 过滤
            if downloader:
                seeding_tasks = [task for task in seeding_tasks if task.get("downloader") == downloader]
            if status:
                seeding_tasks = [task for task in seeding_tasks if task.get("status") == status]
            
            # 限制数量
            if limit:
                seeding_tasks = seeding_tasks[:limit]
            
            return seeding_tasks
            
        except Exception as e:
            logger.error(f"获取做种任务列表失败: {e}")
            return []
    
    async def get_seeding_statistics(
        self,
        downloader: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取做种统计信息
        
        Args:
            downloader: 下载器名称（可选）
            
        Returns:
            做种统计信息
        """
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("seeding_statistics", downloader=downloader or "all")
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 获取做种任务
            seeding_tasks = await self.get_seeding_tasks(downloader=downloader)
            
            # 计算统计信息
            statistics = {
                "total_tasks": len(seeding_tasks),
                "total_size": sum(task.get("size", 0) for task in seeding_tasks),
                "total_uploaded": sum(task.get("uploaded", 0) for task in seeding_tasks),
                "total_downloaded": sum(task.get("downloaded", 0) for task in seeding_tasks),
                "total_upload_speed": sum(task.get("upload_speed", 0) for task in seeding_tasks),
                "total_download_speed": sum(task.get("download_speed", 0) for task in seeding_tasks),
                "total_peers": sum(task.get("peers", 0) for task in seeding_tasks),
                "total_seeds": sum(task.get("seeds", 0) for task in seeding_tasks),
                "average_ratio": 0.0,
                "tasks_by_downloader": {}
            }
            
            # 计算平均分享率
            if seeding_tasks:
                total_ratio = sum(task.get("ratio", 0.0) for task in seeding_tasks)
                statistics["average_ratio"] = total_ratio / len(seeding_tasks)
            
            # 按下载器分组统计
            for task in seeding_tasks:
                downloader_name = task.get("downloader", "unknown")
                if downloader_name not in statistics["tasks_by_downloader"]:
                    statistics["tasks_by_downloader"][downloader_name] = {
                        "count": 0,
                        "total_size": 0,
                        "total_uploaded": 0,
                        "total_upload_speed": 0
                    }
                
                stats = statistics["tasks_by_downloader"][downloader_name]
                stats["count"] += 1
                stats["total_size"] += task.get("size", 0)
                stats["total_uploaded"] += task.get("uploaded", 0)
                stats["total_upload_speed"] += task.get("upload_speed", 0)
            
            # 缓存结果（5分钟）
            await self.cache.set(cache_key, statistics, ttl=300)
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取做种统计信息失败: {e}")
            return {
                "total_tasks": 0,
                "total_size": 0,
                "total_uploaded": 0,
                "total_downloaded": 0,
                "total_upload_speed": 0,
                "total_download_speed": 0,
                "total_peers": 0,
                "total_seeds": 0,
                "average_ratio": 0.0,
                "tasks_by_downloader": {}
            }
    
    async def get_seeding_history(
        self,
        downloader: Optional[str] = None,
        days: int = 7,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取做种历史记录
        
        Args:
            downloader: 下载器名称（可选）
            days: 查询天数（默认7天）
            limit: 限制数量（可选）
            
        Returns:
            做种历史记录列表
        """
        try:
            # 从数据库获取下载任务历史
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(DownloadTask).where(
                DownloadTask.status == "completed",
                DownloadTask.completed_at >= cutoff_date
            )
            
            if downloader:
                query = query.where(DownloadTask.downloader == downloader)
            
            query = query.order_by(DownloadTask.completed_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            # 格式化历史记录
            history = []
            for task in tasks:
                history.append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "downloader": task.downloader,
                    "size_gb": task.size_gb,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "status": "completed"
                })
            
            return history
            
        except Exception as e:
            logger.error(f"获取做种历史记录失败: {e}")
            return []
    
    async def pause_seeding(
        self,
        downloader: str,
        torrent_hash: str
    ) -> bool:
        """
        暂停做种
        
        Args:
            downloader: 下载器名称
            torrent_hash: 种子哈希
            
        Returns:
            是否成功
        """
        try:
            # 获取下载器配置
            from app.modules.settings.service import SettingsService
            settings_service = SettingsService(self.db)
            downloaders = await self._get_downloaders(settings_service)
            
            if downloader not in downloaders:
                logger.error(f"下载器 {downloader} 配置未找到")
                return False
            
            # 创建下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloaders[downloader])
            
            # 暂停种子
            # Transmission需要数字ID，qBittorrent使用hash
            if downloader_type == DownloaderType.TRANSMISSION:
                # 尝试将hash转换为ID（简化处理，实际应该查询）
                try:
                    torrent_id = int(torrent_hash)
                except ValueError:
                    # 如果不是数字，需要查询
                    torrents = await client.get_torrents()
                    torrent_id = None
                    for t in torrents:
                        if t.get("hashString") == torrent_hash:
                            torrent_id = t.get("id")
                            break
                    if not torrent_id:
                        logger.error(f"Transmission种子ID未找到: {torrent_hash}")
                        return False
                success = await client.pause_torrent(str(torrent_id))
            else:
                success = await client.pause_torrent(torrent_hash)
            
            if success:
                logger.info(f"暂停做种成功: {torrent_hash} ({downloader})")
            else:
                logger.error(f"暂停做种失败: {torrent_hash} ({downloader})")
            
            return success
            
        except Exception as e:
            logger.error(f"暂停做种失败: {e}")
            return False
    
    async def resume_seeding(
        self,
        downloader: str,
        torrent_hash: str
    ) -> bool:
        """
        恢复做种
        
        Args:
            downloader: 下载器名称
            torrent_hash: 种子哈希
            
        Returns:
            是否成功
        """
        try:
            # 获取下载器配置
            from app.modules.settings.service import SettingsService
            settings_service = SettingsService(self.db)
            downloaders = await self._get_downloaders(settings_service)
            
            if downloader not in downloaders:
                logger.error(f"下载器 {downloader} 配置未找到")
                return False
            
            # 创建下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloaders[downloader])
            
            # 恢复种子
            # Transmission需要数字ID，qBittorrent使用hash
            if downloader_type == DownloaderType.TRANSMISSION:
                # 尝试将hash转换为ID（简化处理，实际应该查询）
                try:
                    torrent_id = int(torrent_hash)
                except ValueError:
                    # 如果不是数字，需要查询
                    torrents = await client.get_torrents()
                    torrent_id = None
                    for t in torrents:
                        if t.get("hashString") == torrent_hash:
                            torrent_id = t.get("id")
                            break
                    if not torrent_id:
                        logger.error(f"Transmission种子ID未找到: {torrent_hash}")
                        return False
                success = await client.resume_torrent(str(torrent_id))
            else:
                success = await client.resume_torrent(torrent_hash)
            
            if success:
                logger.info(f"恢复做种成功: {torrent_hash} ({downloader})")
            else:
                logger.error(f"恢复做种失败: {torrent_hash} ({downloader})")
            
            return success
            
        except Exception as e:
            logger.error(f"恢复做种失败: {e}")
            return False
    
    async def delete_seeding(
        self,
        downloader: str,
        torrent_hash: str,
        delete_files: bool = False
    ) -> bool:
        """
        删除做种任务
        
        Args:
            downloader: 下载器名称
            torrent_hash: 种子哈希
            delete_files: 是否删除文件
            
        Returns:
            是否成功
        """
        try:
            # 获取下载器配置
            from app.modules.settings.service import SettingsService
            settings_service = SettingsService(self.db)
            downloaders = await self._get_downloaders(settings_service)
            
            if downloader not in downloaders:
                logger.error(f"下载器 {downloader} 配置未找到")
                return False
            
            # 创建下载器客户端
            downloader_type = DownloaderType.QBITTORRENT if downloader == "qBittorrent" else DownloaderType.TRANSMISSION
            client = DownloaderClient(downloader_type, downloaders[downloader])
            
            # 删除种子
            # Transmission需要数字ID，qBittorrent使用hash
            if downloader_type == DownloaderType.TRANSMISSION:
                # 尝试将hash转换为ID（简化处理，实际应该查询）
                try:
                    torrent_id = int(torrent_hash)
                except ValueError:
                    # 如果不是数字，需要查询
                    torrents = await client.get_torrents()
                    torrent_id = None
                    for t in torrents:
                        if t.get("hashString") == torrent_hash:
                            torrent_id = t.get("id")
                            break
                    if not torrent_id:
                        logger.error(f"Transmission种子ID未找到: {torrent_hash}")
                        return False
                success = await client.delete_torrent(str(torrent_id), delete_files=delete_files)
            else:
                success = await client.delete_torrent(torrent_hash, delete_files=delete_files)
            
            if success:
                logger.info(f"删除做种任务成功: {torrent_hash} ({downloader})")
            else:
                logger.error(f"删除做种任务失败: {torrent_hash} ({downloader})")
            
            return success
            
        except Exception as e:
            logger.error(f"删除做种任务失败: {e}")
            return False
    
    async def _get_downloaders(self, settings_service) -> Dict[str, Dict]:
        """获取所有下载器配置"""
        try:
            downloaders = {}
            
            # 获取qBittorrent配置
            try:
                qb_host = await settings_service.get_setting("qbittorrent_host")
                qb_port = await settings_service.get_setting("qbittorrent_port")
                qb_username = await settings_service.get_setting("qbittorrent_username")
                qb_password = await settings_service.get_setting("qbittorrent_password")
                
                if qb_host and qb_port:
                    downloaders["qBittorrent"] = {
                        "host": qb_host,
                        "port": int(qb_port) if isinstance(qb_port, str) else qb_port,
                        "username": qb_username or "",
                        "password": qb_password or ""
                    }
            except Exception as e:
                logger.debug(f"获取qBittorrent配置失败: {e}")
            
            # 获取Transmission配置
            try:
                tr_host = await settings_service.get_setting("transmission_host")
                tr_port = await settings_service.get_setting("transmission_port")
                tr_username = await settings_service.get_setting("transmission_username")
                tr_password = await settings_service.get_setting("transmission_password")
                
                if tr_host and tr_port:
                    downloaders["Transmission"] = {
                        "host": tr_host,
                        "port": int(tr_port) if isinstance(tr_port, str) else tr_port,
                        "username": tr_username or "",
                        "password": tr_password or ""
                    }
            except Exception as e:
                logger.debug(f"获取Transmission配置失败: {e}")
            
            return downloaders
            
        except Exception as e:
            logger.error(f"获取下载器配置失败: {e}")
            return {}

