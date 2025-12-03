"""
事件总线 EventBus

PLUGIN-SDK-1 实现
PLUGIN-SAFETY-1 扩展：错误上报 & 隔离机制

插件可以通过订阅事件来响应主系统的业务动作。
"""

from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable, Optional, Protocol
from loguru import logger


class EventType(str, Enum):
    """
    事件类型枚举
    
    命名约定：领域.动作（小写，点分隔）
    
    v1 支持的事件类型：
    - manga.updated: 漫画系列更新
    - audiobook.tts_finished: 有声书 TTS 任务完成
    - audiobook.ready: 有声书就绪
    - download.completed: 下载任务完成
    - plugin.loaded: 插件加载完成
    - plugin.unloading: 插件即将卸载
    """
    
    # ============== 漫画相关 ==============
    MANGA_UPDATED = "manga.updated"
    MANGA_SYNC_FAILED = "manga.sync_failed"
    
    # ============== 有声书/TTS 相关 ==============
    AUDIOBOOK_TTS_FINISHED = "audiobook.tts_finished"
    AUDIOBOOK_TTS_FAILED = "audiobook.tts_failed"
    AUDIOBOOK_READY = "audiobook.ready"
    
    # ============== 下载相关 ==============
    DOWNLOAD_COMPLETED = "download.completed"
    DOWNLOAD_FAILED = "download.failed"
    
    # ============== 音乐相关 ==============
    MUSIC_CHART_UPDATED = "music.chart_updated"
    MUSIC_TRACKS_READY = "music.tracks_ready"
    
    # ============== 插件生命周期 ==============
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADING = "plugin.unloading"
    
    # ============== 系统事件 ==============
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class EventHandler(Protocol):
    """
    事件处理器协议
    
    所有事件处理函数必须符合此签名：
    async def handler(event: EventType, payload: dict[str, Any]) -> None
    """
    
    async def __call__(self, event: EventType, payload: dict[str, Any]) -> None:
        """
        处理事件
        
        Args:
            event: 事件类型
            payload: 事件数据
        """
        ...


# 类型别名
EventHandlerFunc = Callable[[EventType, dict[str, Any]], Awaitable[None]]


