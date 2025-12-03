"""
插件热更新管理器
支持文件监控、自动重载、状态管理
"""

import asyncio
import importlib
import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

from fastapi import APIRouter
from loguru import logger
from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from app.core.plugins.config_store import PluginConfigStore
from app.core.plugins.graphql_builder import GraphQLSchemaBuilder
from app.core.plugins.spec import (
    PluginContext,
    PluginHooks,
    PluginMetadata,
    metadata_from_object,
)


class PluginFileHandler(FileSystemEventHandler):
    """插件文件变化处理器"""
    
    def __init__(self, manager: 'HotReloadManager'):
        self.manager = manager
        self.debounce_time = 1.0  # 防抖时间（秒）
        self.pending_reloads: Dict[str, asyncio.Task] = {}
    
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
        
        if event.src_path.endswith('.py'):
            self._schedule_reload(event.src_path)
    
    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
        
        if event.src_path.endswith('.py'):
            self._schedule_reload(event.src_path)
    
    def on_deleted(self, event):
        """文件删除事件"""
        if event.is_directory:
            return
        
        if event.src_path.endswith('.py'):
            self._handle_file_deleted(event.src_path)
    
    def _schedule_reload(self, file_path: str):
        """调度重载（防抖）"""
        plugin_name = self.manager._get_plugin_name_from_path(file_path)
        if not plugin_name:
            return
        
        # 取消之前的重载任务
        if plugin_name in self.pending_reloads:
            self.pending_reloads[plugin_name].cancel()
        
        # 创建新的重载任务
        async def delayed_reload():
            await asyncio.sleep(self.debounce_time)
            await self.manager.reload_plugin(plugin_name)
        
        task = asyncio.create_task(delayed_reload())
        self.pending_reloads[plugin_name] = task
    
    def _handle_file_deleted(self, file_path: str):
        """处理文件删除"""
        plugin_name = self.manager._get_plugin_name_from_path(file_path)
        if plugin_name:
            asyncio.create_task(self.manager.unload_plugin(plugin_name))


