"""
WebSocket API
用于实时数据更新
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
import logging
import traceback

try:
    from loguru import logger as loguru_logger  # type: ignore
except ImportError:  # pragma: no cover
    loguru_logger = logging.getLogger("app.api.websocket")

logger = getattr(loguru_logger, "bind", lambda **_: loguru_logger)(module="websocket")

from app.core.database import get_db
from app.modules.dashboard.service import DashboardService
from app.modules.download.service import DownloadService

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, List[str]] = {}  # {websocket: [topics]}
    
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
    
    def subscribe(self, websocket: WebSocket, topics: List[str]):
        """订阅主题"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket] = topics
            logger.info(f"WebSocket订阅主题: {topics}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str, topics: List[str] = None):
        """广播消息到所有连接或指定主题"""
        disconnected = []
        for connection in self.active_connections:
            try:
                # 如果没有指定主题，或者连接订阅了相关主题
                if topics is None or any(topic in self.subscriptions.get(connection, []) for topic in topics):
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点
    
    支持的主题：
    - dashboard: 仪表盘数据
    - downloads: 下载任务
    - system: 系统资源
    - api_performance: API性能指标
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "subscribe":
                    # 订阅主题
                    topics = message.get("topics", [])
                    manager.subscribe(websocket, topics)
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "topics": topics,
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                elif msg_type == "ping":
                    # 心跳检测
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                else:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"未知消息类型: {msg_type}",
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "无效的JSON格式",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket客户端断开连接")


async def broadcast_dashboard_update():
    """广播仪表盘更新"""
    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            service = DashboardService(db)
            dashboard_data = await service.get_dashboard_data()
            
            message = json.dumps({
                "type": "dashboard_update",
                "data": dashboard_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await manager.broadcast(message, topics=["dashboard"])
    except Exception as e:
        logger.error(f"广播仪表盘更新失败: {e}\n{traceback.format_exc()}")


async def broadcast_download_update(download_data: Dict[str, Any]):
    """广播下载任务更新"""
    try:
        message = json.dumps({
            "type": "download_update",
            "data": download_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await manager.broadcast(message, topics=["downloads"])
    except Exception as e:
        logger.error(f"广播下载更新失败: {e}")


async def broadcast_system_update(system_data: Dict[str, Any]):
    """广播系统资源更新"""
    try:
        message = json.dumps({
            "type": "system_update",
            "data": system_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await manager.broadcast(message, topics=["system"])
    except Exception as e:
        logger.error(f"广播系统更新失败: {e}")


# 后台任务：定期推送仪表盘数据
async def dashboard_broadcast_task():
    """定期广播仪表盘数据"""
    while True:
        try:
            await asyncio.sleep(5)  # 每5秒推送一次
            await broadcast_dashboard_update()
        except Exception as e:
            logger.error(f"仪表盘广播任务失败: {e}")
            await asyncio.sleep(5)


# 后台任务：定期推送系统资源数据
async def system_resources_broadcast_task():
    """定期广播系统资源数据"""
    while True:
        try:
            await asyncio.sleep(2)  # 每2秒推送一次
            from app.core.database import AsyncSessionLocal
            from app.modules.monitoring.system_monitor import get_system_monitor
            
            async with AsyncSessionLocal() as db:
                monitor = get_system_monitor(db)
                resources = await monitor.get_system_resources()
                await broadcast_system_update(resources)
        except Exception as e:
            logger.error(f"系统资源广播任务失败: {e}")
            await asyncio.sleep(2)


# 后台任务：定期推送API性能数据
async def api_performance_broadcast_task():
    """定期广播API性能数据"""
    while True:
        try:
            await asyncio.sleep(10)  # 每10秒推送一次
            from app.modules.monitoring.api_monitor import get_api_monitor
            from app.core.middleware import PerformanceMonitoringMiddleware
            
            api_monitor = get_api_monitor()
            middleware = PerformanceMonitoringMiddleware._instance
            
            if middleware:
                metrics = api_monitor.get_performance_metrics(middleware)
                message = json.dumps({
                    "type": "api_performance_update",
                    "data": metrics,
                    "timestamp": datetime.utcnow().isoformat()
                })
                await manager.broadcast(message, topics=["api_performance"])
        except Exception as e:
            logger.error(f"API性能广播任务失败: {e}")
            await asyncio.sleep(10)


# 启动后台任务（在应用启动时调用）
async def start_websocket_tasks():
    """启动WebSocket后台任务"""
    asyncio.create_task(dashboard_broadcast_task())
    asyncio.create_task(system_resources_broadcast_task())
    asyncio.create_task(api_performance_broadcast_task())
    logger.info("WebSocket后台任务已启动（仪表盘、系统资源、API性能）")
