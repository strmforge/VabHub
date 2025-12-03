"""
Indexed Search Service（Phase 9）
索引优先的搜索服务：优先从本地索引查询，不足时补充实时站点搜索
"""

from typing import List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.search import SearchQuery, SearchResultItem
from app.core.intel_local.repo import (
    TorrentIndexRepository,
    TorrentSearchParams,
    SqlAlchemyTorrentIndexRepository,
)
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.modules.search.service import SearchService


class IndexedSearchService:
    """索引优先的搜索服务"""
    
    def __init__(
        self,
        db: AsyncSession,
        index_repo: Optional[TorrentIndexRepository] = None,
        fallback_service: Optional[SearchService] = None,
    ):
        """
        初始化服务
        
        Args:
            db: 数据库会话
            index_repo: Torrent Index Repository（如果为None，使用默认实现）
            fallback_service: 回退搜索服务（用于实时站点搜索）
        """
        self.db = db
        self.index_repo = index_repo or SqlAlchemyTorrentIndexRepository(AsyncSessionLocal)
        self.fallback_service = fallback_service or SearchService(db)
    
    async def search(
        self,
        query: SearchQuery,
        *,
        min_results_threshold: int = 20,
    ) -> List[SearchResultItem]:
        """
        执行搜索（索引优先 + 站点补充）
        
        Args:
            query: 搜索查询参数
            min_results_threshold: 最小结果阈值（如果索引结果 >= 此值，不补充实时搜索）
            
        Returns:
            搜索结果列表
        """
        results: List[SearchResultItem] = []
        
        # 1. 从本地索引查询
        try:
            if settings.INTEL_ENABLED:
                index_params = TorrentSearchParams(
                    keyword=query.keyword,
                    category=query.category,
                    site_ids=query.site_ids,
                    hr_filter=query.hr_filter,
                    min_seeders=query.min_seeders,
                    max_seeders=query.max_seeders,
                    min_size_bytes=int(query.min_size_gb * 1024 ** 3) if query.min_size_gb else None,
                    max_size_bytes=int(query.max_size_gb * 1024 ** 3) if query.max_size_gb else None,
                    sort=query.sort,
                    limit=query.limit,
                    offset=query.offset,
                    exclude_deleted=True,
                )
                
                index_records = await self.index_repo.query_for_search(index_params)
                
                # 转换为 SearchResultItem
                for record in index_records:
                    # 获取 Local Intel 状态
                    intel_hr_status, intel_site_status = await self._get_intel_status(
                        record.site_id,
                        record.torrent_id,
                    )
                    
                    results.append(
                        SearchResultItem(
                            site_id=record.site_id,
                            torrent_id=record.torrent_id,
                            title_raw=record.title_raw,
                            size_bytes=record.size_bytes,
                            seeders=record.seeders,
                            leechers=record.leechers,
                            published_at=record.published_at,
                            is_hr=record.is_hr,
                            is_free=record.is_free,
                            is_half_free=record.is_half_free,
                            is_deleted=record.is_deleted,
                            category=record.category,
                            intel_hr_status=intel_hr_status,
                            intel_site_status=intel_site_status,
                            source="local",  # 本地索引结果
                        )
                    )
                
                logger.info(
                    f"IndexedSearchService: 从本地索引找到 {len(results)} 条结果"
                )
        except Exception as e:
            logger.warning(f"IndexedSearchService: 查询本地索引失败: {e}")
        
        # 2. 如果结果不足，补充实时站点搜索
        if len(results) < min_results_threshold and query.keyword:
            try:
                logger.info(
                    f"IndexedSearchService: 索引结果不足（{len(results)} < {min_results_threshold}），"
                    f"补充实时站点搜索"
                )
                
                # 调用原有的 SearchService（但限制站点，避免重复）
                fallback_results = await self.fallback_service.search(
                    query=query.keyword,
                    media_type=query.category,
                    sites=query.site_ids,
                    min_seeders=query.min_seeders,
                    max_seeders=query.max_seeders,
                    min_size=query.min_size_gb,
                    max_size=query.max_size_gb,
                    sort_by="seeders" if query.sort == "seeders" else "date",
                    sort_order="desc",
                    enable_query_expansion=False,  # 索引搜索已处理，不需要扩展
                )
                
                # 转换为 SearchResultItem（去重：如果索引中已有，跳过）
                existing_keys = {(r.site_id, r.torrent_id) for r in results}
                
                for item in fallback_results:
                    site_id = item.get("site") or item.get("site_id")
                    torrent_id = item.get("torrent_id") or item.get("id")
                    
                    if not site_id or not torrent_id:
                        continue
                    
                    key = (site_id, torrent_id)
                    if key in existing_keys:
                        continue  # 已存在，跳过
                    
                    # 获取 Local Intel 状态
                    intel_hr_status, intel_site_status = await self._get_intel_status(
                        site_id,
                        torrent_id,
                    )
                    
                    results.append(
                        SearchResultItem(
                            site_id=site_id,
                            torrent_id=str(torrent_id),
                            title_raw=item.get("title", ""),
                            size_bytes=int(item.get("size_gb", 0) * 1024 ** 3) if item.get("size_gb") else None,
                            seeders=item.get("seeders", 0),
                            leechers=item.get("leechers", 0),
                            published_at=item.get("upload_date"),
                            is_hr=item.get("is_hr", False),
                            is_free=item.get("is_free", False),
                            is_half_free=item.get("is_half_free", False),
                            is_deleted=False,  # 实时搜索结果默认未删除
                            category=item.get("category"),
                            intel_hr_status=intel_hr_status,
                            intel_site_status=intel_site_status,
                            magnet_link=item.get("magnet_link"),
                            torrent_url=item.get("torrent_url"),
                        )
                    )
                
                logger.info(
                    f"IndexedSearchService: 补充实时搜索找到 {len(fallback_results)} 条，"
                    f"去重后新增 {len(results) - len(existing_keys)} 条"
                )
                
                # 可选：将实时搜索结果写入索引（作为隐性增量）
                # 这里暂时不实现，避免影响性能
                
            except Exception as e:
                logger.warning(f"IndexedSearchService: 补充实时搜索失败: {e}")
        
        # 2.5. 如果结果不足，尝试从外部索引桥接补充
        if len(results) < min_results_threshold and settings.EXTERNAL_INDEXER_ENABLED:
            try:
                from app.core.ext_indexer.registry import get_runtime, get_auth_bridge
                from app.core.ext_indexer.search_provider import ExternalIndexerSearchProvider
                
                runtime = get_runtime()
                if runtime:
                    auth_bridge = get_auth_bridge()
                    provider = ExternalIndexerSearchProvider(runtime, auth_bridge)
                    
                    # 调用外部索引搜索
                    external_results = await provider.search(
                        query=query.keyword or "",
                        media_type=None,  # 可以根据 query.category 推断
                        sites=query.site_ids,  # 如果指定了站点，只搜索这些站点
                        page=1,
                    )
                    
                    # 转换为 SearchResultItem
                    for ext_result in external_results:
                        # 检查是否已存在（去重）
                        existing = any(
                            r.site_id == ext_result.site_id and r.torrent_id == ext_result.torrent_id
                            for r in results
                        )
                        if existing:
                            continue
                        
                        # 获取 Local Intel 状态
                        intel_hr_status, intel_site_status = await self._get_intel_status(
                            ext_result.site_id,
                            ext_result.torrent_id,
                        )
                        
                        # 转换为 SearchResultItem
                        result_item = SearchResultItem(
                            site_id=ext_result.site_id,
                            torrent_id=ext_result.torrent_id,
                            title_raw=ext_result.title,
                            size_bytes=ext_result.size_bytes,
                            seeders=ext_result.seeders or 0,
                            leechers=ext_result.leechers or 0,
                            published_at=ext_result.published_at,
                            is_hr=ext_result.is_hr,
                            is_free=ext_result.is_free,
                            is_half_free=ext_result.is_half_free,
                            is_deleted=False,  # 外部索引不提供删除状态
                            category=ext_result.categories[0] if ext_result.categories else None,
                            intel_site_status=intel_site_status,
                            intel_hr_status=intel_hr_status,
                            source="external",  # 外部索引结果
                        )
                        results.append(result_item)
                    
                    logger.info(f"外部索引桥接补充了 {len(external_results)} 条结果")
                else:
                    logger.debug("外部索引运行时未初始化，跳过外部索引搜索")
            except Exception as e:
                logger.warning(f"IndexedSearchService: 外部索引搜索失败: {e}")
        
        # 3. 应用排序（如果索引查询未完全排序）
        if query.sort == "seeders":
            results.sort(key=lambda x: x.seeders, reverse=True)
        elif query.sort == "published_at":
            results.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        elif query.sort == "size":
            results.sort(key=lambda x: x.size_bytes or 0, reverse=True)
        
        return results[:query.limit]
    
    async def _get_intel_status(
        self,
        site_id: str,
        torrent_id: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        获取 Local Intel 状态（HR 状态和站点状态）
        
        Returns:
            (intel_hr_status, intel_site_status)
        """
        if not settings.INTEL_ENABLED:
            return None, None
        
        try:
            from app.core.intel_local.repo import SqlAlchemyHRCasesRepository
            from app.core.intel_local.models import HRStatus
            from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
            from sqlalchemy import select, func
            from datetime import datetime, timedelta
            
            # 查询 HR 状态
            intel_hr_status = None
            try:
                hr_repo = SqlAlchemyHRCasesRepository(AsyncSessionLocal)
                async for hr_case in hr_repo.list_active_for_site(site_id):  # type: ignore[attr-defined]
                    if hr_case.torrent_id == str(torrent_id):
                        if hr_case.hr_status in (HRStatus.NONE, HRStatus.FINISHED, HRStatus.FAILED):
                            intel_hr_status = "SAFE"
                        elif hr_case.hr_status in (HRStatus.ACTIVE, HRStatus.UNKNOWN):
                            now = datetime.utcnow()
                            if hr_case.deadline:
                                remaining = (hr_case.deadline - now).total_seconds() / 3600
                                if remaining < 24:
                                    intel_hr_status = "RISK"
                                else:
                                    intel_hr_status = "ACTIVE"
                            else:
                                intel_hr_status = "ACTIVE"
                        break
            except Exception as e:
                logger.debug(f"查询 HR 状态失败: {e}")
            
            # 查询站点状态
            intel_site_status = None
            try:
                async with AsyncSessionLocal() as session:
                    guard_query = select(SiteGuardEventModel).where(
                        SiteGuardEventModel.site == site_id
                    ).order_by(SiteGuardEventModel.created_at.desc()).limit(1)
                    guard_result = await session.execute(guard_query)
                    latest_guard_event = guard_result.scalar_one_or_none()
                    
                    if latest_guard_event:
                        if latest_guard_event.block_until and latest_guard_event.block_until > datetime.utcnow():
                            intel_site_status = "THROTTLED"
                        else:
                            error_count_query = select(func.count(SiteGuardEventModel.id)).where(
                                SiteGuardEventModel.site == site_id,
                                SiteGuardEventModel.created_at >= datetime.utcnow() - timedelta(hours=24)
                            )
                            error_count_result = await session.execute(error_count_query)
                            error_count = error_count_result.scalar_one() or 0
                            if error_count > 3:
                                intel_site_status = "ERROR"
                            else:
                                intel_site_status = "OK"
                    else:
                        intel_site_status = "OK"
            except Exception as e:
                logger.debug(f"查询站点状态失败: {e}")
            
            return intel_hr_status, intel_site_status
            
        except Exception as e:
            logger.debug(f"获取 Local Intel 状态失败: {e}")
            return None, None

