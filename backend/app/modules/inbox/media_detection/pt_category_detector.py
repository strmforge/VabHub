"""
基于 PT 站点分类的媒体类型检测器

根据 PT 下载任务的分类（category）和标签（tags）给出高置信度的媒体类型判断。
"""

from typing import Optional, Dict
from loguru import logger

from app.modules.inbox.models import InboxItem
from .base import MediaTypeDetector, MediaTypeGuess, MediaTypeLiteral


# PT 分类到媒体类型的映射
# 支持中英文，忽略大小写，支持子串匹配
DEFAULT_PT_CATEGORY_MEDIA_TYPE_MAPPING: Dict[str, MediaTypeLiteral] = {
    # 英文/数字类
    "movie": "movie",
    "movies": "movie",
    "film": "movie",
    "films": "movie",
    "cinema": "movie",
    "tv": "tv",
    "tv series": "tv",
    "tv show": "tv",
    "television": "tv",
    "series": "tv",
    "anime": "anime",
    "cartoon": "anime",
    "animation": "anime",
    "music": "music",
    "ost": "music",
    "soundtrack": "music",
    "album": "music",
    "audiobook": "audiobook",
    "audio book": "audiobook",
    "audio-book": "audiobook",
    "ebook": "ebook",
    "e-book": "ebook",
    "book": "ebook",
    "books": "ebook",
    "comic": "comic",
    "comics": "comic",
    "manga": "comic",
    
    # 中文类
    "电影": "movie",
    "影片": "movie",
    "剧集": "tv",
    "电视剧": "tv",
    "连续剧": "tv",
    "动漫": "anime",
    "动画": "anime",
    "音乐": "music",
    "原声": "music",
    "原声带": "music",
    "有声书": "audiobook",
    "有聲書": "audiobook",
    "电子书": "ebook",
    "電子書": "ebook",
    "图书": "ebook",
    "书籍": "ebook",
    "漫画": "comic",
    "漫畫": "comic",
}


class PTCategoryDetector:
    """
    基于 PT 分类的检测器
    
    根据 InboxItem 的 source_category 和 source_tags 进行判断。
    """
    
    name = "pt_category"
    
    def __init__(self, mapping: Optional[Dict[str, MediaTypeLiteral]] = None, score: float = 0.95):
        """
        初始化 PT 分类检测器
        
        Args:
            mapping: PT 分类到媒体类型的映射（如果为 None，使用默认映射）
            score: 检测结果的置信度分数（默认 0.95，表示高置信度）
        """
        self._mapping = mapping or DEFAULT_PT_CATEGORY_MEDIA_TYPE_MAPPING
        self._score = score
    
    def guess(self, item: InboxItem) -> Optional[MediaTypeGuess]:
        """
        根据 PT 分类和标签猜测媒体类型
        
        Args:
            item: 待检测的项目
        
        Returns:
            Optional[MediaTypeGuess]: 如果无法判断，返回 None；否则返回猜测结果
        """
        # 优先使用 source_category
        if item.source_category:
            category_lower = item.source_category.lower()
            matched_type = self._match_category(category_lower)
            
            if matched_type:
                return MediaTypeGuess(
                    media_type=matched_type,
                    score=self._score,
                    reason=f"pt_category={item.source_category} => {matched_type} (score={self._score})"
                )
        
        # 如果 category 没有匹配，尝试 source_tags
        if item.source_tags:
            for tag in item.source_tags:
                if not tag:
                    continue
                
                tag_lower = str(tag).lower()
                matched_type = self._match_category(tag_lower)
                
                if matched_type:
                    # 标签匹配的分数可以稍低一些
                    tag_score = max(0.9, self._score - 0.05)
                    return MediaTypeGuess(
                        media_type=matched_type,
                        score=tag_score,
                        reason=f"pt_tag={tag} => {matched_type} (score={tag_score})"
                    )
        
        # 没有匹配，返回 None，让其他检测器处理
        return None
    
    def _match_category(self, category_lower: str) -> Optional[MediaTypeLiteral]:
        """
        在映射中查找匹配的媒体类型
        
        支持子串匹配（忽略大小写）。
        
        Args:
            category_lower: 小写的分类字符串
        
        Returns:
            Optional[MediaTypeLiteral]: 匹配到的媒体类型，如果没有匹配则返回 None
        """
        # 精确匹配优先
        if category_lower in self._mapping:
            return self._mapping[category_lower]
        
        # 子串匹配
        for key, media_type in self._mapping.items():
            if key in category_lower or category_lower in key:
                return media_type
        
        return None

