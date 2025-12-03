"""
远程漫画服务层

提供高层接口，供 API 使用
"""
import asyncio
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.manga_source import MangaSource
from app.schemas.manga_remote import (
    RemoteMangaSourceInfo,
    RemoteMangaSearchResult,
    RemoteMangaSeries,
    RemoteMangaChapter,
    SourceSearchResult,
    AggregatedSearchResult,
)
from app.schemas.manga_source import MangaLibraryInfo
from app.modules.manga_sources.factory import get_manga_source_adapter


async def list_enabled_sources(session: AsyncSession) -> List[RemoteMangaSourceInfo]:
    """列出所有启用的源"""
    stmt = select(MangaSource).where(MangaSource.is_enabled == True)  # noqa: E712
    result = await session.execute(stmt)
    sources = result.scalars().all()
    
    return [
        RemoteMangaSourceInfo(
            id=s.id,
            name=s.name,
            type=s.type,
            is_enabled=s.is_enabled,
        )
        for s in sources
    ]


async def search_series(
    session: AsyncSession,
    query: str,
    source_id: Optional[int],
    page: int,
    page_size: int,
) -> RemoteMangaSearchResult:
    """
    搜索漫画系列
    
    - 如果指定 source_id：只在单一源搜索
    - 如果未指定：使用第一个启用源
    """
    # 1. 选源
    if source_id:
        stmt = select(MangaSource).where(
            MangaSource.id == source_id,
            MangaSource.is_enabled == True  # noqa: E712
        )
    else:
        # 使用第一个启用源
        stmt = select(MangaSource).where(
            MangaSource.is_enabled == True  # noqa: E712
        ).limit(1)
    
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        return RemoteMangaSearchResult(
            total=0,
            page=page,
            page_size=page_size,
            items=[]
        )
    
    # 2. 取 adapter
    adapter = get_manga_source_adapter(source)
    
    # 3. 调用 adapter.search_series 返回结果
    return await adapter.search_series(query, page, page_size)


async def get_series_detail(
    session: AsyncSession,
    source_id: int,
    remote_series_id: str,
) -> Optional[RemoteMangaSeries]:
    """获取漫画详情"""
    stmt = select(MangaSource).where(
        MangaSource.id == source_id,
        MangaSource.is_enabled == True  # noqa: E712
    )
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        return None
    
    adapter = get_manga_source_adapter(source)
    return await adapter.get_series_detail(remote_series_id)


async def list_chapters(
    session: AsyncSession,
    source_id: int,
    remote_series_id: str,
) -> List[RemoteMangaChapter]:
    """获取章节列表"""
    stmt = select(MangaSource).where(
        MangaSource.id == source_id,
        MangaSource.is_enabled == True  # noqa: E712
    )
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        return []
    
    adapter = get_manga_source_adapter(source)
    return await adapter.list_chapters(remote_series_id)


async def list_series_by_library(
    session: AsyncSession,
    source_id: int,
    library_id: str,
    page: int,
    page_size: int,
) -> RemoteMangaSearchResult:
    """按库浏览远程漫画系列。

    仅在指定源上操作；若源不存在或未启用，返回空结果。
    """
    stmt = select(MangaSource).where(
        MangaSource.id == source_id,
        MangaSource.is_enabled == True,  # noqa: E712
    )
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        return RemoteMangaSearchResult(
            total=0,
            page=page,
            page_size=page_size,
            items=[],
        )

    adapter = get_manga_source_adapter(source)
    return await adapter.list_series_by_library(library_id, page=page, page_size=page_size)


async def list_libraries_for_source(
    session: AsyncSession,
    source_id: int,
) -> list[MangaLibraryInfo]:
    """列出指定源下的库/书架列表。

    仅返回已启用源的库信息；若源不存在或不可用，返回空列表。
    """
    stmt = select(MangaSource).where(
        MangaSource.id == source_id,
        MangaSource.is_enabled == True,  # noqa: E712
    )
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()

    if not source:
        return []

    adapter = get_manga_source_adapter(source)
    return await adapter.list_libraries()


