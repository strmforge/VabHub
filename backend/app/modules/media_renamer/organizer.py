"""
媒体文件整理器
自动识别、重命名和整理媒体文件
"""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from app.constants.media_types import is_tv_like
from .classifier import MediaCategory, MediaClassifier
from .identifier import MediaIdentifier
from .nfo_writer import NFOWriter
from .parser import MediaInfo
from .renamer import MediaRenamer


@dataclass
class OrganizeResult:
    """整理结果"""
    original_path: str
    new_path: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    media_info: Optional[MediaInfo] = None


class MediaOrganizer:
    """媒体文件整理器"""
    
    def __init__(self, tmdb_api_key: Optional[str] = None, nfo_format: str = "emby"):
        """
        初始化整理器
        
        Args:
            tmdb_api_key: TMDB API密钥（可选）
            nfo_format: NFO文件格式（emby/jellyfin/plex），默认emby
        """
        self.identifier = MediaIdentifier(tmdb_api_key)
        self.renamer = MediaRenamer()
        self.classifier = MediaClassifier(tmdb_api_key)
        self.nfo_writer = NFOWriter(format=nfo_format)
    
    async def organize_file(
        self,
        file_path: str,
        target_base_dir: str,
        rename_template: Optional[str] = None,
        move_file: bool = True,
        download_subtitle: bool = False,
        subtitle_language: str = "zh",
        use_classification: bool = True,
        write_nfo: bool = True
    ) -> OrganizeResult:
        """
        整理单个媒体文件
        
        Args:
            file_path: 源文件路径
            target_base_dir: 目标基础目录
            rename_template: 重命名模板（可选）
            move_file: 是否移动文件（False则只重命名）
            
        Returns:
            OrganizeResult对象
        """
        try:
            # 1. 识别媒体信息
            media_info = await self.identifier.identify(file_path)
            
            # 2. 生成新文件名
            new_name = self.renamer.generate_name(media_info, template=rename_template)
            
            # 3. 分类媒体（如果启用）
            media_category = None
            if use_classification:
                try:
                    # 查询TMDB数据用于分类
                    tmdb_data = await self.identifier._query_tmdb(media_info)
                    media_category = await self.classifier.classify(media_info, tmdb_data)
                    logger.debug(f"媒体分类: {media_category.category}, 子分类: {media_category.subcategory}, 标签: {media_category.tags}")
                except Exception as e:
                    logger.warning(f"分类媒体失败，使用基础分类: {e}")
            
            # 4. 构建目标路径
            target_path = self._build_target_path(
                target_base_dir,
                media_info,
                new_name,
                Path(file_path).suffix,
                media_category if use_classification else None
            )
            
            # 4. 创建目标目录
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 5. 移动或复制文件
            if move_file:
                shutil.move(file_path, target_path)
            else:
                shutil.copy2(file_path, target_path)
            
            # 7. 下载字幕（如果启用且用户明确要求）
            subtitle_path = None
            if download_subtitle:
                try:
                    from ..subtitle.service import SubtitleService
                    from app.core.database import AsyncSessionLocal
                    
                    async with AsyncSessionLocal() as session:
                        # 强制下载（因为用户明确要求）
                        subtitle_service = SubtitleService(session, auto_download=True)
                        subtitle_path = await subtitle_service.download_subtitle(
                            str(target_path),
                            subtitle_language,
                            force_download=True  # 用户明确要求下载，强制下载
                        )
                        if subtitle_path:
                            logger.info(f"字幕下载成功: {subtitle_path}")
                except Exception as e:
                    logger.warning(f"下载字幕失败: {e}")
            
            # 8. 写入NFO文件（如果启用）
            if write_nfo:
                try:
                    # 构建媒体信息字典（用于NFO写入）
                    nfo_media_info = {
                        "title": media_info.title,
                        "year": media_info.year,
                        "type": media_info.media_type,
                        "season": media_info.season,
                        "episode": media_info.episode,
                    }
                    
                    # 如果识别结果包含ID信息，添加到NFO
                    if hasattr(media_info, 'tmdb_id') and media_info.tmdb_id:
                        nfo_media_info["tmdb_id"] = media_info.tmdb_id
                    if hasattr(media_info, 'tvdb_id') and media_info.tvdb_id:
                        nfo_media_info["tvdb_id"] = media_info.tvdb_id
                    if hasattr(media_info, 'imdb_id') and media_info.imdb_id:
                        nfo_media_info["imdb_id"] = media_info.imdb_id
                    if hasattr(media_info, 'overview') and media_info.overview:
                        nfo_media_info["overview"] = media_info.overview
                    if hasattr(media_info, 'poster_url') and media_info.poster_url:
                        nfo_media_info["poster_url"] = media_info.poster_url
                    if hasattr(media_info, 'backdrop_url') and media_info.backdrop_url:
                        nfo_media_info["backdrop_url"] = media_info.backdrop_url
                    
                    # 写入NFO文件
                    self.nfo_writer.write_nfo(str(target_path), nfo_media_info)
                    logger.info(f"NFO文件写入成功: {target_path.with_suffix('.nfo')}")
                except Exception as e:
                    logger.warning(f"写入NFO文件失败: {e}")
            
            logger.info(f"文件整理成功: {file_path} -> {target_path}")
            
            return OrganizeResult(
                original_path=file_path,
                new_path=str(target_path),
                success=True,
                media_info=media_info
            )
            
        except Exception as e:
            logger.error(f"文件整理失败: {file_path}, 错误: {e}")
            return OrganizeResult(
                original_path=file_path,
                success=False,
                error=str(e)
            )
    
    def _build_target_path(
        self,
        target_base_dir: str,
        media_info: MediaInfo,
        new_name: str,
        extension: str,
        media_category: Optional[MediaCategory] = None
    ) -> Path:
        """
        构建目标文件路径
        
        Args:
            target_base_dir: 目标基础目录
            media_info: 媒体信息
            new_name: 新文件名（不含扩展名）
            extension: 文件扩展名
            
        Returns:
            目标文件路径
        """
        target_base = Path(target_base_dir)
        
        if media_category:
            # 使用分类器生成的分类路径（支持YAML配置）
            media_dir = Path(self.classifier.get_classification_path(media_category, str(target_base)))
        else:
            # 基础分类（不使用YAML配置时的回退逻辑）
            if media_info.media_type == "short_drama":
                media_dir = target_base / "短剧"
            elif media_info.media_type == "movie":
                media_dir = target_base / "电影"
            elif is_tv_like(media_info.media_type):
                media_dir = target_base / "电视剧"
            elif media_info.media_type == "music":
                media_dir = target_base / "音乐"
            else:
                media_dir = target_base / "其他"
        
        # 构建完整路径
        # 新文件名可能包含目录结构（如 "Title (Year)/Title (Year) [quality]"）
        if "/" in new_name:
            # 包含目录结构
            parts = new_name.split("/")
            directory = media_dir / "/".join(parts[:-1])
            filename = parts[-1]
        else:
            # 只有文件名
            directory = media_dir
            filename = new_name
        
        return directory / f"{filename}{extension}"
    
    async def organize_directory(
        self,
        source_dir: str,
        target_base_dir: str,
        rename_template: Optional[str] = None,
        move_file: bool = True,
        media_extensions: Optional[List[str]] = None,
        download_subtitle: bool = False,
        subtitle_language: str = "zh",
        use_classification: bool = True,
        max_concurrent: int = 5
    ) -> List[OrganizeResult]:
        """
        整理目录中的所有媒体文件（并发处理）
        
        Args:
            source_dir: 源目录
            target_base_dir: 目标基础目录
            rename_template: 重命名模板（可选）
            move_file: 是否移动文件
            media_extensions: 媒体文件扩展名列表（默认：常见视频格式）
            max_concurrent: 最大并发处理数
            
        Returns:
            OrganizeResult对象列表
        """
        import asyncio
        
        if media_extensions is None:
            media_extensions = [
                '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
                '.m4v', '.ts', '.m2ts', '.mpg', '.mpeg', '.vob', '.iso'
            ]
        
        source_path = Path(source_dir)
        file_paths = []
        
        # 递归查找所有媒体文件
        for file_path in source_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                file_paths.append(str(file_path))
        
        if not file_paths:
            logger.info(f"目录中没有找到媒体文件: {source_dir}")
            return []
        
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def organize_with_semaphore(file_path: str) -> OrganizeResult:
            async with semaphore:
                try:
                    return await self.organize_file(
                        file_path,
                        target_base_dir,
                        rename_template,
                        move_file,
                        download_subtitle,
                        subtitle_language,
                        use_classification
                    )
                except Exception as e:
                    logger.error(f"整理文件失败: {file_path}, 错误: {e}")
                    return OrganizeResult(
                        original_path=file_path,
                        success=False,
                        error=str(e)
                    )
        
        # 并发处理所有文件
        tasks = [organize_with_semaphore(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"整理文件失败: {file_paths[i]}, 错误: {result}")
                processed_results.append(OrganizeResult(
                    original_path=file_paths[i],
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        logger.info(f"目录整理完成: {source_dir}, 处理 {len(processed_results)} 个文件")
        return processed_results
    
    async def classify_media(self, media_info: MediaInfo, tmdb_data: Optional[Dict] = None) -> MediaCategory:
        """
        分类媒体文件
        
        Args:
            media_info: 媒体信息
            tmdb_data: TMDB数据（可选）
            
        Returns:
            MediaCategory对象
        """
        return await self.classifier.classify(media_info, tmdb_data)

