"""
小说模块基础数据结构
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class StandardChapter:
    """
    标准化章节结构
    
    用于在不同来源之间统一章节数据格式。
    """
    index: int  # 章节顺序（从 1 开始）
    title: str  # 章节标题
    content: str  # 章节内容（可以是 markdown / 纯文本 / 简单 HTML）


@dataclass
class NovelMetadata:
    """
    小说元数据
    
    用于描述小说的基本信息。
    """
    title: str  # 书名
    author: Optional[str] = None  # 作者
    description: Optional[str] = None  # 简介
    language: str = "zh-CN"  # 语言代码，如 "zh-CN", "en"
    tags: Optional[List[str]] = None  # 标签列表

