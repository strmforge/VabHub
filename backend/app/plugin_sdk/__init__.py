"""
VabHub Plugin SDK

插件开发者可以通过此 SDK 安全地调用主系统能力。

基本用法:
    from app.plugin_sdk import VabHubSDK, EventBus, EventType, PluginCapability
    from app.plugin_sdk.context import PluginContext

    def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK) -> None:
        sdk.log.info("Plugin loaded!")
        
        # 订阅事件
        async def on_manga_updated(event: EventType, payload: dict) -> None:
            sdk.log.info(f"Manga updated: {payload}")
        
        bus.subscribe(EventType.MANGA_UPDATED, on_manga_updated)
        
        # 使用宿主服务（需要在 plugin.json 声明 sdk_permissions）
        # await sdk.media.has_movie(tmdb_id=550)
        # await sdk.download.add_task("https://...")

PLUGIN-SDK-1 实现
PLUGIN-SDK-2 扩展：宿主服务能力 + 权限模型
"""

from app.plugin_sdk.context import PluginContext
from app.plugin_sdk.api import VabHubSDK, get_sdk_for_plugin
from app.plugin_sdk.events import EventBus, EventType, get_event_bus
from app.plugin_sdk.types import (
    PluginCapability,
    get_capability_label,
    is_dangerous_capability,
    PluginRoute,
)

__all__ = [
    # 核心类
    "PluginContext",
    "VabHubSDK",
    "get_sdk_for_plugin",
    # 事件系统
    "EventBus",
    "EventType",
    "get_event_bus",
    # PLUGIN-SDK-2：能力模型
    "PluginCapability",
    "get_capability_label",
    "is_dangerous_capability",
    # PLUGIN-UX-3：插件 API 路由
    "PluginRoute",
]

__version__ = "3.0.0"  # PLUGIN-UX-3
