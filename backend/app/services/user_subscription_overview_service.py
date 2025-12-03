"""
用户订阅汇总服务
BOT-TELEGRAM Phase 2

汇总用户的各类订阅（漫画追更、音乐榜单等）
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User


@dataclass
class UserSubscriptionOverviewItem:
    """用户订阅汇总项"""
    id: int
    kind: str  # manga_follow / music_chart / rss / ...
    title: str
    status: str  # enabled / disabled / error
    last_run_at: Optional[datetime] = None
    last_result: Optional[str] = None  # success / failure
    extra: Optional[dict] = None


async def list_user_subscriptions(
    session: AsyncSession,
    user: User,
    kind: Optional[str] = None,
) -> list[UserSubscriptionOverviewItem]:
    """
    获取用户所有订阅的汇总列表
    
    Args:
        session: 数据库会话
        user: 用户对象
        kind: 订阅类型筛选
        
    Returns:
        订阅列表
    """
    items: list[UserSubscriptionOverviewItem] = []
    
    # 1. 漫画追更
    if kind is None or kind == "manga":
        try:
            manga_items = await _get_manga_follows(session, user.id)
            items.extend(manga_items)
        except Exception as e:
            logger.warning(f"[subscription-overview] get manga follows failed: {e}")
    
    # 2. 音乐榜单订阅
    if kind is None or kind == "music":
        try:
            music_items = await _get_music_subscriptions(session, user.id)
            items.extend(music_items)
        except Exception as e:
            logger.warning(f"[subscription-overview] get music subscriptions failed: {e}")
    
    # TODO: 3. RSS 订阅
    # TODO: 4. 其他订阅类型
    
    return items


async def _get_manga_follows(
    session: AsyncSession,
    user_id: int,
) -> list[UserSubscriptionOverviewItem]:
    """获取漫画追更列表"""
    items = []
    
    try:
        from app.models.user_manga_follow import UserMangaFollow
        from app.models.manga_series_local import MangaSeriesLocal
        
        stmt = (
            select(UserMangaFollow, MangaSeriesLocal)
            .join(MangaSeriesLocal, UserMangaFollow.series_id == MangaSeriesLocal.id)
            .where(UserMangaFollow.user_id == user_id)
            .order_by(UserMangaFollow.created_at.desc())
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        for follow, series in rows:
            items.append(UserSubscriptionOverviewItem(
                id=follow.id,
                kind="manga_follow",
                title=series.title,
                status="enabled" if getattr(follow, "is_enabled", True) else "disabled",
                last_run_at=getattr(follow, "last_check_at", None),
                last_result="success" if getattr(follow, "last_check_ok", True) else "failure",
                extra={
                    "series_id": series.id,
                    "chapter_count": series.chapter_count if hasattr(series, "chapter_count") else None,
                },
            ))
    except ImportError:
        logger.debug("[subscription-overview] manga follow models not available")
    except Exception as e:
        logger.warning(f"[subscription-overview] query manga follows failed: {e}")
    
    return items


async def _get_music_subscriptions(
    session: AsyncSession,
    user_id: int,
) -> list[UserSubscriptionOverviewItem]:
    """获取音乐榜单订阅列表"""
    items = []
    
    try:
        from app.models.user_music_subscription import UserMusicSubscription
        
        stmt = (
            select(UserMusicSubscription)
            .where(UserMusicSubscription.user_id == user_id)
            .order_by(UserMusicSubscription.created_at.desc())
        )
        
        result = await session.execute(stmt)
        subscriptions = result.scalars().all()
        
        for sub in subscriptions:
            title = getattr(sub, "name", None) or getattr(sub, "chart_name", None) or f"音乐订阅 #{sub.id}"
            
            items.append(UserSubscriptionOverviewItem(
                id=sub.id,
                kind="music_chart",
                title=title,
                status="enabled" if getattr(sub, "is_enabled", True) else "disabled",
                last_run_at=getattr(sub, "last_sync_at", None),
                last_result="success" if getattr(sub, "last_sync_ok", True) else "failure",
                extra={
                    "chart_type": getattr(sub, "chart_type", None),
                },
            ))
    except ImportError:
        logger.debug("[subscription-overview] music subscription models not available")
    except Exception as e:
        logger.warning(f"[subscription-overview] query music subscriptions failed: {e}")
    
    return items


async def toggle_subscription(
    session: AsyncSession,
    user: User,
    kind: str,
    sub_id: int,
) -> bool:
    """
    切换订阅启用/禁用状态
    
    Returns:
        新的启用状态
    """
    match kind:
        case "manga_follow":
            return await _toggle_manga_follow(session, user.id, sub_id)
        case "music_chart":
            return await _toggle_music_subscription(session, user.id, sub_id)
        case _:
            raise ValueError(f"Unknown subscription kind: {kind}")


async def _toggle_manga_follow(
    session: AsyncSession,
    user_id: int,
    follow_id: int,
) -> bool:
    """切换漫画追更状态"""
    try:
        from app.models.user_manga_follow import UserMangaFollow
        
        stmt = select(UserMangaFollow).where(
            UserMangaFollow.id == follow_id,
            UserMangaFollow.user_id == user_id,
        )
        result = await session.execute(stmt)
        follow = result.scalar_one_or_none()
        
        if not follow:
            raise ValueError("追更不存在")
        
        # 切换状态
        new_status = not getattr(follow, "is_enabled", True)
        if hasattr(follow, "is_enabled"):
            follow.is_enabled = new_status
        
        await session.commit()
        return new_status
        
    except ImportError:
        raise ValueError("漫画追更功能不可用")


async def _toggle_music_subscription(
    session: AsyncSession,
    user_id: int,
    sub_id: int,
) -> bool:
    """切换音乐订阅状态"""
    try:
        from app.models.user_music_subscription import UserMusicSubscription
        
        stmt = select(UserMusicSubscription).where(
            UserMusicSubscription.id == sub_id,
            UserMusicSubscription.user_id == user_id,
        )
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()
        
        if not sub:
            raise ValueError("订阅不存在")
        
        new_status = not getattr(sub, "is_enabled", True)
        if hasattr(sub, "is_enabled"):
            sub.is_enabled = new_status
        
        await session.commit()
        return new_status
        
    except ImportError:
        raise ValueError("音乐订阅功能不可用")


async def run_subscription_once(
    session: AsyncSession,
    user: User,
    kind: str,
    sub_id: int,
) -> bool:
    """
    立即执行一次订阅同步
    
    Returns:
        是否成功触发
    """
    # TODO: 实现立即执行逻辑（可能需要调用 Runner 或任务队列）
    logger.info(f"[subscription-overview] run once: kind={kind}, id={sub_id}, user={user.id}")
    return True


async def remove_subscription(
    session: AsyncSession,
    user: User,
    kind: str,
    sub_id: int,
) -> bool:
    """
    删除订阅
    
    Returns:
        是否成功删除
    """
    match kind:
        case "manga_follow":
            return await _remove_manga_follow(session, user.id, sub_id)
        case "music_chart":
            return await _remove_music_subscription(session, user.id, sub_id)
        case _:
            raise ValueError(f"Unknown subscription kind: {kind}")


async def _remove_manga_follow(
    session: AsyncSession,
    user_id: int,
    follow_id: int,
) -> bool:
    """删除漫画追更"""
    try:
        from app.models.user_manga_follow import UserMangaFollow
        
        stmt = select(UserMangaFollow).where(
            UserMangaFollow.id == follow_id,
            UserMangaFollow.user_id == user_id,
        )
        result = await session.execute(stmt)
        follow = result.scalar_one_or_none()
        
        if not follow:
            raise ValueError("追更不存在")
        
        await session.delete(follow)
        await session.commit()
        return True
        
    except ImportError:
        raise ValueError("漫画追更功能不可用")


async def _remove_music_subscription(
    session: AsyncSession,
    user_id: int,
    sub_id: int,
) -> bool:
    """删除音乐订阅"""
    try:
        from app.models.user_music_subscription import UserMusicSubscription
        
        stmt = select(UserMusicSubscription).where(
            UserMusicSubscription.id == sub_id,
            UserMusicSubscription.user_id == user_id,
        )
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()
        
        if not sub:
            raise ValueError("订阅不存在")
        
        await session.delete(sub)
        await session.commit()
        return True
        
    except ImportError:
        raise ValueError("音乐订阅功能不可用")
