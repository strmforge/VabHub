"""
字幕源客户端
支持多个字幕源：OpenSubtitles、SubHD等
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger
import httpx
import hashlib
import os


@dataclass
class SubtitleInfo:
    """字幕信息"""
    title: str  # 字幕标题
    language: str  # 语言
    language_code: str  # 语言代码
    format: str  # 格式：srt, ass等
    download_url: str  # 下载URL
    file_size: int  # 文件大小（字节）
    rating: Optional[int] = None  # 评分
    downloads: Optional[int] = None  # 下载次数
    source: str = ""  # 来源
    source_id: str = ""  # 来源ID
    is_forced: bool = False  # 是否强制字幕
    is_hearing_impaired: bool = False  # 是否听力 impaired


class SubtitleSource(ABC):
    """字幕源抽象基类"""
    
    @abstractmethod
    async def search(
        self,
        title: str,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        language: str = "zh"
    ) -> List[SubtitleInfo]:
        """
        搜索字幕
        
        Args:
            title: 媒体标题
            year: 年份
            season: 季数（电视剧）
            episode: 集数（电视剧）
            language: 语言
            
        Returns:
            字幕信息列表
        """
        pass
    
    @abstractmethod
    async def download(self, subtitle_info: SubtitleInfo, save_path: str) -> bool:
        """
        下载字幕
        
        Args:
            subtitle_info: 字幕信息
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        pass


