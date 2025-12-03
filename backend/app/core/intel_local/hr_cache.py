"""
HR状态缓存模块
提供统一的内存缓存访问接口，避免循环导入
"""

from typing import Dict
from .models import HRTorrentState

# 全局HR状态缓存
_HR_STATE_CACHE: Dict[tuple[str, str], HRTorrentState] = {}

def get_cache_key(site: str, torrent_id: str) -> tuple[str, str]:
    """生成缓存键"""
    return (site, str(torrent_id))

def get_from_cache(site: str, torrent_id: str) -> HRTorrentState:
    """从缓存获取HR状态"""
    key = get_cache_key(site, torrent_id)
    return _HR_STATE_CACHE.get(key)

def set_to_cache(site: str, torrent_id: str, state: HRTorrentState) -> None:
    """设置HR状态到缓存"""
    key = get_cache_key(site, torrent_id)
    _HR_STATE_CACHE[key] = state

def remove_from_cache(site: str, torrent_id: str) -> None:
    """从缓存移除HR状态"""
    key = get_cache_key(site, torrent_id)
    if key in _HR_STATE_CACHE:
        del _HR_STATE_CACHE[key]

def iter_site_states(site: str):
    """遍历指定站点的所有HR状态"""
    for (site_key, _), state in _HR_STATE_CACHE.items():
        if site_key == site:
            yield state

def clear_cache() -> None:
    """清空所有缓存"""
    _HR_STATE_CACHE.clear()

def get_cache_stats() -> Dict[str, int]:
    """获取缓存统计信息"""
    site_counts = {}
    for (site, _), _ in _HR_STATE_CACHE.items():
        site_counts[site] = site_counts.get(site, 0) + 1
    return {
        "total": len(_HR_STATE_CACHE),
        "by_site": site_counts
    }

def get_all_cache_items():
    """获取所有缓存条目，用于一致性检查"""
    return _HR_STATE_CACHE.items()
