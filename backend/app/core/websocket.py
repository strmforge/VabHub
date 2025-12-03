"""
WebSocket管理
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from loguru import logger
import json
import asyncio


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str = "default"):
        """连接WebSocket"""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        
        self.active_connections[channel].append(websocket)
        logger.info(f"WebSocket连接已建立: {channel}, 当前连接数: {len(self.active_connections[channel])}")
    
    def disconnect(self, websocket: WebSocket, channel: str = "default"):
        """断开WebSocket连接"""
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
                logger.info(f"WebSocket连接已断开: {channel}, 当前连接数: {len(self.active_connections[channel])}")
            
            # 如果没有连接了，删除频道
            if len(self.active_connections[channel]) == 0:
                del self.active_connections[channel]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
    
    async def broadcast(self, message: dict, channel: str = "default"):
        """广播消息到所有连接"""
        if channel not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        for conn in disconnected:
            self.disconnect(conn, channel)
    
    async def broadcast_download_update(self, download_data: dict):
        """广播下载更新"""
        await self.broadcast({
            "type": "download_update",
            "data": download_data
        }, channel="downloads")
    
    async def broadcast_download_progress(self, task_id: str, progress: float, status: str, **kwargs):
        """广播下载进度"""
        await self.broadcast({
            "type": "download_progress",
            "data": {
                "task_id": task_id,
                "progress": progress,
                "status": status,
                **kwargs
            }
        }, channel="downloads")


# 全局连接管理器实例
manager = ConnectionManager()

