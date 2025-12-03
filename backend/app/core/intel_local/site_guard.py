from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from .models import SiteGuardProfile
from .site_profiles import get_site_profile

# TODO: 未来将内存缓存替换为 DB + 内存缓存的组合
# 设计思路：
# 1. 使用 SQLAlchemy 模型 SiteGuardProfile 持久化到数据库
# 2. 保留内存缓存 _SITE_GUARD_CACHE 作为热数据缓存
# 3. get_site_guard_profile: 先查内存缓存，未命中则查 DB，加载到缓存
# 4. record_block_event: 同时更新 DB 和内存缓存
# 5. 站点配置较少，可以全部加载到内存（或使用 LRU 缓存）
_SITE_GUARD_CACHE: Dict[str, SiteGuardProfile] = {}


def get_site_guard_profile(site: str) -> SiteGuardProfile:
    profile = _SITE_GUARD_CACHE.get(site)
    if profile is None:
        # 尝试从站点配置加载默认值
        site_config = get_site_profile(site)
        if site_config and site_config.site_guard.enabled:
            profile = SiteGuardProfile(
                site=site,
                safe_scan_minutes=site_config.site_guard.default_safe_scan_minutes,
                safe_pages_per_hour=site_config.site_guard.default_safe_pages_per_hour,
            )
        else:
            profile = SiteGuardProfile(site=site)
        _SITE_GUARD_CACHE[site] = profile
    return profile


def record_block_event(
    site: str,
    block_until: Optional[datetime],
    cause: str,
    scan_minutes_before_block: Optional[int] = None,
    scan_pages_before_block: Optional[int] = None,
    now: Optional[datetime] = None,
) -> SiteGuardProfile:
    now = now or datetime.utcnow()
    profile = get_site_guard_profile(site)

    profile.last_block_start = now
    profile.last_block_end = block_until
    profile.last_block_cause = cause

    if scan_minutes_before_block:
        profile.last_full_scan_minutes = scan_minutes_before_block
        profile.safe_scan_minutes = max(1, int(scan_minutes_before_block * 0.6))

    if scan_pages_before_block:
        profile.last_full_scan_pages = scan_pages_before_block
        if scan_minutes_before_block and scan_minutes_before_block > 0:
            pages_per_hour = scan_pages_before_block / (scan_minutes_before_block / 60.0)
            profile.safe_pages_per_hour = max(10, int(pages_per_hour * 0.6))

    profile.updated_at = now
    return profile


def is_in_block_window(profile: SiteGuardProfile, now: Optional[datetime] = None) -> bool:
    now = now or datetime.utcnow()
    return bool(profile.last_block_end and now < profile.last_block_end)


def get_scan_budget(site: str, now: Optional[datetime] = None) -> dict:
    now = now or datetime.utcnow()
    profile = get_site_guard_profile(site)

    if is_in_block_window(profile, now):
        return {
            "blocked": True,
            "reason": profile.last_block_cause or "blocked_by_site",
            "until": profile.last_block_end,
            "max_minutes": 0,
            "max_pages": 0,
        }

    return {
        "blocked": False,
        "reason": None,
        "until": None,
        "max_minutes": profile.safe_scan_minutes,
        "max_pages": profile.safe_pages_per_hour,
    }

