"""
漫画源适配器基类
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.manga_source import MangaSource
from app.schemas.manga_remote import (
    RemoteMangaSearchResult,
    RemoteMangaSeries,
    RemoteMangaChapter,
    RemoteMangaPage,
)
from app.schemas.manga_source import MangaLibraryInfo


class BaseMangaSourceAdapter(ABC):
    """漫画源适配器基类"""

    def __init__(self, source: MangaSource) -> None:
        self.source = source

    @abstractmethod
    async def ping(self) -> bool:
        """
        检查当前源是否可用。
        
        Phase 2 建议实现为最简单的 HTTP 探活：
        - 对 OPDS/Komga/Kavita：请求根 OPDS feed 或健康检查接口
        - 对 Suwayomi：请求 /ping 或 /api/v1/info 之类
        """
        pass

    @abstractmethod
    async def search_series(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> RemoteMangaSearchResult:
        """
        按关键字搜索漫画（Series 级）。
        
        必须返回统一的分页结构。
        """
        pass

    @abstractmethod
    async def get_series_detail(
        self,
        remote_series_id: str,
    ) -> Optional[RemoteMangaSeries]:
        """
        获取单个漫画的详情（包括基本信息 + 章节列表）。
        
        remote_series_id 为该源内部使用的 ID。
        """
        pass

    @abstractmethod
    async def list_libraries(self) -> List[MangaLibraryInfo]:
        """列出当前源下的库/书架列表，用于连接测试和预览。"""
        pass

    @abstractmethod
    async def list_series_by_library(
        self,
        library_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> RemoteMangaSearchResult:
        """按库/书架浏览漫画系列，返回统一分页结构。"""
        pass

    @abstractmethod
    async def list_chapters(
        self,
        remote_series_id: str,
    ) -> List[RemoteMangaChapter]:
        """
        返回指定漫画下的所有章节（或卷/话），仅用于展示。
        
        Phase 2 不做实际下载。
        """
        pass

    @abstractmethod
    async def list_pages(
        self,
        remote_series_id: str,
        remote_chapter_id: str,
    ) -> List[RemoteMangaPage]:
        """
        返回该章节的所有页面（图片）信息，按阅读顺序排序。
        """
        pass

    @abstractmethod
    async def fetch_page_content(
        self,
        page: RemoteMangaPage,
    ) -> bytes:
        """
        下载单页图片的二进制内容。
        """
        pass

