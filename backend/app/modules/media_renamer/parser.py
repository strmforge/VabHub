"""
文件名解析器
从文件名中提取媒体信息（标题、年份、季数、集数等）
"""

import re
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class MediaInfo:
    """媒体信息数据类"""
    title: str  # 标题
    year: Optional[int] = None  # 年份
    media_type: str = "unknown"  # 类型：movie, tv, anime
    season: Optional[int] = None  # 季数（电视剧）
    episode: Optional[int] = None  # 集数（电视剧）
    episode_name: Optional[str] = None  # 集名（电视剧）
    quality: Optional[str] = None  # 质量：1080p, 4K等
    resolution: Optional[str] = None  # 分辨率
    codec: Optional[str] = None  # 编码：H.264, H.265等
    source: Optional[str] = None  # 来源：BluRay, WEB-DL等
    group: Optional[str] = None  # 发布组
    language: Optional[str] = None  # 语言
    subtitle: Optional[str] = None  # 字幕信息
    raw_title: str = ""  # 原始标题（未处理的部分）
    # 媒体ID信息（从TMDB/TVDB/IMDB获取）
    tmdb_id: Optional[int] = None  # TMDB ID
    tvdb_id: Optional[int] = None  # TVDB ID
    imdb_id: Optional[str] = None  # IMDB ID
    # 媒体元数据（从TMDB/TVDB获取）
    overview: Optional[str] = None  # 概述
    poster_url: Optional[str] = None  # 海报URL
    backdrop_url: Optional[str] = None  # 背景图URL


