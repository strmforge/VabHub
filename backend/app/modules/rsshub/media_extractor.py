"""
RSSHub媒体信息提取器
用于从RSS标题中提取媒体信息（片名、年份、剧名+集数等）
"""

import re
from typing import Dict, Optional
from loguru import logger


class RSSHubMediaExtractor:
    """RSSHub媒体信息提取器"""
    
    def extract_media_info(self, title: str) -> Dict:
        """
        从标题中提取媒体信息
        
        Args:
            title: RSS项标题
            
        Returns:
            媒体信息字典:
            {
                "title": "片名/剧名",
                "year": 年份,
                "season": 季数（电视剧）,
                "episode": 集数（电视剧）,
                "type": "movie/tv/anime/variety/music"
            }
        """
        if not title:
            return {}
        
        # 清理标题
        title = title.strip()
        
        # 提取年份
        year_match = re.search(r'\((\d{4})\)|（(\d{4})）|(\d{4})年', title)
        year = None
        if year_match:
            year = int(year_match.group(1) or year_match.group(2) or year_match.group(3))
            # 移除年份标记
            title = re.sub(r'\((\d{4})\)|（(\d{4})）|(\d{4})年', '', title).strip()
        
        # 提取季数和集数（电视剧/番剧）
        season_episode_match = re.search(
            r'[Ss](\d+)[Ee](\d+)|第(\d+)季.*第(\d+)集|第(\d+)集|EP(\d+)|EP\.(\d+)',
            title
        )
        season = None
        episode = None
        if season_episode_match:
            if season_episode_match.group(1) and season_episode_match.group(2):
                # S01E01格式
                season = int(season_episode_match.group(1))
                episode = int(season_episode_match.group(2))
            elif season_episode_match.group(3) and season_episode_match.group(4):
                # 第X季第X集格式
                season = int(season_episode_match.group(3))
                episode = int(season_episode_match.group(4))
            elif season_episode_match.group(5):
                # 第X集格式
                episode = int(season_episode_match.group(5))
            elif season_episode_match.group(6):
                # EP格式
                episode = int(season_episode_match.group(6))
            elif season_episode_match.group(7):
                # EP.格式
                episode = int(season_episode_match.group(7))
        
        # 判断类型
        media_type = self._detect_media_type(title, season, episode)
        
        # 提取标题（移除季数集数标记）
        clean_title = re.sub(
            r'[Ss]\d+[Ee]\d+|第\d+季.*第\d+集|第\d+集|EP\d+|EP\.\d+',
            '',
            title
        ).strip()
        
        result = {
            "title": clean_title,
            "type": media_type
        }
        
        if year:
            result["year"] = year
        if season:
            result["season"] = season
        if episode:
            result["episode"] = episode
        
        return result
    
    def _detect_media_type(
        self,
        title: str,
        season: Optional[int],
        episode: Optional[int]
    ) -> str:
        """
        检测媒体类型
        
        Args:
            title: 标题
            season: 季数
            episode: 集数
            
        Returns:
            媒体类型: movie/tv/anime/variety/music
        """
        title_lower = title.lower()
        
        # 如果有季数或集数，判断为电视剧或番剧
        if season or episode:
            # 判断是否为番剧（包含动画相关关键词）
            anime_keywords = ['动画', 'anime', '番剧', '新番', 'アニメ']
            if any(keyword in title_lower for keyword in anime_keywords):
                return 'anime'
            return 'tv'
        
        # 判断综艺
        variety_keywords = ['综艺', 'variety', 'show', '真人秀', '脱口秀']
        if any(keyword in title_lower for keyword in variety_keywords):
            return 'variety'
        
        # 判断音乐
        music_keywords = ['音乐', 'music', '歌曲', '专辑', 'album', '单曲']
        if any(keyword in title_lower for keyword in music_keywords):
            return 'music'
        
        # 判断番剧
        anime_keywords = ['动画', 'anime', '番剧', '新番', 'アニメ']
        if any(keyword in title_lower for keyword in anime_keywords):
            return 'anime'
        
        # 默认为电影
        return 'video'