class OpenSubtitlesClient(SubtitleSource):
    """OpenSubtitles客户端"""
    
    def __init__(self, api_key: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        """
        初始化OpenSubtitles客户端
        
        Args:
            api_key: API密钥（可选）
            username: 用户名（可选）
            password: 密码（可选）
        """
        self.api_key = api_key
        self.username = username
        self.password = password
        self.base_url = "https://api.opensubtitles.com/api/v1"
        self.token = None
    
    async def _authenticate(self) -> bool:
        """
        认证获取token
        
        Returns:
            是否成功
        """
        if not self.username or not self.password:
            # 如果没有用户名和密码，使用API密钥
            if self.api_key:
                self.token = self.api_key
                return True
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/login",
                    json={
                        "username": self.username,
                        "password": self.password
                    },
                    headers={
                        "Api-Key": self.api_key or "your-api-key",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                self.token = data.get("token")
                return self.token is not None
        except Exception as e:
            logger.error(f"OpenSubtitles认证失败: {e}")
            return False
    
    async def search(
        self,
        title: str,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        language: str = "zh"
    ) -> List[SubtitleInfo]:
        """
        搜索字幕
        
        Args:
            title: 媒体标题
            year: 年份
            season: 季数（电视剧）
            episode: 集数（电视剧）
            language: 语言
            
        Returns:
            字幕信息列表
        """
        try:
            # 认证
            if not self.token:
                if not await self._authenticate():
                    logger.warning("OpenSubtitles认证失败，跳过搜索")
                    return []
            
            # 构建搜索查询
            query = title
            if year:
                query += f" {year}"
            
            # 语言代码映射
            language_map = {
                "zh": "chi",
                "en": "eng",
                "ja": "jpn",
                "ko": "kor"
            }
            language_code = language_map.get(language, "chi")
            
            # 搜索参数
            params = {
                "query": query,
                "languages": language_code
            }
            
            if season and episode:
                # 电视剧搜索
                params["season_number"] = season
                params["episode_number"] = episode
                params["type"] = "episode"
            else:
                # 电影搜索
                params["type"] = "movie"
            
            # 发送搜索请求
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Api-Key": self.api_key or "your-api-key",
                    "Authorization": f"Bearer {self.token}" if self.token else ""
                }
                response = await client.get(
                    f"{self.base_url}/subtitles",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
            
            # 解析结果
            subtitles = []
            for item in data.get("data", []):
                attributes = item.get("attributes", {})
                files = attributes.get("files", [])
                if not files:
                    continue
                
                # 获取第一个文件（通常是SRT格式）
                file_info = files[0]
                file_id = file_info.get("file_id")
                if not file_id:
                    continue
                
                # 提取文件格式
                file_name = file_info.get("file_name", "")
                file_format = file_name.split(".")[-1].lower() if "." in file_name else "srt"
                
                # 获取评分和下载次数
                feature_details = attributes.get("feature_details", {})
                ratings = attributes.get("ratings", {})
                rating = ratings.get("average", 0) if isinstance(ratings, dict) else 0
                download_count = attributes.get("download_count", 0)
                
                subtitle_info = SubtitleInfo(
                    title=attributes.get("title", "") or attributes.get("release", ""),
                    language=language,
                    language_code=language_code,
                    format=file_format,
                    download_url=str(file_id),  # 使用file_id作为下载标识
                    file_size=file_info.get("file_size", 0),
                    rating=int(rating) if rating else None,
                    downloads=download_count,
                    source="opensubtitles",
                    source_id=str(item.get("id", "")),
                    is_forced=feature_details.get("hearing_impaired", False) or feature_details.get("forced", False),
                    is_hearing_impaired=feature_details.get("hearing_impaired", False)
                )
                subtitles.append(subtitle_info)
            
            logger.info(f"OpenSubtitles搜索完成: {title}, 找到 {len(subtitles)} 个字幕")
            return subtitles
            
        except Exception as e:
            logger.error(f"OpenSubtitles搜索失败: {e}")
            return []
    
    async def download(self, subtitle_info: SubtitleInfo, save_path: str) -> bool:
        """
        下载字幕
        
        Args:
            subtitle_info: 字幕信息
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            # 认证
            if not self.token:
                if not await self._authenticate():
                    logger.warning("OpenSubtitles认证失败，跳过下载")
                    return False
            
            # 使用file_id获取下载链接
            # OpenSubtitles API v1 使用 /download 端点
            # 需要 file_id (在 subtitle_info.download_url 中，实际上是 file_id)
            file_id = subtitle_info.download_url  # 这里应该是file_id
            
            # 如果 download_url 是完整的URL，提取file_id
            if "/" in file_id:
                file_id = file_id.split("/")[-1]
            
            # 发送下载请求
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "Api-Key": self.api_key or "your-api-key",
                    "Authorization": f"Bearer {self.token}" if self.token else "",
                    "Content-Type": "application/json"
                }
                
                # 使用 /download 端点
                response = await client.post(
                    f"{self.base_url}/download",
                    json={"file_id": int(file_id)},
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
            
            # 获取下载链接
            download_link = data.get("link")
            if not download_link:
                logger.error("未获取到下载链接")
                return False
            
            # 下载字幕文件
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                download_response = await client.get(download_link)
                download_response.raise_for_status()
                
                # 保存文件
                import os
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    f.write(download_response.content)
                
                logger.info(f"字幕下载成功: {save_path}")
                return True
            
        except Exception as e:
            logger.error(f"OpenSubtitles下载失败: {e}")
            return False


class SubHDClient(SubtitleSource):
    """SubHD客户端（示例实现）"""
    
    def __init__(self):
        """初始化SubHD客户端"""
        self.base_url = "https://subhd.tv"
    
    async def search(
        self,
        title: str,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        language: str = "zh"
    ) -> List[SubtitleInfo]:
        """
        搜索字幕
        
        Args:
            title: 媒体标题
            year: 年份
            season: 季数（电视剧）
            episode: 集数（电视剧）
            language: 语言
            
        Returns:
            字幕信息列表
        """
        # TODO: 实现SubHD搜索逻辑
        logger.warning("SubHD搜索功能待实现")
        return []
    
    async def download(self, subtitle_info: SubtitleInfo, save_path: str) -> bool:
        """
        下载字幕
        
        Args:
            subtitle_info: 字幕信息
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        # TODO: 实现SubHD下载逻辑
        logger.warning("SubHD下载功能待实现")
        return False

