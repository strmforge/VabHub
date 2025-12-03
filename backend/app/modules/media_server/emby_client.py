"""
Emby媒体服务器客户端
Emby和Jellyfin API基本相同，可以复用大部分代码
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from .jellyfin_client import JellyfinClient
from .base_client import MediaServerConfig, MediaServerError


class EmbyClient(JellyfinClient):
    """Emby媒体服务器客户端（基于Jellyfin客户端）"""
    
    def __init__(self, config: MediaServerConfig):
        super().__init__(config)
        # Emby使用X-Emby-Authorization header，与Jellyfin相同
        # 但URL可能不同
    
    async def connect(self) -> bool:
        """连接Emby服务器"""
        try:
            # Emby的连接方式与Jellyfin相同
            result = await super().connect()
            if result:
                logger.info(f"Emby服务器连接成功: {self.base_url}")
            return result
        except Exception as e:
            logger.error(f"连接Emby服务器失败: {e}")
            raise MediaServerError(f"连接失败: {str(e)}")

