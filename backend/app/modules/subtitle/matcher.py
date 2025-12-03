"""
字幕匹配器
根据媒体文件信息匹配最合适的字幕
"""

from typing import List, Optional
from pathlib import Path
from loguru import logger
import hashlib
import os

from .sources import SubtitleSource, SubtitleInfo
from ..media_renamer.parser import MediaInfo


class SubtitleMatcher:
    """字幕匹配器"""
    
    def __init__(self, sources: List[SubtitleSource]):
        """
        初始化匹配器
        
        Args:
            sources: 字幕源列表
        """
        self.sources = sources
    
    async def match_subtitle(
        self,
        media_info: MediaInfo,
        media_file_path: str,
        language: str = "zh",
        preferred_sources: Optional[List[str]] = None,
        use_hash_matching: bool = True
    ) -> Optional[SubtitleInfo]:
        """
        匹配字幕
        
        Args:
            media_info: 媒体信息
            media_file_path: 媒体文件路径
            language: 语言
            preferred_sources: 优先使用的字幕源列表
            
        Returns:
            最匹配的字幕信息
        """
        # 在所有字幕源中搜索
        all_subtitles = []
        
        for source in self.sources:
            # 如果指定了优先源，跳过非优先源
            if preferred_sources and source.__class__.__name__ not in preferred_sources:
                continue
            
            try:
                # 对于射手字幕，使用文件哈希搜索
                source_class_name = source.__class__.__name__
                if "Shooter" in source_class_name:
                    if use_hash_matching:
                        # 射手字幕需要特殊的哈希格式（文件大小,前64KB的MD5,整个文件的MD5）
                        file_hash = self._calculate_shooter_hash(media_file_path)
                        if file_hash:
                            subtitles = await source.search_by_hash(file_hash, language)
                            all_subtitles.extend(subtitles)
                else:
                    # 其他字幕源使用标题搜索
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
        
        if not all_subtitles:
            logger.warning(f"未找到字幕: {media_info.title}")
            return None
        
        # 选择最佳字幕
        best_subtitle = self._select_best_subtitle(all_subtitles, media_info)
        
        return best_subtitle
    
    def _select_best_subtitle(
        self,
        subtitles: List[SubtitleInfo],
        media_info: MediaInfo
    ) -> Optional[SubtitleInfo]:
        """
        选择最佳字幕
        
        Args:
            subtitles: 字幕列表
            media_info: 媒体信息
            
        Returns:
            最佳字幕信息
        """
        if not subtitles:
            return None
        
        # 评分标准：
        # 1. 评分（rating）越高越好
        # 2. 下载次数（downloads）越多越好
        # 3. 文件大小适中（不要太小，也不要太大）
        # 4. 格式偏好（SRT > ASS > 其他）
        
        best_subtitle = None
        best_score = 0
        
        for subtitle in subtitles:
            score = 0
            
            # 评分（0-5分，最高25分）
            if subtitle.rating:
                score += subtitle.rating * 5
            
            # 下载次数（归一化到0-20分）
            if subtitle.downloads:
                # 假设下载次数在0-10000之间
                normalized_downloads = min(subtitle.downloads / 10000, 1.0)
                score += normalized_downloads * 20
            
            # 文件大小（适中最好，0-15分）
            if subtitle.file_size:
                # 假设最佳大小在10KB-500KB之间
                if 10 * 1024 <= subtitle.file_size <= 500 * 1024:
                    score += 15
                elif subtitle.file_size < 10 * 1024:
                    # 太小可能不完整
                    score += 5
                elif subtitle.file_size > 500 * 1024:
                    # 太大可能有额外内容
                    score += 10
            
            # 格式偏好（0-10分）
            format_scores = {
                "srt": 10,
                "ass": 8,
                "ssa": 6,
                "vtt": 5,
                "sub": 4
            }
            score += format_scores.get(subtitle.format.lower(), 3)
            
            # 检查是否匹配媒体信息
            if media_info.season and media_info.episode:
                # 电视剧：检查季数和集数是否匹配
                # （这里简化处理，实际应该从字幕标题中提取）
                pass
            
            if score > best_score:
                best_score = score
                best_subtitle = subtitle
        
        logger.info(f"选择最佳字幕: {best_subtitle.title if best_subtitle else 'None'}, 评分: {best_score}")
        return best_subtitle
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值（用于字幕匹配）
        
        Args:
            file_path: 文件路径
            
        Returns:
            哈希值
        """
        try:
            # 计算文件的前64KB的哈希值（OpenSubtitles标准）
            with open(file_path, 'rb') as f:
                chunk = f.read(64 * 1024)
                hash_value = hashlib.md5(chunk).hexdigest()
            return hash_value
        except Exception as e:
            logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return ""
    
    def _calculate_shooter_hash(self, file_path: str) -> str:
        """
        计算射手字幕所需的特殊文件哈希
        格式：文件大小,前64KB的MD5,整个文件的MD5
        
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
            logger.error(f"计算射手字幕哈希失败: {file_path}, 错误: {e}")
            return ""

