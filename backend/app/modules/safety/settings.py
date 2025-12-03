"""
SafetyPolicyEngine 配置服务
实现安全设置的获取、缓存和管理
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.modules.safety.models import (
    GlobalSafetySettings,
    SiteSafetySettings,
    SubscriptionSafetySettings,
    SafetyPolicyConfig,
)


class SafetySettingsService:
    """安全设置服务"""
    
    def __init__(self):
        self._session_factory = AsyncSessionLocal
        self._settings_cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(seconds=300)  # 5分钟缓存
        self._last_cache_update: Dict[str, datetime] = {}
    
    async def get_global(self) -> GlobalSafetySettings:
        """获取全局安全设置"""
        cache_key = "global"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._settings_cache[cache_key]
        
        # 从配置文件获取基础设置
        # 构建全局设置
        global_settings = GlobalSafetySettings(
            mode=getattr(settings, 'SAFETY_MODE', 'BALANCED'),
            min_keep_hours=getattr(settings, 'SAFETY_MIN_KEEP_HOURS', 24.0),
            min_ratio_for_delete=getattr(settings, 'SAFETY_MIN_RATIO_FOR_DELETE', 0.8),
            prefer_copy_on_move_for_hr=getattr(settings, 'SAFETY_PREFER_COPY_ON_MOVE_FOR_HR', True),
            enable_hr_protection=getattr(settings, 'SAFETY_ENABLE_HR_PROTECTION', True),
            auto_approve_hours=getattr(settings, 'SAFETY_AUTO_APPROVE_HOURS', 2.0),
            enable_telegram_integration=getattr(settings, 'SAFETY_ENABLE_TELEGRAM_INTEGRATION', True),
            enable_notification_integration=getattr(settings, 'SAFETY_ENABLE_NOTIFICATION_INTEGRATION', True),
            cache_ttl_seconds=getattr(settings, 'SAFETY_CACHE_TTL_SECONDS', 300),
            batch_check_enabled=getattr(settings, 'SAFETY_BATCH_CHECK_ENABLED', True),
        )
        
        # 更新缓存
        self._settings_cache[cache_key] = global_settings
        self._last_cache_update[cache_key] = datetime.utcnow()
        
        return global_settings
    
    async def get_site(self, site_key: str) -> Optional[SiteSafetySettings]:
        """获取站点安全设置"""
        cache_key = f"site:{site_key}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._settings_cache[cache_key]
        
        # 从数据库获取站点设置
        async with self._session_factory() as session:
            # 这里需要创建站点安全设置的数据库表
            # 暂时返回基于站点键的默认设置
            site_settings = self._get_default_site_settings(site_key)
            
            # 更新缓存
            self._settings_cache[cache_key] = site_settings
            self._last_cache_update[cache_key] = datetime.utcnow()
            
            return site_settings
    
    async def get_subscription(self, subscription_id: int) -> Optional[SubscriptionSafetySettings]:
        """获取订阅安全设置"""
        cache_key = f"subscription:{subscription_id}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._settings_cache[cache_key]
        
        # 从数据库获取订阅设置
        async with self._session_factory() as session:
            # 这里需要创建订阅安全设置的数据库表
            # 暂时返回基于订阅ID的默认设置
            subscription_settings = self._get_default_subscription_settings(subscription_id)
            
            # 更新缓存
            self._settings_cache[cache_key] = subscription_settings
            self._last_cache_update[cache_key] = datetime.utcnow()
            
            return subscription_settings
    
    async def get_all_sites(self) -> List[SiteSafetySettings]:
        """获取所有站点安全设置"""
        # 暂时返回空列表，后续从数据库获取
        return []
    
    async def get_all_subscriptions(self) -> List[SubscriptionSafetySettings]:
        """获取所有订阅安全设置"""
        # 暂时返回空列表，后续从数据库获取
        return []
    
    async def update_global(self, settings: GlobalSafetySettings) -> bool:
        """更新全局安全设置"""
        try:
            # 这里需要实现全局设置的持久化
            # 暂时只更新缓存
            cache_key = "global"
            self._settings_cache[cache_key] = settings
            self._last_cache_update[cache_key] = datetime.utcnow()
            
            return True
        except Exception:
            return False
    
    async def update_site(self, site_key: str, settings: SiteSafetySettings) -> bool:
        """更新站点安全设置"""
        try:
            # 这里需要实现站点设置的持久化
            # 暂时只更新缓存
            cache_key = f"site:{site_key}"
            self._settings_cache[cache_key] = settings
            self._last_cache_update[cache_key] = datetime.utcnow()
            
            return True
        except Exception:
            return False
    
    async def update_subscription(self, subscription_id: int, settings: SubscriptionSafetySettings) -> bool:
        """更新订阅安全设置"""
        try:
            # 这里需要实现订阅设置的持久化
            # 暂时只更新缓存
            cache_key = f"subscription:{subscription_id}"
            self._settings_cache[cache_key] = settings
            self._last_cache_update[cache_key] = datetime.utcnow()
            
            return True
        except Exception:
            return False
    
    async def get_full_config(self) -> SafetyPolicyConfig:
        """获取完整的安全策略配置"""
        global_settings = await self.get_global()
        site_settings = await self.get_all_sites()
        subscription_settings = await self.get_all_subscriptions()
        
        return SafetyPolicyConfig(
            global_settings=global_settings,
            site_settings=site_settings,
            subscription_settings=subscription_settings,
            feature_enabled=global_settings.enable_hr_protection,
            debug_mode=getattr(settings, 'SAFETY_DEBUG_MODE', False),
            config_version="1.0",
            last_updated=datetime.utcnow()
        )
    
    def clear_cache(self, pattern: Optional[str] = None):
        """清除缓存"""
        if pattern is None:
            # 清除所有缓存
            self._settings_cache.clear()
            self._last_cache_update.clear()
        else:
            # 清除匹配模式的缓存
            keys_to_remove = [key for key in self._settings_cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._settings_cache.pop(key, None)
                self._last_cache_update.pop(key, None)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._settings_cache:
            return False
        
        if cache_key not in self._last_cache_update:
            return False
        
        age = datetime.utcnow() - self._last_cache_update[cache_key]
        return age < self._cache_ttl
    
    def _get_default_site_settings(self, site_key: str) -> SiteSafetySettings:
        """获取默认站点设置"""
        # 基于站点键的启发式设置
        if any(keyword in site_key.lower() for keyword in ['hd', 'uhd', '4k']):
            hr_sensitivity = "sensitive"
        elif any(keyword in site_key.lower() for keyword in ['pt', 'chd', 'hdchina']):
            hr_sensitivity = "highly_sensitive"
        else:
            hr_sensitivity = "normal"
        
        return SiteSafetySettings(
            site_key=site_key,
            hr_sensitivity=hr_sensitivity,
            min_keep_ratio=1.0 if hr_sensitivity == "highly_sensitive" else 0.8,
            min_keep_time_hours=72.0 if hr_sensitivity == "highly_sensitive" else 48.0,
            enable_hr_download_block=True,
            enable_hr_delete_block=True,
            enable_hr_move_warning=True,
            site_name=site_key.upper(),
            hr_rules_url=f"https://{site_key}.com/rules",
            hr_description=f"{site_key.upper()}站点HR规则"
        )
    
    def _get_default_subscription_settings(self, subscription_id: int) -> SubscriptionSafetySettings:
        """获取默认订阅设置"""
        # 基于订阅ID的默认设置
        return SubscriptionSafetySettings(
            allow_hr=False,
            allow_h3h5=False,
            strict_free_only=False,
            enable_hr_warning=True,
            enable_hr_confirmation=True,
            auto_skip_hr=False,
            subscription_name=f"订阅#{subscription_id}",
            owner_id=None
        )


# 全局实例
_safety_settings_service: Optional[SafetySettingsService] = None


def get_safety_settings_service() -> SafetySettingsService:
    """获取安全设置服务单例"""
    global _safety_settings_service
    if _safety_settings_service is None:
        _safety_settings_service = SafetySettingsService()
    return _safety_settings_service


# 便捷函数
async def get_global_safety_settings() -> GlobalSafetySettings:
    """获取全局安全设置（便捷函数）"""
    service = get_safety_settings_service()
    return await service.get_global()


async def get_site_safety_settings(site_key: str) -> Optional[SiteSafetySettings]:
    """获取站点安全设置（便捷函数）"""
    service = get_safety_settings_service()
    return await service.get_site(site_key)


async def get_subscription_safety_settings(subscription_id: int) -> Optional[SubscriptionSafetySettings]:
    """获取订阅安全设置（便捷函数）"""
    service = get_safety_settings_service()
    return await service.get_subscription(subscription_id)
