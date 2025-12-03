"""
Jellyfin媒体服务器客户端
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


class JellyfinClient(BaseMediaServerClient):
    """Jellyfin媒体服务器客户端"""
    
    def __init__(self, config: MediaServerConfig):
        super().__init__(config)
        self.base_url = config.url.rstrip('/')
        self.api_key = config.api_key
        self.user_id = config.user_id
        self.client = None
    
    async def connect(self) -> bool:
        """连接Jellyfin服务器"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-Emby-Authorization": f"MediaBrowser Client=\"VabHub\", Device=\"Server\", DeviceId=\"VabHub\", Version=\"1.0.0\", Token=\"{self.api_key}\"",
                    "Content-Type": "application/json"
                },
                timeout=self.config.timeout
            )
            
            # 测试连接
            response = await self.client.get("/System/Info")
            if response.status_code == 200:
                self._connected = True
                logger.info(f"Jellyfin服务器连接成功: {self.base_url}")
                return True
            else:
                raise MediaServerError(f"连接失败: {response.status_code}")
        except Exception as e:
            logger.error(f"连接Jellyfin服务器失败: {e}")
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
            response = await self.client.get("/System/Info")
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data.get("ServerName", "Jellyfin"),
                    "version": data.get("Version", "Unknown"),
                    "platform": data.get("OperatingSystem", "Unknown")
                }
            else:
                raise MediaServerError(f"获取服务器信息失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Jellyfin服务器信息失败: {e}")
            raise MediaServerError(f"获取服务器信息失败: {str(e)}")
    
    async def get_libraries(self) -> List[MediaLibrary]:
        """获取媒体库列表"""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self.client.get("/Library/VirtualFolders")
            if response.status_code == 200:
                data = response.json()
                libraries = []
                for lib in data:
                    libraries.append(MediaLibrary(
                        id=lib.get("ItemId", ""),
                        name=lib.get("Name", ""),
                        type=lib.get("CollectionType", ""),
                        path=lib.get("Path", ""),
                        item_count=lib.get("ItemCount")
                    ))
                return libraries
            else:
                raise MediaServerError(f"获取媒体库失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Jellyfin媒体库失败: {e}")
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
            params = {
                "ParentId": library_id,
                "IncludeItemTypes": "Movie,Series,Episode"
            }
            if limit:
                params["Limit"] = limit
            if offset:
                params["StartIndex"] = offset
            
            response = await self.client.get("/Items", params=params)
            if response.status_code == 200:
                data = response.json()
                items = []
                for item_data in data.get("Items", []):
                    items.append(self._parse_item(item_data))
                return items
            else:
                raise MediaServerError(f"获取媒体库项目失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Jellyfin媒体库项目失败: {e}")
            raise MediaServerError(f"获取媒体库项目失败: {str(e)}")
    
    async def get_item(self, item_id: str) -> Optional[MediaItem]:
        """获取媒体项详情"""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self.client.get(f"/Users/{self.user_id}/Items/{item_id}")
            if response.status_code == 200:
                data = response.json()
                return self._parse_item(data)
            else:
                return None
        except Exception as e:
            logger.error(f"获取Jellyfin媒体项失败: {e}")
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
            params = {
                "SearchTerm": query,
                "IncludeItemTypes": "Movie,Series,Episode" if not media_type else media_type
            }
            if limit:
                params["Limit"] = limit
            
            response = await self.client.get("/Search/Hints", params=params)
            if response.status_code == 200:
                data = response.json()
                items = []
                for item_data in data.get("SearchHints", []):
                    # 需要获取完整项目信息
                    item = await self.get_item(item_data.get("Id", ""))
                    if item:
                        items.append(item)
                return items
            else:
                raise MediaServerError(f"搜索失败: {response.status_code}")
        except Exception as e:
            logger.error(f"Jellyfin搜索失败: {e}")
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
            params = {
                "UserId": self.user_id,
                "Limit": limit,
                "IncludeItemTypes": "Movie,Series,Episode" if not media_type else media_type,
                "SortBy": "DateCreated",
                "SortOrder": "Descending"
            }
            
            response = await self.client.get("/Users/{}/Items/Latest".format(self.user_id), params=params)
            if response.status_code == 200:
                data = response.json()
                items = []
                for item_data in data:
                    items.append(self._parse_item(item_data))
                return items
            else:
                raise MediaServerError(f"获取最近添加失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Jellyfin最近添加失败: {e}")
            raise MediaServerError(f"获取最近添加失败: {str(e)}")
    
    async def get_playback_sessions(self) -> List[PlaybackInfo]:
        """获取当前播放会话"""
        if not self._connected:
            await self.connect()
        
        try:
            response = await self.client.get("/Sessions")
            if response.status_code == 200:
                data = response.json()
                sessions = []
                for session_data in data:
                    sessions.append(self._parse_playback_session(session_data))
                return sessions
            else:
                raise MediaServerError(f"获取播放会话失败: {response.status_code}")
        except Exception as e:
            logger.error(f"获取Jellyfin播放会话失败: {e}")
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
                response = await self.client.post(
                    f"/Users/{self.user_id}/PlayedItems/{item_id}",
                    json={}
                )
            else:
                # 取消观看标记
                response = await self.client.delete(
                    f"/Users/{self.user_id}/PlayedItems/{item_id}"
                )
            
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"更新Jellyfin观看状态失败: {e}")
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
            logger.error(f"同步Jellyfin媒体库失败: {e}")
            raise MediaServerError(f"同步媒体库失败: {str(e)}")
    
    async def sync_metadata(self, item_id: str) -> bool:
        """同步元数据"""
        if not self._connected:
            await self.connect()
        
        try:
            item = await self.get_item(item_id)
            return item is not None
        except Exception as e:
            logger.error(f"同步Jellyfin元数据失败: {e}")
            return False
    
    def _parse_item(self, item_data: Dict[str, Any]) -> MediaItem:
        """解析媒体项数据"""
        # 解析观看状态
        user_data = item_data.get("UserData", {})
        watched = user_data.get("Played", False)
        play_count = user_data.get("PlayCount", 0)
        play_percentage = user_data.get("PlayedPercentage", 0.0)
        
        # 解析日期
        last_played = None
        if user_data.get("LastPlayedDate"):
            try:
                last_played = datetime.fromisoformat(user_data["LastPlayedDate"].replace("Z", "+00:00"))
            except:
                pass
        
        watched_at = None
        if user_data.get("PlayedDate"):
            try:
                watched_at = datetime.fromisoformat(user_data["PlayedDate"].replace("Z", "+00:00"))
            except:
                pass
        
        # 解析年份
        year = None
        if item_data.get("ProductionYear"):
            try:
                year = int(item_data["ProductionYear"])
            except:
                pass
        
        # 解析类型
        media_type = item_data.get("Type", "").lower()
        if media_type == "series":
            media_type = "tv_show"
        elif media_type == "movie":
            media_type = "movie"
        elif media_type == "episode":
            media_type = "episode"
        
        return MediaItem(
            id=item_data.get("Id", ""),
            title=item_data.get("Name", ""),
            type=media_type,
            year=year,
            tmdb_id=self._extract_provider_id(item_data, "Tmdb"),
            imdb_id=self._extract_provider_id(item_data, "Imdb"),
            poster_url=self._get_image_url(item_data.get("Id", ""), "Primary"),
            backdrop_url=self._get_image_url(item_data.get("Id", ""), "Backdrop"),
            overview=item_data.get("Overview"),
            rating=item_data.get("CommunityRating"),
            genres=item_data.get("Genres", []),
            watched=watched,
            watched_at=watched_at,
            play_count=play_count,
            play_percentage=play_percentage,
            last_played=last_played
        )
    
    def _parse_playback_session(self, session_data: Dict[str, Any]) -> PlaybackInfo:
        """解析播放会话数据"""
        now_playing_item = session_data.get("NowPlayingItem", {})
        
        return PlaybackInfo(
            session_id=session_data.get("Id", ""),
            item_id=now_playing_item.get("Id", ""),
            user_id=session_data.get("UserId", ""),
            user_name=session_data.get("UserName", ""),
            is_paused=session_data.get("PlayState", {}).get("IsPaused", False),
            is_playing=session_data.get("PlayState", {}).get("IsPlaying", False),
            position_ticks=session_data.get("PlayState", {}).get("PositionTicks", 0),
            play_percentage=session_data.get("PlayState", {}).get("PlayedPercentage", 0.0),
            client_name=session_data.get("Client", ""),
            device_name=session_data.get("DeviceName", ""),
            device_type=session_data.get("DeviceType", "")
        )
    
    def _extract_provider_id(self, item_data: Dict[str, Any], provider: str) -> Optional[str]:
        """提取提供商ID"""
        provider_ids = item_data.get("ProviderIds", {})
        return provider_ids.get(provider)
    
    def _get_image_url(self, item_id: str, image_type: str) -> Optional[str]:
        """获取图片URL"""
        if not item_id:
            return None
        return f"{self.base_url}/Items/{item_id}/Images/{image_type}"