class HotReloadManager:
    """插件热更新管理器"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        """
        初始化热更新管理器
        
        Args:
            plugins_dir: 插件目录路径
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.hot_reload_enabled = True
        self.loaded_plugins: Dict[str, Any] = {}
        self.plugin_states: Dict[str, Dict[str, Any]] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_hooks: Dict[str, PluginHooks] = {}
        self.plugin_contexts: Dict[str, PluginContext] = {}
        self.plugin_rest_routers: Dict[str, APIRouter] = {}
        self.plugin_graphql_mixins: Dict[str, Dict[str, Any]] = {}
        self.observer: Optional[Observer] = None
        self.event_handler = PluginFileHandler(self)
        
        # 加载现有插件
        self._load_all_plugins()
    
    def _get_plugin_name_from_path(self, file_path: str) -> Optional[str]:
        """从文件路径获取插件名称"""
        try:
            path = Path(file_path)
            if path.parent == self.plugins_dir:
                return path.stem
            return None
        except Exception:
            return None
    
    def _load_all_plugins(self):
        """加载所有插件"""
        if not self.plugins_dir.exists():
            logger.warning(f"插件目录不存在: {self.plugins_dir}")
            return
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            plugin_name = plugin_file.stem
            try:
                self._load_plugin(plugin_name)
            except Exception as e:
                logger.error(f"加载插件 {plugin_name} 失败: {e}")
    
    def _load_plugin(self, plugin_name: str) -> bool:
        """
        加载插件
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            是否加载成功
        """
        try:
            # 如果插件已加载，先卸载
            if plugin_name in self.loaded_plugins:
                self._unload_plugin(plugin_name)
            self.plugin_rest_routers.pop(plugin_name, None)
            self.plugin_graphql_mixins.pop(plugin_name, None)
            
            # 构建模块路径
            module_path = f"plugins.{plugin_name}"
            
            # 如果模块已在sys.modules中，先移除
            if module_path in sys.modules:
                del sys.modules[module_path]
            
            # 动态导入插件
            spec = importlib.util.spec_from_file_location(
                module_path,
                self.plugins_dir / f"{plugin_name}.py"
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"无法创建插件 {plugin_name} 的模块规范")
                return False
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path] = module
            spec.loader.exec_module(module)
            
            metadata = metadata_from_object(getattr(module, "PLUGIN_METADATA", None))

            context = PluginContext(plugin_name)
            hooks: Optional[PluginHooks] = None
            if hasattr(module, "register"):
                register_fn = getattr(module, "register")
                hooks = register_fn(context) or PluginHooks()
                if hooks.on_startup:
                    try:
                        hooks.on_startup(context)
                    except Exception as startup_exc:
                        logger.error(f"插件 {plugin_name} on_startup 失败: {startup_exc}")
                        raise

            # 保存插件模块
            self.loaded_plugins[plugin_name] = module
            self.plugin_metadata[plugin_name] = metadata
            self.plugin_contexts[plugin_name] = context
            if hooks:
                self.plugin_hooks[plugin_name] = hooks
                if hooks.register_rest:
                    router = APIRouter()
                    try:
                        hooks.register_rest(router)
                        self.plugin_rest_routers[plugin_name] = router
                    except Exception as rest_exc:
                        logger.error(f"插件 {plugin_name} register_rest 失败: {rest_exc}")
                else:
                    self.plugin_rest_routers.pop(plugin_name, None)

                if hooks.register_graphql:
                    builder = GraphQLSchemaBuilder(plugin_name)
                    try:
                        hooks.register_graphql(builder)
                        payload = builder.dump()
                        if payload["query"] or payload["mutation"]:
                            self.plugin_graphql_mixins[plugin_name] = payload
                        else:
                            self.plugin_graphql_mixins.pop(plugin_name, None)
                    except Exception as gql_exc:
                        logger.error(f"插件 {plugin_name} register_graphql 失败: {gql_exc}")
                else:
                    self.plugin_graphql_mixins.pop(plugin_name, None)
            
            # 更新插件状态
            self.plugin_states[plugin_name] = {
                "status": "loaded",
                "loaded_at": datetime.now().isoformat(),
                "reload_count": self.plugin_states.get(plugin_name, {}).get("reload_count", 0),
                "last_error": None,
                "metadata": metadata.__dict__,
            }
            
            logger.info(f"插件 {plugin_name} 加载成功")
            return True
            
        except Exception as e:
            logger.error(f"加载插件 {plugin_name} 失败: {e}")
            self.plugin_states[plugin_name] = {
                "status": "error",
                "loaded_at": None,
                "reload_count": self.plugin_states.get(plugin_name, {}).get("reload_count", 0),
                "last_error": str(e)
            }
            return False
    
    def _unload_plugin(self, plugin_name: str):
        """卸载插件"""
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
        
        module_path = f"plugins.{plugin_name}"
        if module_path in sys.modules:
            del sys.modules[module_path]

        context = self.plugin_contexts.get(plugin_name)
        if plugin_name in self.plugin_hooks:
            hooks = self.plugin_hooks.pop(plugin_name)
            if hooks.on_shutdown and context:
                try:
                    hooks.on_shutdown(context)
                except Exception as exc:  # pragma: no cover
                    logger.warning(f"插件 {plugin_name} on_shutdown 失败: {exc}")
        if plugin_name in self.plugin_contexts:
            self.plugin_contexts.pop(plugin_name, None)
        self.plugin_rest_routers.pop(plugin_name, None)
        self.plugin_graphql_mixins.pop(plugin_name, None)

        logger.info(f"插件 {plugin_name} 已卸载")
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        重载插件
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            是否重载成功
        """
        if not self.hot_reload_enabled:
            logger.warning("热更新已禁用")
            return False
        
        logger.info(f"开始重载插件 {plugin_name}")
        
        # 更新重载计数
        if plugin_name in self.plugin_states:
            self.plugin_states[plugin_name]["reload_count"] = \
                self.plugin_states[plugin_name].get("reload_count", 0) + 1
        
        # 在后台线程中执行重载
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, self._load_plugin, plugin_name)
        
        if success:
            logger.info(f"插件 {plugin_name} 重载成功")
        else:
            logger.error(f"插件 {plugin_name} 重载失败")
        
        return success
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            是否卸载成功
        """
        try:
            self._unload_plugin(plugin_name)
            
            if plugin_name in self.plugin_states:
                self.plugin_states[plugin_name]["status"] = "unloaded"
            
            return True
        except Exception as e:
            logger.error(f"卸载插件 {plugin_name} 失败: {e}")
            return False
    
    def start_watching(self):
        """开始监控插件目录"""
        if self.observer is not None:
            logger.warning("文件监控已启动")
            return
        
        if not self.hot_reload_enabled:
            logger.info("热更新已禁用，不启动文件监控")
            return
        
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.plugins_dir),
            recursive=False
        )
        self.observer.start()
        logger.info(f"开始监控插件目录: {self.plugins_dir}")
    
    def stop_watching(self):
        """停止监控插件目录"""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("已停止监控插件目录")
    
    def get_all_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有插件状态"""
        return self.plugin_states.copy()
    
    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件状态"""
        return self.plugin_states.get(plugin_name)

    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        return self.plugin_metadata.get(plugin_name)

    def get_config_store(self, plugin_name: str) -> Optional[PluginConfigStore]:
        context = self.plugin_contexts.get(plugin_name)
        if context:
            return context.config
        return None
    
    def get_rest_routers(self) -> Dict[str, APIRouter]:
        return self.plugin_rest_routers.copy()

    def get_graphql_mixins(self) -> Dict[str, Dict[str, Any]]:
        return self.plugin_graphql_mixins.copy()
    
    def enable_hot_reload(self):
        """启用热更新"""
        self.hot_reload_enabled = True
        if self.observer is None:
            self.start_watching()
        logger.info("热更新已启用")
    
    def disable_hot_reload(self):
        """禁用热更新"""
        self.hot_reload_enabled = False
        self.stop_watching()
        logger.info("热更新已禁用")


# 全局热更新管理器实例
_hot_reload_manager: Optional[HotReloadManager] = None


def get_hot_reload_manager() -> HotReloadManager:
    """获取热更新管理器实例（单例模式）"""
    global _hot_reload_manager
    if _hot_reload_manager is None:
        _hot_reload_manager = HotReloadManager()
    return _hot_reload_manager
