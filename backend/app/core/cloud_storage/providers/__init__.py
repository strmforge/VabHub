"""
云存储提供商
"""

from app.core.cloud_storage.providers.base import CloudStorageProvider
from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
from app.core.cloud_storage.providers.rclone import RCloneProvider
from app.core.cloud_storage.providers.openlist import OpenListProvider

__all__ = [
    "CloudStorageProvider",
    "Cloud115Provider",
    "RCloneProvider",
    "OpenListProvider",
]