class FilenameParser:
    """文件名解析器"""
    
    def __init__(self):
        """初始化解析器"""
        # 年份模式（1900-2099）
        self.year_pattern = re.compile(r'\b(19|20)\d{2}\b')
        
        # 季数模式：S01, S1, Season 1, 第1季
        self.season_pattern = re.compile(
            r'(?:S|Season|第)\s*(\d{1,2})',
            re.IGNORECASE
        )
        
        # 集数模式：E01, E1, EP01, EP1, 第01集, 第1集
        self.episode_pattern = re.compile(
            r'(?:E|EP|Episode|第)\s*(\d{1,3})(?:集)?',
            re.IGNORECASE
        )
        
        # 质量模式：1080p, 720p, 4K, 2160p等
        self.quality_pattern = re.compile(
            r'\b(4K|2160p|1080p|720p|480p|360p|240p)\b',
            re.IGNORECASE
        )
        
        # 分辨率模式：1920x1080, 1280x720等
        self.resolution_pattern = re.compile(
            r'\b(\d{3,4}x\d{3,4})\b'
        )
        
        # 编码模式：H.264, H.265, HEVC, x264, x265等
        self.codec_pattern = re.compile(
            r'\b(H\.?264|H\.?265|HEVC|x264|x265|AVC|MPEG-?2)\b',
            re.IGNORECASE
        )
        
        # 来源模式：BluRay, WEB-DL, WEBRip, HDTV等
        self.source_pattern = re.compile(
            r'\b(BluRay|BDRip|WEB-DL|WEBRip|HDTV|DVDRip|CAM|TS|TC|SCR)\b',
            re.IGNORECASE
        )
        
        # 语言模式：中文, 英文, CHS, ENG等
        self.language_pattern = re.compile(
            r'\b(中文|英文|CHS|CHT|ENG|简体|繁体|中字|双语)\b',
            re.IGNORECASE
        )
        
        # 字幕模式：字幕, Sub, 外挂字幕等
        self.subtitle_pattern = re.compile(
            r'\b(字幕|Sub|外挂字幕|内嵌字幕|硬字幕)\b',
            re.IGNORECASE
        )
        
        # 发布组模式（通常在方括号或圆括号中）
        self.group_pattern = re.compile(
            r'[\[\(]([A-Za-z0-9\-_]+)[\]\)]'
        )
    
    def parse(self, filename: str) -> MediaInfo:
        """
        解析文件名，提取媒体信息
        
        Args:
            filename: 文件名（不包含路径和扩展名）
            
        Returns:
            MediaInfo对象
        """
        # 移除文件扩展名（如果存在）
        filename = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # 清理文件名：移除多余空格
        filename = re.sub(r'\s+', ' ', filename).strip()
        
        media_info = MediaInfo(
            title="",
            raw_title=filename
        )
        
        # 提取年份
        year_match = self.year_pattern.search(filename)
        if year_match:
            try:
                media_info.year = int(year_match.group())
            except ValueError:
                pass
        
        # 提取季数和集数（判断是否为电视剧）
        season_match = self.season_pattern.search(filename)
        episode_match = self.episode_pattern.search(filename)
        
        if season_match or episode_match:
            media_info.media_type = "tv"
            
            if season_match:
                try:
                    media_info.season = int(season_match.group(1))
                except (ValueError, IndexError):
                    pass
            
            if episode_match:
                try:
                    media_info.episode = int(episode_match.group(1))
                except (ValueError, IndexError):
                    pass
            
            # 尝试提取集名（通常在集数后面）
            if episode_match:
                episode_end = episode_match.end()
                # 查找集名（通常在集数后，用 - 或 . 分隔）
                episode_name_match = re.search(
                    r'[-\s]+([^-\s]+(?:\s+[^-\s]+)*?)(?:\s+\[|\s+\(|\s+\d{3,4}p|\s*$|\.)',
                    filename[episode_end:]
                )
                if episode_name_match:
                    media_info.episode_name = episode_name_match.group(1).strip()
        else:
            # 没有季数和集数，可能是电影
            media_info.media_type = "movie"
        
        # 提取质量
        quality_match = self.quality_pattern.search(filename)
        if quality_match:
            quality = quality_match.group(1).upper()
            # 标准化质量标识
            if quality in ['4K', '2160P']:
                media_info.quality = "4K"
            elif quality in ['1080P']:
                media_info.quality = "1080p"
            elif quality in ['720P']:
                media_info.quality = "720p"
            else:
                media_info.quality = quality.lower()
        
        # 提取分辨率
        resolution_match = self.resolution_pattern.search(filename)
        if resolution_match:
            media_info.resolution = resolution_match.group(1)
        
        # 提取编码
        codec_match = self.codec_pattern.search(filename)
        if codec_match:
            codec = codec_match.group(1).upper()
            # 标准化编码标识
            if codec in ['H.264', 'H264', 'AVC', 'X264']:
                media_info.codec = "H.264"
            elif codec in ['H.265', 'H265', 'HEVC', 'X265']:
                media_info.codec = "H.265"
            else:
                media_info.codec = codec
        
        # 提取来源
        source_match = self.source_pattern.search(filename)
        if source_match:
            media_info.source = source_match.group(1)
        
        # 提取语言
        language_match = self.language_pattern.search(filename)
        if language_match:
            media_info.language = language_match.group(1)
        
        # 提取字幕信息
        subtitle_match = self.subtitle_pattern.search(filename)
        if subtitle_match:
            media_info.subtitle = subtitle_match.group(1)
        
        # 提取发布组（最后一个匹配的）
        group_matches = self.group_pattern.findall(filename)
        if group_matches:
            # 通常发布组在文件名末尾
            media_info.group = group_matches[-1]
        
        # 提取标题（移除所有已识别的部分）
        title = filename
        
        # 移除年份
        if media_info.year:
            title = self.year_pattern.sub('', title)
        
        # 移除季数和集数信息
        if season_match:
            title = self.season_pattern.sub('', title)
        if episode_match:
            title = self.episode_pattern.sub('', title)
            # 移除集名
            if media_info.episode_name:
                title = title.replace(media_info.episode_name, '')
        
        # 移除质量、分辨率、编码等信息
        if quality_match:
            title = self.quality_pattern.sub('', title)
        if resolution_match:
            title = self.resolution_pattern.sub('', title)
        if codec_match:
            title = self.codec_pattern.sub('', title)
        if source_match:
            title = self.source_pattern.sub('', title)
        if language_match:
            title = self.language_pattern.sub('', title)
        if subtitle_match:
            title = self.subtitle_pattern.sub('', title)
        
        # 移除发布组（方括号和圆括号中的内容）
        title = self.group_pattern.sub('', title)
        
        # 清理标题：移除多余的分隔符和空格
        title = re.sub(r'[\[\](){}]', '', title)  # 移除括号
        title = re.sub(r'[._-]+', ' ', title)  # 将分隔符替换为空格
        title = re.sub(r'\s+', ' ', title).strip()  # 移除多余空格
        
        # 如果标题为空，使用原始文件名的一部分
        if not title:
            # 尝试提取第一个有意义的部分作为标题
            parts = filename.split()
            if parts:
                media_info.title = parts[0]
            else:
                media_info.title = filename
        else:
            media_info.title = title
        
        logger.debug(f"解析文件名: {filename} -> {media_info}")
        return media_info
    
    def parse_with_tmdb(self, filename: str) -> MediaInfo:
        """
        解析文件名并尝试从TMDB获取更准确的媒体信息
        
        Args:
            filename: 文件名
            
        Returns:
            MediaInfo对象（包含TMDB信息）
        """
        # 先进行基础解析
        media_info = self.parse(filename)
        
        # TODO: 集成TMDB API获取更准确的信息
        # 1. 使用解析出的标题和年份查询TMDB
        # 2. 如果找到匹配，更新媒体信息
        # 3. 对于电视剧，获取季数和集数信息
        
        return media_info

