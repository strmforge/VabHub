"""
小说来源适配器抽象基类

定义不关心具体站点实现的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Iterable

from .models import StandardChapter, NovelMetadata


class NovelSourceAdapter(ABC):
    """
    抽象的小说来源适配器，不关心具体站点。
    
    用户需要实现此接口来适配不同的小说来源（网站、API、本地文件等）。
    """
    
    @abstractmethod
    def get_metadata(self) -> NovelMetadata:
        """
        获取小说的元数据信息。
        
        Returns:
            NovelMetadata: 小说的元数据（标题、作者、简介等）
        """
        ...
    
    @abstractmethod
    def iter_chapters(self) -> Iterable[StandardChapter]:
        """
        迭代获取所有章节。
        
        返回一个可迭代对象，按顺序生成 StandardChapter。
        
        Yields:
            StandardChapter: 标准化的章节数据
        """
        ...

