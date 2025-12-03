"""
Torrent Indexer（Phase 9）
负责从 PT 站点抓取种子列表并写入本地索引
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger

from .site_profiles import IntelSiteProfile, get_site_profile
from .http_clients import get_http_client_registry
from .scheduler_hooks import before_pt_scan
from .parsers.torrent_list_parser import (
    parse_torrent_list_page_generic,
    parse_torrent_list_page_hdsky,
    ParsedTorrentRow,
)
from .repo import (
    TorrentIndexRepository,
    TorrentIndexCreate,
    SqlAlchemyTorrentIndexRepository,
)
from app.core.database import AsyncSessionLocal


class TorrentIndexer:
    """Torrent Indexer：负责抓取和索引 PT 站点种子"""
    
    def __init__(
        self,
        index_repo: TorrentIndexRepository | None = None,
    ):
        """
        初始化 Indexer
        
        Args:
            index_repo: Torrent Index Repository（如果为None，使用默认实现）
        """
        self.index_repo = index_repo or SqlAlchemyTorrentIndexRepository(AsyncSessionLocal)
        self.http_registry = get_http_client_registry()
    
    async def sync_site_full(
        self,
        site_id: str,
        *,
        max_pages: int = 100,
        pages_per_batch: int = 10,
    ) -> dict:
        """
        全站慢速扫描（分页抓取）
        
        Args:
            site_id: 站点ID
            max_pages: 最大页数（防止无限扫描）
            pages_per_batch: 每批处理的页数（用于 SiteGuard 检查）
            
        Returns:
            扫描结果字典
        """
        logger.info(f"LocalIntel Indexer: 开始全站扫描 {site_id}（最多 {max_pages} 页）")
        
        profile = get_site_profile(site_id)
        if not profile:
            logger.error(f"LocalIntel Indexer: 站点 {site_id} 配置不存在")
            return {"success": False, "error": "site_profile_not_found"}
        
        client = self.http_registry.get(site_id)
        if not client:
            logger.error(f"LocalIntel Indexer: 站点 {site_id} HTTP 客户端未注册")
            return {"success": False, "error": "http_client_not_registered"}
        
        all_rows: List[TorrentIndexCreate] = []
        pages_scanned = 0
        errors = []
        
        try:
            # 从第1页开始扫描
            page = 1
            while page <= max_pages:
                # 每 pages_per_batch 页检查一次 SiteGuard
                if page % pages_per_batch == 1:
                    budget = await before_pt_scan(site_id)
                    if budget.get("blocked", False):
                        logger.warning(
                            f"LocalIntel Indexer: 站点 {site_id} 被限流，停止扫描 "
                            f"（已扫描 {pages_scanned} 页）"
                        )
                        break
                    
                    max_pages_for_batch = budget.get("max_pages", pages_per_batch)
                    if max_pages_for_batch < pages_per_batch:
                        logger.info(
                            f"LocalIntel Indexer: 站点 {site_id} 限速，本批最多扫描 {max_pages_for_batch} 页"
                        )
                
                try:
                    # 获取种子列表页面（NexusPHP 通常使用 browse.php?page=N）
                    html = await client.fetch(f"browse.php?page={page}")
                    
                    # 解析页面
                    if site_id.lower() == "hdsky":
                        parsed_rows = parse_torrent_list_page_hdsky(
                            site=site_id,
                            html=html,
                            profile=profile,
                        )
                    else:
                        parsed_rows = parse_torrent_list_page_generic(
                            site=site_id,
                            html=html,
                            profile=profile,
                        )
                    
                    if not parsed_rows:
                        logger.info(f"LocalIntel Indexer: 站点 {site_id} 第 {page} 页无数据，停止扫描")
                        break
                    
                    # 转换为 TorrentIndexCreate
                    now = datetime.utcnow()
                    for row in parsed_rows:
                        all_rows.append(
                            TorrentIndexCreate(
                                site_id=site_id,
                                torrent_id=row.torrent_id,
                                title_raw=row.title_raw,
                                category=row.category,
                                is_hr=row.is_hr,
                                is_free=row.is_free,
                                is_half_free=row.is_half_free,
                                size_bytes=row.size_bytes,
                                seeders=row.seeders,
                                leechers=row.leechers,
                                completed=row.completed,
                                published_at=row.published_at,
                                last_seen_at=now,
                            )
                        )
                    
                    pages_scanned += 1
                    logger.info(
                        f"LocalIntel Indexer: 站点 {site_id} 第 {page} 页完成，"
                        f"找到 {len(parsed_rows)} 条种子"
                    )
                    
                    # 如果本页数据少于预期，可能已到最后一页
                    if len(parsed_rows) < 20:  # 假设每页通常有20+条
                        logger.info(f"LocalIntel Indexer: 站点 {site_id} 可能已到最后一页")
                        break
                    
                    page += 1
                    
                    # 避免请求过快
                    import asyncio
                    await asyncio.sleep(1)  # 每页间隔1秒
                    
                except Exception as e:
                    error_msg = f"扫描第 {page} 页失败: {e}"
                    logger.error(f"LocalIntel Indexer: {error_msg}")
                    errors.append(error_msg)
                    # 如果连续失败，停止扫描
                    if len(errors) >= 3:
                        logger.error(f"LocalIntel Indexer: 连续失败3次，停止扫描")
                        break
                    page += 1
                    continue
            
            # 批量写入索引
            if all_rows:
                logger.info(f"LocalIntel Indexer: 开始写入 {len(all_rows)} 条索引记录")
                count = await self.index_repo.upsert_many(all_rows)
                logger.info(f"LocalIntel Indexer: 成功写入 {count} 条索引记录")
            
            return {
                "success": True,
                "pages_scanned": pages_scanned,
                "records_found": len(all_rows),
                "records_written": count if all_rows else 0,
                "errors": errors,
            }
            
        except Exception as e:
            logger.error(f"LocalIntel Indexer: 全站扫描失败: {e}", exc_info=True)
            return {"success": False, "error": str(e), "pages_scanned": pages_scanned}
    
    async def sync_site_incremental(
        self,
        site_id: str,
        *,
        max_pages: int = 5,
    ) -> dict:
        """
        增量扫描（最近 N 页）
        
        Args:
            site_id: 站点ID
            max_pages: 最多扫描页数（默认5页）
            
        Returns:
            扫描结果字典
        """
        logger.info(f"LocalIntel Indexer: 开始增量扫描 {site_id}（最近 {max_pages} 页）")
        
        profile = get_site_profile(site_id)
        if not profile:
            logger.error(f"LocalIntel Indexer: 站点 {site_id} 配置不存在")
            return {"success": False, "error": "site_profile_not_found"}
        
        client = self.http_registry.get(site_id)
        if not client:
            logger.error(f"LocalIntel Indexer: 站点 {site_id} HTTP 客户端未注册")
            return {"success": False, "error": "http_client_not_registered"}
        
        # 检查 SiteGuard
        budget = await before_pt_scan(site_id)
        if budget.get("blocked", False):
            logger.warning(f"LocalIntel Indexer: 站点 {site_id} 被限流，跳过增量扫描")
            return {"success": False, "error": "site_throttled"}
        
        all_rows: List[TorrentIndexCreate] = []
        errors = []
        
        try:
            # 只扫描前 max_pages 页（最新内容）
            for page in range(1, max_pages + 1):
                try:
                    html = await client.fetch(f"browse.php?page={page}")
                    
                    # 解析页面
                    if site_id.lower() == "hdsky":
                        parsed_rows = parse_torrent_list_page_hdsky(
                            site=site_id,
                            html=html,
                            profile=profile,
                        )
                    else:
                        parsed_rows = parse_torrent_list_page_generic(
                            site=site_id,
                            html=html,
                            profile=profile,
                        )
                    
                    if not parsed_rows:
                        break
                    
                    # 转换为 TorrentIndexCreate
                    now = datetime.utcnow()
                    for row in parsed_rows:
                        all_rows.append(
                            TorrentIndexCreate(
                                site_id=site_id,
                                torrent_id=row.torrent_id,
                                title_raw=row.title_raw,
                                category=row.category,
                                is_hr=row.is_hr,
                                is_free=row.is_free,
                                is_half_free=row.is_half_free,
                                size_bytes=row.size_bytes,
                                seeders=row.seeders,
                                leechers=row.leechers,
                                completed=row.completed,
                                published_at=row.published_at,
                                last_seen_at=now,
                            )
                        )
                    
                    logger.debug(f"LocalIntel Indexer: 站点 {site_id} 第 {page} 页完成，找到 {len(parsed_rows)} 条")
                    
                    # 避免请求过快
                    import asyncio
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    error_msg = f"扫描第 {page} 页失败: {e}"
                    logger.warning(f"LocalIntel Indexer: {error_msg}")
                    errors.append(error_msg)
                    continue
            
            # 批量写入索引
            count = 0
            if all_rows:
                count = await self.index_repo.upsert_many(all_rows)
                logger.info(f"LocalIntel Indexer: 增量扫描完成，写入 {count} 条索引记录")
            
            return {
                "success": True,
                "pages_scanned": max_pages,
                "records_found": len(all_rows),
                "records_written": count,
                "errors": errors,
            }
            
        except Exception as e:
            logger.error(f"LocalIntel Indexer: 增量扫描失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

