from __future__ import annotations

from app.core.config import settings
from .hr_state import get_hr_state_for_torrent
from .file_guard import should_protect_source_file
from .site_guard import get_scan_budget


async def before_pt_scan(site: str) -> dict:
    """
    站点扫描前的预算检查（Site Guard）
    
    如果 Local Intel 未启用或 Site Guard 未启用，返回允许扫描的预算
    """
    if not settings.INTEL_ENABLED or not settings.INTEL_SITE_GUARD_ENABLED:
        # 未启用时，返回无限制预算
        return {
            "blocked": False,
            "reason": None,
            "until": None,
            "max_minutes": 999999,  # 无限制
            "max_pages": 999999,  # 无限制
        }
    return get_scan_budget(site)


async def should_keep_source_after_download(site: str, torrent_id: str) -> bool:
    """
    检查下载完成后是否应该保留源文件（HR 保护）
    
    如果 Local Intel 未启用或 HR Guard 未启用，返回 False（不保护）
    """
    if not settings.INTEL_ENABLED or not settings.INTEL_HR_GUARD_ENABLED:
        return False  # 未启用时，不保护源文件
    
    state = get_hr_state_for_torrent(site, str(torrent_id))
    return should_protect_source_file(state)

