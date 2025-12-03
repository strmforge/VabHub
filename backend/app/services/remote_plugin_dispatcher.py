"""
远程插件事件分发器
PLUGIN-REMOTE-1 实现

订阅 EventBus 事件，分发给远程插件
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.plugin_sdk.events import EventBus, EventType
from app.plugin_sdk.remote_protocol import (
    RemotePluginClient, 
    RemotePluginEvent, 
    RemotePluginResponse,
    create_remote_client
)
from app.models.plugin import Plugin, PluginType, PluginStatus
from app.core.database import get_async_session
from app.services.plugin_statistics_service import record_plugin_event_handled


class RemotePluginDispatcher:
    """
    远程插件事件分发器
    
    订阅 EventBus 的所有事件，将事件推送到相应的远程插件
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._client_cache: Dict[str, RemotePluginClient] = {}
        
    async def start(self):
        """启动分发器，订阅所有事件"""
        logger.info("[remote-dispatcher] Starting remote plugin dispatcher")
        
        # 订阅所有相关事件
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._handle_event, source="remote_dispatcher")
        
        logger.info(f"[remote-dispatcher] Subscribed to {len(EventType)} event types")
    
    async def stop(self):
        """停止分发器"""
        logger.info("[remote-dispatcher] Stopping remote plugin dispatcher")
        # EventBus 会自动清理订阅者
    
    async def _handle_event(self, event: EventType, payload: Dict[str, Any]):
        """
        处理单个事件，分发给所有订阅的远程插件
        
        Args:
            event: 事件类型
            payload: 事件载荷
        """
        try:
            # 查找订阅此事件的远程插件
            remote_plugins = await self._find_remote_plugins_for_event(event.value)
            
            if not remote_plugins:
                return
            
            logger.debug(f"[remote-dispatcher] Found {len(remote_plugins)} remote plugins for event {event.value}")
            
            # 并发推送到所有远程插件
            tasks = []
            for plugin in remote_plugins:
                task = self._push_event_to_plugin(plugin, event, payload)
                tasks.append(task)
            
            # 等待所有推送完成（不阻塞主流程）
            import asyncio
            asyncio.create_task(self._batch_push_events(tasks))
            
        except Exception as e:
            logger.error(f"[remote-dispatcher] Error handling event {event.value}: {e}")
    
    async def _find_remote_plugins_for_event(self, event_name: str) -> List[Plugin]:
        """
        查找订阅指定事件的远程插件
        
        Args:
            event_name: 事件名称
            
        Returns:
            订阅该事件的远程插件列表
        """
        async for session in get_async_session():
            try:
                # 使用更兼容的 JSON 查询方式
                # PostgreSQL: @> 操作符, SQLite: JSON_EXTRACT
                from sqlalchemy import text
                
                # 尝试 PostgreSQL 语法
                try:
                    stmt = select(Plugin).where(
                        Plugin.plugin_type == PluginType.REMOTE,
                        Plugin.status == PluginStatus.ENABLED,
                        text("subscribed_events @> :event_name").bindparams(event_name=f'["{event_name}"]')
                    )
                    result = await session.execute(stmt)
                    return result.scalars().all()
                except Exception:
                    # 回退到通用方式：获取所有远程插件然后在内存中过滤
                    stmt = select(Plugin).where(
                        Plugin.plugin_type == PluginType.REMOTE,
                        Plugin.status == PluginStatus.ENABLED
                    )
                    result = await session.execute(stmt)
                    all_remote_plugins = result.scalars().all()
                    
                    # 在内存中过滤订阅了该事件的插件
                    filtered_plugins = [
                        plugin for plugin in all_remote_plugins
                        if hasattr(plugin, 'subscribed_events') and 
                        isinstance(plugin.subscribed_events, list) and 
                        event_name in plugin.subscribed_events
                    ]
                    
                    logger.debug(f"[remote-dispatcher] Filtered {len(filtered_plugins)} plugins for event {event_name} (memory filter)")
                    return filtered_plugins
                    
            except Exception as e:
                logger.error(f"[remote-dispatcher] Error finding remote plugins for {event_name}: {e}")
                return []
    
    async def _push_event_to_plugin(
        self, 
        plugin: Plugin, 
        event: EventType, 
        payload: Dict[str, Any]
    ) -> tuple[str, bool, Optional[str]]:
        """
        推送事件到单个远程插件
        
        Args:
            plugin: 目标插件
            event: 事件类型
            payload: 事件载荷
            
        Returns:
            (plugin_name, success, error_message)
        """
        try:
            # 获取或创建客户端
            client = self._get_client_for_plugin(plugin)
            if not client:
                return plugin.name, False, "Failed to create remote client"
            
            # 创建事件对象
            remote_event = RemotePluginEvent(
                plugin_id=plugin.name,
                event=event.value,
                payload=payload,
                timestamp=datetime.utcnow()
            )
            
            # 推送事件
            response = await client.push_event(remote_event)
            
            if response.status == "success":
                logger.debug(f"[remote-dispatcher] Event pushed successfully to {plugin.name}")
                
                # 记录事件处理统计
                try:
                    async for session in get_async_session():
                        await record_plugin_event_handled(session, plugin.name)
                        break
                except Exception as e:
                    logger.warning(f"[remote-dispatcher] Failed to record statistics for {plugin.name}: {e}")
                
                return plugin.name, True, None
            else:
                logger.warning(f"[remote-dispatcher] Plugin {plugin.name} returned error: {response.message}")
                return plugin.name, False, response.message
                
        except Exception as e:
            logger.error(f"[remote-dispatcher] Failed to push event to {plugin.name}: {e}")
            return plugin.name, False, str(e)
    
    def _get_client_for_plugin(self, plugin: Plugin) -> Optional[RemotePluginClient]:
        """
        获取插件的远程客户端（带缓存）
        
        Args:
            plugin: 插件对象
            
        Returns:
            RemotePluginClient 或 None
        """
        # 检查缓存
        if plugin.name in self._client_cache:
            client = self._client_cache[plugin.name]
            # 如果客户端健康，直接返回
            if client.is_healthy:
                return client
            else:
                # 移除不健康的客户端
                del self._client_cache[plugin.name]
        
        # 创建新客户端
        if not plugin.remote_config:
            logger.error(f"[remote-dispatcher] Plugin {plugin.name} missing remote config")
            return None
        
        client = create_remote_client(plugin.remote_config)
        if client:
            self._client_cache[plugin.name] = client
            logger.debug(f"[remote-dispatcher] Created client for {plugin.name}")
        
        return client
    
    async def _batch_push_events(self, tasks: List):
        """
        批量推送事件（异步执行，不阻塞主流程）
        
        Args:
            tasks: 推送任务列表
        """
        try:
            import asyncio
            
            # 等待所有任务完成，设置超时
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            success_count = 0
            error_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                    logger.error(f"[remote-dispatcher] Batch push error: {result}")
                else:
                    plugin_name, success, error = result
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        logger.warning(f"[remote-dispatcher] {plugin_name} push failed: {error}")
            
            if success_count > 0 or error_count > 0:
                logger.info(f"[remote-dispatcher] Batch push completed: {success_count} success, {error_count} errors")
                
        except Exception as e:
            logger.error(f"[remote-dispatcher] Error in batch push: {e}")
    
    async def get_dispatcher_status(self) -> Dict[str, Any]:
        """
        获取分发器状态
        
        Returns:
            分发器状态信息
        """
        # 统计客户端状态
        healthy_clients = sum(1 for client in self._client_cache.values() if client.is_healthy)
        total_clients = len(self._client_cache)
        
        return {
            "started": True,
            "total_clients": total_clients,
            "healthy_clients": healthy_clients,
            "unhealthy_clients": total_clients - healthy_clients,
            "client_cache_size": len(self._client_cache)
        }


# 全局分发器实例
_remote_dispatcher: Optional[RemotePluginDispatcher] = None


async def get_remote_dispatcher(event_bus: EventBus) -> RemotePluginDispatcher:
    """
    获取全局远程插件分发器实例
    
    Args:
        event_bus: EventBus 实例
        
    Returns:
        RemotePluginDispatcher 实例
    """
    global _remote_dispatcher
    
    if _remote_dispatcher is None:
        _remote_dispatcher = RemotePluginDispatcher(event_bus)
        await _remote_dispatcher.start()
    
    return _remote_dispatcher


async def shutdown_remote_dispatcher():
    """关闭远程插件分发器"""
    global _remote_dispatcher
    
    if _remote_dispatcher:
        await _remote_dispatcher.stop()
        _remote_dispatcher = None
        logger.info("[remote-dispatcher] Remote dispatcher shutdown")
