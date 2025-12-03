"""
OPDS 漫画源适配器

支持 OPDS 1.2+ 标准的漫画源（如 Komga、Kavita 等）
"""
import httpx
from typing import List, Optional
from xml.etree import ElementTree as ET
from urllib.parse import urljoin, urlparse, parse_qs
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


class OpdsMangaSourceAdapter(BaseMangaSourceAdapter):
    """OPDS 漫画源适配器"""

    def __init__(self, source: MangaSource) -> None:
        super().__init__(source)
        self.base_url = source.base_url.rstrip('/')
        self.api_key = source.api_key
        self.extra_config = source.extra_config or {}

    def _get_headers(self) -> dict:
        """获取请求头"""
        headers = {
            'User-Agent': 'VabHub/1.0',
            'Accept': 'application/atom+xml,application/xml,text/xml',
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    async def ping(self) -> bool:
        """检查源是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 尝试访问根 OPDS feed
                url = f"{self.base_url}/opds"
                response = await client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    return True
                # 如果 /opds 不存在，尝试根路径
                response = await client.get(self.base_url, headers=self._get_headers())
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OPDS ping failed for {self.base_url}: {e}")
            return False

    async def list_libraries(self) -> List[MangaLibraryInfo]:
        """尝试从 OPDS 根 feed 中解析库/书架列表。

        不同实现差异很大，这里采用宽松策略：
        - 优先找 rel 包含 'shelf' 或 'collection' 的 link/entry
        - 否则退化为使用所有 entry 作为可浏览入口
        - 如果完全解析失败，则返回一个默认库
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{self.base_url}/opds"
                response = await client.get(url, headers=self._get_headers())
                if response.status_code != 200:
                    # 尝试根路径
                    response = await client.get(self.base_url, headers=self._get_headers())
                    response.raise_for_status()

                root = ET.fromstring(response.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                libraries: List[MangaLibraryInfo] = []

                # 先尝试通过 link 的 rel 识别 bookshelf
                for link in root.findall('.//atom:link', ns):
                    rel = link.get('rel') or ''
                    if 'shelf' in rel or 'collection' in rel:
                        href = link.get('href') or ''
                        title = link.get('title') or href or 'Bookshelf'
                        if href:
                            libraries.append(
                                MangaLibraryInfo(
                                    id=href,
                                    name=title,
                                )
                            )

                # 如果没有通过 link 解析到，则退化为所有 entry 作为库入口
                if not libraries:
                    for entry in root.findall('atom:entry', ns):
                        title_elem = entry.find('atom:title', ns)
                        id_elem = entry.find('atom:id', ns)
                        title = title_elem.text if title_elem is not None else '入口'
                        remote_id = id_elem.text if id_elem is not None else title
                        libraries.append(
                            MangaLibraryInfo(
                                id=str(remote_id),
                                name=str(title),
                            )
                        )

                if not libraries:
                    # 仍然为空时返回一个默认库，至少证明连得上
                    libraries.append(MangaLibraryInfo(id="default", name="默认库"))

                return libraries
        except Exception as e:
            logger.error(f"Failed to list OPDS libraries: {e}")
            # 连接已在 ping 阶段验证，这里失败则返回默认库
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
                # OPDS 搜索通常通过 search URI template
                # 常见格式：/opds/search?q={query}
                search_url = f"{self.base_url}/opds/search"
                params = {
                    'q': query,
                    'page': page,
                    'size': page_size,
                }
                
                response = await client.get(
                    search_url,
                    params=params,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                # 解析 OPDS XML
                root = ET.fromstring(response.text)
                items = []
                
                # OPDS 使用 Atom feed 格式
                # 查找所有 <entry> 元素
                for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                    series = self._parse_opds_entry(entry)
                    if series:
                        items.append(series)
                
                # 尝试从 feed 中获取总数（如果支持）
                total = len(items)  # 默认使用当前页数量
                # 某些 OPDS 实现会在 feed 中提供总数信息
                
                return RemoteMangaSearchResult(
                    total=total,
                    page=page,
                    page_size=page_size,
                    items=items
                )
        except Exception as e:
            logger.error(f"OPDS search failed: {e}")
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
        """按库/书架浏览漫画系列。

        这里将 library_id 视为 OPDS feed 的 href，拉取该 feed 并解析 entry。
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # library_id 可能是相对路径
                feed_url = library_id
                if not feed_url.startswith("http"):
                    feed_url = urljoin(self.base_url + "/", feed_url)

                response = await client.get(feed_url, headers=self._get_headers())
                response.raise_for_status()

                root = ET.fromstring(response.text)
                items: List[RemoteMangaSeries] = []

                for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                    series = self._parse_opds_entry(entry)
                    if series:
                        items.append(series)

                total = len(items)

                # 简单分页（本地切片）
                start = (page - 1) * page_size
                end = start + page_size
                paged_items = items[start:end]

                return RemoteMangaSearchResult(
                    total=total,
                    page=page,
                    page_size=page_size,
                    items=paged_items,
                )
        except Exception as e:
            logger.error(f"OPDS list_series_by_library failed for {library_id}: {e}")
            return RemoteMangaSearchResult(
                total=0,
                page=page,
                page_size=page_size,
                items=[],
            )

    def _parse_opds_entry(self, entry: ET.Element) -> Optional[RemoteMangaSeries]:
        """解析 OPDS entry 元素"""
        try:
            # 获取标题
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            title = title_elem.text if title_elem is not None else '未知标题'
            
            # 获取 ID（通常作为 remote_id）
            id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
            remote_id = id_elem.text if id_elem is not None else ''
            
            # 获取封面
            cover_url = None
            link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link[@rel="http://opds-spec.org/image"]')
            if link_elem is None:
                link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link[@rel="http://opds-spec.org/image/thumbnail"]')
            if link_elem is not None:
                href = link_elem.get('href', '')
                if href:
                    cover_url = urljoin(self.base_url, href)
            
            # 获取摘要
            summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
            summary = summary_elem.text if summary_elem is not None else None
            
            # 获取作者
            authors = []
            for author_elem in entry.findall('{http://www.w3.org/2005/Atom}author'):
                name_elem = author_elem.find('{http://www.w3.org/2005/Atom}name')
                if name_elem is not None:
                    authors.append(name_elem.text)
            
            # 获取分类（标签）
            tags = []
            for category in entry.findall('{http://www.w3.org/2005/Atom}category'):
                term = category.get('term', '')
                if term:
                    tags.append(term)
            
            return RemoteMangaSeries(
                source_id=self.source.id,
                source_type=self.source.type,
                remote_id=remote_id,
                title=title,
                cover_url=cover_url,
                summary=summary,
                authors=authors if authors else None,
                tags=tags if tags else None,
            )
        except Exception as e:
            logger.error(f"Failed to parse OPDS entry: {e}")
            return None

    async def get_series_detail(
        self,
        remote_series_id: str,
    ) -> Optional[RemoteMangaSeries]:
        """获取漫画详情"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 构建详情 URL（通常是 entry 的 self link）
                detail_url = remote_series_id
                if not detail_url.startswith('http'):
                    # 如果不是完整 URL，尝试构建
                    detail_url = f"{self.base_url}/opds/series/{remote_series_id}"
                
                response = await client.get(
                    detail_url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                root = ET.fromstring(response.text)
                entry = root.find('{http://www.w3.org/2005/Atom}entry')
                if entry is None:
                    return None
                
                series = self._parse_opds_entry(entry)
                if series:
                    # 尝试获取章节数
                    # 某些 OPDS 实现会在 feed 中列出所有章节
                    chapters = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                    series.chapters_count = len(chapters)
                
                return series
        except Exception as e:
            logger.error(f"Failed to get OPDS series detail: {e}")
            return None

    async def list_chapters(
        self,
        remote_series_id: str,
    ) -> List[RemoteMangaChapter]:
        """获取章节列表"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 构建章节列表 URL
                chapters_url = f"{self.base_url}/opds/series/{remote_series_id}/chapters"
                
                response = await client.get(
                    chapters_url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                root = ET.fromstring(response.text)
                chapters = []
                
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    chapter = self._parse_opds_chapter_entry(entry, remote_series_id)
                    if chapter:
                        chapters.append(chapter)
                
                return chapters
        except Exception as e:
            logger.error(f"Failed to list OPDS chapters: {e}")
            return []

    def _parse_opds_chapter_entry(
        self,
        entry: ET.Element,
        series_remote_id: str
    ) -> Optional[RemoteMangaChapter]:
        """解析章节 entry"""
        try:
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            title = title_elem.text if title_elem is not None else '未知章节'
            
            id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
            remote_id = id_elem.text if id_elem is not None else ''
            
            # 尝试从标题或 ID 中提取章节号
            number = None
            # 简单提取：查找数字
            import re
            match = re.search(r'(\d+\.?\d*)', title)
            if match:
                try:
                    number = float(match.group(1))
                except ValueError:
                    pass
            
            return RemoteMangaChapter(
                source_id=self.source.id,
                source_type=self.source.type,
                series_remote_id=series_remote_id,
                remote_id=remote_id,
                title=title,
                number=number,
            )
        except Exception as e:
            logger.error(f"Failed to parse OPDS chapter entry: {e}")
            return None

    async def list_pages(
        self,
        remote_series_id: str,
        remote_chapter_id: str,
    ) -> List[RemoteMangaPage]:
        """获取章节页面列表"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # OPDS 中，章节的页面通常通过 chapter 的 self link 获取
                # 或者通过特定的 pages feed
                pages_url = f"{self.base_url}/opds/series/{remote_series_id}/chapters/{remote_chapter_id}/pages"
                
                response = await client.get(
                    pages_url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                root = ET.fromstring(response.text)
                pages = []
                
                # OPDS 中页面通常作为 entry 列出
                for idx, entry in enumerate(root.findall('{http://www.w3.org/2005/Atom}entry'), start=1):
                    # 查找图片链接
                    link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link[@type="image/jpeg"]')
                    if link_elem is None:
                        link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link[@type="image/png"]')
                    if link_elem is None:
                        # 尝试任何链接
                        link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link')
                    
                    if link_elem is not None:
                        href = link_elem.get('href', '')
                        if href:
                            image_url = urljoin(self.base_url, href)
                            pages.append(RemoteMangaPage(
                                index=idx,
                                image_url=image_url,
                            ))
                
                return pages
        except Exception as e:
            logger.error(f"Failed to list OPDS pages: {e}")
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
            logger.error(f"Failed to fetch OPDS page content: {e}")
            raise

