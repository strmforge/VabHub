"""
事件日志示例插件 - 主模块

PLUGIN-SDK-1 示例
演示如何使用 setup_plugin 入口和 EventBus 订阅事件。
"""

from typing import Any

from app.plugin_sdk.context import PluginContext
from app.plugin_sdk.api import VabHubSDK
from app.plugin_sdk.events import EventBus, EventType


def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK) -> None:
    """
    插件入口函数
    
    这是 PLUGIN-SDK-1 推荐的新插件入口。
    在这里注册事件订阅、初始化资源等。
    
    Args:
        ctx: 插件上下文，包含插件 ID、数据目录等信息
        bus: 全局事件总线，用于订阅/发布事件
        sdk: VabHub SDK 实例，提供日志、HTTP、通知等能力
    """
    sdk.log.info("=" * 50)
    sdk.log.info(f"事件日志示例插件已加载")
    sdk.log.info(f"插件 ID: {ctx.plugin_id}")
    sdk.log.info(f"数据目录: {ctx.data_dir}")
    sdk.log.info(f"应用版本: {sdk.env.app_version}")
    sdk.log.info("=" * 50)
    
    # 注册事件处理器
    # 注意：handler 必须是 async 函数
    
    async def on_manga_updated(event: EventType, payload: dict[str, Any]) -> None:
        """漫画更新事件处理器"""
        sdk.log.info(f"[EVENT] 漫画更新: {payload.get('series_title', 'unknown')}")
        sdk.log.info(f"  - 系列 ID: {payload.get('series_id')}")
        sdk.log.info(f"  - 新章节数: {payload.get('new_chapters')}")
    
    async def on_tts_finished(event: EventType, payload: dict[str, Any]) -> None:
        """TTS 完成事件处理器"""
        sdk.log.info(f"[EVENT] TTS 任务完成: {payload.get('ebook_title', 'unknown')}")
        sdk.log.info(f"  - 任务 ID: {payload.get('job_id')}")
        sdk.log.info(f"  - 有声书 ID: {payload.get('audiobook_id')}")
    
    async def on_audiobook_ready(event: EventType, payload: dict[str, Any]) -> None:
        """有声书就绪事件处理器"""
        sdk.log.info(f"[EVENT] 有声书就绪: {payload.get('audiobook_title', 'unknown')}")
        sdk.log.info(f"  - 来源类型: {payload.get('source_type')}")
    
    async def on_plugin_loaded(event: EventType, payload: dict[str, Any]) -> None:
        """插件加载事件处理器"""
        plugin_id = payload.get('plugin_id', 'unknown')
        if plugin_id != ctx.plugin_id:  # 不记录自己的加载事件
            sdk.log.info(f"[EVENT] 其他插件已加载: {plugin_id}")
    
    # 订阅事件
    # source 参数用于标识订阅来源，在插件卸载时自动清理
    bus.subscribe(EventType.MANGA_UPDATED, on_manga_updated, source=ctx.plugin_id)
    bus.subscribe(EventType.AUDIOBOOK_TTS_FINISHED, on_tts_finished, source=ctx.plugin_id)
    bus.subscribe(EventType.AUDIOBOOK_READY, on_audiobook_ready, source=ctx.plugin_id)
    bus.subscribe(EventType.PLUGIN_LOADED, on_plugin_loaded, source=ctx.plugin_id)
    
    sdk.log.info(f"已订阅 {bus.get_handler_count()} 个事件")


def register_plugin(registry: Any) -> None:
    """
    旧版插件入口（兼容）
    
    如果插件同时实现了 setup_plugin 和 register_plugin，
    两者都会被调用（register_plugin 先于 setup_plugin）。
    """
    # 这里可以注册搜索提供者、Bot 命令等
    # 但对于纯事件监听插件，不需要注册任何东西
    pass
