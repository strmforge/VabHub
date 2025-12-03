"""
基于文件扩展名的媒体类型检测器

根据文件扩展名进行粗分类。
"""

from pathlib import Path
from typing import Optional
from loguru import logger

from app.modules.inbox.models import InboxItem
from .base import MediaTypeDetector, MediaTypeGuess, MediaTypeLiteral


class ExtensionDetector:
    """
    基于扩展名的检测器
    
    根据文件扩展名进行初步分类。
    """
    
    name = "extension"
    
    # 视频扩展名
    VIDEO_EXTENSIONS = {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".3gp", ".mpg", ".mpeg", ".ts", ".m2ts", ".vob",
        ".rmvb", ".rm", ".asf", ".divx", ".xvid"
    }
    
    # 电子书扩展名
    EBOOK_EXTENSIONS = {
        ".epub", ".mobi", ".azw3", ".pdf", ".fb2", ".djvu"
    }
    
    # 音频扩展名（可能是有声书或音乐）
    AUDIO_EXTENSIONS = {
        ".mp3", ".flac", ".m4a", ".m4b", ".ogg", ".opus", ".aac", ".wav",
        ".wma", ".ape", ".dsf", ".dff"
    }
    
    # 漫画扩展名
    COMIC_EXTENSIONS = {
        ".cbz", ".cbr", ".zip", ".rar"  # 注意：zip/rar 也可能是其他类型，需要进一步判断
    }
    
    def guess(self, item: InboxItem) -> Optional[MediaTypeGuess]:
        """
        根据文件扩展名猜测媒体类型
        
        Args:
            item: 待检测的项目
        
        Returns:
            Optional[MediaTypeGuess]: 猜测结果
        """
        path = item.path
        suffix = path.suffix.lower()
        
        # 视频文件
        if suffix in self.VIDEO_EXTENSIONS:
            # 先统一返回 "movie"，后续可以由其他检测器进一步细分 tv/anime
            return MediaTypeGuess(
                media_type="movie",
                score=0.9,
                reason=f"extension={suffix} => movie (0.9)"
            )
        
        # 电子书文件
        if suffix in self.EBOOK_EXTENSIONS:
            return MediaTypeGuess(
                media_type="ebook",
                score=0.9,
                reason=f"extension={suffix} => ebook (0.9)"
            )
        
        # 音频文件（可能是有声书或音乐）
        if suffix in self.AUDIO_EXTENSIONS:
            # 先给中等分数，后续可以由其他检测器提升或区分 music/audiobook
            return MediaTypeGuess(
                media_type="audiobook",  # 默认假设是有声书，后续可优化
                score=0.6,
                reason=f"extension={suffix} => audiobook (0.6, may be music)"
            )
        
        # TXT 文件（可能是小说，但需要进一步判断）
        if suffix == ".txt":
            return MediaTypeGuess(
                media_type="novel_txt",
                score=0.5,  # 较低分数，需要 novel_txt_detector 进一步确认
                reason=f"extension=txt => novel_txt (0.5, needs content check)"
            )
        
        # 漫画文件
        if suffix in self.COMIC_EXTENSIONS:
            return MediaTypeGuess(
                media_type="comic",
                score=0.8,
                reason=f"extension={suffix} => comic (0.8)"
            )
        
        # 其他扩展名，无法判断
        return None

