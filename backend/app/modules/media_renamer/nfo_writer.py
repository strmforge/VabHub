"""
NFO文件写入模块
支持Emby/Jellyfin/Plex格式的NFO文件生成
包含TVDB ID、TMDB ID、IMDB ID等信息
"""
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
import xml.etree.ElementTree as ET
from xml.dom import minidom


class NFOWriter:
    """NFO文件写入器"""
    
    def __init__(self, format: str = "emby"):
        """
        初始化NFO写入器
        
        Args:
            format: NFO格式（emby/jellyfin/plex），默认emby
        """
        self.format = format.lower()
        if self.format not in ["emby", "jellyfin", "plex"]:
            logger.warning(f"不支持的NFO格式: {format}，使用默认格式: emby")
            self.format = "emby"
    
    def write_nfo(
        self,
        file_path: str,
        media_info: Dict[str, Any],
        overwrite: bool = False
    ) -> bool:
        """
        写入NFO文件
        
        Args:
            file_path: 媒体文件路径
            media_info: 媒体信息字典，包含：
                - title: 标题
                - year: 年份
                - media_type: 媒体类型（movie/tv）
                - tmdb_id: TMDB ID（可选）
                - tvdb_id: TVDB ID（可选）
                - imdb_id: IMDB ID（可选）
                - overview: 概述（可选）
                - poster_url: 海报URL（可选）
                - backdrop_url: 背景图URL（可选）
                - season: 季数（电视剧，可选）
                - episode: 集数（电视剧，可选）
            overwrite: 是否覆盖已存在的NFO文件
            
        Returns:
            是否成功
        """
        try:
            media_file = Path(file_path)
            if not media_file.exists():
                logger.error(f"媒体文件不存在: {file_path}")
                return False
            
            # 生成NFO文件路径（与媒体文件同名，扩展名为.nfo）
            nfo_path = media_file.with_suffix('.nfo')
            
            # 检查NFO文件是否已存在
            if nfo_path.exists() and not overwrite:
                logger.debug(f"NFO文件已存在，跳过: {nfo_path}")
                return True
            
            # 根据格式生成NFO内容
            if self.format == "emby" or self.format == "jellyfin":
                nfo_content = self._generate_emby_nfo(media_info)
            elif self.format == "plex":
                nfo_content = self._generate_plex_nfo(media_info)
            else:
                logger.error(f"不支持的NFO格式: {self.format}")
                return False
            
            # 写入文件
            nfo_path.write_text(nfo_content, encoding='utf-8')
            logger.info(f"NFO文件写入成功: {nfo_path}")
            return True
            
        except Exception as e:
            logger.error(f"写入NFO文件失败: {e}")
            return False
    
    def _generate_emby_nfo(self, media_info: Dict[str, Any]) -> str:
        """
        生成Emby/Jellyfin格式的NFO文件内容
        
        Args:
            media_info: 媒体信息字典
            
        Returns:
            NFO文件内容（XML字符串）
        """
        # 支持多种字段名
        media_type = media_info.get("type") or media_info.get("media_type", "movie")
        
        if media_type == "movie":
            return self._generate_movie_nfo(media_info)
        else:
            return self._generate_tv_nfo(media_info)
    
    def _generate_movie_nfo(self, media_info: Dict[str, Any]) -> str:
        """生成电影NFO文件内容"""
        root = ET.Element("movie")
        
        # 基本信息
        title = media_info.get("title", "")
        if title:
            ET.SubElement(root, "title").text = title
        
        year = media_info.get("year")
        if year:
            ET.SubElement(root, "year").text = str(year)
        
        # ID信息
        tmdb_id = media_info.get("tmdb_id")
        if tmdb_id:
            ET.SubElement(root, "tmdbid").text = str(tmdb_id)
        
        imdb_id = media_info.get("imdb_id")
        if imdb_id:
            ET.SubElement(root, "imdbid").text = imdb_id
        
        # 概述（转义XML特殊字符）
        overview = media_info.get("overview")
        if overview:
            # 转义XML特殊字符
            overview_escaped = overview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            ET.SubElement(root, "plot").text = overview_escaped
        
        # 海报和背景图
        poster_url = media_info.get("poster_url")
        if poster_url:
            ET.SubElement(root, "poster").text = poster_url
        
        backdrop_url = media_info.get("backdrop_url")
        if backdrop_url:
            ET.SubElement(root, "fanart").text = backdrop_url
        
        # 生成格式化的XML
        return self._format_xml(root)
    
    def _generate_tv_nfo(self, media_info: Dict[str, Any]) -> str:
        """生成电视剧NFO文件内容"""
        season = media_info.get("season")
        episode = media_info.get("episode")
        
        # 如果是单集，生成episodedetails格式
        if season is not None and episode is not None:
            root = ET.Element("episodedetails")
            
            # 基本信息
            title = media_info.get("title", "")
            if title:
                ET.SubElement(root, "title").text = title
            
            season_num = season
            episode_num = episode
            ET.SubElement(root, "season").text = str(season_num)
            ET.SubElement(root, "episode").text = str(episode_num)
            
            # 概述（转义XML特殊字符）
            overview = media_info.get("overview")
            if overview:
                overview_escaped = overview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                ET.SubElement(root, "plot").text = overview_escaped
            
            # ID信息
            tmdb_id = media_info.get("tmdb_id")
            if tmdb_id:
                ET.SubElement(root, "tmdbid").text = str(tmdb_id)
            
            tvdb_id = media_info.get("tvdb_id")
            if tvdb_id:
                ET.SubElement(root, "tvdbid").text = str(tvdb_id)
            
            imdb_id = media_info.get("imdb_id")
            if imdb_id:
                ET.SubElement(root, "imdbid").text = imdb_id
            
            # 海报和背景图
            poster_url = media_info.get("poster_url")
            if poster_url:
                ET.SubElement(root, "thumb").text = poster_url
            
            backdrop_url = media_info.get("backdrop_url")
            if backdrop_url:
                ET.SubElement(root, "fanart").text = backdrop_url
            
            return self._format_xml(root)
        else:
            # 如果是整部剧，生成tvshow格式
            root = ET.Element("tvshow")
            
            # 基本信息
            title = media_info.get("title", "")
            if title:
                ET.SubElement(root, "title").text = title
            
            year = media_info.get("year")
            if year:
                ET.SubElement(root, "year").text = str(year)
            
            # ID信息
            tmdb_id = media_info.get("tmdb_id")
            if tmdb_id:
                ET.SubElement(root, "tmdbid").text = str(tmdb_id)
            
            tvdb_id = media_info.get("tvdb_id")
            if tvdb_id:
                ET.SubElement(root, "tvdbid").text = str(tvdb_id)
            
            imdb_id = media_info.get("imdb_id")
            if imdb_id:
                ET.SubElement(root, "imdbid").text = imdb_id
            
            # 概述（转义XML特殊字符）
            overview = media_info.get("overview")
            if overview:
                overview_escaped = overview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                ET.SubElement(root, "plot").text = overview_escaped
            
            # 海报和背景图
            poster_url = media_info.get("poster_url")
            if poster_url:
                ET.SubElement(root, "poster").text = poster_url
            
            backdrop_url = media_info.get("backdrop_url")
            if backdrop_url:
                ET.SubElement(root, "fanart").text = backdrop_url
            
            return self._format_xml(root)
    
    def _generate_plex_nfo(self, media_info: Dict[str, Any]) -> str:
        """
        生成Plex格式的NFO文件内容
        
        Args:
            media_info: 媒体信息字典
            
        Returns:
            NFO文件内容（XML字符串）
        """
        # Plex使用与Emby/Jellyfin类似的格式，但有一些差异
        # 这里先使用Emby格式（Plex也支持）
        return self._generate_emby_nfo(media_info)
    
    def _format_xml(self, root: ET.Element) -> str:
        """
        格式化XML元素为字符串
        
        Args:
            root: XML根元素
            
        Returns:
            格式化的XML字符串
        """
        # 转换为字符串
        rough_string = ET.tostring(root, encoding='unicode')
        
        # 使用minidom格式化
        reparsed = minidom.parseString(rough_string)
        
        # 返回格式化的XML（带UTF-8声明）
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

