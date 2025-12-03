"""
字幕文件处理器
识别、重命名和处理字幕文件
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger
import re


class SubtitleHandler:
    """字幕文件处理器"""
    
    # 字幕文件扩展名
    SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.ssa', '.vtt', '.sub']
    
    # 语言代码映射
    LANGUAGE_CODES = {
        'chi': 'chi',
        'chinese': 'chi',
        'zh-cn': 'chi',
        'zh': 'chi',
        'eng': 'eng',
        'english': 'eng',
        'en': 'eng',
        'jpn': 'jpn',
        'japanese': 'jpn',
        'ja': 'jpn'
    }
    
    async def find_subtitle_files(self, media_file_path: str) -> List[str]:
        """
        查找媒体文件关联的字幕文件
        
        Args:
            media_file_path: 媒体文件路径
        
        Returns:
            字幕文件列表
        """
        media_path = Path(media_file_path)
        media_dir = media_path.parent
        media_stem = media_path.stem
        
        subtitle_files = []
        
        # 查找同名的字幕文件
        for ext in self.SUBTITLE_EXTENSIONS:
            # 精确匹配：movie.srt
            subtitle_path = media_dir / f"{media_stem}{ext}"
            if subtitle_path.exists() and subtitle_path.is_file():
                subtitle_files.append(str(subtitle_path))
                continue
            
            # 语言匹配：movie.chi.zh-cn.srt
            for lang_code in self.LANGUAGE_CODES.keys():
                # 尝试多种格式
                patterns = [
                    f"{media_stem}.{lang_code}{ext}",
                    f"{media_stem}.{lang_code}.{ext}",
                    f"{media_stem}.default.{lang_code}{ext}",
                    f"{media_stem}.{lang_code}.zh-cn{ext}",
                ]
                
                for pattern in patterns:
                    subtitle_path = media_dir / pattern
                    if subtitle_path.exists() and subtitle_path.is_file():
                        if str(subtitle_path) not in subtitle_files:
                            subtitle_files.append(str(subtitle_path))
                        break
        
        logger.info(f"找到 {len(subtitle_files)} 个字幕文件: {media_file_path}")
        return subtitle_files
    
    def generate_subtitle_name(
        self,
        media_info: Dict[str, Any],
        subtitle_file: str,
        language: Optional[str] = None
    ) -> str:
        """
        生成字幕文件名（匹配媒体文件名）
        
        Args:
            media_info: 媒体信息
            subtitle_file: 字幕文件路径
            language: 语言代码（如果为None，则从文件名中提取）
        
        Returns:
            新的字幕文件名
        """
        # 从原文件名提取语言代码
        if not language:
            language = self._extract_language_from_filename(subtitle_file)
        
        # 默认语言为中文
        if not language:
            language = 'chi'
        
        media_type = media_info.get('type', 'movie')
        subtitle_ext = Path(subtitle_file).suffix
        
        if media_type == 'movie':
            # 电影：Title (Year).chi.srt
            title = media_info.get('title', 'unknown')
            year = media_info.get('year', '')
            if year:
                base_name = f"{title} ({year})"
            else:
                base_name = title
        elif media_type == 'tv' or media_type == 'tv_series':
            # 电视剧：Title - S01E01.chi.srt
            title = media_info.get('title', 'unknown')
            season = media_info.get('season', 1)
            episode = media_info.get('episode', 1)
            base_name = f"{title} - S{season:02d}E{episode:02d}"
        else:
            base_name = media_info.get('title', 'unknown')
        
        # 清理文件名
        base_name = self._sanitize_filename(base_name)
        
        return f"{base_name}.{language}{subtitle_ext}"
    
    def _extract_language_from_filename(self, filename: str) -> Optional[str]:
        """从文件名提取语言代码"""
        filename_lower = filename.lower()
        
        for lang_key, lang_code in self.LANGUAGE_CODES.items():
            if lang_key in filename_lower:
                return lang_code
        
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        filename = filename.strip(' .')
        return filename
    
    async def rename_subtitle_file(
        self,
        subtitle_file: str,
        new_name: str,
        target_dir: Optional[str] = None
    ) -> str:
        """
        重命名字幕文件
        
        Args:
            subtitle_file: 原字幕文件路径
            new_name: 新文件名
            target_dir: 目标目录（如果为None，则在同一目录）
        
        Returns:
            新的字幕文件路径
        """
        subtitle_path = Path(subtitle_file)
        
        if target_dir:
            target_path = Path(target_dir) / new_name
        else:
            target_path = subtitle_path.parent / new_name
        
        # 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 重命名文件
        subtitle_path.rename(target_path)
        
        logger.info(f"重命名字幕文件: {subtitle_file} -> {target_path}")
        return str(target_path)

