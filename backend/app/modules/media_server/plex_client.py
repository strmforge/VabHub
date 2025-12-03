"""
Plex媒体服务器客户端
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .base_client import (
    BaseMediaServerClient,
    MediaServerConfig,
    MediaLibrary,
    MediaItem,
    PlaybackInfo,
    MediaServerError
)


class PlexClient(BaseMediaServerClient):
    """Plex媒体服务器客户端"""
    
    def __init__(self, config: MediaServerConfig):
        super().__init__(config)
        self.base_url = config.url.rstrip('/')
        self.token = config.token
        self.client = None
    
    async def connect(self) -> bool:
        """连接Plex服务器"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-Plex-Token": self.token,
                    "Accept": "application/json"
                },
                timeout=self.config.timeout
            )
            
            # 测试连接
            response = await self.client.get("/")
            if response.status_code == 200:
                self._connected = True
                logger.info(f"Plex服务器连接成功: {self.base_url}")
                return True
            else:
                raise MediaServerError(f"连接失败: {response.status_code}")
        except Exception as e:
            logger.error(f"连接Plex服务器失败: {e}")
            self._connected = False
            raise MediaServerError(f"连接失败: {str(e)}")
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._connected = False
    
    async def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self.client.get("/")
            if response.status_code == 200:
                # Plex返回XML，需要解析
                # 这里简化处理，实际应该解析XML
                return {
                    "name": "Plex Media Server",
                    "version": "Unknown",
                    "platform": "Unknown"
                }
            else:
                raise MediaServerError(f"获取服务器信息失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Plex服务器信息失败: {e}")
            raise MediaServerError(f"获取服务器信息失败: {str(e)}")
    
    async def get_libraries(self) -> List[MediaLibrary]:
        """获取媒体库列表"""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self.client.get("/library/sections")
            if response.status_code == 200:
                # Plex返回XML，需要解析
                # 这里简化处理，实际应该解析XML
                libraries = []
                # TODO: 解析XML响应
                return libraries
            else:
                raise MediaServerError(f"获取媒体库失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Plex媒体库失败: {e}")
            raise MediaServerError(f"获取媒体库失败: {str(e)}")
    
    async def get_library_items(
        self,
        library_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MediaItem]:
        """获取媒体库中的项目"""
        if not self._connected:
            await self.connect()
        
        try:
            params = {}
            if limit:
                params["X-Plex-Container-Size"] = str(limit)
            if offset:
                params["X-Plex-Container-Start"] = str(offset)
            
            response = await self.client.get(f"/library/sections/{library_id}/all", params=params)
            if response.status_code == 200:
                # Plex返回XML，需要解析
                items = []
                # TODO: 解析XML响应
                return items
            else:
                raise MediaServerError(f"获取媒体库项目失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Plex媒体库项目失败: {e}")
            raise MediaServerError(f"获取媒体库项目失败: {str(e)}")
    
    async def get_item(self, item_id: str) -> Optional[MediaItem]:
        """获取媒体项详情"""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self.client.get(f"/library/metadata/{item_id}")
            if response.status_code == 200:
                # Plex返回XML，需要解析
                # TODO: 解析XML响应并转换为MediaItem
                return None
            else:
                return None
        except Exception as e:
            logger.error(f"获取Plex媒体项失败: {e}")
            return None
    
    async def search_items(
        self,
        query: str,
        media_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MediaItem]:
        """搜索媒体项"""
        if not self._connected:
            await self.connect()
        
        try:
            params = {"query": query}
            if media_type:
                params["type"] = media_type
            if limit:
                params["limit"] = str(limit)
            
            response = await self.client.get("/search", params=params)
            if response.status_code == 200:
                # Plex返回XML，需要解析
                items = []
                # TODO: 解析XML响应
                return items
            else:
                raise MediaServerError(f"搜索失败: {response.status_code}")
        except Exception as e:
            logger.error(f"Plex搜索失败: {e}")
            raise MediaServerError(f"搜索失败: {str(e)}")
    
    async def get_recently_added(
        self,
        limit: int = 20,
        media_type: Optional[str] = None
    ) -> List[MediaItem]:
        """获取最近添加的媒体"""
        if not self._connected:
            await self.connect()
        
        try:
            libraries = await self.get_libraries()
            items = []
            
            for library in libraries:
                if media_type and library.type != media_type:
                    continue
                
                response = await self.client.get(
                    f"/library/sections/{library.id}/recentlyAdded",
                    params={"X-Plex-Container-Size": str(limit)}
                )
                if response.status_code == 200:
                    # Plex返回XML，需要解析
                    # TODO: 解析XML响应
                    pass
            
            return items
        except Exception as e:
            logger.error(f"获取Plex最近添加失败: {e}")
            raise MediaServerError(f"获取最近添加失败: {str(e)}")
    
    async def get_playback_sessions(self) -> List[PlaybackInfo]:
        """获取当前播放会话"""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self.client.get("/status/sessions")
            if response.status_code == 200:
                # Plex返回XML，需要解析
                sessions = []
                # TODO: 解析XML响应
                return sessions
            else:
                raise MediaServerError(f"获取播放会话失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Plex播放会话失败: {e}")
            raise MediaServerError(f"获取播放会话失败: {str(e)}")
    
    async def update_watched_status(
        self,
        item_id: str,
        watched: bool,
        play_percentage: float = 0.0
    ) -> bool:
        """更新观看状态"""
        if not self._connected:
            await self.connect()
        
        try:
            if watched:
                # 标记为已观看
                response = await self.client.put(f"/:/scrobble", params={"key": item_id})
            else:
                # 取消观看标记
                response = await self.client.put(f"/:/unscrobble", params={"key": item_id})
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"更新Plex观看状态失败: {e}")
            return False
    
    async def sync_libraries(self) -> Dict[str, Any]:
        """同步媒体库"""
        if not self._connected:
            await self.connect()
        
        try:
            libraries = await self.get_libraries()
            return {
                "libraries": [lib.__dict__ for lib in libraries],
                "count": len(libraries)
            }
        except Exception as e:
            logger.error(f"同步Plex媒体库失败: {e}")
            raise MediaServerError(f"同步媒体库失败: {str(e)}")
    
    async def sync_metadata(self, item_id: str) -> bool:
        """同步元数据"""
        if not self._connected:
            await self.connect()
        
        try:
            item = await self.get_item(item_id)
            return item is not None
        except Exception as e:
            logger.error(f"同步Plex元数据失败: {e}")
            return False

