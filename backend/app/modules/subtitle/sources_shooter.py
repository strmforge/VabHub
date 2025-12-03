"""
射手字幕客户端
"""

from typing import List, Optional
from loguru import logger
import httpx
import hashlib
import os

from .sources import SubtitleSource, SubtitleInfo


class ShooterClient(SubtitleSource):
    """射手字幕客户端"""
    
    def __init__(self):
        """初始化射手字幕客户端"""
        self.base_url = "https://www.shooter.cn/api/subapi.php"
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值（射手字幕使用文件哈希匹配）
        
        Args:
            file_path: 文件路径
            
        Returns:
            哈希值（格式：文件大小,前64KB的MD5,整个文件的MD5）
        """
        try:
            file_size = os.path.getsize(file_path)
            
            # 读取前64KB
            with open(file_path, 'rb') as f:
                first_64k = f.read(64 * 1024)
                first_hash = hashlib.md5(first_64k).hexdigest()
            
            # 读取整个文件
            with open(file_path, 'rb') as f:
                full_content = f.read()
                full_hash = hashlib.md5(full_content).hexdigest()
            
            # 格式：文件大小,前64KB的MD5,整个文件的MD5
            return f"{file_size},{first_hash},{full_hash}"
        except Exception as e:
            logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return ""
    
    async def search(
        self,
        title: str,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        language: str = "zh"
    ) -> List[SubtitleInfo]:
        """
        搜索字幕（射手字幕主要使用文件哈希搜索）
        
        Args:
            title: 媒体标题
            year: 年份
            season: 季数（电视剧）
            episode: 集数（电视剧）
            language: 语言
            
        Returns:
            字幕信息列表
        """
        # 注意：射手字幕主要支持文件哈希搜索，不支持标题搜索
        # 这里返回空列表，实际使用时需要通过文件哈希搜索
        logger.warning("射手字幕不支持标题搜索，请使用文件哈希搜索")
        return []
    
    async def search_by_hash(self, file_hash: str, language: str = "zh") -> List[SubtitleInfo]:
        """
        通过文件哈希搜索字幕
        
        Args:
            file_hash: 文件哈希（格式：文件大小,前64KB的MD5,整个文件的MD5）
            language: 语言
            
        Returns:
            字幕信息列表
        """
        try:
            # 射手字幕API参数
            params = {
                "filehash": file_hash,
                "pathinfo": "",
                "format": "json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # 解析结果
            subtitles = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "Files" in item:
                        files = item.get("Files", [])
                        for file_info in files:
                            subtitle_info = SubtitleInfo(
                                title=file_info.get("Ext", ""),
                                language=language,
                                language_code="chi" if language == "zh" else "eng",
                                format=file_info.get("Ext", "srt"),
                                download_url=file_info.get("Link", ""),
                                file_size=0,
                                source="shooter",
                                source_id=""
                            )
                            subtitles.append(subtitle_info)
            
            logger.info(f"射手字幕搜索完成: 找到 {len(subtitles)} 个字幕")
            return subtitles
            
        except Exception as e:
            logger.error(f"射手字幕搜索失败: {e}")
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
            if not subtitle_info.download_url:
                logger.error("字幕下载URL为空")
                return False
            
            # 下载字幕文件
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                download_response = await client.get(subtitle_info.download_url)
                download_response.raise_for_status()
                
                # 保存文件
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    f.write(download_response.content)
                
                logger.info(f"字幕下载成功: {save_path}")
                return True
            
        except Exception as e:
            logger.error(f"射手字幕下载失败: {e}")
            return False

