"""
目录监控服务
文件系统实时监控
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog未安装，目录监控功能不可用。请安装: pip install watchdog")

from app.models.directory import Directory
from app.schemas.directory import DirectoryConfig
from app.modules.file_operation.transfer_service import TransferService


class DirectoryMonitorHandler(FileSystemEventHandler):
    """目录监控事件处理器"""
    
    def __init__(self, db: AsyncSession, directory_config: DirectoryConfig):
        self.db = db
        self.directory_config = directory_config
        self.transfer_service = TransferService(db)
        self._processing_files = set()  # 正在处理的文件集合，避免重复处理
    
    def on_created(self, event: FileSystemEvent):
        """文件/目录创建事件"""
        if event.is_directory:
            return
        asyncio.create_task(self._handle_file_event(event.src_path, "created"))
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if event.is_directory:
            return
        asyncio.create_task(self._handle_file_event(event.src_path, "modified"))
    
    async def _handle_file_event(self, file_path: str, event_type: str):
        """处理文件事件"""
        try:
            # 避免重复处理
            if file_path in self._processing_files:
                return
            
            self._processing_files.add(file_path)
            
            # 等待文件写入完成（避免文件还在下载中就被处理）
            await asyncio.sleep(5)
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                self._processing_files.discard(file_path)
                return
            
            # 检查文件大小是否稳定（避免文件还在下载中）
            initial_size = file_path_obj.stat().st_size
            await asyncio.sleep(2)
            if file_path_obj.exists():
                current_size = file_path_obj.stat().st_size
                if current_size != initial_size:
                    # 文件还在变化，跳过
                    self._processing_files.discard(file_path)
                    return
            
            logger.info(f"目录监控检测到文件{event_type}: {file_path}")
            
            # 调用文件整理服务
            result = await self.transfer_service.transfer_directory(
                source_dir=str(file_path_obj.parent),
                directory_config=self.directory_config,
                media_info=None,  # 目录监控时没有媒体信息，需要识别
                overwrite_mode="never"
            )
            
            if result.get("success"):
                logger.info(f"目录监控整理成功: {file_path}")
            else:
                logger.error(f"目录监控整理失败: {file_path} - {result.get('error')}")
            
            self._processing_files.discard(file_path)
            
        except Exception as e:
            logger.error(f"处理文件事件异常: {e}", exc_info=True)
            self._processing_files.discard(file_path)


class DirectoryMonitor:
    """目录监控服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._observers: List[Observer] = []
        self._running = False
    
    async def start(self):
        """启动目录监控"""
        if not WATCHDOG_AVAILABLE:
            logger.error("watchdog未安装，无法启动目录监控")
            return
        
        if self._running:
            logger.warning("目录监控已在运行")
            return
        
        try:
            # 获取目录监控配置
            monitor_dirs = await self._get_directory_monitor_dirs()
            if not monitor_dirs:
                logger.info("没有配置目录监控目录，跳过启动")
                return
            
            logger.info(f"启动目录监控，监控目录数: {len(monitor_dirs)}")
            
            # 为每个目录创建监控
            for dir_config in monitor_dirs:
                try:
                    await self._start_monitor(dir_config)
                except Exception as e:
                    logger.error(f"启动目录监控失败: {dir_config.download_path} - {e}", exc_info=True)
            
            self._running = True
            logger.info("目录监控启动完成")
            
        except Exception as e:
            logger.error(f"启动目录监控异常: {e}", exc_info=True)
    
    async def stop(self):
        """停止目录监控"""
        if not self._running:
            return
        
        try:
            for observer in self._observers:
                observer.stop()
                observer.join()
            
            self._observers.clear()
            self._running = False
            logger.info("目录监控已停止")
            
        except Exception as e:
            logger.error(f"停止目录监控异常: {e}", exc_info=True)
    
    async def _start_monitor(self, directory_config: DirectoryConfig):
        """启动单个目录的监控"""
        if not directory_config.download_path:
            return
        
        try:
            monitor_path = Path(directory_config.download_path)
            if not monitor_path.exists():
                logger.warning(f"监控目录不存在: {monitor_path}")
                return
            
            # 创建事件处理器
            event_handler = DirectoryMonitorHandler(self.db, directory_config)
            
            # 创建观察者
            observer = Observer()
            observer.schedule(event_handler, str(monitor_path), recursive=True)
            observer.start()
            
            self._observers.append(observer)
            logger.info(f"目录监控已启动: {monitor_path}")
            
        except Exception as e:
            logger.error(f"启动目录监控失败: {directory_config.download_path} - {e}", exc_info=True)
            raise
    
    async def _get_directory_monitor_dirs(self) -> List[DirectoryConfig]:
        """获取目录监控配置"""
        try:
            result = await self.db.execute(
                select(Directory).where(
                    Directory.monitor_type == "directory",
                    Directory.enabled == True,
                    Directory.storage == "local"
                ).order_by(Directory.priority)
            )
            directories = result.scalars().all()
            
            return [
                DirectoryConfig(
                    download_path=dir.download_path,
                    library_path=dir.library_path,
                    storage=dir.storage,
                    library_storage=dir.library_storage,
                    monitor_type=dir.monitor_type,
                    transfer_type=dir.transfer_type,
                    media_type=dir.media_type,
                    media_category=dir.media_category,
                    priority=dir.priority,
                    enabled=dir.enabled
                )
                for dir in directories
            ]
        except Exception as e:
            logger.error(f"获取目录监控配置失败: {e}")
            return []

