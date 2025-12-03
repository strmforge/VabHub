"""
文件操作覆盖模式处理器
支持never、always、size、latest四种覆盖模式
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.constants.media_types import is_tv_like
from app.modules.media_renamer.parser import FilenameParser, MediaInfo


class OverwriteMode(str, Enum):
    """覆盖模式"""
    NEVER = "never"  # 从不覆盖
    ALWAYS = "always"  # 总是覆盖
    SIZE = "size"  # 按文件大小覆盖（大覆盖小）
    LATEST = "latest"  # 仅保留最新版本


class OverwriteHandler:
    """覆盖模式处理器"""
    
    # 媒体文件扩展名（用于识别版本文件）
    MEDIA_EXTENSIONS = {
        '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        '.m4v', '.mpg', '.mpeg', '.ts', '.m2ts', '.iso', '.vob'
    }
    
    @staticmethod
    async def check_overwrite(
        target_path: Path,
        overwrite_mode: str,
        new_file_size: Optional[int] = None,
        storage_type: str = "local",
        storage_oper: Optional[Any] = None
    ) -> Tuple[bool, str]:
        """
        检查是否应该覆盖现有文件
        
        Args:
            target_path: 目标文件路径
            overwrite_mode: 覆盖模式（never/always/size/latest）
            new_file_size: 新文件大小（字节），用于size模式比较
            storage_type: 存储类型（local/115/123）
            storage_oper: 存储操作对象（用于云存储文件检查）
        
        Returns:
            (是否覆盖, 原因说明)
        """
        # 检查目标文件是否存在
        file_exists = await OverwriteHandler._check_file_exists(
            target_path, storage_type, storage_oper
        )
        
        if not file_exists:
            return True, "目标文件不存在，可以创建"
        
        # 文件已存在，根据覆盖模式决定
        if overwrite_mode == OverwriteMode.NEVER:
            return False, "目标文件已存在，覆盖模式为never，跳过覆盖"
        
        elif overwrite_mode == OverwriteMode.ALWAYS:
            return True, "目标文件已存在，覆盖模式为always，将覆盖"
        
        elif overwrite_mode == OverwriteMode.SIZE:
            if new_file_size is None:
                logger.warning(f"覆盖模式为size，但未提供新文件大小，跳过覆盖: {target_path}")
                return False, "覆盖模式为size，但未提供新文件大小"
            
            # 获取现有文件大小
            existing_size = await OverwriteHandler._get_file_size(
                target_path, storage_type, storage_oper
            )
            
            if existing_size is None:
                logger.warning(f"无法获取现有文件大小，跳过覆盖: {target_path}")
                return False, "无法获取现有文件大小"
            
            # 比较文件大小
            if new_file_size > existing_size:
                return True, f"新文件更大 ({new_file_size} > {existing_size})，将覆盖现有文件"
            else:
                return False, f"现有文件更大或相等 ({existing_size} >= {new_file_size})，跳过覆盖"
        
        elif overwrite_mode == OverwriteMode.LATEST:
            return True, "覆盖模式为latest，将覆盖并删除旧版本文件"
        
        else:
            logger.warning(f"未知的覆盖模式: {overwrite_mode}")
            return False, f"未知的覆盖模式: {overwrite_mode}"
    
    @staticmethod
    async def delete_version_files(
        target_path: Path,
        storage_type: str = "local",
        storage_oper: Optional[Any] = None,
        media_info: Optional[MediaInfo] = None
    ) -> List[str]:
        """
        删除版本文件（latest模式）
        
        功能：删除同一目录下的其他版本文件（例如：movie.mkv, movie.1080p.mkv, movie.720p.mkv等）
        
        Args:
            target_path: 目标文件路径
            storage_type: 存储类型（local/115/123）
            storage_oper: 存储操作对象（用于云存储文件操作）
            media_info: 媒体信息（用于识别季集信息）
        
        Returns:
            删除的文件列表
        """
        deleted_files = []
        
        try:
            # 1. 解析媒体信息
            if not media_info:
                parser = FilenameParser()
                media_info = parser.parse(target_path.name)
            
            if not media_info:
                logger.warning(f"无法解析媒体信息，跳过版本文件删除: {target_path}")
                return deleted_files
            
            # 2. 获取父目录
            parent_dir = target_path.parent
            
            # 3. 获取目录下的所有文件
            files = await OverwriteHandler._list_files(
                parent_dir, storage_type, storage_oper
            )
            
            if not files:
                logger.info(f"目录中没有文件: {parent_dir}")
                return deleted_files
            
            # 4. 识别并删除版本文件
            for file_path, file_info in files:
                # 跳过当前文件
                if file_path == target_path:
                    continue
                
                # 只处理媒体文件
                if not OverwriteHandler._is_media_file(file_path):
                    continue
                
                # 解析文件媒体信息
                if storage_type == "local":
                    parser = FilenameParser()
                    file_media_info = parser.parse(file_path.name)
                else:
                    file_media_info = None
                
                if not file_media_info:
                    continue
                
                # 检查是否是相同媒体（电影：title+year，剧集：title+season+episode）
                if OverwriteHandler._is_same_media(media_info, file_media_info):
                    # 删除版本文件
                    success = await OverwriteHandler._delete_file(
                        file_path, storage_type, storage_oper
                    )
                    
                    if success:
                        deleted_files.append(str(file_path))
                        logger.info(f"删除版本文件: {file_path}")
            
            logger.info(f"版本文件删除完成: 删除了 {len(deleted_files)} 个文件")
            return deleted_files
            
        except Exception as e:
            logger.error(f"删除版本文件失败: {e}", exc_info=True)
            return deleted_files
    
    @staticmethod
    def _is_same_media(media_info1: MediaInfo, media_info2: MediaInfo) -> bool:
        """
        检查是否是相同媒体
        
        Args:
            media_info1: 媒体信息1
            media_info2: 媒体信息2
        
        Returns:
            是否是相同媒体
        """
        # 电影：检查title和year
        if media_info1.media_type == "movie" and media_info2.media_type == "movie":
            return (
                media_info1.title == media_info2.title and
                media_info1.year == media_info2.year
            )
        
        # 剧集：检查title、season和episode
        elif is_tv_like(media_info1.media_type) and is_tv_like(media_info2.media_type):
            return (
                media_info1.title == media_info2.title and
                media_info1.season == media_info2.season and
                media_info1.episode == media_info2.episode
            )
        
        return False
    
    @staticmethod
    def _is_media_file(file_path: Path) -> bool:
        """检查是否是媒体文件"""
        return file_path.suffix.lower() in OverwriteHandler.MEDIA_EXTENSIONS
    
    @staticmethod
    async def _check_file_exists(
        target_path: Path,
        storage_type: str,
        storage_oper: Optional[Any]
    ) -> bool:
        """检查文件是否存在"""
        if storage_type == "local":
            return target_path.exists()
        else:
            # 云存储：使用storage_oper检查
            if storage_oper:
                try:
                    # 这里需要根据实际的storage_oper接口实现
                    # 假设有get_item方法
                    if hasattr(storage_oper, 'get_item'):
                        item = storage_oper.get_item(target_path)
                        return item is not None
                except Exception as e:
                    logger.error(f"检查云存储文件是否存在失败: {e}")
            return False
    
    @staticmethod
    async def _get_file_size(
        target_path: Path,
        storage_type: str,
        storage_oper: Optional[Any]
    ) -> Optional[int]:
        """获取文件大小"""
        if storage_type == "local":
            try:
                return target_path.stat().st_size
            except Exception as e:
                logger.error(f"获取本地文件大小失败: {e}")
                return None
        else:
            # 云存储：使用storage_oper获取文件大小
            if storage_oper:
                try:
                    if hasattr(storage_oper, 'get_item'):
                        item = storage_oper.get_item(target_path)
                        if item and hasattr(item, 'size'):
                            return item.size
                except Exception as e:
                    logger.error(f"获取云存储文件大小失败: {e}")
            return None
    
    @staticmethod
    async def _list_files(
        parent_dir: Path,
        storage_type: str,
        storage_oper: Optional[Any]
    ) -> List[Tuple[Path, Dict[str, Any]]]:
        """列出目录下的所有文件"""
        files = []
        
        if storage_type == "local":
            try:
                for file_path in parent_dir.iterdir():
                    if file_path.is_file():
                        files.append((file_path, {
                            'path': file_path,
                            'name': file_path.name,
                            'size': file_path.stat().st_size
                        }))
            except Exception as e:
                logger.error(f"列出本地目录文件失败: {e}")
        else:
            # 云存储：使用storage_oper列出文件
            if storage_oper:
                try:
                    if hasattr(storage_oper, 'list'):
                        items = storage_oper.list(parent_dir)
                        for item in items:
                            if hasattr(item, 'type') and item.type == "file":
                                files.append((Path(item.path), {
                                    'path': item.path,
                                    'name': item.name,
                                    'size': item.size if hasattr(item, 'size') else 0
                                }))
                except Exception as e:
                    logger.error(f"列出云存储目录文件失败: {e}")
        
        return files
    
    @staticmethod
    async def _delete_file(
        file_path: Path,
        storage_type: str,
        storage_oper: Optional[Any]
    ) -> bool:
        """删除文件"""
        if storage_type == "local":
            try:
                file_path.unlink()
                return True
            except Exception as e:
                logger.error(f"删除本地文件失败: {e}")
                return False
        else:
            # 云存储：使用storage_oper删除文件
            if storage_oper:
                try:
                    if hasattr(storage_oper, 'delete'):
                        # 需要先获取文件项
                        if hasattr(storage_oper, 'get_item'):
                            item = storage_oper.get_item(file_path)
                            if item:
                                storage_oper.delete(item)
                                return True
                except Exception as e:
                    logger.error(f"删除云存储文件失败: {e}")
            return False

