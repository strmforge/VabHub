"""
云存储模块
支持115网盘、RClone和OpenList
"""

from app.core.cloud_storage.providers.base import (
    CloudStorageProvider,
    CloudFileInfo,
    CloudStorageUsage
)
from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
from app.core.cloud_storage.providers.rclone import RCloneProvider
from app.core.cloud_storage.providers.openlist import OpenListProvider
from app.core.cloud_storage.schemas import (
    FileItem,
    StorageUsage,
    StorageConfig,
    TransferInfo,
    cloud_file_info_to_file_item,
    file_item_to_cloud_file_info,
    cloud_storage_usage_to_storage_usage
)
from app.core.cloud_storage.manager import (
    StorageProviderManager,
    get_storage_provider_manager,
    register_storage_provider,
    get_storage_provider,
    list_storage_providers
)

__all__ = [
    # 基类
    "CloudStorageProvider",
    "CloudFileInfo",
    "CloudStorageUsage",
    # Provider实现
    "Cloud115Provider",
    "RCloneProvider",
    "OpenListProvider",
    # 数据模型
    "FileItem",
    "StorageUsage",
    "StorageConfig",
    "TransferInfo",
    # 模型转换工具
    "cloud_file_info_to_file_item",
    "file_item_to_cloud_file_info",
    "cloud_storage_usage_to_storage_usage",
    # Provider管理器
    "StorageProviderManager",
    "get_storage_provider_manager",
    "register_storage_provider",
    "get_storage_provider",
    "list_storage_providers",
]

