"""
统一待整理收件箱模型
"""

from pathlib import Path
from typing import Optional, NamedTuple, List


class InboxItem(NamedTuple):
    """
    待整理收件箱中的项目
    
    表示一个待处理的文件或目录。
    """
    path: Path  # 文件或目录路径
    
    # PT 下载任务相关 hint
    download_task_id: Optional[int] = None  # 关联的下载任务 ID
    source_site_id: Optional[int] = None  # 来源站点 ID
    source_site_name: Optional[str] = None  # 来源站点名称
    source_category: Optional[str] = None  # PT 站点的分类字段（如 "Movies", "TV", "音乐", "有声书" 等）
    source_tags: Optional[List[str]] = None  # PT 站点或种子标签（如 ["有声书", "漫画"]）

