"""
搜索服务（增强版）
集成多源索引器、去重、HNR检测、缓存等功能
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import hashlib
from loguru import logger

from app.modules.search.engine import SearchEngine
from app.modules.search.indexer_manager import IndexerManager
from app.modules.search.deduplicator import ResultDeduplicator
from app.modules.search.query_expander import QueryExpander
from app.modules.search.result_aggregator import ResultAggregator
from app.models.search_history import SearchHistory
from app.core.cache import get_cache
from app.core.config import settings
from app.core.intel.service import get_intel_service, IntelService
from app.modules.global_rules import GlobalRulesService


class SearchService:
    """搜索服务（增强版）"""
    
    def __init__(self, db: AsyncSession, apply_global_rules: bool = True):
        self.db = db
        self.engine = SearchEngine()
        self.indexer_manager = IndexerManager()
        self.deduplicator = ResultDeduplicator(similarity_threshold=0.8)
        self.aggregator = ResultAggregator(similarity_threshold=0.8)
        self.query_expander = QueryExpander()
        self.cache = get_cache()
        self.intel: IntelService = get_intel_service()  # Intel服务注入
        self.global_rules_service = GlobalRulesService(db)  # 全局规则服务
        self.apply_global_rules = apply_global_rules  # 是否应用全局规则过滤
    
    async def search(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        quality: Optional[str] = None,
        resolution: Optional[str] = None,
        min_size: Optional[float] = None,
        max_size: Optional[float] = None,
        min_seeders: Optional[int] = None,
        max_seeders: Optional[int] = None,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        sites: Optional[List[str]] = None,
        sort_by: str = "seeders",
        sort_order: str = "desc",
        enable_query_expansion: bool = True
    ) -> List[dict]:
        """
        执行搜索（基础版，支持查询扩展）
        
        注意：此方法已被增强版search方法替代，保留用于向后兼容
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型（movie/tv/anime）
            year: 年份
            quality: 质量（4K/1080p/720p等）
            resolution: 分辨率
            min_size: 最小文件大小（GB）
            max_size: 最大文件大小（GB）
            min_seeders: 最小做种数
            max_seeders: 最大做种数
            include: 包含关键词
            exclude: 排除关键词
            sites: 站点列表
            sort_by: 排序字段
            sort_order: 排序方向（asc/desc）
            enable_query_expansion: 是否启用查询扩展
        
        Returns:
            搜索结果列表
        """
        # 生成缓存键（包含全局规则设置）
        cache_params = {
            "query": query,
            "media_type": media_type,
            "year": year,
            "quality": quality,
            "resolution": resolution,
            "min_size": min_size,
            "max_size": max_size,
            "min_seeders": min_seeders,
            "max_seeders": max_seeders,
            "include": include,
            "exclude": exclude,
            "sites": sites,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "apply_global_rules": self.apply_global_rules
        }
        
        # 如果启用全局规则，包含规则更新时间到缓存键
        if self.apply_global_rules:
            try:
                global_rules = await self.global_rules_service.get_settings()
                cache_params["global_rules_updated_at"] = global_rules.updated_at.isoformat()
            except Exception as e:
                logger.warning(f"获取全局规则设置失败，使用默认缓存键: {e}")
        
        cache_key = f"search:{hashlib.md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()}"
        
        # 尝试从缓存获取（5分钟TTL）
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"搜索结果缓存命中: {query}")
            return cached_result
        
        # Intel预处理：标准化标题和获取优先站点
        normalized_query = query
        release_key = None
        preferred_sites = None
        
        try:
            intel_result = await self.intel.resolve_title(query)
            if intel_result:
                normalized_query = intel_result.get("title") or normalized_query
                release_key = intel_result.get("release_key")
                
                # 如果有release_key，获取优先站点列表
                if release_key:
                    try:
                        sites_info = await self.intel.get_release_sites(release_key)
                        site_items = sites_info.get("sites") or []
                        preferred_sites = [
                            item["site"] for item in sorted(
                                site_items,
                                key=lambda x: x.get("score", 0),
                                reverse=True,
                            )
                            if "site" in item
                        ] or None
                        if preferred_sites:
                            logger.info(f"[SearchService] Intel识别到优先站点: {preferred_sites}")
                    except Exception as e:
                        logger.warning(f"[SearchService] 调用 Intel.get_release_sites 失败: {e!r}")
        except Exception as e:
            logger.warning(f"[SearchService] 调用 Intel.resolve_title 失败: {e!r}")
        
        # 如果Intel提供了优先站点，且用户未指定站点，则使用优先站点
        engine_sites = sites
        if (not engine_sites) and preferred_sites:
            engine_sites = preferred_sites
        
        # Local Intel Site Guard: 过滤被阻止的站点
        # 注意：开关判断已集中在 scheduler_hooks.before_pt_scan 中
        if engine_sites:
            filtered_sites = []
            for site_name in engine_sites:
                try:
                    from app.core.intel_local.scheduler_hooks import before_pt_scan
                    budget = await before_pt_scan(site_name)
                    
                    if budget.get("blocked"):
                        logger.warning(
                            f"LocalIntel: 站点 {site_name} 当前处于风控冷却期 "
                            f"(原因: {budget.get('reason')}, 直到: {budget.get('until')})，跳过搜索"
                        )
                        continue  # 跳过被阻止的站点
                    
                    filtered_sites.append(site_name)
                except Exception as e:
                    logger.warning(f"LocalIntel Site Guard 检查失败 (站点: {site_name}): {e}，继续搜索")
                    filtered_sites.append(site_name)  # 检查失败时，保守处理：继续搜索
            
            if filtered_sites:
                engine_sites = filtered_sites
            elif engine_sites:  # 只有在原本有站点但全部被阻止时才返回空
                logger.warning("LocalIntel: 所有站点均被阻止，无法执行搜索")
                return []  # 所有站点都被阻止，返回空结果
        
        # 执行搜索
        if enable_query_expansion:
            # 使用QueryExpander进行查询扩展
            expanded_queries = self.query_expander.expand_query(query, year, media_type)
        else:
            expanded_queries = [query]
        
        all_results = []
        for expanded_query in expanded_queries:
            # 使用标准化查询和优先站点
            search_query = normalized_query if expanded_query == query else expanded_query
            results = await self.engine.search(
                query=search_query,
                media_type=media_type,
                year=year,
                quality=quality,
                resolution=resolution,
                min_size=min_size,
                max_size=max_size,
                min_seeders=min_seeders,
                max_seeders=max_seeders,
                include=include,
                exclude=exclude,
                sites=engine_sites  # 使用Intel提供的优先站点
            )
            all_results.extend(results)
        
        # 使用增强版聚合器（去重、评分、排序）
        aggregated_results = self.aggregator.aggregate(
            all_results,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # 应用全局规则过滤
        if self.apply_global_rules:
            try:
                filtered_results = await self.global_rules_service.filter_torrents(aggregated_results)
                logger.info(f"全局规则过滤完成: {len(aggregated_results)} -> {len(filtered_results)}")
                aggregated_results = filtered_results
            except Exception as e:
                logger.error(f"全局规则过滤失败，使用原始结果: {e}")
                # 降级处理：使用原始结果，避免影响用户搜索体验
        else:
            logger.debug("全局规则过滤已禁用")
        
        # 缓存结果（5分钟）
        await self.cache.set(cache_key, aggregated_results, ttl=300)
        
        # 记录搜索历史
        try:
            search_history = SearchHistory(
                query=query,
                media_type=media_type,
                result_count=len(aggregated_results)
            )
            self.db.add(search_history)
            await self.db.commit()
        except Exception as e:
            logger.warning(f"记录搜索历史失败: {e}")
            await self.db.rollback()
        
        return aggregated_results
    
    def group_results(
        self,
        results: List[Dict[str, Any]],
        group_by: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        分组搜索结果
        
        Args:
            results: 搜索结果列表
            group_by: 分组字段（site, quality, resolution, category）
        
        Returns:
            分组后的结果字典
        """
        return self.aggregator._group_results(results, group_by)
