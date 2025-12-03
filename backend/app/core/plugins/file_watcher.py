"""
插件文件监控
使用watchdog监控插件文件变化
"""

import asyncio
import time
from pathlib import Path
from typing import Callable, Optional, Dict
from loguru import logger

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not available, plugin hot reload will be disabled")


class PluginFileEventHandler(FileSystemEventHandler):
    """插件文件事件处理器"""
    
    def __init__(
        self,
        plugins_dir: str,
        on_file_changed: Callable[[str], None],
        debounce_seconds: float = 2.0
    ):
        """
        初始化事件处理器
        
        Args:
            plugins_dir: 插件目录
            on_file_changed: 文件变化回调函数
            debounce_seconds: 防抖时间（秒）
        """
        self.plugins_dir = Path(plugins_dir)
        self.on_file_changed = on_file_changed
        self.debounce_seconds = debounce_seconds
        self.last_modified: Dict[str, float] = {}
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # 只处理Python文件
        if not file_path.suffix == '.py':
            return
        
        # 跳过__pycache__目录
        if '__pycache__' in file_path.parts:
            return
        
        # 检查文件是否在插件目录中
        try:
            file_path.relative_to(self.plugins_dir)
        except ValueError:
            return
        
        # 防抖处理
        current_time = time.time()
        last_time = self.last_modified.get(str(file_path), 0)
        
        if current_time - last_time < self.debounce_seconds:
            return
        
        self.last_modified[str(file_path)] = current_time
        
        # 调用回调函数
        try:
            self.on_file_changed(str(file_path))
        except Exception as e:
            logger.error(f"处理文件变化失败 {file_path}: {e}")
    
    def on_created(self, event: FileSystemEvent):
        """文件创建事件"""
        self.on_modified(event)
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # 只处理Python文件
        if not file_path.suffix == '.py':
            return
        
        # 检查文件是否在插件目录中
        try:
            file_path.relative_to(self.plugins_dir)
        except ValueError:
            return
        
        # 调用回调函数（文件删除）
        try:
            self.on_file_changed(str(file_path), deleted=True)
        except Exception as e:
            logger.error(f"处理文件删除失败 {file_path}: {e}")


class PluginFileWatcher:
    """插件文件监控器"""
    
    def __init__(
        self,
        plugins_dir: str,
        on_file_changed: Callable[[str], None],
        debounce_seconds: float = 2.0
    ):
        """
        初始化文件监控器
        
        Args:
            plugins_dir: 插件目录
            on_file_changed: 文件变化回调函数
            debounce_seconds: 防抖时间（秒）
        """
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog is not installed, cannot use file watcher")
        
        self.plugins_dir = Path(plugins_dir)
        self.on_file_changed = on_file_changed
        self.debounce_seconds = debounce_seconds
        
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[PluginFileEventHandler] = None
        self.running = False
    
    def start(self):
        """启动文件监控"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog not available, file watcher not started")
            return
        
        if self.running:
            logger.warning("File watcher is already running")
            return
        
        # 确保插件目录存在
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建事件处理器
        self.event_handler = PluginFileEventHandler(
            plugins_dir=str(self.plugins_dir),
            on_file_changed=self.on_file_changed,
            debounce_seconds=self.debounce_seconds
        )
        
        # 创建观察者
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.plugins_dir),
            recursive=True
        )
        
        # 启动观察者
        self.observer.start()
        self.running = True
        
        logger.info(f"Plugin file watcher started: {self.plugins_dir}")
    
    def stop(self):
        """停止文件监控"""
        if not self.running:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None
        
        self.running = False
        logger.info("Plugin file watcher stopped")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.running