class EventBus:
    """
    事件总线
    
    支持订阅、取消订阅、发布事件。
    所有事件处理器异步执行，异常不会影响其他处理器。
    
    Example:
        bus = EventBus()
        
        async def on_manga_updated(event: EventType, payload: dict) -> None:
            print(f"Manga updated: {payload}")
        
        bus.subscribe(EventType.MANGA_UPDATED, on_manga_updated)
        
        await bus.publish(EventType.MANGA_UPDATED, {
            "series_id": 123,
            "title": "One Piece",
            "new_chapters": 5
        })
    """
    
    def __init__(self) -> None:
        """初始化事件总线"""
        self._handlers: dict[EventType, list[EventHandlerFunc]] = defaultdict(list)
        self._handler_sources: dict[EventHandlerFunc, str] = {}  # handler -> plugin_id
    
    def subscribe(
        self,
        event: EventType,
        handler: EventHandlerFunc,
        *,
        source: Optional[str] = None
    ) -> None:
        """
        订阅事件
        
        Args:
            event: 事件类型
            handler: 事件处理函数
            source: 订阅来源（插件 ID，用于调试和清理）
        """
        if handler not in self._handlers[event]:
            self._handlers[event].append(handler)
            if source:
                self._handler_sources[handler] = source
            logger.debug(f"[event-bus] Subscribed to {event.value} from {source or 'unknown'}")
    
    def unsubscribe(self, event: EventType, handler: EventHandlerFunc) -> bool:
        """
        取消订阅
        
        Args:
            event: 事件类型
            handler: 事件处理函数
            
        Returns:
            是否成功取消
        """
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)
            self._handler_sources.pop(handler, None)
            logger.debug(f"[event-bus] Unsubscribed from {event.value}")
            return True
        return False
    
    def unsubscribe_all_from_source(self, source: str) -> int:
        """
        取消指定来源的所有订阅
        
        用于插件卸载时清理其所有事件订阅。
        
        Args:
            source: 来源标识（插件 ID）
            
        Returns:
            取消的订阅数量
        """
        count = 0
        handlers_to_remove = [
            (event, handler)
            for handler, src in self._handler_sources.items()
            if src == source
            for event, handlers in self._handlers.items()
            if handler in handlers
        ]
        
        for event, handler in handlers_to_remove:
            if handler in self._handlers[event]:
                self._handlers[event].remove(handler)
                self._handler_sources.pop(handler, None)
                count += 1
        
        if count > 0:
            logger.debug(f"[event-bus] Removed {count} subscriptions from {source}")
        
        return count
    
    async def publish(
        self,
        event: EventType,
        payload: dict[str, Any],
        *,
        source: Optional[str] = None
    ) -> int:
        """
        发布事件
        
        异步调用所有订阅该事件的处理器。
        异常会被捕获并记录，不会影响其他处理器。
        
        Args:
            event: 事件类型
            payload: 事件数据
            source: 事件来源（用于调试）
            
        Returns:
            成功处理的处理器数量
        """
        handlers = list(self._handlers[event])
        if not handlers:
            logger.debug(f"[event-bus] No handlers for {event.value}")
            return 0
        
        # 添加元数据
        enriched_payload = {
            **payload,
            "_event_type": event.value,
            "_event_time": datetime.utcnow().isoformat(),
            "_event_source": source,
        }
        
        success_count = 0
        for handler in handlers:
            handler_source = self._handler_sources.get(handler, "unknown")
            
            # PLUGIN-SAFETY-1: 跳过被隔离的插件
            if handler_source != "unknown":
                try:
                    # 使用 PluginRegistry 的内存隔离状态检查
                    from app.services.plugin_registry import PluginRegistry
                    registry = PluginRegistry()
                    
                    if registry.is_plugin_quarantined(handler_source):
                        logger.debug(f"[event-bus] Skipping quarantined plugin: {handler_source}")
                        continue
                    
                except Exception as check_error:
                    logger.warning(f"[event-bus] Failed to check quarantine for {handler_source}: {check_error}")
            
            try:
                await handler(event, enriched_payload)
                success_count += 1
            except Exception as e:
                handler_source = self._handler_sources.get(handler, "unknown")
                logger.error(
                    f"[event-bus] Handler error for {event.value} from {handler_source}: {e}",
                    exc_info=True
                )
                
                # PLUGIN-SAFETY-1: 上报错误到监控服务
                try:
                    # 异步上报，不阻塞主流程
                    import asyncio
                    from app.services.plugin_monitor_service import PluginMonitorService
                    
                    # 创建新的数据库会话用于上报
                    from app.core.database import get_async_session
                    
                    async def report_error():
                        async for session in get_async_session():
                            await PluginMonitorService.report_error(
                                session,
                                handler_source,
                                {
                                    "event": event.value,
                                    "error": str(e),
                                    "source": f"event_handler:{event.value}",
                                    "payload": payload  # 原始 payload 参数（不含元数据）
                                }
                            )
                            break
                    
                    asyncio.create_task(report_error())
                    
                except Exception as report_error:
                    logger.error(f"[event-bus] Failed to report handler error: {report_error}")
        
        logger.debug(
            f"[event-bus] Published {event.value}: "
            f"{success_count}/{len(handlers)} handlers succeeded"
        )
        
        return success_count
    
    def get_handler_count(self, event: Optional[EventType] = None) -> int:
        """
        获取处理器数量
        
        Args:
            event: 事件类型，如果为 None 则返回总数
            
        Returns:
            处理器数量
        """
        if event:
            return len(self._handlers[event])
        return sum(len(handlers) for handlers in self._handlers.values())
    
    def get_subscribed_events(self) -> list[EventType]:
        """获取有订阅者的事件类型列表"""
        return [event for event, handlers in self._handlers.items() if handlers]


# ============== 全局事件总线单例 ==============

_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    获取全局事件总线实例
    
    Returns:
        EventBus 单例
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """重置事件总线（用于测试）"""
    global _event_bus
    _event_bus = None


# ============== 便捷函数 ==============

async def publish_event(
    event: EventType,
    payload: dict[str, Any],
    *,
    source: Optional[str] = None
) -> int:
    """
    发布事件的便捷函数
    
    Args:
        event: 事件类型
        payload: 事件数据
        source: 事件来源
        
    Returns:
        成功处理的处理器数量
    """
    return await get_event_bus().publish(event, payload, source=source)