async def aggregated_search_series(
    session: AsyncSession,
    query: str,
    source_ids: Optional[List[int]] = None,
    page: int = 1,
    page_size: int = 20,
    timeout_per_source: int = 10,
) -> AggregatedSearchResult:
    """
    聚合搜索漫画系列
    
    并发调用多个源的搜索，合并结果
    
    Args:
        query: 搜索关键字
        source_ids: 指定源ID列表，不传则搜索所有启用的源
        page: 页码（每个源独立分页）
        page_size: 每页数量（每个源独立）
        timeout_per_source: 每个源的超时时间（秒）
    
    Returns:
        AggregatedSearchResult: 聚合搜索结果
    """
    # 1. 获取要搜索的源
    if source_ids:
        stmt = select(MangaSource).where(
            MangaSource.id.in_(source_ids),
            MangaSource.is_enabled == True  # noqa: E712
        )
    else:
        stmt = select(MangaSource).where(MangaSource.is_enabled == True)  # noqa: E712
    
    result = await session.execute(stmt)
    sources = result.scalars().all()
    
    if not sources:
        return AggregatedSearchResult(
            query=query,
            total_sources=0,
            successful_sources=0,
            failed_sources=0,
            results_by_source=[],
            total_items=0,
            has_failures=False,
        )
    
    # 2. 并发搜索每个源
    async def search_single_source(source: MangaSource) -> SourceSearchResult:
        """搜索单个源"""
        try:
            adapter = get_manga_source_adapter(source)
            # 设置超时
            search_result = await asyncio.wait_for(
                adapter.search_series(query, page, page_size),
                timeout=timeout_per_source
            )
            
            return SourceSearchResult(
                source_id=source.id,
                source_name=source.name,
                source_type=source.type,
                success=True,
                result=search_result,
            )
        except asyncio.TimeoutError:
            logger.warning(f"搜索源 {source.name} 超时")
            return SourceSearchResult(
                source_id=source.id,
                source_name=source.name,
                source_type=source.type,
                success=False,
                error_message="搜索超时",
            )
        except Exception as e:
            logger.error(f"搜索源 {source.name} 失败: {e}")
            return SourceSearchResult(
                source_id=source.id,
                source_name=source.name,
                source_type=source.type,
                success=False,
                error_message=str(e),
            )
    
    # 3. 并发执行搜索
    tasks = [search_single_source(source) for source in sources]
    source_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 4. 处理结果
    results_by_source = []
    successful_sources = 0
    failed_sources = 0
    total_items = 0
    
    for result in source_results:
        if isinstance(result, Exception):
            logger.error(f"搜索任务异常: {result}")
            failed_sources += 1
            continue
        
        results_by_source.append(result)
        
        if result.success:
            successful_sources += 1
            if result.result:
                total_items += len(result.result.items)
        else:
            failed_sources += 1
    
    return AggregatedSearchResult(
        query=query,
        total_sources=len(sources),
        successful_sources=successful_sources,
        failed_sources=failed_sources,
        results_by_source=results_by_source,
        total_items=total_items,
        has_failures=failed_sources > 0,
    )


async def build_external_url(
    session: AsyncSession,
    source_id: int,
    remote_series_id: str,
) -> Optional[str]:
    """
    构建外部阅读URL
    
    Args:
        source_id: 源ID
        remote_series_id: 远程系列ID
    
    Returns:
        外部阅读URL，失败返回None
    """
    stmt = select(MangaSource).where(
        MangaSource.id == source_id,
        MangaSource.is_enabled == True  # noqa: E712
    )
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        return None
    
    try:
        adapter = get_manga_source_adapter(source)
        
        # 检查适配器是否有构建外部URL的方法
        if hasattr(adapter, 'build_external_url'):
            return await adapter.build_external_url(remote_series_id)
        else:
            # 默认实现：根据源类型构建URL
            if source.type.value == 'KOMGA':
                return f"{source.base_url.rstrip('/')}/series/{remote_series_id}"
            elif source.type.value == 'SUWAYOMI':
                return f"{source.base_url.rstrip('/')}/manga/{remote_series_id}"
            else:
                logger.warning(f"源类型 {source.type} 不支持构建外部URL")
                return None
    except Exception as e:
        logger.error(f"构建外部URL失败: {e}")
        return None

