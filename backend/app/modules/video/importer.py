"""
视频媒体导入器

负责将视频文件从待整理目录导入到对应的媒体库根目录，并调用 MediaOrganizer 完成二级分类和重命名。
"""

from pathlib import Path
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.constants.media_types import (
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_TV,
    MEDIA_TYPE_ANIME,
    MEDIA_TYPE_SHORT_DRAMA
)
from app.modules.media_renamer.organizer import MediaOrganizer, OrganizeResult


class VideoImporter:
    """
    视频媒体导入器
    
    根据 media_type 将视频文件导入到对应的媒体库根目录，
    并调用 MediaOrganizer 完成二级分类和重命名。
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化视频导入器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self._organizer: Optional[MediaOrganizer] = None
    
    def _get_organizer(self) -> MediaOrganizer:
        """
        获取 MediaOrganizer 实例（懒加载）
        
        Returns:
            MediaOrganizer: 媒体整理器实例
        """
        if self._organizer is None:
            # 从 settings 获取 TMDB API key
            tmdb_api_key = settings.TMDB_API_KEY if hasattr(settings, 'TMDB_API_KEY') else None
            self._organizer = MediaOrganizer(tmdb_api_key=tmdb_api_key)
        return self._organizer
    
    def _get_library_root_for_media_type(self, media_type: str) -> Path:
        """
        根据媒体类型获取对应的媒体库根目录
        
        Args:
            media_type: 媒体类型（movie/tv/anime/short_drama）
        
        Returns:
            Path: 媒体库根目录路径
        """
        if media_type == MEDIA_TYPE_MOVIE:
            return Path(settings.MOVIE_LIBRARY_ROOT)
        elif media_type == MEDIA_TYPE_TV:
            return Path(settings.TV_LIBRARY_ROOT)
        elif media_type == MEDIA_TYPE_ANIME:
            # 如果未配置 ANIME_LIBRARY_ROOT，默认使用 TV_LIBRARY_ROOT
            anime_root = settings.ANIME_LIBRARY_ROOT or settings.TV_LIBRARY_ROOT
            return Path(anime_root)
        elif media_type == MEDIA_TYPE_SHORT_DRAMA:
            # 如果未配置 SHORT_DRAMA_LIBRARY_ROOT，默认使用 TV_LIBRARY_ROOT
            short_drama_root = settings.SHORT_DRAMA_LIBRARY_ROOT or settings.TV_LIBRARY_ROOT
            return Path(short_drama_root)
        else:
            # 防御性兜底：未知类型默认使用电影库
            logger.warning(f"未知的视频媒体类型: {media_type}，使用 MOVIE_LIBRARY_ROOT 作为默认路径")
            return Path(settings.MOVIE_LIBRARY_ROOT)
    
    async def import_video_from_path(
        self,
        file_path: Path,
        media_type: str,
        download_task_id: Optional[int] = None,
        source_site_id: Optional[int] = None,
        extra_metadata: Optional[dict] = None
    ) -> Optional[Path]:
        """
        根据 media_type 和文件路径，将视频移动/整理到对应媒体库根目录下
        
        Args:
            file_path: 源文件路径
            media_type: 媒体类型（movie/tv/anime/short_drama）
            download_task_id: 下载任务 ID（可选）
            source_site_id: 来源站点 ID（可选）
            extra_metadata: 额外元数据（可选）
        
        Returns:
            Optional[Path]: 成功时返回新路径，失败时返回 None
        """
        try:
            # 检查文件是否存在
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"视频文件不存在或不是文件: {file_path}")
                return None
            
            # 获取对应的媒体库根目录
            target_base = self._get_library_root_for_media_type(media_type)
            
            # 确保目标根目录存在
            target_base.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始导入视频: {file_path} -> {target_base} (media_type={media_type})")
            
            # 获取 MediaOrganizer 实例
            organizer = self._get_organizer()
            
            # 调用 MediaOrganizer 进行整理
            # organize_file 会自动完成：
            # 1. 识别媒体信息（从文件名解析）
            # 2. 查询 TMDB 获取元数据
            # 3. 分类（根据 category.yaml）
            # 4. 重命名
            # 5. 移动到目标目录（target_base / category / subcategory / new_name.ext）
            result: OrganizeResult = await organizer.organize_file(
                file_path=str(file_path),
                target_base_dir=str(target_base),
                move_file=True,  # 移动文件（从 INBOX 移动到媒体库）
                use_classification=True,  # 启用分类（使用 category.yaml）
                write_nfo=True  # 写入 NFO 文件
            )
            
            if result.success and result.new_path:
                new_path = Path(result.new_path)
                logger.info(f"视频导入成功: {file_path} -> {new_path}")
                return new_path
            else:
                error_msg = result.error or "未知错误"
                logger.warning(f"视频导入失败: {file_path}, 错误: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"视频导入异常: {file_path}, 错误: {e}", exc_info=True)
            return None

