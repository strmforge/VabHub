"""
站点 AI 适配配置 → External Indexer Site Config 转换桥接

Phase AI-2: 将 AI 生成的站点适配配置转换为 External Indexer 可用的站点配置。
"""

from typing import Optional
from loguru import logger

from app.models.site import Site
from app.core.site_ai_adapter.models import ParsedAISiteAdapterConfig
from app.core.ext_indexer.models import ExternalSiteConfig
from app.core.config import settings


def ai_config_to_external_site_config(
    site: Site,
    cfg: ParsedAISiteAdapterConfig,
) -> Optional[ExternalSiteConfig]:
    """
    将 AI 生成的站点适配配置转换为 External Indexer 的站点配置
    
    Phase AI-2: 当站点没有手工配置时，使用 AI 配置生成 ExternalSiteConfig
    
    Args:
        site: 站点对象（包含 id, name, url 等信息）
        cfg: 解析后的 AI 适配配置
        
    Returns:
        ExternalSiteConfig 或 None（如果转换失败）
    """
    if not settings.AI_ADAPTER_ENABLED:
        logger.debug(f"AI 适配功能已禁用，跳过转换为 External Site Config (site_id: {site.id})")
        return None
    
    try:
        # 构建能力列表
        capabilities = []
        if cfg.search and cfg.search.url:
            capabilities.append("search")
        if cfg.detail and cfg.detail.url:
            capabilities.append("detail")
        # RSS 能力需要额外配置，AI 配置中可能没有，暂时不添加
        
        # 构建站点配置
        site_config = ExternalSiteConfig(
            site_id=str(site.id),
            name=site.name or f"Site_{site.id}",
            base_url=site.url.rstrip("/") if site.url else "",
            framework=cfg.engine,  # 使用 AI 配置中的 engine 字段
            enabled=True,  # 默认启用
            capabilities=capabilities,
        )
        
        logger.info(f"成功将 AI 配置转换为 External Site Config (site_id: {site.id}, name: {site_config.name})")
        return site_config
        
    except Exception as e:
        logger.warning(
            f"将 AI 配置转换为 External Site Config 失败 (site_id: {site.id}): {e}",
            exc_info=True
        )
        return None

