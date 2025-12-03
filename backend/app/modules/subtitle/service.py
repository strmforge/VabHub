"""
字幕服务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from pathlib import Path
from loguru import logger
import shutil
import asyncio
from app.core.cache import get_cache

from app.models.subtitle import Subtitle, SubtitleDownloadHistory
from app.modules.settings.service import SettingsService
from .matcher import SubtitleMatcher
from .sources import OpenSubtitlesClient, SubHDClient, SubtitleInfo
from .sources_shooter import ShooterClient
from ..media_renamer.identifier import MediaIdentifier
from ..media_renamer.parser import MediaInfo
from app.core.config import settings


class SubtitleService:
    """字幕服务"""
    
    def __init__(self, db: AsyncSession, auto_download: Optional[bool] = None, max_concurrent: int = 3):
        """
        初始化字幕服务
        
        Args:
            db: 数据库会话
            auto_download: 是否自动下载字幕（如果为None，从配置读取）
            max_concurrent: 最大并发搜索数
        """
        self.db = db
        self.max_concurrent = max_concurrent
        self.cache = get_cache()
        
        # 获取自动下载配置（优先使用参数，其次从系统设置读取，最后从配置读取）
        if auto_download is None:
            # 尝试从系统设置读取
            auto_download = getattr(settings, 'SUBTITLE_AUTO_DOWNLOAD', False)
        self.auto_download = auto_download
        
        # 初始化字幕源
        self.sources = []
        
        # OpenSubtitles（如果配置了API密钥）
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        opensubtitles_api_key = getattr(settings, 'OPENSUBTITLES_API_KEY', None)
        if opensubtitles_api_key:
            self.sources.append(OpenSubtitlesClient(api_key=opensubtitles_api_key))
        
        # 射手字幕（无需API密钥，支持文件哈希搜索）
        self.sources.append(ShooterClient())
        
        # SubHD（可以添加）
        # self.sources.append(SubHDClient())
        
        # 初始化匹配器
        self.matcher = SubtitleMatcher(self.sources)
        
        # 初始化媒体识别器
        self.identifier = MediaIdentifier(tmdb_api_key)
    
    async def download_subtitle(
        self,
        media_file_path: str,
        language: str = "zh",
        save_path: Optional[str] = None,
        force_download: bool = False
    ) -> Optional[str]:
        """
        下载字幕
        
        Args:
            media_file_path: 媒体文件路径
            language: 语言
            save_path: 保存路径（如果为None，自动生成）
            
        Returns:
            字幕文件路径（如果成功）
        """
        try:
            # 检查是否启用自动下载（除非强制下载）
            # 如果auto_download为None，尝试从系统设置异步读取
            if not force_download:
                if self.auto_download is None:
                    try:
                        settings_service = SettingsService(self.db)
                        auto_download_setting = await settings_service.get_setting("subtitle_auto_download", "false")
                        self.auto_download = auto_download_setting.lower() == "true" if isinstance(auto_download_setting, str) else bool(auto_download_setting)
                    except Exception as e:
                        logger.warning(f"读取字幕自动下载设置失败，使用默认值: {e}")
                        self.auto_download = getattr(settings, 'SUBTITLE_AUTO_DOWNLOAD', False)
                
                if not self.auto_download:
                    logger.info(f"字幕自动下载已关闭，跳过下载: {media_file_path}（提示：PT站大多有内置字幕，如需下载请手动调用API或开启自动下载）")
                    return None
            
            # 1. 识别媒体信息
            media_info = await self.identifier.identify(media_file_path)
            
            # 2. 匹配字幕
            subtitle_info = await self.matcher.match_subtitle(
                media_info,
                media_file_path,
                language,
                use_hash_matching=True  # 启用文件哈希匹配（用于射手字幕）
            )
            
            if not subtitle_info:
                logger.warning(f"未找到字幕: {media_file_path}")
                return None
            
            # 3. 确定保存路径
            if not save_path:
                media_path = Path(media_file_path)
                # 字幕文件名：与媒体文件同名，扩展名为字幕格式
                save_path = str(media_path.parent / f"{media_path.stem}.{subtitle_info.format}")
            
            # 4. 下载字幕
            # 找到对应的字幕源
            source = None
            for s in self.sources:
                if s.__class__.__name__.replace("Client", "").lower() == subtitle_info.source:
                    source = s
                    break
            
            if not source:
                logger.error(f"未找到字幕源: {subtitle_info.source}")
                return None
            
            # 下载字幕
            success = await source.download(subtitle_info, save_path)
            
            if not success:
                logger.error(f"下载字幕失败: {subtitle_info.title}")
                return None
            
            # 5. 保存字幕记录到数据库
            subtitle = Subtitle(
                media_file_path=media_file_path,
                media_type=media_info.media_type,
                media_title=media_info.title,
                media_year=media_info.year,
                season=media_info.season,
                episode=media_info.episode,
                subtitle_path=save_path,
                language=subtitle_info.language,
                language_code=subtitle_info.language_code,
                format=subtitle_info.format,
                source=subtitle_info.source,
                source_id=subtitle_info.source_id,
                download_url=subtitle_info.download_url,
                file_size=subtitle_info.file_size,
                rating=subtitle_info.rating,
                downloads=subtitle_info.downloads,
                is_forced=subtitle_info.is_forced,
                is_hearing_impaired=subtitle_info.is_hearing_impaired
            )
            
            self.db.add(subtitle)
            await self.db.commit()
            await self.db.refresh(subtitle)
            
            # 6. 记录下载历史
            history = SubtitleDownloadHistory(
                media_file_path=media_file_path,
                subtitle_id=subtitle.id,
                source=subtitle_info.source,
                language=language,
                success=True
            )
            self.db.add(history)
            await self.db.commit()
            
            logger.info(f"字幕下载成功: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"下载字幕失败: {media_file_path}, 错误: {e}")
            
            # 记录失败历史
            try:
                history = SubtitleDownloadHistory(
                    media_file_path=media_file_path,
                    source="unknown",
                    language=language,
                    success=False,
                    error_message=str(e)
                )
                self.db.add(history)
                await self.db.commit()
            except Exception as history_error:
                logger.error(f"记录下载历史失败: {history_error}")
            
            return None
    
    async def list_subtitles(
        self,
        media_file_path: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[Subtitle]:
        """获取字幕列表"""
        query = select(Subtitle)
        
        if media_file_path:
            query = query.where(Subtitle.media_file_path == media_file_path)
        if language:
            query = query.where(Subtitle.language == language)
        
        query = query.order_by(Subtitle.downloaded_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_subtitle(self, subtitle_id: int) -> Optional[Subtitle]:
        """获取字幕详情"""
        result = await self.db.execute(
            select(Subtitle).where(Subtitle.id == subtitle_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_subtitle(self, subtitle_id: int) -> bool:
        """删除字幕"""
        subtitle = await self.get_subtitle(subtitle_id)
        if not subtitle:
            return False
        
        # 删除文件
        try:
            subtitle_path = Path(subtitle.subtitle_path)
            if subtitle_path.exists():
                subtitle_path.unlink()
        except Exception as e:
            logger.warning(f"删除字幕文件失败: {subtitle.subtitle_path}, 错误: {e}")
        
        # 删除数据库记录
        await self.db.delete(subtitle)
        await self.db.commit()
        
        logger.info(f"删除字幕成功: {subtitle_id}")
        return True
    
    async def search_subtitles(
        self,
        media_file_path: str,
        language: str = "zh"
    ) -> List[SubtitleInfo]:
        """
        搜索字幕（不下载）
        
        Args:
            media_file_path: 媒体文件路径
            language: 语言
            
        Returns:
            字幕信息列表
        """
        try:
            # 识别媒体信息
            media_info = await self.identifier.identify(media_file_path)
            
            # 在所有字幕源中搜索
            all_subtitles = []
            for source in self.sources:
                try:
                    subtitles = await source.search(
                        title=media_info.title,
                        year=media_info.year,
                        season=media_info.season,
                        episode=media_info.episode,
                        language=language
                    )
                    all_subtitles.extend(subtitles)
                except Exception as e:
                    logger.warning(f"从 {source.__class__.__name__} 搜索字幕失败: {e}")
                    continue
            
            return all_subtitles
            
        except Exception as e:
            logger.error(f"搜索字幕失败: {media_file_path}, 错误: {e}")
            return []

