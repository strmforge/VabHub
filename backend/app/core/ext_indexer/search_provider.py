"""
外部索引搜索提供者

提供统一的搜索接口，整合多个外部站点的搜索结果。
"""

from typing import List, Optional
from loguru import logger

from app.core.ext_indexer.models import ExternalTorrentResult
from app.core.ext_indexer.interfaces import (
    ExternalIndexerRuntime,
    ExternalAuthBridge,
)
from app.core.ext_indexer.registry import get_auth_bridge


class ExternalIndexerSearchProvider:
    """
    外部索引搜索提供者
    
    对多个外部站点进行搜索，合并结果并去重。
    """
    
    def __init__(
        self,
        runtime: ExternalIndexerRuntime,
        auth_bridge: Optional[ExternalAuthBridge] = None,
    ):
        """
        初始化搜索提供者
        
        Args:
            runtime: 外部索引运行时
            auth_bridge: 授权桥接（如果为 None，使用默认的）
        """
        self.runtime = runtime
        self.auth_bridge = auth_bridge or get_auth_bridge()
    
    async def search(
        self,
        query: str,
        *,
        media_type: Optional[str] = None,
        sites: Optional[List[str]] = None,
        page: int = 1,
    ) -> List[ExternalTorrentResult]:
        """
        搜索种子
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            sites: 站点 ID 列表（如果为 None，搜索所有已配置的站点）
            page: 页码
            
        Returns:
            搜索结果列表
        """
        if not query:
            return []
        
        # 如果没有指定站点，使用所有已配置的站点
        if sites is None:
            from app.core.ext_indexer.site_importer import load_all_site_configs
            site_configs = load_all_site_configs()
            sites = [config.site_id for config in site_configs if config.enabled]
            
            # Phase AI-2: 如果没有手工配置的站点，尝试从数据库加载站点并使用 AI 配置
            if not sites:
                try:
                    from app.core.database import AsyncSessionLocal
                    from app.models.site import Site
                    from sqlalchemy import select
                    from app.core.ext_indexer.site_importer import get_site_config_with_ai_fallback
                    
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(
                            select(Site).where(Site.is_active == True)
                        )
                        all_sites = result.scalars().all()
                        
                        for site in all_sites:
                            ai_config = await get_site_config_with_ai_fallback(
                                str(site.id),
                                site_obj=site,
                                db=db,
                            )
                            if ai_config and ai_config.enabled:
                                sites.append(ai_config.site_id)
                                logger.debug(f"使用 AI 配置的站点: {ai_config.site_id}")
                except Exception as e:
                    logger.warning(f"尝试从 AI 配置加载站点列表失败: {e}")
        
        if not sites:
            logger.debug("没有可用的外部站点进行搜索")
            return []
        
        all_results: List[ExternalTorrentResult] = []
        
        # 逐个站点搜索
        for site_id in sites:
            try:
                # 检查授权状态
                auth_state = await self.auth_bridge.get_auth_state(site_id)
                
                # 如果有挑战，跳过该站点
                if auth_state.has_challenge:
                    logger.warning(f"站点 {site_id} 需要人机验证，跳过搜索")
                    continue
                
                # 如果未登录，记录警告但继续尝试
                if not auth_state.logged_in:
                    logger.warning(f"站点 {site_id} 未登录，搜索结果可能不完整")
                
                # 调用运行时搜索
                raw_results = await self.runtime.search_torrents(
                    site_id=site_id,
                    keyword=query,
                    media_type=media_type,
                    page=page,
                )
                
                # 转换为 ExternalTorrentResult
                for raw_result in raw_results:
                    try:
                        result = self._dict_to_torrent_result(site_id, raw_result)
                        all_results.append(result)
                    except Exception as e:
                        logger.error(f"转换搜索结果失败: {e}")
                        continue
                
            except Exception as e:
                logger.warning(f"搜索站点 {site_id} 失败: {e}")
                continue
        
        # 去重（按 site_id + torrent_id）
        seen = set()
        unique_results: List[ExternalTorrentResult] = []
        for result in all_results:
            key = (result.site_id, result.torrent_id)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        logger.info(f"外部索引搜索完成: {len(unique_results)} 条结果（去重前 {len(all_results)} 条）")
        return unique_results
    
    def _dict_to_torrent_result(
        self,
        site_id: str,
        data: dict,
    ) -> ExternalTorrentResult:
        """
        将字典转换为 ExternalTorrentResult
        
        Args:
            site_id: 站点 ID
            data: 原始数据字典
            
        Returns:
            ExternalTorrentResult 对象
        """
        # 提取字段（支持多种可能的字段名）
        torrent_id = str(data.get("torrent_id") or data.get("id") or data.get("tid") or "")
        title = str(data.get("title") or data.get("name") or "")
        
        # 大小
        size_bytes = data.get("size_bytes") or data.get("size")
        if isinstance(size_bytes, str):
            # 尝试解析字符串大小（如 "1.5GB"）
            try:
                size_bytes = int(float(size_bytes.replace("GB", "").replace("MB", "")) * (1024 ** 3))
            except (ValueError, AttributeError):
                size_bytes = None
        
        # 做种数和下载数
        seeders = data.get("seeders") or data.get("seeds") or 0
        leechers = data.get("leechers") or data.get("peers") or 0
        
        # 发布时间
        published_at = data.get("published_at") or data.get("pubdate") or data.get("date")
        if isinstance(published_at, str):
            from datetime import datetime
            try:
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                published_at = None
        
        # 分类和标签
        categories = data.get("categories") or data.get("category") or []
        if isinstance(categories, str):
            categories = [categories]
        
        tags = data.get("tags") or data.get("label") or []
        if isinstance(tags, str):
            tags = [tags]
        
        # HR 标记
        is_hr = data.get("is_hr") or data.get("hit_and_run") or False
        
        # 免费百分比
        free_percent = data.get("free_percent") or data.get("free")
        if free_percent is None:
            # 尝试从其他字段推断
            download_volume_factor = data.get("download_volume_factor") or data.get("download_factor")
            if download_volume_factor == 0.0:
                free_percent = 100
            elif download_volume_factor == 0.5:
                free_percent = 50
            else:
                free_percent = 0
        
        return ExternalTorrentResult(
            site_id=site_id,
            site_name=data.get("site_name"),
            torrent_id=torrent_id,
            title=title,
            size_bytes=size_bytes,
            seeders=seeders,
            leechers=leechers,
            published_at=published_at,
            categories=categories if isinstance(categories, list) else [],
            tags=tags if isinstance(tags, list) else [],
            is_hr=is_hr,
            free_percent=free_percent,
            raw=data,
        )

