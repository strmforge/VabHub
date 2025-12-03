"""
Suwayomi 漫画源适配器

支持 Tachiyomi-Server / Suwayomi 风格的 API
"""
import httpx
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


class SuwayomiMangaSourceAdapter(BaseMangaSourceAdapter):
    """Suwayomi 漫画源适配器"""

    def __init__(self, source: MangaSource) -> None:
        super().__init__(source)
        self.base_url = source.base_url.rstrip('/')
        self.api_key = source.api_key
        self.extra_config = source.extra_config or {}

    def _get_headers(self) -> dict:
        """获取请求头"""
        headers = {
            'User-Agent': 'VabHub/1.0',
            'Accept': 'application/json',
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    async def ping(self) -> bool:
        """检查源是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Suwayomi 通常有 /api/v1/info 或 /ping
                url = f"{self.base_url}/api/v1/info"
                response = await client.get(url, headers=self._get_headers())
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Suwayomi ping failed for {self.base_url}: {e}")
            return False

    async def list_libraries(self) -> List[MangaLibraryInfo]:
        """列出 Suwayomi 中的库/分类列表。

        不同版本 API 可能差异较大，这里按以下顺序尝试：
        - GET /api/v1/library
        - GET /api/v1/libraries
        响应可以是 list 或 dict，字段名尽量从 id/name/title 等中推断。
        失败时返回一个默认库。
        """
        endpoints = [
            f"{self.base_url}/api/v1/library",
            f"{self.base_url}/api/v1/libraries",
        ]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                for url in endpoints:
                    try:
                        response = await client.get(url, headers=self._get_headers())
                        if response.status_code != 200:
                            continue
                        data = response.json()

                        items = data
                        if isinstance(data, dict):
                            # 某些实现可能包一层
                            items = data.get('libraries') or data.get('items') or []

                        libraries: List[MangaLibraryInfo] = []
                        if isinstance(items, list):
                            for lib in items:
                                if not isinstance(lib, dict):
                                    continue
                                lib_id = lib.get('id') or lib.get('libraryId') or lib.get('name')
                                name = lib.get('name') or lib.get('label') or str(lib_id)
                                if lib_id is None and name is None:
                                    continue
                                libraries.append(
                                    MangaLibraryInfo(
                                        id=str(lib_id or name),
                                        name=str(name or lib_id),
                                    )
                                )

                        if libraries:
                            return libraries
                    except Exception as e:  # 单个端点失败不影响其它尝试
                        logger.warning(f"Failed to list Suwayomi libraries from {url}: {e}")

        except Exception as e:
            logger.error(f"Suwayomi list_libraries overall failed: {e}")

        # 若所有尝试均失败，返回一个默认库以表明连接可用
        return [MangaLibraryInfo(id="default", name="默认库")]

    async def search_series(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> RemoteMangaSearchResult:
        """搜索漫画系列"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Suwayomi API: GET /api/v1/manga?q={query}&page={page}
                url = f"{self.base_url}/api/v1/manga"
                params = {
                    'q': query,
                    'page': page,
                    'size': page_size,
                }
                
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                
                items = []
                # 根据实际 API 响应格式解析
                manga_list = data.get('manga', []) if isinstance(data, dict) else data
                
                for manga in manga_list:
                    series = RemoteMangaSeries(
                        source_id=self.source.id,
                        source_type=self.source.type,
                        remote_id=str(manga.get('id', '')),
                        title=manga.get('title', '未知标题'),
                        cover_url=manga.get('thumbnailUrl') or manga.get('coverUrl'),
                        summary=manga.get('description'),
                        authors=[manga.get('author')] if manga.get('author') else None,
                        status=manga.get('status'),
                    )
                    items.append(series)
                
                total = data.get('total', len(items)) if isinstance(data, dict) else len(items)
                
                return RemoteMangaSearchResult(
                    total=total,
                    page=page,
                    page_size=page_size,
                    items=items
                )
        except Exception as e:
            logger.error(f"Suwayomi search failed: {e}")
            return RemoteMangaSearchResult(
                total=0,
                page=page,
                page_size=page_size,
                items=[]
            )

    async def list_series_by_library(
        self,
        library_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> RemoteMangaSearchResult:
        """按库/分类浏览漫画系列（最佳努力实现）。

        若 Suwayomi 提供类似 /api/v1/library/{id}/manga 或 /api/v1/category/{id}/manga
        的接口则使用；否则退化为全库浏览，忽略 library_id。
        """
        endpoints = [
            f"{self.base_url}/api/v1/library/{library_id}/manga",
            f"{self.base_url}/api/v1/category/{library_id}/manga",
        ]

        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in endpoints:
                try:
                    params = {"page": page, "size": page_size}
                    response = await client.get(url, params=params, headers=self._get_headers())
                    if response.status_code != 200:
                        continue
                    data = response.json()

                    items = []
                    manga_list = data.get("manga", []) if isinstance(data, dict) else data

                    for manga in manga_list:
                        series = RemoteMangaSeries(
                            source_id=self.source.id,
                            source_type=self.source.type,
                            remote_id=str(manga.get("id", "")),
                            title=manga.get("title", "未知标题"),
                            cover_url=manga.get("thumbnailUrl") or manga.get("coverUrl"),
                            summary=manga.get("description"),
                            authors=[manga.get("author")] if manga.get("author") else None,
                            status=manga.get("status"),
                        )
                        items.append(series)

                    total = data.get("total", len(items)) if isinstance(data, dict) else len(items)

                    return RemoteMangaSearchResult(
                        total=total,
                        page=page,
                        page_size=page_size,
                        items=items,
                    )
                except Exception as e:
                    logger.warning(f"Suwayomi list_series_by_library failed for {url}: {e}")

        # 退化：调用搜索接口，相当于在全库浏览
        logger.warning("Suwayomi list_series_by_library falling back to global search without filter")
        return await self.search_series("", page=page, page_size=page_size)

    async def get_series_detail(
        self,
        remote_series_id: str,
    ) -> Optional[RemoteMangaSeries]:
        """获取漫画详情"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/api/v1/manga/{remote_series_id}"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                # 获取章节数
                chapters_url = f"{self.base_url}/api/v1/manga/{remote_series_id}/chapters"
                chapters_response = await client.get(chapters_url, headers=self._get_headers())
                chapters_count = 0
                if chapters_response.status_code == 200:
                    chapters_data = chapters_response.json()
                    chapters_count = len(chapters_data) if isinstance(chapters_data, list) else chapters_data.get('total', 0)
                
                return RemoteMangaSeries(
                    source_id=self.source.id,
                    source_type=self.source.type,
                    remote_id=remote_series_id,
                    title=data.get('title', '未知标题'),
                    cover_url=data.get('thumbnailUrl') or data.get('coverUrl'),
                    summary=data.get('description'),
                    authors=[data.get('author')] if data.get('author') else None,
                    status=data.get('status'),
                    chapters_count=chapters_count,
                )
        except Exception as e:
            logger.error(f"Failed to get Suwayomi series detail: {e}")
            return None

    async def list_chapters(
        self,
        remote_series_id: str,
    ) -> List[RemoteMangaChapter]:
        """获取章节列表"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/api/v1/manga/{remote_series_id}/chapters"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                chapters = []
                chapter_list = data if isinstance(data, list) else data.get('chapters', [])
                
                for ch in chapter_list:
                    chapter = RemoteMangaChapter(
                        source_id=self.source.id,
                        source_type=self.source.type,
                        series_remote_id=remote_series_id,
                        remote_id=str(ch.get('id', '')),
                        title=ch.get('name', '未知章节'),
                        number=ch.get('chapterNumber'),
                        volume=ch.get('volumeNumber'),
                    )
                    chapters.append(chapter)
                
                return chapters
        except Exception as e:
            logger.error(f"Failed to list Suwayomi chapters: {e}")
            return []

    async def list_pages(
        self,
        remote_series_id: str,
        remote_chapter_id: str,
    ) -> List[RemoteMangaPage]:
        """获取章节页面列表"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/api/v1/manga/{remote_series_id}/chapters/{remote_chapter_id}/pages"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                pages = []
                page_list = data if isinstance(data, list) else data.get('pages', [])
                
                for idx, page_data in enumerate(page_list, start=1):
                    if isinstance(page_data, dict):
                        image_url = page_data.get('url') or page_data.get('imageUrl')
                        page_id = page_data.get('id') or str(idx)
                    else:
                        # 如果是字符串 URL
                        image_url = str(page_data)
                        page_id = str(idx)
                    
                    if image_url:
                        pages.append(RemoteMangaPage(
                            index=idx,
                            image_url=image_url,
                            remote_page_id=page_id,
                        ))
                
                return pages
        except Exception as e:
            logger.error(f"Failed to list Suwayomi pages: {e}")
            return []

    async def fetch_page_content(
        self,
        page: RemoteMangaPage,
    ) -> bytes:
        """下载页面图片内容"""
        if not page.image_url:
            raise ValueError("Page has no image_url")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    str(page.image_url),
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to fetch Suwayomi page content: {e}")
            raise

