"""
媒体服务器基础客户端
定义所有媒体服务器客户端的通用接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class MediaLibrary:
    """媒体库"""
    id: str
    name: str
    type: str  # movie, tv, music, etc.
    path: str
    item_count: Optional[int] = None


@dataclass
class MediaItem:
    """媒体项"""
    id: str
    title: str
    type: str  # movie, episode, etc.
    year: Optional[int] = None
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    overview: Optional[str] = None
    rating: Optional[float] = None
    genres: Optional[List[str]] = None
    watched: bool = False
    watched_at: Optional[datetime] = None
    play_count: int = 0
    play_percentage: float = 0.0
    last_played: Optional[datetime] = None


@dataclass
class PlaybackInfo:
    """播放信息"""
    session_id: str
    item_id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    is_paused: bool = False
    is_playing: bool = False
    position_ticks: int = 0
    play_percentage: float = 0.0
    client_name: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None


@dataclass
class MediaServerConfig:
    """媒体服务器配置"""
    url: str
    api_key: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    user_id: Optional[str] = None
    timeout: int = 30


class MediaServerError(Exception):
    """媒体服务器错误"""
    pass


class BaseMediaServerClient(ABC):
    """媒体服务器基础客户端"""
    
    def __init__(self, config: MediaServerConfig):
        self.config = config
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接媒体服务器"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        pass
    
    @abstractmethod
    async def get_libraries(self) -> List[MediaLibrary]:
        """获取媒体库列表"""
        pass
    
    @abstractmethod
    async def get_library_items(
        self,
        library_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MediaItem]:
        """获取媒体库中的项目"""
        pass
    
    @abstractmethod
    async def get_item(self, item_id: str) -> Optional[MediaItem]:
        """获取媒体项详情"""
        pass
    
    @abstractmethod
    async def search_items(
        self,
        query: str,
        media_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MediaItem]:
        """搜索媒体项"""
        pass
    
    @abstractmethod
    async def get_recently_added(
        self,
        limit: int = 20,
        media_type: Optional[str] = None
    ) -> List[MediaItem]:
        """获取最近添加的媒体"""
        pass
    
    @abstractmethod
    async def get_playback_sessions(self) -> List[PlaybackInfo]:
        """获取当前播放会话"""
        pass
    
    @abstractmethod
    async def update_watched_status(
        self,
        item_id: str,
        watched: bool,
        play_percentage: float = 0.0
    ) -> bool:
        """更新观看状态"""
        pass
    
    @abstractmethod
    async def sync_libraries(self) -> Dict[str, Any]:
        """同步媒体库"""
        pass
    
    @abstractmethod
    async def sync_metadata(self, item_id: str) -> bool:
        """同步元数据"""
        pass
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

