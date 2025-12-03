"""
RSS项媒体信息提取器
从RSS项标题和描述中提取媒体信息（电影/电视剧名称、年份、季数、集数等）
"""

import re
from typing import Optional, Dict
from dataclasses import dataclass
from loguru import logger

from ..media_renamer.parser import FilenameParser, MediaInfo


@dataclass
class ExtractedMediaInfo:
    """提取的媒体信息"""
    title: str  # 标题
    year: Optional[int] = None  # 年份
    media_type: str = "unknown"  # 类型：movie, tv
    season: Optional[int] = None  # 季数（电视剧）
    episode: Optional[int] = None  # 集数（电视剧）
    quality: Optional[str] = None  # 质量
    resolution: Optional[str] = None  # 分辨率
    codec: Optional[str] = None  # 编码
    source: Optional[str] = None  # 来源
    group: Optional[str] = None  # 发布组
    raw_title: str = ""  # 原始标题


class RSSMediaExtractor:
    """RSS项媒体信息提取器"""
    
    def __init__(self):
        """初始化提取器"""
        self.filename_parser = FilenameParser()
    
    def extract(self, rss_item_title: str, rss_item_description: Optional[str] = None) -> ExtractedMediaInfo:
        """
        从RSS项中提取媒体信息
        
        Args:
            rss_item_title: RSS项标题
            rss_item_description: RSS项描述（可选）
            
        Returns:
            ExtractedMediaInfo对象
        """
        # 使用文件名解析器解析标题
        media_info = self.filename_parser.parse(rss_item_title)
        
        # 转换为ExtractedMediaInfo
        extracted_info = ExtractedMediaInfo(
            title=media_info.title,
            year=media_info.year,
            media_type=media_info.media_type,
            season=media_info.season,
            episode=media_info.episode,
            quality=media_info.quality,
            resolution=media_info.resolution,
            codec=media_info.codec,
            source=media_info.source,
            group=media_info.group,
            raw_title=rss_item_title
        )
        
        # 如果从标题中未提取到足够的信息，尝试从描述中提取
        if not extracted_info.title or extracted_info.media_type == "unknown":
            if rss_item_description:
                desc_info = self._extract_from_description(rss_item_description)
                if desc_info:
                    # 合并信息
                    if not extracted_info.title:
                        extracted_info.title = desc_info.get("title", "")
                    if not extracted_info.year:
                        extracted_info.year = desc_info.get("year")
                    if extracted_info.media_type == "unknown":
                        extracted_info.media_type = desc_info.get("media_type", "unknown")
        
        logger.debug(f"从RSS项提取媒体信息: {rss_item_title} -> {extracted_info}")
        return extracted_info
    
    def _extract_from_description(self, description: str) -> Optional[Dict]:
        """
        从描述中提取媒体信息
        
        Args:
            description: RSS项描述
            
        Returns:
            媒体信息字典
        """
        # 简单的描述解析逻辑
        # 可以扩展为更复杂的NLP处理
        
        info = {}
        
        # 提取年份
        year_match = re.search(r'\b(19|20)\d{2}\b', description)
        if year_match:
            try:
                info["year"] = int(year_match.group())
            except ValueError:
                pass
        
        # 提取季数和集数
        season_match = re.search(r'(?:S|Season|第)\s*(\d{1,2})', description, re.IGNORECASE)
        episode_match = re.search(r'(?:E|EP|Episode|第)\s*(\d{1,3})(?:集)?', description, re.IGNORECASE)
        
        if season_match or episode_match:
            info["media_type"] = "tv"
            if season_match:
                try:
                    info["season"] = int(season_match.group(1))
                except (ValueError, IndexError):
                    pass
            if episode_match:
                try:
                    info["episode"] = int(episode_match.group(1))
                except (ValueError, IndexError):
                    pass
        else:
            info["media_type"] = "movie"
        
        return info if info else None

