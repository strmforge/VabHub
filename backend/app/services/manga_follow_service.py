"""漫画追更（追更关系）服务

基于 UserMangaFollow 表，为 API 提供最小追更能力：
- follow_series: 关注某个本地漫画系列
- unfollow_series: 取消关注
- list_following: 列出当前用户所有追更中的漫画及其追更状态
- mark_read: 标记某个系列已读（清零未读计数 / 更新 last_seen_chapter_id）
- follow_remote_series: 关注外部源漫画系列（不下载章节）
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manga_series_local import MangaSeriesLocal
from app.models.user_manga_follow import UserMangaFollow
from app.schemas.manga_follow import (
    UserMangaFollowRead,
    FollowedMangaItem,
)
from app.services.manga_remote_service import get_series_detail
from app.modules.manga_sources.factory import get_manga_source_adapter


async def follow_series(
    session: AsyncSession,
    *,
    user_id: int,
    series_id: int,
) -> UserMangaFollowRead:
    """关注某个本地漫画系列。

    - 如果已存在 user_id + series_id 的追更记录，则直接返回
    - 如果不存在，则创建一条新记录，未读数默认为 0
    """
    stmt = select(UserMangaFollow).where(
        and_(
            UserMangaFollow.user_id == user_id,
            UserMangaFollow.series_id == series_id,
        )
    )
    result = await session.execute(stmt)
    follow = result.scalar_one_or_none()

    if not follow:
        follow = UserMangaFollow(
            user_id=user_id,
            series_id=series_id,
            unread_chapter_count=0,
        )
        session.add(follow)
        await session.commit()
        await session.refresh(follow)

    return UserMangaFollowRead.model_validate(follow)


async def unfollow_series(
    session: AsyncSession,
    *,
    user_id: int,
    series_id: int,
) -> bool:
    """取消关注某个本地漫画系列。

    返回是否删除了记录。
    """
    stmt = select(UserMangaFollow).where(
        and_(
            UserMangaFollow.user_id == user_id,
            UserMangaFollow.series_id == series_id,
        )
    )
    result = await session.execute(stmt)
    follow = result.scalar_one_or_none()

    if not follow:
        return False

    await session.delete(follow)
    await session.commit()
    return True


async def list_following(
    session: AsyncSession,
    *,
    user_id: int,
) -> List[FollowedMangaItem]:
    """列出当前用户追更中的所有漫画系列。

    当前实现为最小集：
    - 仅使用 UserMangaFollow + MangaSeriesLocal
    - 未读数量由 unread_chapter_count 字段直接返回
    章节级的精细未读统计可在后续同步逻辑中逐步完善。
    """
    stmt = (
        select(UserMangaFollow, MangaSeriesLocal)
        .join(MangaSeriesLocal, UserMangaFollow.series_id == MangaSeriesLocal.id)
        .where(UserMangaFollow.user_id == user_id)
        .order_by(MangaSeriesLocal.title.asc())
    )
    result = await session.execute(stmt)
    rows = result.all()

    items: List[FollowedMangaItem] = []
    for follow, series in rows:
        items.append(
            FollowedMangaItem(
                follow_id=follow.id,
                series_id=series.id,
                series_title=series.title,
                cover_url=f"/media/{series.cover_path}" if series.cover_path else None,
                source_id=series.source_id,
                unread_chapter_count=follow.unread_chapter_count,
                last_synced_chapter_id=follow.last_synced_chapter_id,
                last_seen_chapter_id=follow.last_seen_chapter_id,
                created_at=follow.created_at,
                updated_at=follow.updated_at,
            )
        )

    return items


async def mark_read(
    session: AsyncSession,
    *,
    user_id: int,
    series_id: int,
    last_seen_chapter_id: Optional[int] = None,
) -> Optional[UserMangaFollowRead]:
    """标记某个系列为已读或更新 last_seen_chapter_id。

    行为：
    - 找到当前用户的追更记录
    - 如果存在：
        - 更新 last_seen_chapter_id（如果提供）
        - 将 unread_chapter_count 置为 0
    - 如果不存在：返回 None（API 层可据此返回 404 或静默成功）
    """
    stmt = select(UserMangaFollow).where(
        and_(
            UserMangaFollow.user_id == user_id,
            UserMangaFollow.series_id == series_id,
        )
    )
    result = await session.execute(stmt)
    follow = result.scalar_one_or_none()

    if not follow:
        return None

    if last_seen_chapter_id is not None:
        follow.last_seen_chapter_id = last_seen_chapter_id

    follow.unread_chapter_count = 0

    await session.commit()
    await session.refresh(follow)

    return UserMangaFollowRead.model_validate(follow)


async def follow_remote_series(
    session: AsyncSession,
    *,
    user_id: int,
    source_id: int,
    remote_series_id: str,
) -> UserMangaFollowRead:
    """关注外部源漫画系列（不下载章节）。
    
    1. 检查是否已存在对应的 MangaSeriesLocal 记录
    2. 如果不存在，从远程源获取元数据并创建记录
    3. 创建或更新 UserMangaFollow 记录
    
    注意：此函数创建的 MangaSeriesLocal 记录：
    - downloaded_chapters = 0（表示纯远程追更）
    - total_chapters 从远程源获取
    """
    # 1. 查找是否已存在对应的本地系列记录
    series_stmt = select(MangaSeriesLocal).where(
        and_(
            MangaSeriesLocal.source_id == source_id,
            MangaSeriesLocal.remote_series_id == remote_series_id,
        )
    )
    series_result = await session.execute(series_stmt)
    series = series_result.scalar_one_or_none()
    
    # 2. 如果不存在，从远程源获取元数据并创建记录
    if not series:
        # 获取远程系列详情
        remote_series = await get_series_detail(
            session=session,
            source_id=source_id,
            remote_series_id=remote_series_id,
        )
        
        if not remote_series:
            raise ValueError(f"无法从源 {source_id} 获取远程系列 {remote_series_id} 的详情")
        
        # 创建本地系列记录（仅元数据，不下载章节）
        series = MangaSeriesLocal(
            source_id=source_id,
            remote_series_id=remote_series_id,
            title=remote_series.title,
            alt_titles=remote_series.alt_titles,
            summary=remote_series.summary,
            authors=remote_series.authors,
            tags=remote_series.tags,
            status=remote_series.status,
            total_chapters=remote_series.chapters_count,
            downloaded_chapters=0,  # 标记为纯远程追更
            new_chapter_count=0,
            remote_meta=remote_series.model_dump(),
        )
        session.add(series)
        await session.flush()  # 获取 ID 但不提交
        await session.refresh(series)
    
    # 3. 创建或更新追更记录
    follow_stmt = select(UserMangaFollow).where(
        and_(
            UserMangaFollow.user_id == user_id,
            UserMangaFollow.series_id == series.id,
        )
    )
    follow_result = await session.execute(follow_stmt)
    follow = follow_result.scalar_one_or_none()
    
    if not follow:
        follow = UserMangaFollow(
            user_id=user_id,
            series_id=series.id,
            unread_chapter_count=0,
        )
        session.add(follow)
    
    await session.commit()
    await session.refresh(follow)
    
    return UserMangaFollowRead.model_validate(follow)
