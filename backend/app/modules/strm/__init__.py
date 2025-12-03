"""
STRM文件生成系统
原生集成STRM功能，提供完整的自动化工作流
"""

from .generator import STRMGenerator
from .subtitle_handler import SubtitleHandler
from .config import STRMConfig, STRMWorkflowConfig
from .file_operation_mode import (
    FileOperationMode,
    MediaLibraryDestination,
    FileOperationConfig,
    STRMSyncConfig,
    get_available_modes,
    validate_operation_mode
)
from .lifecycle_tracker import LifecycleTracker
from .sync_manager import STRMSyncManager
from .file_tree_manager import FileTreeManager
from .task_manager import STRMSyncTaskManager, get_sync_task_manager, SyncTaskStatus

# 待实现的模块
# from .workflow import STRMWorkflowManager
# from .uploader import FileUploader
# from .scraper import MediaScraper
# from .media_server_notifier import MediaServerNotifier
# from .file_tree_manager import FileTreeManager

__all__ = [
    'STRMGenerator',
    'SubtitleHandler',
    'STRMConfig',
    'STRMWorkflowConfig',
    'FileOperationMode',
    'MediaLibraryDestination',
    'FileOperationConfig',
    'STRMSyncConfig',
    'get_available_modes',
    'validate_operation_mode',
    'LifecycleTracker',
    'STRMSyncManager',
    'FileTreeManager',
    'STRMSyncTaskManager',
    'get_sync_task_manager',
    'SyncTaskStatus',
]

