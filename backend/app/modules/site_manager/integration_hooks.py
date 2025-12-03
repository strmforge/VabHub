"""
SITE-MANAGER-1 集成钩子系统
为其他模块提供站点管理事件的集成点
"""

from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from enum import Enum
from loguru import logger
import asyncio

from app.schemas.site_manager import SiteDetail, SiteBrief, HealthStatus


class IntegrationEvent(Enum):
    """集成事件类型"""
    SITE_UPDATED = "site_updated"
    SITE_HEALTH_CHANGED = "site_health_changed"
    SITE_ACCESS_CONFIG_CHANGED = "site_access_config_changed"
    SITE_ENABLED_DISABLED = "site_enabled_disabled"


class SiteManagerIntegrationHooks:
    """站点管理集成钩子系统"""
    
    def __init__(self):
        self._hooks: Dict[IntegrationEvent, List[Callable]] = {
            event: [] for event in IntegrationEvent
        }
    
    def register_hook(self, event: IntegrationEvent, callback: Callable):
        """注册集成钩子"""
        self._hooks[event].append(callback)
        logger.info(f"注册集成钩子: {event.value} -> {callback.__name__}")
    
    async def trigger_event(self, event: IntegrationEvent, **kwargs):
        """触发集成事件"""
        logger.debug(f"触发集成事件: {event.value}, 参数: {list(kwargs.keys())}")
        
        for callback in self._hooks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(**kwargs)
                else:
                    callback(**kwargs)
            except Exception as e:
                logger.error(f"集成钩子执行失败 {event.value} -> {callback.__name__}: {e}")


# 全局钩子实例
integration_hooks = SiteManagerIntegrationHooks()


# === CookieCloud 集成钩子 ===

async def cookiecloud_sync_hook(site: SiteDetail, **kwargs):
    """
    CookieCloud同步钩子
    当站点更新时触发CookieCloud同步（fire-and-forget模式，避免阻塞主事务）
    """
    try:
        logger.info(f"触发CookieCloud同步: {site.name} (ID: {site.id})")
        
        # 获取数据库会话（通过kwargs传递，避免循环依赖）
        db = kwargs.get("db")
        if not db:
            logger.warning("CookieCloud同步钩子缺少数据库会话，跳过同步")
            return
        
        # 导入CookieCloudSyncService（延迟导入避免循环依赖）
        from app.modules.cookiecloud.service import CookieCloudSyncService
        
        # 创建同步服务
        sync_service = CookieCloudSyncService(db)
        
        # 使用fire-and-forget模式，避免阻塞主事务
        async def _sync_and_log():
            try:
                # 创建独立的数据库会话，避免与主事务冲突
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as new_db:
                    new_sync_service = CookieCloudSyncService(new_db)
                    result = await new_sync_service.sync_site(site.id)
                    
                    if result.success:
                        if result.cookie_updated:
                            logger.info(f"CookieCloud同步完成: {site.name}，Cookie已更新")
                        else:
                            logger.info(f"CookieCloud同步完成: {site.name}，无匹配Cookie")
                    else:
                        logger.error(f"CookieCloud同步失败: {site.name} - {result.error_message}")
                        
            except Exception as e:
                logger.error(f"CookieCloud同步后台任务失败 {site.name}: {e}")
        
        # 创建后台任务，不等待完成
        asyncio.create_task(_sync_and_log())
        logger.debug(f"CookieCloud同步任务已提交到后台: {site.name}")
        
    except Exception as e:
        logger.error(f"CookieCloud同步钩子启动失败 {site.name}: {e}")




# === Local Intel 集成辅助函数 ===

async def sync_site_health_to_local_intel(site_id: int, health_status: HealthStatus, **kwargs):
    """
    将站点健康状态同步到Local Intel
    使用Site.id替代字符串站点名称
    """
    try:
        # TODO: 集成Local Intel API
        logger.info(f"同步健康状态到Local Intel: 站点ID {site_id} -> {health_status.value}")
        
        # 这里应该调用Local Intel的更新API
        # 将字符串站点名称映射到Site.id
        
    except Exception as e:
        logger.error(f"同步健康状态到Local Intel失败: {e}")


def register_default_hooks():
    """注册默认的集成钩子"""
    # 注册CookieCloud钩子
    integration_hooks.register_hook(
        IntegrationEvent.SITE_UPDATED, 
        cookiecloud_sync_hook
    )
    
    # 注册Local Intel钩子
    integration_hooks.register_hook(
        IntegrationEvent.SITE_HEALTH_CHANGED,
        sync_site_health_to_local_intel
    )
    
    logger.info("默认集成钩子注册完成")


# === 集成测试函数 ===

async def test_integration_points():
    """测试所有集成点"""
    logger.info("🔗 测试SITE-MANAGER-1集成点...")
    
    # 1. 测试CookieCloud集成
    logger.info("☁️  测试CookieCloud集成...")
    test_site = SiteDetail(
        id=1,
        name="测试站点",
        url="https://test.com",
        enabled=True,
        category="PT",
        priority=0
    )
    
    await integration_hooks.trigger_event(
        IntegrationEvent.SITE_UPDATED,
        site=test_site
    )
    
    # 2. 测试External Indexer集成
    logger.info("🔍 测试External Indexer集成...")
    # 这里需要实际的service实例，在实际使用中提供
    
    # 3. 测试Local Intel集成
    logger.info("🧠 测试Local Intel集成...")
    await integration_hooks.trigger_event(
        IntegrationEvent.SITE_HEALTH_CHANGED,
        site_id=1,
        health_status=HealthStatus.OK
    )
    
    logger.info("✅ 集成点测试完成")


# 初始化默认钩子
register_default_hooks()
