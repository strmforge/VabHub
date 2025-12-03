"""
媒体重命名引擎
根据模板生成新的文件名
"""

import re
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from app.constants.media_types import is_tv_like
from .parser import MediaInfo


class MediaRenamer:
    """媒体重命名引擎"""
    
    def __init__(self):
        """初始化重命名引擎"""
        # 默认重命名模板
        self.templates = {
            "movie": "{title} ({year})/{title} ({year}) [{quality}]",
            "tv": "{title} ({year})/Season {season:02d}/{title} - S{season:02d}E{episode:02d} - {episode_name} [{quality}]",
            "anime": "{title} ({year})/Season {season:02d}/{title} - S{season:02d}E{episode:02d} - {episode_name} [{quality}]",
            "short_drama": "短剧/{title}/S{season:02d}/{title}.S{season:02d}E{episode:02d} {source} {quality}",
        }
        # 兼容显式模板名称
        self.templates["shortdrama_default"] = self.templates["short_drama"]
    
    def generate_name(
        self,
        media_info: MediaInfo,
        template: Optional[str] = None,
        custom_variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        根据模板生成新文件名
        
        Args:
            media_info: 媒体信息
            template: 自定义模板（如果为None，使用默认模板）
            custom_variables: 自定义变量字典
            
        Returns:
            新文件名（不含扩展名）
        """
        # 选择模板
        if template:
            template = self.templates.get(template, template)
        else:
            template = self.templates.get(media_info.media_type, self.templates["movie"])
        
        # 准备变量字典
        season_value = media_info.season or (1 if is_tv_like(media_info.media_type) else 0)
        episode_value = media_info.episode or (1 if is_tv_like(media_info.media_type) else 0)

        variables = {
            "title": media_info.title,
            "year": media_info.year or "",
            "season": season_value,
            "episode": episode_value,
            "episode_name": media_info.episode_name or "",
            "quality": media_info.quality or "",
            "resolution": media_info.resolution or "",
            "codec": media_info.codec or "",
            "source": media_info.source or "",
            "group": media_info.group or "",
            "language": media_info.language or "",
            "subtitle": media_info.subtitle or "",
            "episode_span": self._extract_episode_span(media_info, episode_value),
        }
        
        # 添加自定义变量
        if custom_variables:
            variables.update(custom_variables)
        
        # 替换模板中的变量
        try:
            new_name = template.format(**variables)
        except KeyError as e:
            logger.warning(f"模板变量缺失: {e}, 使用默认值")
            # 对于缺失的变量，使用空字符串
            new_name = template
            for key, value in variables.items():
                new_name = new_name.replace(f"{{{key}}}", str(value))
                new_name = new_name.replace(f"{{{key}:02d}}", f"{value:02d}" if isinstance(value, int) else str(value))
        
        # 清理文件名：移除不允许的字符
        new_name = self._sanitize_filename(new_name)
        
        return new_name
    
    def _extract_episode_span(self, media_info: MediaInfo, episode_value: int) -> str:
        """尝试从原始标题解析集数范围，若失败则回退到单集编号。"""
        raw = media_info.raw_title or ""
        match = re.search(r"(E\d{2,3}\s*[-~]\s*E?\d{2,3})", raw, re.IGNORECASE)
        if match:
            return match.group(1).upper().replace(" ", "")
        if episode_value:
            return f"E{episode_value:02d}"
        return ""
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不允许的字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # Windows不允许的字符：< > : " / \ | ? *
        # 替换为安全的字符
        filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
        
        # 移除多余的点（文件名不能以点开头或结尾）
        filename = filename.strip('.')
        
        # 移除多余的空格和分隔符
        filename = re.sub(r'\s+', ' ', filename)
        filename = re.sub(r'[-_]+', '-', filename)
        filename = filename.strip(' -_')
        
        # 限制文件名长度（Windows限制为255字符）
        if len(filename) > 200:  # 留一些余量
            filename = filename[:200].rstrip(' -_')
        
        return filename
    
    async def rename_file(
        self,
        file_path: str,
        new_name: str,
        keep_extension: bool = True
    ) -> str:
        """
        重命名文件
        
        Args:
            file_path: 原文件路径
            new_name: 新文件名（不含扩展名）
            keep_extension: 是否保留原扩展名
            
        Returns:
            新文件路径
        """
        file_path_obj = Path(file_path)
        
        # 获取原扩展名
        extension = file_path_obj.suffix if keep_extension else ""
        
        # 构建新文件路径
        new_file_path = file_path_obj.parent / f"{new_name}{extension}"
        
        # 如果新文件已存在，添加序号
        counter = 1
        original_new_file_path = new_file_path
        while new_file_path.exists():
            new_file_path = original_new_file_path.parent / f"{new_name} ({counter}){extension}"
            counter += 1
        
        # 重命名文件
        try:
            file_path_obj.rename(new_file_path)
            logger.info(f"文件重命名成功: {file_path} -> {new_file_path}")
            return str(new_file_path)
        except Exception as e:
            logger.error(f"文件重命名失败: {file_path} -> {new_file_path}, 错误: {e}")
            raise

