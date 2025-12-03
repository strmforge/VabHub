"""
SITE-MANAGER-1 服务层实现
站点管理模块的业务逻辑封装
"""

import asyncio
import json
import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from loguru import logger

from app.core.database import get_db
from app.models.site import Site, SiteStats, SiteAccessConfig, SiteCategory, SiteHealthCheck
from app.schemas.site_manager import (
    SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
    SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
    ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
)
from app.modules.site.service import SiteService  # 复用现有服务
from app.modules.site_manager.integration_hooks import integration_hooks, IntegrationEvent


class SiteManagerService:
    """站点管理服务 (SITE-MANAGER-1)"""
    
    def __init__(self, db):
        self.db = db
        self._legacy_service = SiteService(db)  # 复用现有服务
        
    # === 基础CRUD操作 ===
    
    async def list_sites(self, filters: SiteListFilter) -> List[SiteBrief]:
        """获取站点列表（支持过滤）"""
        query = select(Site).options(
            selectinload(Site.stats),
            selectinload(Site.access_config)
        )
        
        # 构建过滤条件
        conditions = []
        
        if filters.enabled is not None:
            conditions.append(Site.is_active == filters.enabled)
        
        if filters.category:
            conditions.append(Site.category == filters.category)
        
        if filters.health_status:
            query = query.join(SiteStats)
            conditions.append(SiteStats.health_status == filters.health_status.value)
        
        if filters.keyword:
            keyword = f"%{filters.keyword}%"
            conditions.append(
                or_(
                    Site.name.ilike(keyword),
                    Site.domain.ilike(keyword),
                    Site.key.ilike(keyword)
                )
            )
        
        if filters.tags:
            for tag in filters.tags:
                conditions.append(Site.tags.ilike(f"%{tag}%"))
        
        if filters.priority_min is not None:
            conditions.append(Site.priority >= filters.priority_min)
        
        if filters.priority_max is not None:
            conditions.append(Site.priority <= filters.priority_max)
        
        # 应用过滤条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 按优先级和创建时间排序
        query = query.order_by(Site.priority.desc(), Site.created_at.desc())
        
        result = await self.db.execute(query)
        sites = result.scalars().all()
        
        # 转换为SiteBrief
        site_briefs = []
        for site in sites:
            site_brief = SiteBrief.from_orm(site)
            site_briefs.append(site_brief)
        
        return site_briefs
    
    async def get_site_detail(self, site_id: int) -> Optional[SiteDetail]:
        """获取站点详细信息"""
        query = select(Site).options(
            selectinload(Site.stats),
            selectinload(Site.access_config)
        ).where(Site.id == site_id)
        
        result = await self.db.execute(query)
        site = result.scalar_one_or_none()
        
        if not site:
            return None
        
        # 获取最近健康检查记录
        health_query = select(SiteHealthCheck).where(
            SiteHealthCheck.site_id == site_id
        ).order_by(SiteHealthCheck.checked_at.desc()).limit(10)
        
        health_result = await self.db.execute(health_query)
        recent_health_checks = health_result.scalars().all()
        
        # 构建详细信息
        site_detail = SiteDetail.from_orm(site)
        site_detail.recent_health_checks = [
            SiteHealthResult.from_orm(check) for check in recent_health_checks
        ]
        
        return site_detail
    
    async def update_site(self, site_id: int, payload: SiteUpdatePayload) -> Optional[SiteDetail]:
        """更新站点基本信息"""
        # 构建更新数据
        update_data = payload.dict(exclude_unset=True)
        
        if not update_data:
            return await self.get_site_detail(site_id)
        
        # 执行更新
        query = update(Site).where(Site.id == site_id).values(**update_data)
        await self.db.execute(query)
        await self.db.commit()
        
        logger.info(f"更新站点 {site_id}: {update_data}")
        
        # 获取更新后的站点详情并触发集成事件
        updated_site = await self.get_site_detail(site_id)
        if updated_site:
            await integration_hooks.trigger_event(
                IntegrationEvent.SITE_UPDATED,
                site=updated_site
            )
        
        return updated_site
    
    async def get_active_healthy_sites(self) -> List[SiteBrief]:
        """
        获取活跃健康的站点列表
        供External Indexer使用
        """
        try:
            # 构建过滤器：启用且健康状态不为ERROR
            filters = SiteListFilter(enabled=True)
            
            sites = await self.list_sites(filters)
            
            # 过滤掉ERROR状态的站点
            healthy_sites = [
                site for site in sites 
                if site.stats and site.stats.health_status != HealthStatus.ERROR
            ]
            
            logger.info(f"为External Indexer提供 {len(healthy_sites)} 个健康站点")
            return healthy_sites
            
        except Exception as e:
            logger.error(f"获取健康站点列表失败: {e}")
            return []
    
    async def update_site_access_config(self, site_id: int, payload: SiteAccessConfigPayload) -> Optional[SiteDetail]:
        """更新站点访问配置"""
        # 获取或创建访问配置
        config_query = select(SiteAccessConfig).where(SiteAccessConfig.site_id == site_id)
        result = await self.db.execute(config_query)
        config = result.scalar_one_or_none()
        
        update_data = payload.dict(exclude_unset=True)
        
        if config:
            # 更新现有配置
            query = update(SiteAccessConfig).where(
                SiteAccessConfig.site_id == site_id
            ).values(**update_data, updated_at=datetime.utcnow())
            await self.db.execute(query)
        else:
            # 创建新配置
            config = SiteAccessConfig(site_id=site_id, **update_data)
            self.db.add(config)
        
        await self.db.commit()
        
        logger.info(f"更新站点访问配置 {site_id}: {update_data}")
        
        return await self.get_site_detail(site_id)
    
    async def delete_site(self, site_id: int) -> bool:
        """删除站点（级联删除相关数据）"""
        try:
            # 删除相关数据
            await self.db.execute(delete(SiteStats).where(SiteStats.site_id == site_id))
            await self.db.execute(delete(SiteAccessConfig).where(SiteAccessConfig.site_id == site_id))
            await self.db.execute(delete(SiteHealthCheck).where(SiteHealthCheck.site_id == site_id))
            
            # 删除站点
            await self.db.execute(delete(Site).where(Site.id == site_id))
            
            await self.db.commit()
            logger.info(f"删除站点 {site_id} 及相关数据")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除站点 {site_id} 失败: {e}")
            return False
    
    # === 健康检查功能 ===
    
    async def check_site_health(self, site_id: int, check_type: CheckType = CheckType.BASIC) -> SiteHealthResult:
        """执行站点健康检查"""
        site = await self.get_site_detail(site_id)
        if not site:
            raise ValueError(f"站点不存在: {site_id}")
        
        start_time = time.time()
        status = HealthStatus.OK
        error_message = None
        http_status_code = None
        response_time_ms = None
        
        try:
            # 根据检查类型执行不同的检查
            if check_type == CheckType.BASIC:
                http_status_code, response_time_ms = await self._basic_health_check(site.url)
            elif check_type == CheckType.RSS:
                http_status_code, response_time_ms = await self._rss_health_check(site)
            elif check_type == CheckType.API:
                http_status_code, response_time_ms = await self._api_health_check(site)
            else:
                raise ValueError(f"不支持的检查类型: {check_type}")
            
            # 判断健康状态
            if http_status_code and http_status_code >= 400:
                status = HealthStatus.ERROR
                error_message = f"HTTP {http_status_code}"
            elif response_time_ms and response_time_ms > 10000:  # 超过10秒
                status = HealthStatus.WARN
                error_message = f"响应时间过长: {response_time_ms}ms"
            
        except Exception as e:
            status = HealthStatus.ERROR
            error_message = str(e)
            logger.warning(f"站点 {site_id} 健康检查失败: {e}")
        
        # 记录检查结果
        health_check = SiteHealthCheck(
            site_id=site_id,
            status=status.value,
            response_time_ms=response_time_ms,
            error_message=error_message,
            http_status_code=http_status_code,
            check_type=check_type.value,
            checked_at=datetime.utcnow()
        )
        self.db.add(health_check)
        
        # 更新站点统计
        await self._update_site_stats(site_id, status, response_time_ms)
        
        await self.db.commit()
        
        return SiteHealthResult(
            site_id=site_id,
            status=status,
            response_time_ms=response_time_ms,
            error_message=error_message,
            http_status_code=http_status_code,
            check_type=check_type,
            checked_at=health_check.checked_at
        )
    
    async def batch_health_check(self, site_ids: List[int], check_type: CheckType = CheckType.BASIC) -> BatchHealthCheckResult:
        """批量健康检查（带速率限制）"""
        results = []
        success_count = 0
        failed_count = 0
        
        # 速率限制：每次检查间隔1秒，避免DDOS
        for site_id in site_ids:
            try:
                result = await self.check_site_health(site_id, check_type)
                results.append(result)
                if result.status == HealthStatus.OK:
                    success_count += 1
                else:
                    failed_count += 1
                
                # 速率限制
                await asyncio.sleep(1)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"批量健康检查失败 {site_id}: {e}")
        
        return BatchHealthCheckResult(
            total=len(site_ids),
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            message=f"批量检查完成: 成功 {success_count}, 失败 {failed_count}"
        )
    
    # === 导入导出功能 ===
    
    async def import_sites(self, sites_data: List[SiteImportItem]) -> ImportResult:
        """导入站点配置"""
        success_count = 0
        failed_count = 0
        failed_items = []
        
        for site_data in sites_data:
            try:
                # 检查是否已存在（根据key或domain）
                existing_site = None
                
                if site_data.key:
                    query = select(Site).where(Site.key == site_data.key)
                    result = await self.db.execute(query)
                    existing_site = result.scalar_one_or_none()
                
                if not existing_site and site_data.domain:
                    query = select(Site).where(Site.domain == site_data.domain)
                    result = await self.db.execute(query)
                    existing_site = result.scalar_one_or_none()
                
                if existing_site:
                    # 更新现有站点
                    update_data = site_data.dict(exclude_unset=True, exclude={"key"})
                    query = update(Site).where(Site.id == existing_site.id).values(**update_data)
                    await self.db.execute(query)
                    
                    # 更新访问配置
                    if any([site_data.rss_url, site_data.use_proxy, site_data.use_browser_emulation]):
                        await self.update_site_access_config(existing_site.id, SiteAccessConfigPayload(
                            rss_url=site_data.rss_url,
                            use_proxy=site_data.use_proxy,
                            use_browser_emulation=site_data.use_browser_emulation,
                            min_interval_seconds=site_data.min_interval_seconds,
                            max_concurrent_requests=site_data.max_concurrent_requests
                        ))
                    
                    logger.info(f"更新站点: {existing_site.name}")
                else:
                    # 创建新站点
                    site = Site(**site_data.dict())
                    self.db.add(site)
                    await self.db.flush()  # 获取ID
                    
                    # 创建访问配置
                    config = SiteAccessConfig(
                        site_id=site.id,
                        rss_url=site_data.rss_url,
                        use_proxy=site_data.use_proxy,
                        use_browser_emulation=site_data.use_browser_emulation,
                        min_interval_seconds=site_data.min_interval_seconds,
                        max_concurrent_requests=site_data.max_concurrent_requests
                    )
                    self.db.add(config)
                    
                    # 创建统计记录
                    stats = SiteStats(
                        site_id=site.id,
                        health_status=HealthStatus.OK
                    )
                    self.db.add(stats)
                    
                    logger.info(f"创建站点: {site.name}")
                
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_items.append({
                    "site": site_data.dict(),
                    "error": str(e)
                })
                logger.error(f"导入站点失败 {site_data.name}: {e}")
        
        await self.db.commit()
        
        return ImportResult(
            total=len(sites_data),
            success_count=success_count,
            failed_count=failed_count,
            failed_items=failed_items,
            message=f"导入完成: 成功 {success_count}, 失败 {failed_count}"
        )
    
    async def export_sites(self, site_ids: Optional[List[int]] = None) -> List[SiteExportItem]:
        """导出站点配置"""
        query = select(Site).options(selectinload(Site.access_config))
        
        if site_ids:
            query = query.where(Site.id.in_(site_ids))
        
        result = await self.db.execute(query)
        sites = result.scalars().all()
        
        export_items = []
        for site in sites:
            export_data = SiteExportItem(
                key=site.key,
                name=site.name,
                domain=site.domain,
                category=site.category,
                icon_url=site.icon_url,
                enabled=site.enabled,
                priority=site.priority,
                tags=site.tags,
                url=site.url,
                rss_url=site.access_config.rss_url if site.access_config else None,
                use_proxy=site.access_config.use_proxy if site.access_config else False,
                use_browser_emulation=site.access_config.use_browser_emulation if site.access_config else False,
                min_interval_seconds=site.access_config.min_interval_seconds if site.access_config else 10,
                max_concurrent_requests=site.access_config.max_concurrent_requests if site.access_config else 1
            )
            export_items.append(export_data)
        
        return export_items
    
    # === 私有辅助方法 ===
    
    async def _basic_health_check(self, url: str) -> Tuple[int, int]:
        """基础健康检查（HTTP HEAD请求）"""
        import aiohttp
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            start_time = time.time()
            async with session.head(url) as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                return response.status, response_time_ms
    
    async def _rss_health_check(self, site: SiteDetail) -> Tuple[int, int]:
        """RSS健康检查"""
        import aiohttp
        
        rss_url = site.access_config.rss_url if site.access_config else None
        if not rss_url:
            # 尝试构造RSS URL
            rss_url = site.url.rstrip('/') + '/rss.php'
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            start_time = time.time()
            async with session.get(rss_url) as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                return response.status, response_time_ms
    
    async def _api_health_check(self, site: SiteDetail) -> Tuple[int, int]:
        """API健康检查"""
        # 这里可以根据不同站点的API规范实现具体检查
        # 暂时使用基础检查
        return await self._basic_health_check(site.url)
    
    async def _update_site_stats(self, site_id: int, status: HealthStatus, response_time_ms: Optional[int]):
        """更新站点统计信息"""
        query = select(SiteStats).where(SiteStats.site_id == site_id)
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()
        
        if stats:
            # 更新统计
            update_data = {
                "total_requests": stats.total_requests + 1,
                "updated_at": datetime.utcnow()
            }
            
            if status == HealthStatus.OK:
                update_data["successful_requests"] = stats.successful_requests + 1
                update_data["last_seen_at"] = datetime.utcnow()
                update_data["health_status"] = HealthStatus.OK
                update_data["error_count"] = 0
            else:
                update_data["last_error_at"] = datetime.utcnow()
                update_data["health_status"] = status.value
                update_data["error_count"] = stats.error_count + 1
            
            if response_time_ms:
                # 更新平均响应时间
                if stats.avg_response_time:
                    update_data["avg_response_time"] = (
                        stats.avg_response_time * stats.successful_requests + response_time_ms
                    ) / (stats.successful_requests + 1)
                else:
                    update_data["avg_response_time"] = response_time_ms
            
            await self.db.execute(
                update(SiteStats).where(SiteStats.site_id == site_id).values(**update_data)
            )
            
            # 触发健康状态变化事件
            await integration_hooks.trigger_event(
                IntegrationEvent.SITE_HEALTH_CHANGED,
                site_id=site_id,
                health_status=status
            )
        else:
            # 创建统计记录
            stats = SiteStats(
                site_id=site_id,
                total_requests=1,
                successful_requests=1 if status == HealthStatus.OK else 0,
                health_status=status.value,
                last_seen_at=datetime.utcnow() if status == HealthStatus.OK else None,
                last_error_at=datetime.utcnow() if status != HealthStatus.OK else None,
                error_count=0 if status == HealthStatus.OK else 1,
                avg_response_time=response_time_ms
            )
            self.db.add(stats)
