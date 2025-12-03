from __future__ import annotations

from sqlalchemy import select
from loguru import logger

from app.core.database import AsyncSessionLocal
from app.models.site import Site
from .engine import LocalIntelEngine, LocalIntelEngineConfig
from .hr_policy import HRPolicyConfig
from .inbox_policy import InboxPolicyConfig
from .repo import (
    SqlAlchemyHRCasesRepository,
    SqlAlchemySiteGuardRepository,
    SqlAlchemyInboxCursorRepository,
)
from .hr_watcher import HRWatcher
from .inbox_watcher import InboxWatcher
from .site_profiles import get_all_site_profiles, get_site_profile
from .http_clients import SiteHttpClientRegistry, get_http_client_registry, set_http_client_registry
from .http_clients_impl import HttpxSiteHttpClient


def build_local_intel_engine() -> LocalIntelEngine:
    """
    构建 LocalIntelEngine 的默认实例。
    依赖 AsyncSessionLocal 作为 SQLAlchemy Session factory。
    """

    hr_repo = SqlAlchemyHRCasesRepository(AsyncSessionLocal)
    site_guard_repo = SqlAlchemySiteGuardRepository(AsyncSessionLocal)
    inbox_cursor_repo = SqlAlchemyInboxCursorRepository(AsyncSessionLocal)

    site_profiles = get_all_site_profiles()

    hr_watcher = HRWatcher(site_profiles=site_profiles, hr_repo=hr_repo)
    inbox_watcher = InboxWatcher(site_profiles=site_profiles, inbox_cursor_repo=inbox_cursor_repo)

    config = LocalIntelEngineConfig(
        hr=HRPolicyConfig(),
        inbox=InboxPolicyConfig(),
    )

    return LocalIntelEngine(
        hr_repo=hr_repo,
        site_guard_repo=site_guard_repo,
        inbox_cursor_repo=inbox_cursor_repo,
        hr_watcher=hr_watcher,
        inbox_watcher=inbox_watcher,
        config=config,
    )


async def register_site_http_clients() -> None:
    """
    从数据库加载站点信息，注册 HTTP 客户端到 SiteHttpClientRegistry（Phase 4）。
    
    只注册：
    - 已激活的站点（is_active=True）
    - 有 cookie 的站点
    - 在 intel_sites 配置中存在的站点
    """
    try:
        registry = get_http_client_registry()
        site_profiles = get_all_site_profiles()
        
        if not site_profiles:
            logger.debug("LocalIntel: 没有站点配置，跳过 HTTP 客户端注册")
            return
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Site).where(Site.is_active == True, Site.cookie.isnot(None))
            )
            sites = result.scalars().all()
        
        registered_count = 0
        for site in sites:
            # 站点名可能存储在 name 字段，需要匹配到 intel_sites 配置中的 site 标识
            # 这里使用站点名的小写作为匹配键（可能需要根据实际情况调整）
            site_key = site.name.lower().replace(" ", "").replace("-", "")
            
            # 尝试多种匹配方式
            matched_profile = None
            for profile_site, profile in site_profiles.items():
                if (
                    profile_site.lower() == site_key
                    or profile_site.lower() in site_key
                    or site_key in profile_site.lower()
                ):
                    matched_profile = profile
                    break
            
            # Phase AI-2: 如果没有手工配置，尝试从 AI 配置转换
            if not matched_profile:
                try:
                    from app.core.site_ai_adapter import load_parsed_config
                    from app.core.site_ai_adapter.intel_bridge import ai_config_to_intel_profile
                    from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback
                    
                    # 尝试使用 AI 配置回退
                    ai_profile = await get_site_profile_with_ai_fallback(
                        site_key,
                        site_obj=site,
                        db=db,
                    )
                    
                    if ai_profile:
                        matched_profile = ai_profile
                        logger.info(f"LocalIntel: 站点 {site.name} 使用 AI 生成的配置（回退模式）")
                    else:
                        logger.debug(f"LocalIntel: 站点 {site.name} 未在 intel_sites 配置中找到，且无 AI 配置，跳过注册")
                        continue
                except Exception as e:
                    logger.debug(
                        f"LocalIntel: 站点 {site.name} 尝试 AI 配置回退失败: {e}，跳过注册"
                    )
                    continue
            
            if not matched_profile:
                logger.debug(f"LocalIntel: 站点 {site.name} 未在 intel_sites 配置中找到，跳过注册")
                continue
            
            try:
                # 创建 HTTP 客户端
                client = HttpxSiteHttpClient(
                    site_id=matched_profile.site,
                    site_url=site.url,
                    cookies=site.cookie,
                )
                
                # 注册到注册表
                registry.register(matched_profile.site, client)
                registered_count += 1
                logger.info(
                    f"LocalIntel: 已注册站点 {matched_profile.site} ({site.name}) 的 HTTP 客户端"
                )
            except Exception as e:
                logger.warning(
                    f"LocalIntel: 注册站点 {site.name} HTTP 客户端失败: {e}",
                    exc_info=True,
                )
        
        logger.info(f"LocalIntel: HTTP 客户端注册完成，共注册 {registered_count} 个站点")
        
    except Exception as e:
        logger.error(f"LocalIntel: 注册 HTTP 客户端失败: {e}", exc_info=True)

