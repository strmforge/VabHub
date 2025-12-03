from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Iterable, Optional

from .models import HRStatus, HRTorrentState, TorrentLife
from .hr_cache import get_from_cache, set_to_cache, remove_from_cache, iter_site_states as cache_iter_site_states

def _get_hr_repository():
    """获取HR仓库实例"""
    from app.modules.hr_case.repository import get_hr_repository
    return get_hr_repository()

# TODO: 未来将内存缓存替换为 DB + 内存缓存的组合
# 设计思路：
# 1. 使用 SQLAlchemy 模型 HRCase 持久化到数据库
# 2. 保留内存缓存 _HR_STATE_CACHE 作为热数据缓存（LRU 或 TTL）
# 3. get_hr_state_for_torrent: 先查内存缓存，未命中则查 DB，加载到缓存
# 4. update_from_hr_page 等更新函数：同时更新 DB 和内存缓存
# 5. 定期清理过期的内存缓存项（例如：超过 7 天未访问的）


def get_hr_state_for_torrent(site: str, torrent_id: str) -> HRTorrentState:
    """获取指定种子的HR状态，优先从缓存，未命中则从数据库加载"""
    state = get_from_cache(site, str(torrent_id))
    
    if state is None:
        # 尝试从数据库加载
        try:
            hr_case = asyncio.run(_get_hr_repository().get(site, str(torrent_id)))
            if hr_case:
                # 从HrCase转换为HRTorrentState
                # 转换为HRTorrentState
                from app.modules.hr_case.repository import to_hr_torrent_state
                state = to_hr_torrent_state(hr_case)
                set_to_cache(site, str(torrent_id), state)
                return state
        except Exception as e:
            # 数据库失败时记录错误，降级到创建新状态
            import logging
            logging.getLogger(__name__).warning(f"从数据库加载HR状态失败: {e}")
        
        # 创建新状态
        state = HRTorrentState(site=site, torrent_id=str(torrent_id))
        set_to_cache(site, str(torrent_id), state)
    
    return state


def update_from_hr_page(
    site: str,
    torrent_id: str,
    required_seed_hours: float,
    seeded_hours: float,
    deadline: Optional[datetime],
    now: Optional[datetime] = None,
) -> HRTorrentState:
    """从HR页面更新状态，同时更新数据库和缓存"""
    now = now or datetime.utcnow()
    state = get_hr_state_for_torrent(site, str(torrent_id))

    state.hr_status = HRStatus.ACTIVE
    state.required_seed_hours = required_seed_hours
    state.seeded_hours = seeded_hours
    state.deadline = deadline
    state.last_seen_at = now
    if state.first_seen_at is None:
        state.first_seen_at = now

    # 通过仓库更新数据库（双写：DB + 缓存）
    try:
        asyncio.run(_get_hr_repository().upsert_from_hr_page(
            site_key=site,
            torrent_id=str(torrent_id),
            site_id=None,  # 仓库内部会获取
            required_hours=required_seed_hours,
            seeded_hours=seeded_hours,
            deadline=deadline
        ))
    except Exception as e:
        # 数据库失败时记录错误，但缓存已更新
        import logging
        logging.getLogger(__name__).error(f"更新HR状态到数据库失败: {e}")

    return state


def mark_from_hr_page_disappear(
    state: HRTorrentState,
    disappear_semantics: str,
    now: Optional[datetime] = None,
) -> HRTorrentState:
    """标记HR页面消失，更新数据库和缓存"""
    now = now or datetime.utcnow()

    if disappear_semantics.upper() == "FINISHED":
        state.hr_status = HRStatus.FINISHED
    else:
        state.hr_status = HRStatus.UNKNOWN

    state.last_seen_at = now
    
    # 通过仓库更新数据库
    try:
        asyncio.run(_get_hr_repository().upsert(state))
    except Exception as e:
        # 数据库失败时记录错误，但缓存已更新
        import logging
        logging.getLogger(__name__).error(f"标记HR页面消失到数据库失败: {e}")
    
    return state


def mark_penalized(state: HRTorrentState, now: Optional[datetime] = None) -> HRTorrentState:
    """标记违规，更新数据库和缓存"""
    now = now or datetime.utcnow()
    state.hr_status = HRStatus.FAILED
    state.last_seen_at = now
    
    # 通过仓库标记违规
    try:
        asyncio.run(_get_hr_repository().mark_penalized(
            state.site, str(state.torrent_id)
        ))
    except Exception as e:
        # 数据库失败时记录错误，但缓存已更新
        import logging
        logging.getLogger(__name__).error(f"标记HR违规到数据库失败: {e}")
    
    return state


def mark_torrent_deleted(state: HRTorrentState, now: Optional[datetime] = None) -> HRTorrentState:
    """标记种子删除，更新数据库和缓存"""
    now = now or datetime.utcnow()
    state.life_status = TorrentLife.DELETED
    state.last_seen_at = now
    
    # 通过仓库标记删除
    try:
        asyncio.run(_get_hr_repository().mark_deleted(
            state.site, str(state.torrent_id)
        ))
    except Exception as e:
        # 数据库失败时记录错误，但缓存已更新
        import logging
        logging.getLogger(__name__).error(f"标记种子删除到数据库失败: {e}")
    
    return state


def iter_site_states(site: str) -> Iterable[HRTorrentState]:
    """遍历指定站点当前缓存的 HR 状态。"""
    return cache_iter_site_states(site)

