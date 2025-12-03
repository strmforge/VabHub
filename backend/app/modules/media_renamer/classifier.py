"""
媒体分类器
基于TMDB、语言等信息对媒体进行分类
支持YAML配置文件方式
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from app.constants.media_types import is_tv_like
from ..media_renamer.identifier import MediaIdentifier
from .category_helper import CategoryHelper
from .parser import MediaInfo


@dataclass
class MediaCategory:
    """媒体分类"""
    category: str  # 分类名称：如"华语电影"、"外语电影"、"动画电影"等
    subcategory: Optional[str] = None  # 子分类
    tags: List[str] = None  # 标签列表
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class MediaClassifier:
    """媒体分类器"""
    
    def __init__(self, tmdb_api_key: Optional[str] = None, category_config_path: Optional[Path] = None):
        """
        初始化分类器
        
        Args:
            tmdb_api_key: TMDB API密钥（可选）
            category_config_path: 分类配置文件路径（可选，默认使用config/category.yaml）
        """
        self.identifier = MediaIdentifier(tmdb_api_key)
        
        # 初始化分类助手（基于YAML配置）
        self.category_helper = CategoryHelper(category_config_path)
        
        # 语言到地区的映射
        self.language_to_region = {
            "zh": "华语",
            "zh-CN": "华语",
            "zh-TW": "华语",
            "en": "欧美",
            "ja": "日本",
            "ko": "韩国",
            "fr": "欧洲",
            "de": "欧洲",
            "es": "欧洲",
            "it": "欧洲",
            "ru": "俄罗斯",
            "hi": "印度",
            "th": "泰国",
            "vi": "越南",
        }
        
        # TMDB类型ID到分类的映射
        self.genre_to_category = {
            # 电影类型
            28: "动作",  # Action
            12: "冒险",  # Adventure
            16: "动画",  # Animation
            35: "喜剧",  # Comedy
            80: "犯罪",  # Crime
            99: "纪录片",  # Documentary
            18: "剧情",  # Drama
            10751: "家庭",  # Family
            14: "奇幻",  # Fantasy
            36: "历史",  # History
            27: "恐怖",  # Horror
            10402: "音乐",  # Music
            9648: "悬疑",  # Mystery
            10749: "爱情",  # Romance
            878: "科幻",  # Science Fiction
            10770: "电视电影",  # TV Movie
            53: "惊悚",  # Thriller
            10752: "战争",  # War
            37: "西部",  # Western
        }
    
    async def classify(self, media_info: MediaInfo, tmdb_data: Optional[Dict] = None) -> MediaCategory:
        """
        分类媒体
        
        Args:
            media_info: 媒体信息
            tmdb_data: TMDB数据（可选，如果提供则使用，否则尝试查询）
            
        Returns:
            MediaCategory对象
        """
        # 如果提供了TMDB数据，使用它；否则尝试查询
        if not tmdb_data:
            try:
                tmdb_data = await self.identifier._query_tmdb(media_info)
            except Exception as e:
                logger.warning(f"查询TMDB失败，使用基础信息分类: {e}")
                tmdb_data = None
        
        # 基础分类
        category = self._classify_basic(media_info, tmdb_data)
        
        # 添加子分类和标签
        subcategory = self._get_subcategory(media_info, tmdb_data)
        tags = self._get_tags(media_info, tmdb_data)
        
        return MediaCategory(
            category=category,
            subcategory=subcategory,
            tags=tags
        )
    
    def _classify_basic(self, media_info: MediaInfo, tmdb_data: Optional[Dict] = None) -> str:
        """
        基础分类
        优先使用YAML配置的分类策略，如果未配置或未匹配，则使用默认分类逻辑
        
        Args:
            media_info: 媒体信息
            tmdb_data: TMDB数据
            
        Returns:
            分类名称
        """
        # 优先使用YAML配置的分类策略
        if tmdb_data:
            if media_info.media_type == "movie" and self.category_helper.is_movie_category:
                category = self.category_helper.get_movie_category(tmdb_data)
                if category:
                    return category
            elif media_info.media_type in ["tv", "tv_series"] and self.category_helper.is_tv_category:
                category = self.category_helper.get_tv_category(tmdb_data)
                if category:
                    return category
            elif media_info.media_type == "music" and self.category_helper.is_music_category:
                # 音乐分类（使用音乐信息）
                music_info = {
                    "original_language": media_info.language,
                    "genre_ids": tmdb_data.get("genre_ids", []),
                    "artist": getattr(media_info, "artist", None),
                    "album": getattr(media_info, "album", None),
                }
                category = self.category_helper.get_music_category(music_info)
                if category:
                    return category
        
        # 如果YAML配置未匹配或未启用，使用默认分类逻辑
        # 1. 根据媒体类型分类
        if media_info.media_type == "movie":
            base_category = "电影"
        elif is_tv_like(media_info.media_type):
            base_category = "电视剧"
        elif media_info.media_type == "anime":
            base_category = "动画"
        elif media_info.media_type == "music":
            base_category = "音乐"
        else:
            base_category = "其他"
        
        # 2. 根据语言分类
        region = "其他"
        if media_info.language:
            region = self.language_to_region.get(media_info.language, "其他")
        
        # 3. 根据TMDB类型分类
        genre_category = None
        if tmdb_data:
            genre_ids = tmdb_data.get("genre_ids", [])
            if genre_ids:
                # 使用第一个类型作为主要类型
                primary_genre_id = genre_ids[0]
                genre_category = self.genre_to_category.get(primary_genre_id)
        
        # 组合分类
        if genre_category and genre_category == "动画":
            # 动画类型优先
            return f"{genre_category}{base_category}"
        elif region != "其他":
            return f"{region}{base_category}"
        elif genre_category:
            return f"{genre_category}{base_category}"
        else:
            return base_category
    
    def _get_subcategory(self, media_info: MediaInfo, tmdb_data: Optional[Dict] = None) -> Optional[str]:
        """
        获取子分类
        
        Args:
            media_info: 媒体信息
            tmdb_data: TMDB数据
            
        Returns:
            子分类名称
        """
        # 根据质量分类
        if media_info.quality:
            quality_map = {
                "4K": "4K",
                "1080p": "高清",
                "720p": "标清",
                "480p": "低清"
            }
            return quality_map.get(media_info.quality)
        
        # 根据来源分类
        if media_info.source:
            source_map = {
                "BluRay": "蓝光",
                "WEB-DL": "网络",
                "HDTV": "电视",
                "DVDRip": "DVD"
            }
            return source_map.get(media_info.source)
        
        return None
    
    def _get_tags(self, media_info: MediaInfo, tmdb_data: Optional[Dict] = None) -> List[str]:
        """
        获取标签列表
        
        Args:
            media_info: 媒体信息
            tmdb_data: TMDB数据
            
        Returns:
            标签列表
        """
        tags = []
        
        # 质量标签
        if media_info.quality:
            tags.append(media_info.quality)
        
        # 来源标签
        if media_info.source:
            tags.append(media_info.source)
        
        # 编码标签
        if media_info.codec:
            tags.append(media_info.codec)
        
        # TMDB类型标签
        if tmdb_data:
            genre_ids = tmdb_data.get("genre_ids", [])
            for genre_id in genre_ids[:3]:  # 最多3个类型
                genre_name = self.genre_to_category.get(genre_id)
                if genre_name and genre_name not in tags:
                    tags.append(genre_name)
        
        # 特效标签
        if media_info.source and "HDR" in media_info.source:
            tags.append("HDR")
        if media_info.source and "DV" in media_info.source:
            tags.append("Dolby Vision")
        
        return tags
    
    def get_classification_path(self, category: MediaCategory, base_dir: str) -> str:
        """
        根据分类生成目录路径
        
        Args:
            category: 媒体分类
            base_dir: 基础目录
            
        Returns:
            完整目录路径
        """
        from pathlib import Path
        
        path_parts = [base_dir]
        
        # 主分类
        path_parts.append(category.category)
        
        # 子分类（如果有）
        if category.subcategory:
            path_parts.append(category.subcategory)
        
        return str(Path(*path_parts))

