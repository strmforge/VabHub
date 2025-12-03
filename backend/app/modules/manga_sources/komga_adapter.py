"""
Komga 漫画源适配器

支持 Komga 的 REST API
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


class KomgaMangaSourceAdapter(BaseMangaSourceAdapter):
    """Komga 漫画源适配器"""

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
                # Komga 有 /actuator/health 端点
                url = f"{self.base_url}/actuator/health"
                response = await client.get(url, headers=self._get_headers())
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Komga ping failed for {self.base_url}: {e}")
            return False

    async def list_libraries(self) -> List[MangaLibraryInfo]:
        """调用 Komga 的 /api/v1/libraries 获取库列表。"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{self.base_url}/api/v1/libraries"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()

                libraries: List[MangaLibraryInfo] = []
                items = data if isinstance(data, list) else data.get('content', [])

                for lib in items:
                    if not isinstance(lib, dict):
                        continue
                    lib_id = lib.get('id')
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
        except Exception as e:
            logger.error(f"Failed to list Komga libraries: {e}")

        # 出错或为空时返回一个默认库
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
                # Komga API: GET /api/v1/series?search={query}&page={page}&size={size}
                url = f"{self.base_url}/api/v1/series"
                params = {
                    'search': query,
                    'page': page - 1,  # Komga 使用 0-based 分页
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
                series_list = data.get('content', [])
                
                for series in series_list:
                    item = RemoteMangaSeries(
                        source_id=self.source.id,
                        source_type=self.source.type,
                        remote_id=str(series.get('id', '')),
                        title=series.get('title', '未知标题'),
                        cover_url=series.get('thumbnailUrl'),
                        summary=series.get('summary'),
                        authors=series.get('authors'),
                        tags=series.get('tags'),
                        status=series.get('status'),
                        chapters_count=series.get('booksCount', 0),
                    )
                    items.append(item)
                
                total = data.get('totalElements', len(items))
                
                return RemoteMangaSearchResult(
                    total=total,
                    page=page,
                    page_size=page_size,
                    items=items
                )
        except Exception as e:
            logger.error(f"Komga search failed: {e}")
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
        """按库浏览漫画系列。

        优先使用 Komga 的按库筛选参数 library_id（或 libraryIds）。
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/api/v1/series"
                params = {
                    "library_id": library_id,
                    "page": page - 1,
                    "size": page_size,
                }

                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                items = []
                series_list = data.get("content", [])

                for series in series_list:
                    item = RemoteMangaSeries(
                        source_id=self.source.id,
                        source_type=self.source.type,
                        remote_id=str(series.get("id", "")),
                        title=series.get("title", "未知标题"),
                        cover_url=series.get("thumbnailUrl"),
                        summary=series.get("summary"),
                        authors=series.get("authors"),
                        tags=series.get("tags"),
                        status=series.get("status"),
                        chapters_count=series.get("booksCount", 0),
                    )
                    items.append(item)

                total = data.get("totalElements", len(items))

                return RemoteMangaSearchResult(
                    total=total,
                    page=page,
                    page_size=page_size,
                    items=items,
                )
        except Exception as e:
            logger.error(f"Komga list_series_by_library failed: {e}")
            return RemoteMangaSearchResult(
                total=0,
                page=page,
                page_size=page_size,
                items=[],
            )

    async def get_series_detail(
        self,
        remote_series_id: str,
    ) -> Optional[RemoteMangaSeries]:
        """获取漫画详情"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/api/v1/series/{remote_series_id}"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                return RemoteMangaSeries(
                    source_id=self.source.id,
                    source_type=self.source.type,
                    remote_id=remote_series_id,
                    title=data.get('title', '未知标题'),
                    cover_url=data.get('thumbnailUrl'),
                    summary=data.get('summary'),
                    authors=data.get('authors'),
                    tags=data.get('tags'),
                    status=data.get('status'),
                    chapters_count=data.get('booksCount', 0),
                )
        except Exception as e:
            logger.error(f"Failed to get Komga series detail: {e}")
            return None

    async def list_chapters(
        self,
        remote_series_id: str,
    ) -> List[RemoteMangaChapter]:
        """获取章节列表（Komga 中称为 books）"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/api/v1/series/{remote_series_id}/books"
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                chapters = []
                books = data.get('content', []) if isinstance(data, dict) else data
                
                for book in books:
                    chapter = RemoteMangaChapter(
                        source_id=self.source.id,
                        source_type=self.source.type,
                        series_remote_id=remote_series_id,
                        remote_id=str(book.get('id', '')),
                        title=book.get('name', '未知章节'),
                        number=book.get('number'),
                        volume=book.get('volumeNumber'),
                    )
                    chapters.append(chapter)
                
                return chapters
        except Exception as e:
            logger.error(f"Failed to list Komga chapters: {e}")
            return []

    async def list_pages(
        self,
        remote_series_id: str,
        remote_chapter_id: str,
    ) -> List[RemoteMangaPage]:
        """获取章节页面列表（Komga 中章节称为 book）"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Komga API: GET /api/v1/books/{book_id}/pages
                url = f"{self.base_url}/api/v1/books/{remote_chapter_id}/pages"
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
                        image_url = str(page_data)
                        page_id = str(idx)
                    
                    if image_url:
                        # Komga 的图片 URL 可能需要完整路径
                        if not str(image_url).startswith('http'):
                            image_url = f"{self.base_url}{image_url}"
                        
                        pages.append(RemoteMangaPage(
                            index=idx,
                            image_url=image_url,
                            remote_page_id=page_id,
                        ))
                
                return pages
        except Exception as e:
            logger.error(f"Failed to list Komga pages: {e}")
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
            logger.error(f"Failed to fetch Komga page content: {e}")
            raise

