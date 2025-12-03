"""
通用 HTTP 漫画源适配器

占位实现，Phase 2 暂不实现具体逻辑
"""
from typing import List, Optional
from loguru import logger

from app.models.manga_source import MangaSource
from app.modules.manga_sources.adapter_base import BaseMangaSourceAdapter
from app.schemas.manga_remote import (
    RemoteMangaSearchResult,
    RemoteMangaSeries,
    RemoteMangaChapter,
    RemoteMangaPage,
)
from app.schemas.manga_source import MangaLibraryInfo


class GenericHttpMangaSourceAdapter(BaseMangaSourceAdapter):
    """通用 HTTP 漫画源适配器（占位）"""

    def __init__(self, source: MangaSource) -> None:
        super().__init__(source)
        self.base_url = source.base_url.rstrip('/')

    async def ping(self) -> bool:
        """检查源是否可用（占位实现）"""
        logger.warning(f"Generic HTTP adapter ping not implemented for {self.base_url}")
        return False

    async def search_series(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> RemoteMangaSearchResult:
        """搜索漫画系列（占位实现）"""
        logger.warning(f"Generic HTTP adapter search not implemented")
        return RemoteMangaSearchResult(
            total=0,
            page=page,
            page_size=page_size,
            items=[]
        )

    async def list_libraries(self) -> List[MangaLibraryInfo]:
        """占位实现：当前不支持列库，直接返回空列表。"""
        logger.warning(f"Generic HTTP adapter list_libraries not implemented for {self.base_url}")
        return []

    async def get_series_detail(
        self,
        remote_series_id: str,
    ) -> Optional[RemoteMangaSeries]:
        """获取漫画详情（占位实现）"""
        logger.warning(f"Generic HTTP adapter get_series_detail not implemented")
        return None

    async def list_chapters(
        self,
        remote_series_id: str,
    ) -> List[RemoteMangaChapter]:
        """获取章节列表（占位实现）"""
        logger.warning(f"Generic HTTP adapter list_chapters not implemented")
        return []

    async def list_series_by_library(
        self,
        library_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> RemoteMangaSearchResult:
        """占位实现：Generic HTTP 源不支持按库浏览。"""
        logger.warning(f"Generic HTTP adapter list_series_by_library not implemented for {self.base_url}")
        return RemoteMangaSearchResult(
            total=0,
            page=page,
            page_size=page_size,
            items=[],
        )

    async def list_pages(
        self,
        remote_series_id: str,
        remote_chapter_id: str,
    ) -> List[RemoteMangaPage]:
        """获取章节页面列表（占位实现）"""
        logger.warning(f"Generic HTTP adapter list_pages not implemented")
        return []

    async def fetch_page_content(
        self,
        page: RemoteMangaPage,
    ) -> bytes:
        """下载页面图片内容（占位实现）"""
        logger.warning(f"Generic HTTP adapter fetch_page_content not implemented")
        raise NotImplementedError("Generic HTTP adapter fetch_page_content not implemented")

