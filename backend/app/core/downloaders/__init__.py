"""
下载器客户端统一接口
"""
from typing import Optional, Dict, List
from enum import Enum
from loguru import logger


class DownloaderType(str, Enum):
    """下载器类型"""
    QBITTORRENT = "qBittorrent"
    TRANSMISSION = "Transmission"


class DownloaderClient:
    """下载器客户端统一接口"""
    
    def __init__(self, downloader_type: DownloaderType, config: Dict):
        self.downloader_type = downloader_type
        self.config = config
        self.client = None
        
        if downloader_type == DownloaderType.QBITTORRENT:
            from .qbittorrent import QBittorrentClient
            self.client = QBittorrentClient(
                host=config.get("host", "localhost"),
                port=config.get("port", 8080),
                username=config.get("username", ""),
                password=config.get("password", "")
            )
        elif downloader_type == DownloaderType.TRANSMISSION:
            from .transmission import TransmissionClient
            self.client = TransmissionClient(
                host=config.get("host", "localhost"),
                port=config.get("port", 9091),
                username=config.get("username", ""),
                password=config.get("password", ""),
                rpc_path=config.get("rpc_path", "/transmission/rpc")
            )
    
    async def add_torrent(
        self, 
        torrent: str, 
        save_path: Optional[str] = None, 
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> bool:
        """添加种子或磁力链接"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.add_torrent(
                torrent, 
                save_path, 
                category=kwargs.get("category"),
                tags=tags
            )
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            # Transmission在添加任务后需要单独设置标签
            result = await self.client.add_torrent(torrent, save_path)
            if result is not None and tags:
                # 设置标签
                if isinstance(result, int):
                    await self.client.set_torrent_labels([result], tags)
            return result is not None
        return False
    
    async def get_torrents(
        self, 
        status_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict]:
        """获取种子列表"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.get_torrents(status_filter=status_filter, tags=tags)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            torrents = await self.client.get_torrents(kwargs.get("ids"))
            if tags:
                # 根据标签过滤
                filtered = []
                for torrent in torrents:
                    torrent_labels = torrent.get("labels", [])
                    if isinstance(torrent_labels, str):
                        torrent_labels = [label.strip() for label in torrent_labels.split(",") if label.strip()]
                    
                    # 检查是否包含任一标签
                    if any(tag in torrent_labels for tag in tags):
                        filtered.append(torrent)
                return filtered
            return torrents
        return []
    
    async def get_completed_torrents(self, tags: Optional[List[str]] = None) -> List[Dict]:
        """获取已完成的种子"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.get_completed_torrents(tags=tags)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            # TODO: 实现Transmission已完成任务查询（带标签过滤）
            return await self.get_torrents(tags=tags)
        return []
    
    async def get_downloading_torrents(self, tags: Optional[List[str]] = None) -> List[Dict]:
        """获取正在下载的种子"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.get_downloading_torrents(tags=tags)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            # TODO: 实现Transmission下载中任务查询（带标签过滤）
            return await self.get_torrents(tags=tags)
        return []
    
    async def get_torrent_info(self, torrent_id: str) -> Optional[Dict]:
        """获取单个种子详细信息"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            if hasattr(self.client, 'get_torrent_properties'):
                return await self.client.get_torrent_properties(torrent_id)
            else:
                # 如果没有get_torrent_properties方法，从列表中查找
                torrents = await self.client.get_torrents()
                for torrent in torrents:
                    if torrent.get("hash") == torrent_id:
                        return torrent
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            # Transmission的torrent_id可能是hash字符串，需要通过hashString匹配
            # 先尝试作为ID（整数）处理
            try:
                torrent_id_int = int(torrent_id)
                torrents = await self.client.get_torrents([torrent_id_int])
                if torrents:
                    return torrents[0]
            except ValueError:
                # 如果不是整数，说明是hash字符串，需要从所有任务中查找
                torrents = await self.client.get_torrents()
                for torrent in torrents:
                    if torrent.get("hashString") == torrent_id:
                        return torrent
        return None
    
    async def pause_torrent(self, torrent_id: str) -> bool:
        """暂停种子"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.pause_torrent(torrent_id)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            return await self.client.pause_torrent([int(torrent_id)])
        return False
    
    async def resume_torrent(self, torrent_id: str) -> bool:
        """恢复种子"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.resume_torrent(torrent_id)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            return await self.client.resume_torrent([int(torrent_id)])
        return False
    
    async def delete_torrent(self, torrent_id: str, delete_files: bool = False) -> bool:
        """删除种子"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.delete_torrent(torrent_id, delete_files)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            return await self.client.remove_torrent([int(torrent_id)], delete_files)
        return False
    
    async def set_torrent_tags(self, torrent_id: str, tags: List[str]) -> bool:
        """设置种子标签"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.set_torrent_tags(torrent_id, tags)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            return await self.client.set_torrent_labels([int(torrent_id)], tags)
        return False
    
    async def remove_torrent_tags(self, torrent_id: str, tags: List[str]) -> bool:
        """移除种子标签"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.remove_torrent_tags(torrent_id, tags)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            return await self.client.remove_torrent_labels([int(torrent_id)], tags)
        return False
    
    async def increase_priority(self, torrent_id: str) -> bool:
        """提高队列优先级（上移）"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.increase_priority(torrent_id)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            # Transmission需要先获取ID
            torrent_info = await self.get_torrent_info(torrent_id)
            if torrent_info and "id" in torrent_info:
                return await self.client.queue_move_up([torrent_info["id"]])
        return False
    
    async def decrease_priority(self, torrent_id: str) -> bool:
        """降低队列优先级（下移）"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.decrease_priority(torrent_id)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            torrent_info = await self.get_torrent_info(torrent_id)
            if torrent_info and "id" in torrent_info:
                return await self.client.queue_move_down([torrent_info["id"]])
        return False
    
    async def top_priority(self, torrent_id: str) -> bool:
        """置顶（最高优先级）"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.top_priority(torrent_id)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            torrent_info = await self.get_torrent_info(torrent_id)
            if torrent_info and "id" in torrent_info:
                return await self.client.queue_move_top([torrent_info["id"]])
        return False
    
    async def bottom_priority(self, torrent_id: str) -> bool:
        """置底（最低优先级）"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.bottom_priority(torrent_id)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            torrent_info = await self.get_torrent_info(torrent_id)
            if torrent_info and "id" in torrent_info:
                return await self.client.queue_move_bottom([torrent_info["id"]])
        return False
    
    async def batch_pause(self, torrent_ids: List[str]) -> bool:
        """批量暂停"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.batch_pause(torrent_ids)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            # 需要将hash转换为ID
            ids = []
            for torrent_id in torrent_ids:
                torrent_info = await self.get_torrent_info(torrent_id)
                if torrent_info and "id" in torrent_info:
                    ids.append(torrent_info["id"])
            if ids:
                return await self.client.batch_pause(ids)
        return False
    
    async def batch_resume(self, torrent_ids: List[str]) -> bool:
        """批量恢复"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.batch_resume(torrent_ids)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            ids = []
            for torrent_id in torrent_ids:
                torrent_info = await self.get_torrent_info(torrent_id)
                if torrent_info and "id" in torrent_info:
                    ids.append(torrent_info["id"])
            if ids:
                return await self.client.batch_resume(ids)
        return False
    
    async def batch_delete(self, torrent_ids: List[str], delete_files: bool = False) -> bool:
        """批量删除"""
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.batch_delete(torrent_ids, delete_files)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            ids = []
            for torrent_id in torrent_ids:
                torrent_info = await self.get_torrent_info(torrent_id)
                if torrent_info and "id" in torrent_info:
                    ids.append(torrent_info["id"])
            if ids:
                return await self.client.batch_delete(ids, delete_files)
        return False
    
    async def set_global_speed_limit(
        self, 
        download_limit: Optional[float] = None, 
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        设置全局速度限制
        
        Args:
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.set_global_speed_limit(download_limit, upload_limit)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            return await self.client.set_global_speed_limit(download_limit, upload_limit)
        return False
    
    async def get_global_speed_limit(self) -> Optional[Dict[str, float]]:
        """
        获取全局速度限制
        
        Returns:
            包含download_limit和upload_limit的字典（MB/s），None表示无限制
        """
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.get_global_speed_limit()
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            return await self.client.get_global_speed_limit()
        return None
    
    async def set_torrent_speed_limit(
        self, 
        torrent_id: str, 
        download_limit: Optional[float] = None, 
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        设置单个种子的速度限制
        
        Args:
            torrent_id: 种子ID（qBittorrent使用hash，Transmission使用数字ID）
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        if self.downloader_type == DownloaderType.QBITTORRENT:
            return await self.client.set_torrent_speed_limit(torrent_id, download_limit, upload_limit)
        elif self.downloader_type == DownloaderType.TRANSMISSION:
            # Transmission需要数字ID
            try:
                torrent_id_int = int(torrent_id)
                return await self.client.set_torrent_speed_limit(torrent_id_int, download_limit, upload_limit)
            except ValueError:
                logger.error(f"Transmission种子ID必须是数字: {torrent_id}")
                return False
        return False
    
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.close()

