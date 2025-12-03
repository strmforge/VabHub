"""
全局搜索服务
SEARCH-1 实现
DEV-SDK-1 扩展

跨媒体类型搜索，支持插件扩展
"""
import logging
from typing import List, Protocol, Iterable, Any, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebook import EBook
from app.models.music import Music
from app.models.manga_series_local import MangaSeriesLocal

from app.schemas.global_search import GlobalSearchItem, GlobalSearchResponse

logger = logging.getLogger(__name__)


# ============== 搜索提供者接口（供插件使用） ==============

class SearchProvider(Protocol):
    """
    搜索提供者接口
    
    插件实现此接口以扩展全局搜索功能
    """
    id: str  # 唯一 ID，如 'hello_world.sample_search'
    
    async def search(
        self,
        session: AsyncSession,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
    ) -> Iterable[GlobalSearchItem]:
        """
        执行搜索
        
        Args:
            session: 数据库会话
            query: 搜索关键词
            scope: 搜索范围（可选）
            limit: 返回数量限制
            
        Returns:
            搜索结果列表
        """
        ...


async def search_all(
    db: AsyncSession,
    query: str,
    limit_per_type: int = 5,
) -> GlobalSearchResponse:
    """
    全局搜索
    
    对小说/有声书/漫画/音乐等做 ILIKE 查询
    """
    items: List[GlobalSearchItem] = []
    search_pattern = f"%{query}%"
    
    # 1. 搜索小说/电子书
    try:
        stmt = (
            select(EBook)
            .where(
                or_(
                    EBook.title.ilike(search_pattern),
                    EBook.author.ilike(search_pattern),
                    EBook.series.ilike(search_pattern),
                )
            )
            .limit(limit_per_type)
        )
        result = await db.execute(stmt)
        ebooks = result.scalars().all()
        
        for ebook in ebooks:
            cover_url = None
            if ebook.cover_url:
                cover_url = ebook.cover_url if ebook.cover_url.startswith('http') else f"/media/{ebook.cover_url}"
            
            items.append(GlobalSearchItem(
                media_type="novel",
                id=str(ebook.id),
                title=ebook.title,
                sub_title=ebook.author,
                cover_url=cover_url,
                route_name="WorkDetail",
                route_params={"ebookId": ebook.id},
            ))
    except Exception as e:
        logger.warning(f"搜索电子书失败: {e}")
    
    # 2. 搜索漫画
    try:
        stmt = (
            select(MangaSeriesLocal)
            .where(
                or_(
                    MangaSeriesLocal.title.ilike(search_pattern),
                    MangaSeriesLocal.author.ilike(search_pattern) if hasattr(MangaSeriesLocal, 'author') else False,
                )
            )
            .limit(limit_per_type)
        )
        result = await db.execute(stmt)
        series_list = result.scalars().all()
        
        for series in series_list:
            cover_url = f"/media/{series.cover_path}" if series.cover_path else None
            
            items.append(GlobalSearchItem(
                media_type="manga",
                id=str(series.id),
                title=series.title,
                sub_title=series.author if hasattr(series, 'author') else None,
                cover_url=cover_url,
                route_name="MangaReaderPage",
                route_params={"series_id": series.id},
            ))
    except Exception as e:
        logger.warning(f"搜索漫画失败: {e}")
    
    # 3. 搜索音乐
    try:
        stmt = (
            select(Music)
            .where(
                or_(
                    Music.title.ilike(search_pattern),
                    Music.artist.ilike(search_pattern),
                    Music.album.ilike(search_pattern),
                )
            )
            .limit(limit_per_type)
        )
        result = await db.execute(stmt)
        musics = result.scalars().all()
        
        for music in musics:
            items.append(GlobalSearchItem(
                media_type="music",
                id=str(music.id),
                title=music.title,
                sub_title=music.artist,
                cover_url=None,
                route_name="MusicCenter",
                route_params={},
            ))
    except Exception as e:
        logger.warning(f"搜索音乐失败: {e}")
    
    # 4. 插件扩展搜索
    try:
        from app.services.plugin_registry import get_plugin_registry
        
        registry = get_plugin_registry()
        providers = registry.get_search_providers()
        
        for provider in providers:
            try:
                plugin_results = await provider.search(
                    db, query, scope=None, limit=limit_per_type
                )
                for item in plugin_results:
                    items.append(item)
            except Exception as e:
                logger.warning(f"插件搜索 {provider.id} 失败: {e}")
    except Exception as e:
        logger.warning(f"加载插件搜索提供者失败: {e}")
    
    return GlobalSearchResponse(items=items)
