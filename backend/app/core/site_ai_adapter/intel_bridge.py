"""
站点 AI 适配配置 → Local Intel Profile 转换桥接

Phase AI-2: 将 AI 生成的站点适配配置转换为 Local Intel 可用的站点配置。
"""

from typing import Optional
from loguru import logger

from app.models.site import Site
from app.core.site_ai_adapter.models import ParsedAISiteAdapterConfig
from app.core.intel_local.site_profiles import IntelSiteProfile, HRConfig, InboxConfig, SiteGuardConfig
from app.core.config import settings


def ai_config_to_intel_profile(
    site: Site,
    cfg: ParsedAISiteAdapterConfig,
) -> Optional[IntelSiteProfile]:
    """
    将 AI 生成的站点适配配置转换为 Local Intel 的站点配置
    
    Phase AI-2: 当站点没有手工配置时，使用 AI 配置生成 IntelSiteProfile
    
    Args:
        site: 站点对象（包含 id, name, url 等信息）
        cfg: 解析后的 AI 适配配置
        
    Returns:
        IntelSiteProfile 或 None（如果转换失败）
    """
    if not settings.AI_ADAPTER_ENABLED:
        logger.debug(f"AI 适配功能已禁用，跳过转换为 Intel Profile (site_id: {site.id})")
        return None
    
    try:
        # 使用站点名或 ID 作为 site 标识
        site_key = site.name.lower().strip() if site.name else f"site_{site.id}"
        
        # 转换 HR 配置
        hr_config = HRConfig(
            enabled=cfg.hr.enabled if cfg.hr else False,
            mode="TASK_LIST" if cfg.hr.enabled else None,  # 默认使用任务列表模式
            disappear_semantics="UNKNOWN",  # AI 配置中可能没有此字段，使用默认值
            max_observe_days=60,  # 默认值
            hr_page_url=None,  # 从 search.url 或 detail.url 推断
            page_path=cfg.hr.page_path or "hr.php",  # 使用 AI 配置的 page_path 或默认值
        )
        
        # 如果 AI 配置中有 HR 规则，尝试提取页面路径
        if cfg.hr and cfg.hr.rules:
            # 尝试从规则中提取页面路径（如果规则中有 location 信息）
            for rule in cfg.hr.rules:
                if rule.location and "hr" in rule.location.lower():
                    # 可以尝试从 location 推断路径，但这里简化处理
                    pass
        
        # 转换站内信配置（AI 配置中可能没有，使用默认值）
        inbox_config = InboxConfig(
            enabled=False,  # AI 配置中通常不包含站内信配置，默认禁用
            parser=None,
            pm_keywords={},
            page_path="messages.php",  # 默认路径
        )
        
        # 站点防护配置（使用默认值）
        site_guard_config = SiteGuardConfig(
            enabled=True,
            default_safe_scan_minutes=10,
            default_safe_pages_per_hour=200,
        )
        
        profile = IntelSiteProfile(
            site=site_key,
            hr=hr_config,
            inbox=inbox_config,
            site_guard=site_guard_config,
        )
        
        logger.info(f"成功将 AI 配置转换为 Local Intel Profile (site_id: {site.id}, site: {site_key})")
        return profile
        
    except Exception as e:
        logger.warning(
            f"将 AI 配置转换为 Local Intel Profile 失败 (site_id: {site.id}): {e}",
            exc_info=True
        )
        return None

