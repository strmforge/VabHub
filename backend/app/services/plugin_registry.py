"""
插件运行时注册表
DEV-SDK-1 实现
PLUGIN-SDK-1 扩展：SDK + EventBus 集成
PLUGIN-UX-3 扩展：Dashboard + Plugin API
PLUGIN-SAFETY-1 扩展：隔离状态追踪

管理已加载插件的扩展点
"""

import asyncio
import importlib
import inspect
import time
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable, Awaitable, Iterable, Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.plugin import Plugin, PluginStatus


# ============== 扩展点接口定义 ==============

class SearchProvider(Protocol):
    """搜索提供者接口"""
    id: str
    
    async def search(
        self,
        session: AsyncSession,
        query: str,
        scope: Any = None,
        limit: int = 10,
    ) -> Iterable[Any]:
        """执行搜索"""
        ...


class BotCommandExtension(Protocol):
    """Bot 命令扩展接口"""
    command: str  # 不含斜杠，如 'hello'
    
    async def handle(self, ctx: Any) -> None:
        """处理命令"""
        ...


class WorkflowExtension(Protocol):
    """工作流扩展接口"""
    id: str
    name: str
    description: str
    
    async def run(
        self,
        session: AsyncSession,
        payload: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """执行工作流"""
        ...


class PluginPanelProvider(Protocol):
    """
    面板数据提供者接口
    
    插件实现此接口以提供 UI 面板的数据
    """
    
    def get_panel_data(
        self,
        panel_id: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        获取面板数据
        
        Args:
            panel_id: 面板 ID
            context: 上下文信息（用户、请求参数等）
            
        Returns:
            面板数据，格式由面板类型决定
        """
        ...


# ============== 已加载插件数据结构 ==============

@dataclass
class LoadedPlugin:
    """已加载的插件"""
    plugin: Plugin
    module: Any = None
    search_providers: list[SearchProvider] = field(default_factory=list)
    bot_commands: list[BotCommandExtension] = field(default_factory=list)
    workflows: list[WorkflowExtension] = field(default_factory=list)
    panel_provider: Optional[PluginPanelProvider] = None
    # PLUGIN-SDK-1：SDK 实例
    sdk: Optional[Any] = None  # VabHubSDK 实例
    has_setup_plugin: bool = False  # 是否实现了 setup_plugin
    # PLUGIN-UX-3：Dashboard 和 Routes
    has_dashboard: bool = False  # 是否实现了 get_dashboard
    has_routes: bool = False  # 是否实现了 get_routes
    routes: list[Any] = field(default_factory=list)  # 插件注册的路由


# ============== 插件注册表单例 ==============

class PluginRegistry:
    """
    插件运行时注册表
    
    单例模式，管理所有已加载插件的扩展点
    """
    
    _instance: Optional["PluginRegistry"] = None
    
    def __new__(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self) -> None:
        """初始化"""
        self.loaded_plugins: dict[str, LoadedPlugin] = {}
        self.quarantined_plugins: set[str] = set()  # PLUGIN-SAFETY-1: 内存中的隔离插件集合
        self._initialized = False
    
    def reset(self) -> None:
        """重置注册表（用于测试）"""
        self.loaded_plugins.clear()
        self.quarantined_plugins.clear()  # PLUGIN-SAFETY-1: 清理隔离状态
        self._initialized = False
    
    # ============== 注册方法 ==============
    
    def register_search_provider(self, plugin_id: str, provider: SearchProvider) -> None:
        """注册搜索提供者"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"[plugin-registry] Unknown plugin: {plugin_id}")
            return
        
        self.loaded_plugins[plugin_id].search_providers.append(provider)
        logger.info(f"[plugin-registry] Registered SearchProvider: {provider.id} from {plugin_id}")
    
    def register_bot_command(self, plugin_id: str, extension: BotCommandExtension) -> None:
        """注册 Bot 命令"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"[plugin-registry] Unknown plugin: {plugin_id}")
            return
        
        self.loaded_plugins[plugin_id].bot_commands.append(extension)
        logger.info(f"[plugin-registry] Registered BotCommand: /{extension.command} from {plugin_id}")
    
    def register_workflow(self, plugin_id: str, extension: WorkflowExtension) -> None:
        """注册工作流扩展"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"[plugin-registry] Unknown plugin: {plugin_id}")
            return
        
        self.loaded_plugins[plugin_id].workflows.append(extension)
        logger.info(f"[plugin-registry] Registered Workflow: {extension.id} from {plugin_id}")
    
    def register_panel_provider(self, plugin_id: str, provider: PluginPanelProvider) -> None:
        """注册面板数据提供者"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"[plugin-registry] Unknown plugin: {plugin_id}")
            return
        
        self.loaded_plugins[plugin_id].panel_provider = provider
        logger.info(f"[plugin-registry] Registered PanelProvider from {plugin_id}")
    
    # ============== 获取方法 ==============
    
    def get_search_providers(self) -> list[SearchProvider]:
        """获取所有搜索提供者"""
        providers = []
        for loaded in self.loaded_plugins.values():
            providers.extend(loaded.search_providers)
        return providers
    
    def get_bot_commands(self) -> list[BotCommandExtension]:
        """获取所有 Bot 命令扩展"""
        commands = []
        for loaded in self.loaded_plugins.values():
            commands.extend(loaded.bot_commands)
        return commands
    
    def get_workflows(self) -> list[WorkflowExtension]:
        """获取所有工作流扩展"""
        workflows = []
        for loaded in self.loaded_plugins.values():
            workflows.extend(loaded.workflows)
        return workflows
    
    def get_workflow_by_id(self, workflow_id: str) -> Optional[tuple[WorkflowExtension, str]]:
        """
        根据 ID 获取工作流
        
        Returns:
            (WorkflowExtension, plugin_name) 或 None
        """
        for plugin_id, loaded in self.loaded_plugins.items():
            for wf in loaded.workflows:
                if wf.id == workflow_id:
                    return (wf, plugin_id)
        return None
    
    def get_bot_command(self, command: str) -> Optional[BotCommandExtension]:
        """根据命令名获取 Bot 命令扩展"""
        for loaded in self.loaded_plugins.values():
            for cmd in loaded.bot_commands:
                if cmd.command == command:
                    return cmd
        return None
    
    def get_panel_data(
        self,
        plugin_id: str,
        panel_id: str,
        context: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        获取面板数据
        
        Args:
            plugin_id: 插件 ID
            panel_id: 面板 ID
            context: 上下文信息
            
        Returns:
            面板数据，如果找不到提供者则返回 None
        """
        loaded = self.loaded_plugins.get(plugin_id)
        if not loaded:
            logger.warning(f"[plugin-registry] Plugin not loaded: {plugin_id}")
            return None
        
        if not loaded.panel_provider:
            logger.warning(f"[plugin-registry] No panel provider for: {plugin_id}")
            return None
        
        try:
            return loaded.panel_provider.get_panel_data(panel_id, context)
        except Exception as e:
            logger.error(f"[plugin-registry] Panel data error {plugin_id}/{panel_id}: {e}")
            return None
    
    # ============== PLUGIN-UX-3：Dashboard 和 Routes ==============
    
    def get_dashboard(self, plugin_id: str) -> Optional[Any]:
        """
        获取插件 Dashboard
        
        Args:
            plugin_id: 插件 ID
            
        Returns:
            PluginDashboardSchema 或 None
        """
        loaded = self.loaded_plugins.get(plugin_id)
        if not loaded or not loaded.has_dashboard:
            return None
        
        get_dashboard_fn = getattr(loaded.module, "get_dashboard", None)
        if not callable(get_dashboard_fn):
            return None
        
        try:
            return get_dashboard_fn(loaded.sdk)
        except Exception as e:
            logger.error(f"[plugin-registry] Dashboard error {plugin_id}: {e}")
            return None
    
    def get_routes(self, plugin_id: str) -> list[Any]:
        """
        获取插件路由
        
        Args:
            plugin_id: 插件 ID
            
        Returns:
            路由列表
        """
        loaded = self.loaded_plugins.get(plugin_id)
        if not loaded:
            return []
        return loaded.routes
    
    def get_all_routes(self) -> dict[str, list[Any]]:
        """
        获取所有插件的路由
        
        Returns:
            {plugin_id: routes} 字典
        """
        return {
            plugin_id: loaded.routes
            for plugin_id, loaded in self.loaded_plugins.items()
            if loaded.routes
        }
    
    # ============== PLUGIN-SAFETY-1: 隔离状态管理 ==============
    
    def is_plugin_quarantined(self, plugin_id: str) -> bool:
        """
        检查插件是否被隔离
        
        Args:
            plugin_id: 插件 ID
            
        Returns:
            是否被隔离
        """
        return plugin_id in self.quarantined_plugins
    
    def quarantine_plugin(self, plugin_id: str) -> None:
        """
        隔离插件
        
        Args:
            plugin_id: 插件 ID
        """
        if plugin_id not in self.quarantined_plugins:
            self.quarantined_plugins.add(plugin_id)
            logger.warning(f"[plugin-registry] Plugin quarantined: {plugin_id}")
    
    def unquarantine_plugin(self, plugin_id: str) -> None:
        """
        解除插件隔离
        
        Args:
            plugin_id: 插件 ID
        """
        if plugin_id in self.quarantined_plugins:
            self.quarantined_plugins.remove(plugin_id)
            logger.info(f"[plugin-registry] Plugin unquarantined: {plugin_id}")
    
    async def sync_quarantine_status(self, session: AsyncSession) -> None:
        """
        从数据库同步隔离状态到内存
        
        Args:
            session: 数据库会话
        """
        from sqlalchemy import select
        from app.models.plugin import Plugin
        
        try:
            stmt = select(Plugin.name).where(Plugin.is_quarantined == True)
            result = await session.execute(stmt)
            quarantined_names = {row[0] for row in result.fetchall()}
            
            # 更新内存状态
            self.quarantined_plugins = quarantined_names
            
            logger.info(f"[plugin-registry] Synced quarantine status: {len(quarantined_names)} quarantined")
            
        except Exception as e:
            logger.error(f"[plugin-registry] Failed to sync quarantine status: {e}", exc_info=True)
    
    # ============== 加载方法 ==============
    
    async def load_enabled_plugins(self, session: AsyncSession) -> None:
        """
        加载所有已启用的插件
        
        Args:
            session: 数据库会话
        """
        from app.services.plugin_service import get_enabled_plugins, add_plugin_to_path, set_plugin_status
        
        if self._initialized:
            logger.debug("[plugin-registry] Already initialized, skipping")
            return
        
        # PLUGIN-SAFETY-1: 初始化隔离状态
        await self.sync_quarantine_status(session)
        
        plugins = await get_enabled_plugins(session)
        logger.info(f"[plugin-registry] Loading {len(plugins)} enabled plugins...")
        
        for plugin in plugins:
            await self._load_plugin(session, plugin)
        
        self._initialized = True
        logger.info(f"[plugin-registry] Loaded {len(self.loaded_plugins)} plugins successfully")
    
    async def _load_plugin(self, session: AsyncSession, plugin: Plugin) -> bool:
        """
        加载单个插件
        
        PLUGIN-SDK-1：支持 setup_plugin(ctx, bus, sdk) 入口
        
        Returns:
            是否加载成功
        """
        from app.services.plugin_service import add_plugin_to_path, set_plugin_status, build_plugin_context
        from app.plugin_sdk.api import VabHubSDK, register_sdk_instance
        from app.plugin_sdk.events import get_event_bus, EventType, publish_event
        
        plugin_id = plugin.name
        
        try:
            # 添加路径
            add_plugin_to_path(plugin)
            
            # 创建 LoadedPlugin 占位
            self.loaded_plugins[plugin_id] = LoadedPlugin(plugin=plugin)
            
            # 动态导入模块
            module = importlib.import_module(plugin.entry_module)
            self.loaded_plugins[plugin_id].module = module
            
            # PLUGIN-SDK-1：构建 SDK 实例
            # PLUGIN-SDK-2：注入 sdk_permissions
            ctx = build_plugin_context(plugin)
            sdk_permissions = getattr(plugin, 'sdk_permissions', None) or []
            sdk = VabHubSDK(ctx, sdk_permissions=sdk_permissions)
            self.loaded_plugins[plugin_id].sdk = sdk
            register_sdk_instance(plugin_id, sdk)
            
            if sdk_permissions:
                logger.debug(f"[plugin-registry] {plugin_id} sdk_permissions: {sdk_permissions}")
            
            # 调用 register_plugin（兼容旧插件）
            if hasattr(module, "register_plugin"):
                module.register_plugin(self)
            
            # PLUGIN-SDK-1：调用 setup_plugin（新插件入口）
            setup_fn = getattr(module, "setup_plugin", None)
            if callable(setup_fn):
                self.loaded_plugins[plugin_id].has_setup_plugin = True
                event_bus = get_event_bus()
                
                try:
                    result = setup_fn(ctx, event_bus, sdk)
                    # 支持同步和异步两种写法
                    if inspect.iscoroutine(result):
                        await result
                    
                    sdk.log.info(f"setup_plugin completed")
                except Exception as e:
                    sdk.log.error(f"setup_plugin failed: {e}")
                    # setup_plugin 失败不影响插件加载，只记录警告
                    logger.warning(f"[plugin-registry] {plugin_id} setup_plugin error: {e}")
            
            # PLUGIN-UX-3：检测 get_dashboard
            get_dashboard_fn = getattr(module, "get_dashboard", None)
            if callable(get_dashboard_fn):
                self.loaded_plugins[plugin_id].has_dashboard = True
                logger.debug(f"[plugin-registry] {plugin_id} has get_dashboard")
            
            # PLUGIN-UX-3：检测 get_routes
            get_routes_fn = getattr(module, "get_routes", None)
            if callable(get_routes_fn):
                self.loaded_plugins[plugin_id].has_routes = True
                try:
                    routes = get_routes_fn(sdk)
                    if routes:
                        self.loaded_plugins[plugin_id].routes = list(routes)
                        logger.debug(f"[plugin-registry] {plugin_id} registered {len(routes)} routes")
                except Exception as e:
                    logger.warning(f"[plugin-registry] {plugin_id} get_routes error: {e}")
            
            # 检查插件是否有效（至少有 register_plugin 或 setup_plugin）
            if not hasattr(module, "register_plugin") and not callable(setup_fn):
                logger.warning(f"[plugin-registry] {plugin_id}: no register_plugin or setup_plugin")
                del self.loaded_plugins[plugin_id]
                await set_plugin_status(
                    session, plugin.id, PluginStatus.BROKEN,
                    "Missing register_plugin or setup_plugin function"
                )
                return False
            
            logger.info(f"[plugin-registry] Loaded: {plugin_id} v{plugin.version}")
            
            # 发布插件加载完成事件
            await publish_event(
                EventType.PLUGIN_LOADED,
                {
                    "plugin_id": plugin_id,
                    "plugin_name": plugin.display_name,
                    "version": plugin.version,
                },
                source="plugin_registry"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[plugin-registry] Failed to load {plugin_id}: {e}", exc_info=True)
            
            # 清理
            if plugin_id in self.loaded_plugins:
                del self.loaded_plugins[plugin_id]
            
            # 标记为 BROKEN
            await set_plugin_status(
                session, plugin.id, PluginStatus.BROKEN,
                str(e)[:500]
            )
            return False
    
    async def reload_plugin(self, session: AsyncSession, plugin: Plugin) -> bool:
        """
        重新加载插件
        
        PLUGIN-SDK-1：正确清理 SDK 资源和事件订阅
        
        Args:
            session: 数据库会话
            plugin: 插件对象
            
        Returns:
            是否加载成功
        """
        plugin_id = plugin.name
        
        # 先卸载
        await self._unload_plugin(plugin_id)
        
        # 重新加载
        if plugin.status == PluginStatus.ENABLED:
            return await self._load_plugin(session, plugin)
        
        return True
    
    async def _unload_plugin(self, plugin_id: str) -> None:
        """
        卸载插件，清理资源
        
        PLUGIN-SDK-1：清理 SDK 实例和事件订阅
        
        Args:
            plugin_id: 插件 ID
        """
        from app.plugin_sdk.api import unregister_sdk_instance
        from app.plugin_sdk.events import get_event_bus, EventType, publish_event
        
        if plugin_id not in self.loaded_plugins:
            return
        
        loaded = self.loaded_plugins[plugin_id]
        
        # 发布卸载事件
        await publish_event(
            EventType.PLUGIN_UNLOADING,
            {
                "plugin_id": plugin_id,
                "plugin_name": loaded.plugin.display_name,
            },
            source="plugin_registry"
        )
        
        # 清理事件订阅
        event_bus = get_event_bus()
        event_bus.unsubscribe_all_from_source(plugin_id)
        
        # 清理 SDK 资源
        if loaded.sdk:
            try:
                await loaded.sdk.cleanup()
            except Exception as e:
                logger.warning(f"[plugin-registry] SDK cleanup error for {plugin_id}: {e}")
        
        # 注销 SDK 实例
        unregister_sdk_instance(plugin_id)
        
        # 移除插件
        del self.loaded_plugins[plugin_id]
        logger.info(f"[plugin-registry] Unloaded: {plugin_id}")
    
    def get_plugin_sdk(self, plugin_id: str) -> Optional[Any]:
        """
        获取插件的 SDK 实例
        
        Args:
            plugin_id: 插件 ID
            
        Returns:
            VabHubSDK 实例或 None
        """
        loaded = self.loaded_plugins.get(plugin_id)
        return loaded.sdk if loaded else None


# ============== 全局单例 ==============

_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """获取插件注册表单例"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


# ============== 初始化工具函数 ==============

async def init_plugins_for_process(session: AsyncSession) -> None:
    """
    为当前进程初始化插件
    
    在 FastAPI 启动或 Runner 进程中调用
    """
    from app.core.config import settings
    from app.services.plugin_service import scan_plugins_from_filesystem
    
    registry = get_plugin_registry()
    
    # 可选：自动扫描
    if settings.PLUGINS_AUTO_SCAN:
        await scan_plugins_from_filesystem(session)
    
    # 可选：自动加载
    if settings.PLUGINS_AUTO_LOAD:
        await registry.load_enabled_plugins(session)
