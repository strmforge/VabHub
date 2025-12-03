"""
媒体服务器服务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.models.media_server import MediaServer, MediaServerSyncHistory, MediaServerItem, MediaServerPlaybackSession
from app.modules.media_server.base_client import MediaServerConfig, MediaServerError
from app.modules.media_server.plex_client import PlexClient
from app.modules.media_server.jellyfin_client import JellyfinClient
from app.modules.media_server.emby_client import EmbyClient


class MediaServerService:
    """媒体服务器服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._clients: Dict[int, Any] = {}  # 缓存客户端实例
    
    def _get_client(self, server: MediaServer):
        """获取媒体服务器客户端"""
        if server.id in self._clients:
            return self._clients[server.id]
        
        config = MediaServerConfig(
            url=server.url,
            api_key=server.api_key,
            token=server.token,
            username=server.username,
            password=server.password,
            user_id=server.user_id
        )
        
        if server.server_type == "plex":
            client = PlexClient(config)
        elif server.server_type == "jellyfin":
            client = JellyfinClient(config)
        elif server.server_type == "emby":
            client = EmbyClient(config)
        else:
            raise ValueError(f"不支持的服务器类型: {server.server_type}")
        
        self._clients[server.id] = client
        return client
    
    async def create_media_server(
        self,
        name: str,
        server_type: str,
        url: str,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        user_id: Optional[str] = None,
        enabled: bool = True
    ) -> MediaServer:
        """创建媒体服务器"""
        server = MediaServer(
            name=name,
            server_type=server_type,
            url=url,
            api_key=api_key,
            token=token,
            username=username,
            password=password,
            user_id=user_id,
            enabled=enabled
        )
        self.db.add(server)
        await self.db.flush()
        
        # 测试连接
        if enabled:
            await self.check_server_status(server.id)
        
        return server
    
    async def update_media_server(
        self,
        server_id: int,
        **kwargs
    ) -> Optional[MediaServer]:
        """更新媒体服务器"""
        server = await self.db.get(MediaServer, server_id)
        if not server:
            return None
        
        for key, value in kwargs.items():
            if hasattr(server, key):
                setattr(server, key, value)
        
        server.updated_at = datetime.utcnow()
        await self.db.flush()
        
        # 清除客户端缓存
        if server_id in self._clients:
            del self._clients[server_id]
        
        # 如果启用了，测试连接
        if server.enabled:
            await self.check_server_status(server_id)
        
        return server
    
    async def delete_media_server(self, server_id: int) -> bool:
        """删除媒体服务器"""
        server = await self.db.get(MediaServer, server_id)
        if not server:
            return False
        
        # 清除客户端缓存
        if server_id in self._clients:
            client = self._clients[server_id]
            await client.disconnect()
            del self._clients[server_id]
        
        await self.db.delete(server)
        await self.db.flush()
        return True
    
    async def list_media_servers(
        self,
        enabled: Optional[bool] = None,
        server_type: Optional[str] = None
    ) -> List[MediaServer]:
        """获取媒体服务器列表"""
        query = select(MediaServer)
        if enabled is not None:
            query = query.where(MediaServer.enabled == enabled)
        if server_type:
            query = query.where(MediaServer.server_type == server_type)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_media_server(self, server_id: int) -> Optional[MediaServer]:
        """获取媒体服务器"""
        return await self.db.get(MediaServer, server_id)
    
    async def check_server_status(self, server_id: int) -> Dict[str, Any]:
        """检查服务器状态"""
        server = await self.db.get(MediaServer, server_id)
        if not server:
            raise ValueError(f"服务器不存在: {server_id}")
        
        try:
            client = self._get_client(server)
            await client.connect()
            
            # 获取服务器信息
            server_info = await client.get_server_info()
            
            # 更新状态
            server.status = "online"
            server.last_check = datetime.utcnow()
            server.error_message = None
            await self.db.flush()
            
            return {
                "status": "online",
                "server_info": server_info,
                "last_check": server.last_check.isoformat()
            }
        except Exception as e:
            logger.error(f"检查服务器状态失败: {e}")
            server.status = "error"
            server.last_check = datetime.utcnow()
            server.error_message = str(e)
            await self.db.flush()
            
            return {
                "status": "error",
                "error_message": str(e),
                "last_check": server.last_check.isoformat()
            }
    
    async def sync_libraries(self, server_id: int) -> Dict[str, Any]:
        """同步媒体库"""
        server = await self.db.get(MediaServer, server_id)
        if not server:
            raise ValueError(f"服务器不存在: {server_id}")
        
        start_time = datetime.utcnow()
        sync_history = MediaServerSyncHistory(
            media_server_id=server_id,
            sync_type="libraries",
            status="running",
            started_at=start_time
        )
        self.db.add(sync_history)
        await self.db.flush()
        
        try:
            client = self._get_client(server)
            await client.connect()
            
            # 同步媒体库
            result = await client.sync_libraries()
            libraries = result.get("libraries", [])
            
            # 更新服务器配置
            server.libraries = libraries
            server.last_sync = datetime.utcnow()
            server.next_sync = datetime.utcnow() + timedelta(seconds=server.sync_interval)
            await self.db.flush()
            
            # 更新同步历史
            sync_history.status = "success"
            sync_history.items_synced = len(libraries)
            sync_history.completed_at = datetime.utcnow()
            sync_history.duration = (sync_history.completed_at - start_time).total_seconds()
            await self.db.flush()
            
            return {
                "success": True,
                "libraries": libraries,
                "count": len(libraries)
            }
        except Exception as e:
            logger.error(f"同步媒体库失败: {e}")
            sync_history.status = "failed"
            sync_history.error_message = str(e)
            sync_history.completed_at = datetime.utcnow()
            sync_history.duration = (sync_history.completed_at - start_time).total_seconds()
            await self.db.flush()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_metadata(
        self,
        server_id: int,
        item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """同步元数据"""
        server = await self.db.get(MediaServer, server_id)
        if not server:
            raise ValueError(f"服务器不存在: {server_id}")
        
        start_time = datetime.utcnow()
        sync_history = MediaServerSyncHistory(
            media_server_id=server_id,
            sync_type="metadata",
            status="running",
            started_at=start_time
        )
        self.db.add(sync_history)
        await self.db.flush()
        
        try:
            client = self._get_client(server)
            await client.connect()
            
            items_synced = 0
            items_failed = 0
            
            if item_id:
                # 同步单个项目
                success = await client.sync_metadata(item_id)
                if success:
                    items_synced = 1
                else:
                    items_failed = 1
            else:
                # 同步所有库中的项目
                libraries = await client.get_libraries()
                for library in libraries:
                    try:
                        items = await client.get_library_items(library.id, limit=1000)
                        for item in items:
                            try:
                                success = await client.sync_metadata(item.id)
                                if success:
                                    items_synced += 1
                                else:
                                    items_failed += 1
                            except Exception as e:
                                logger.error(f"同步项目失败: {item.id} - {e}")
                                items_failed += 1
                    except Exception as e:
                        logger.error(f"同步媒体库失败: {library.id} - {e}")
            
            # 更新同步历史
            sync_history.status = "success" if items_failed == 0 else "partial"
            sync_history.items_synced = items_synced
            sync_history.items_failed = items_failed
            sync_history.completed_at = datetime.utcnow()
            sync_history.duration = (sync_history.completed_at - start_time).total_seconds()
            await self.db.flush()
            
            return {
                "success": True,
                "items_synced": items_synced,
                "items_failed": items_failed
            }
        except Exception as e:
            logger.error(f"同步元数据失败: {e}")
            sync_history.status = "failed"
            sync_history.error_message = str(e)
            sync_history.completed_at = datetime.utcnow()
            sync_history.duration = (sync_history.completed_at - start_time).total_seconds()
            await self.db.flush()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_playback_sessions(self, server_id: int) -> List[Dict[str, Any]]:
        """获取播放会话"""
        server = await self.db.get(MediaServer, server_id)
        if not server:
            raise ValueError(f"服务器不存在: {server_id}")
        
        try:
            client = self._get_client(server)
            await client.connect()
            
            sessions = await client.get_playback_sessions()
            
            # 保存到数据库
            for session in sessions:
                playback_session = MediaServerPlaybackSession(
                    media_server_id=server_id,
                    item_id=session.item_id,
                    session_id=session.session_id,
                    user_id=session.user_id,
                    user_name=session.user_name,
                    is_paused=session.is_paused,
                    is_playing=session.is_playing,
                    position_ticks=session.position_ticks,
                    play_percentage=session.play_percentage,
                    client_name=session.client_name,
                    device_name=session.device_name,
                    device_type=session.device_type
                )
                self.db.add(playback_session)
            
            await self.db.flush()
            
            return [session.__dict__ for session in sessions]
        except Exception as e:
            logger.error(f"获取播放会话失败: {e}")
            raise
    
    async def get_sync_history(
        self,
        server_id: Optional[int] = None,
        limit: int = 100
    ) -> List[MediaServerSyncHistory]:
        """获取同步历史"""
        query = select(MediaServerSyncHistory)
        if server_id:
            query = query.where(MediaServerSyncHistory.media_server_id == server_id)
        
        query = query.order_by(MediaServerSyncHistory.started_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

