"""
文件浏览器服务
支持本地和云存储的文件浏览和操作
"""

import os
import stat
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cloud_storage.service import CloudStorageService
from app.core.cloud_storage.providers.base import CloudFileInfo


class FileBrowserService:
    """文件浏览器服务"""
    
    # 支持的媒体文件扩展名
    MEDIA_EXTENSIONS = {
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v',
        '.mp3', '.flac', '.ape', '.wav', '.aac', '.ogg', '.wma',
        '.srt', '.ass', '.ssa', '.vtt', '.sub', '.idx'
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cloud_storage_service = CloudStorageService(db)
    
    async def list_files(
        self,
        storage: str,
        path: str = "/",
        recursion: bool = False,
        sort: str = "name"
    ) -> List[Dict[str, Any]]:
        """
        列出文件和目录
        
        Args:
            storage: 存储类型 (local, 115, rclone, openlist)
            path: 路径
            recursion: 是否递归
            sort: 排序方式 (name, size, time)
        
        Returns:
            文件列表
        """
        try:
            if storage == "local":
                return await self._list_local_files(path, recursion, sort)
            else:
                return await self._list_cloud_files(storage, path, recursion, sort)
        except Exception as e:
            logger.error(f"列出文件失败: {storage}:{path} - {e}")
            return []
    
    async def _list_local_files(
        self,
        path: str,
        recursion: bool,
        sort: str
    ) -> List[Dict[str, Any]]:
        """列出本地文件"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return []
            
            items = []
            
            if path_obj.is_file():
                # 如果是文件，返回文件信息
                items.append(self._file_info_to_dict(path_obj))
            else:
                # 如果是目录，列出目录内容
                if recursion:
                    # 递归列出所有文件
                    for item in path_obj.rglob('*'):
                        if item.is_file() or item.is_dir():
                            items.append(self._file_info_to_dict(item, base_path=path_obj))
                else:
                    # 只列出当前目录
                    for item in path_obj.iterdir():
                        items.append(self._file_info_to_dict(item, base_path=path_obj))
            
            # 排序
            items = self._sort_items(items, sort)
            
            return items
            
        except Exception as e:
            logger.error(f"列出本地文件失败: {path} - {e}")
            return []
    
    def _file_info_to_dict(
        self,
        path: Path,
        base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """将文件信息转换为字典"""
        try:
            stat_info = path.stat()
            
            # 计算相对路径
            if base_path:
                try:
                    relative_path = str(path.relative_to(base_path))
                except ValueError:
                    relative_path = str(path)
            else:
                relative_path = path.name
            
            item = {
                "storage": "local",
                "type": "file" if path.is_file() else "dir",
                "path": str(path),
                "name": path.name,
                "basename": path.stem,
                "extension": path.suffix.lower() if path.is_file() else None,
                "size": stat_info.st_size if path.is_file() else 0,
                "modify_time": stat_info.st_mtime,
                "children": [],
                "fileid": str(path),
                "parent_fileid": str(path.parent) if path.parent != path else None,
                "thumbnail": None,
                "is_media": path.suffix.lower() in self.MEDIA_EXTENSIONS if path.is_file() else False
            }
            
            return item
            
        except Exception as e:
            logger.error(f"转换文件信息失败: {path} - {e}")
            return {
                "storage": "local",
                "type": "file",
                "path": str(path),
                "name": path.name,
                "basename": path.stem,
                "extension": path.suffix.lower() if path.is_file() else None,
                "size": 0,
                "modify_time": 0,
                "children": [],
                "fileid": str(path),
                "parent_fileid": None,
                "thumbnail": None,
                "is_media": False
            }
    
    def _sort_items(self, items: List[Dict[str, Any]], sort: str) -> List[Dict[str, Any]]:
        """排序文件列表"""
        if sort == "name":
            return sorted(items, key=lambda x: (x["type"] == "file", x["name"].lower()))
        elif sort == "size":
            return sorted(items, key=lambda x: (x["type"] == "file", -x["size"]))
        elif sort == "time":
            return sorted(items, key=lambda x: (x["type"] == "file", -x["modify_time"]))
        else:
            return items
    
    async def _list_cloud_files(
        self,
        storage: str,
        path: str,
        recursion: bool,
        sort: str
    ) -> List[Dict[str, Any]]:
        """列出云存储文件"""
        try:
            # 获取云存储配置
            storages = await self.cloud_storage_service.list_storages(provider=storage)
            if not storages:
                logger.warning(f"未找到云存储配置: {storage}")
                return []
            
            storage_config = storages[0]
            
            # 使用CloudStorageService的list_files方法
            file_items = await self.cloud_storage_service.list_files(
                storage_config.id,
                path=path,
                recursive=recursion
            )
            
            # 转换为统一格式
            items = []
            for file_item in file_items:
                is_file = file_item.get("type") == "file"
                file_name = file_item.get("name", "")
                
                item = {
                    "storage": storage,
                    "type": "file" if is_file else "dir",
                    "path": file_item.get("path", ""),
                    "name": file_name,
                    "basename": Path(file_name).stem if is_file else file_name,
                    "extension": Path(file_name).suffix.lower() if is_file else None,
                    "size": file_item.get("size", 0),
                    "modify_time": self._parse_datetime(file_item.get("modified_at")),
                    "children": [],
                    "fileid": file_item.get("id") or file_item.get("path", ""),
                    "parent_fileid": file_item.get("parent_id"),
                    "thumbnail": file_item.get("thumbnail"),
                    "pickcode": file_item.get("metadata", {}).get("pickcode"),
                    "drive_id": file_item.get("metadata", {}).get("drive_id"),
                    "url": file_item.get("download_url"),
                    "is_media": Path(file_name).suffix.lower() in self.MEDIA_EXTENSIONS if is_file else False
                }
                items.append(item)
            
            # 排序
            items = self._sort_items(items, sort)
            
            return items
            
        except Exception as e:
            logger.error(f"列出云存储文件失败: {storage}:{path} - {e}")
            return []
    
    def _parse_datetime(self, dt_str: Optional[str]) -> float:
        """解析ISO格式的日期时间字符串为时间戳"""
        if not dt_str:
            return 0.0
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.timestamp()
        except Exception:
            return 0.0
    
    async def get_file_item(
        self,
        storage: str,
        path: str
    ) -> Optional[Dict[str, Any]]:
        """获取文件项"""
        try:
            if storage == "local":
                path_obj = Path(path)
                if not path_obj.exists():
                    return None
                return self._file_info_to_dict(path_obj)
            else:
                # 云存储：先列出父目录，然后查找匹配的文件
                path_obj = Path(path)
                parent_path = str(path_obj.parent) if path_obj.parent != path_obj else "/"
                
                # 列出父目录文件
                items = await self._list_cloud_files(storage, parent_path, False, "name")
                
                # 查找匹配的文件
                for item in items:
                    if item.get("path") == path or item.get("name") == path_obj.name:
                        return item
                
                return None
        except Exception as e:
            logger.error(f"获取文件项失败: {storage}:{path} - {e}")
            return None
    
    async def create_folder(
        self,
        storage: str,
        path: str,
        name: str
    ) -> Optional[Dict[str, Any]]:
        """创建目录"""
        try:
            if storage == "local":
                new_path = Path(path) / name
                new_path.mkdir(parents=True, exist_ok=True)
                return self._file_info_to_dict(new_path)
            else:
                # 云存储：使用CloudStorageService的方法
                storages = await self.cloud_storage_service.list_storages(provider=storage)
                if not storages:
                    return None
                
                storage_config = storages[0]
                
                # 初始化provider
                if not await self.cloud_storage_service.initialize_provider(storage_config.id):
                    return None
                
                # 获取provider并创建目录
                provider = self.cloud_storage_service._get_provider(storage_config)
                if not provider:
                    return None
                
                result = await provider.create_folder(path, name)
                if result:
                    return await self.get_file_item(storage, result.path)
                return None
        except Exception as e:
            logger.error(f"创建目录失败: {storage}:{path}/{name} - {e}")
            return None
    
    async def rename_file(
        self,
        storage: str,
        path: str,
        new_name: str
    ) -> bool:
        """重命名文件或目录"""
        try:
            if storage == "local":
                path_obj = Path(path)
                if not path_obj.exists():
                    return False
                
                new_path = path_obj.parent / new_name
                path_obj.rename(new_path)
                return True
            else:
                # 云存储：需要先获取文件ID
                file_item = await self.get_file_item(storage, path)
                if not file_item:
                    return False
                
                storages = await self.cloud_storage_service.list_storages(provider=storage)
                if not storages:
                    return False
                
                storage_config = storages[0]
                
                # 初始化provider
                if not await self.cloud_storage_service.initialize_provider(storage_config.id):
                    return False
                
                provider = self.cloud_storage_service._get_provider(storage_config)
                if not provider:
                    return False
                
                # 使用文件ID重命名
                file_id = file_item.get("fileid")
                if not file_id:
                    return False
                
                # 检查provider是否支持rename_file方法
                if hasattr(provider, 'rename_file'):
                    return await provider.rename_file(file_id, new_name)
                else:
                    logger.warning(f"Provider {storage} 不支持重命名操作")
                    return False
        except Exception as e:
            logger.error(f"重命名文件失败: {storage}:{path} -> {new_name} - {e}")
            return False
    
    async def delete_file(
        self,
        storage: str,
        path: str
    ) -> bool:
        """删除文件或目录"""
        try:
            if storage == "local":
                path_obj = Path(path)
                if not path_obj.exists():
                    return False
                
                if path_obj.is_file():
                    path_obj.unlink()
                else:
                    import shutil
                    shutil.rmtree(path_obj)
                return True
            else:
                # 云存储：需要先获取文件ID
                file_item = await self.get_file_item(storage, path)
                if not file_item:
                    return False
                
                storages = await self.cloud_storage_service.list_storages(provider=storage)
                if not storages:
                    return False
                
                storage_config = storages[0]
                
                # 初始化provider
                if not await self.cloud_storage_service.initialize_provider(storage_config.id):
                    return False
                
                provider = self.cloud_storage_service._get_provider(storage_config)
                if not provider:
                    return False
                
                # 使用文件ID删除
                file_id = file_item.get("fileid")
                if not file_id:
                    return False
                
                return await provider.delete_file(file_id)
        except Exception as e:
            logger.error(f"删除文件失败: {storage}:{path} - {e}")
            return False
    
    async def get_storage_usage(
        self,
        storage: str
    ) -> Optional[Dict[str, Any]]:
        """获取存储使用情况"""
        try:
            if storage == "local":
                # 获取本地磁盘使用情况
                import shutil
                # Windows系统使用C盘，Linux使用根目录
                import platform
                if platform.system() == "Windows":
                    total, used, free = shutil.disk_usage("C:\\")
                else:
                    total, used, free = shutil.disk_usage("/")
                return {
                    "total": total,
                    "used": used,
                    "available": free,
                    "usage_percent": (used / total) * 100 if total > 0 else 0
                }
            else:
                # 云存储：使用CloudStorageService的方法
                storages = await self.cloud_storage_service.list_storages(provider=storage)
                if not storages:
                    return None
                
                storage_config = storages[0]
                usage = await self.cloud_storage_service.get_storage_usage(storage_config.id)
                if usage:
                    return {
                        "total": usage.get("total", 0),
                        "used": usage.get("used", 0),
                        "available": usage.get("available", 0),
                        "usage_percent": usage.get("percentage", 0)
                    }
                return None
        except Exception as e:
            logger.error(f"获取存储使用情况失败: {storage} - {e}")
            return None
    
    async def get_supported_transfer_types(
        self,
        storage: str
    ) -> Dict[str, str]:
        """获取支持的传输类型"""
        try:
            if storage == "local":
                return {
                    "copy": "复制",
                    "move": "移动",
                    "link": "硬链接",
                    "softlink": "软链接"
                }
            else:
                # 云存储
                storages = await self.cloud_storage_service.list_storages(provider=storage)
                if not storages:
                    return {}
                
                storage_config = storages[0]
                
                # 初始化provider
                if not await self.cloud_storage_service.initialize_provider(storage_config.id):
                    return {}
                
                provider = self.cloud_storage_service._get_provider(storage_config)
                if not provider:
                    return {}
                
                # 获取支持的传输类型
                if hasattr(provider, 'support_transtype'):
                    return provider.support_transtype()
                elif hasattr(provider, 'transtype'):
                    return provider.transtype
                else:
                    return {}
        except Exception as e:
            logger.error(f"获取支持的传输类型失败: {storage} - {e}")
            return {}

