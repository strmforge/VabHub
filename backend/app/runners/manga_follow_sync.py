"""漫画追更 Runner

扫描所有 UserMangaFollow 记录，对每个系列执行同步，并根据新增章节数：
- 更新 UserMangaFollow.last_synced_chapter_id
- 递增 UserMangaFollow.unread_chapter_count
- 为每个追更该系列的用户发送漫画更新通知

支持两种模式：
- 本地导入模式：downloaded_chapters > 0，下载章节到本地
- 纯远程追更模式：downloaded_chapters == 0 且 source_id 不为空，仅检查远程更新

可以通过 CLI 启动，例如：
    python -m app.runners.manga_follow_sync
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal
from app.models.user_manga_follow import UserMangaFollow
from app.models.manga_source import MangaSource
from app.services.manga_sync_service import sync_series_from_remote
from app.services.notification_service import notify_manga_updated_for_user
from app.services.runner_heartbeat import runner_context
from app.modules.manga_sources.factory import get_manga_source_adapter


async def _sync_remote_series(
    db: AsyncSession,
    series: MangaSeriesLocal,
    follows: List[UserMangaFollow]
) -> int:
    """同步远程漫画系列（不下载章节）
    
    Args:
        db: 数据库会话
        series: 漫画系列信息
        follows: 该系列的追更记录列表
        
    Returns:
        新增章节数
    """
    if not series.source_id or not series.remote_series_id:
        logger.warning(f"系列 {series.id} 缺少源信息，跳过远程同步")
        return 0
    
    try:
        # 获取适配器和源信息
        adapter = await get_manga_source_adapter(db, series.source_id)
        if not adapter:
            logger.warning(f"无法获取源 {series.source_id} 的适配器，跳过系列 {series.id}")
            return 0
        
        # 获取源名称用于通知
        source_stmt = select(MangaSource).where(MangaSource.id == series.source_id)
        source_result = await db.execute(source_stmt)
        manga_source = source_result.scalar_one_or_none()
        source_name = manga_source.name if manga_source else f"源{series.source_id}"
        
        # 获取远程章节列表
        remote_chapters = await adapter.list_chapters(series.remote_series_id)
        if not remote_chapters:
            logger.info(f"系列 {series.title} 无远程章节数据")
            return 0
        
        # 按章节号排序，获取最新章节
        remote_chapters.sort(key=lambda x: (x.number or 0, x.published_at or ""), reverse=True)
        latest_remote_chapter = remote_chapters[0]
        
        # 计算新章节（基于所有用户的最新同步点）
        earliest_sync_index = len(remote_chapters)  # 默认认为所有章节都是新的
        
        for follow in follows:
            last_remote_id = follow.last_remote_chapter_id
            if last_remote_id:
                # 找到上次同步的章节在列表中的位置
                last_index = next((i for i, ch in enumerate(remote_chapters) if ch.remote_id == last_remote_id), -1)
                if last_index >= 0:
                    # 取最早的同步点（最小索引）
                    earliest_sync_index = min(earliest_sync_index, last_index)
        
        # 新章节是最早同步点之前的所有章节
        new_chapters = remote_chapters[:earliest_sync_index] if earliest_sync_index < len(remote_chapters) else []
        
        # 为每个用户更新追更记录和发送通知
        for follow in follows:
            if new_chapters:
                # 更新追更记录
                follow.last_remote_chapter_id = latest_remote_chapter.remote_id
                follow.unread_chapter_count = len(new_chapters)
                
                # 发送远程更新通知
                try:
                    from app.schemas.notification_reading import create_manga_updated_payload
                    
                    payload = create_manga_updated_payload(
                        series_id=series.id,
                        title=series.title,
                        cover_url=series.cover_url,
                        new_chapters=[ch.title for ch in new_chapters],
                        latest_chapter_id=None,  # 远程模式没有本地章节ID
                        is_remote=True,  # 标记为远程更新
                        source_name=source_name,
                    )
                    
                    await notify_manga_updated_for_user(
                        session=db,
                        user_id=follow.user_id,
                        payload=payload.dict(),
                    )
                    
                    logger.info(
                        f"为用户 {follow.user_id} 发送远程漫画更新通知：《{series.title}》新增 {len(new_chapters)} 章节"
                    )
                except Exception as notify_err:
                    logger.error(f"为用户 {follow.user_id} 发送远程漫画更新通知失败: {notify_err}")
        
        return len(new_chapters)
        
    except Exception as e:
        logger.error(f"远程同步系列 {series.title} 失败: {e}", exc_info=True)
        return 0


async def _is_remote_series(db: AsyncSession, series_id: int) -> bool:
    """检查是否为纯远程追更系列"""
    stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()
    
    if not series:
        return False
    
    return (
        series.downloaded_chapters == 0 and 
        series.source_id is not None and 
        series.remote_series_id is not None
    )


async def _sync_followed_manga_once(db: AsyncSession) -> None:
    """执行一次漫画追更同步。

    步骤：
    1. 扫描所有 UserMangaFollow，按 series_id 分组
    2. 对每个系列检测模式（本地导入 vs 纯远程追更）
    3. 本地模式：调用 sync_series_from_remote 下载章节
    4. 远程模式：调用 _sync_remote_series 检查更新
    5. 若有新增章节：
       - 更新对应的 last_synced_chapter_id 或 last_remote_chapter_id
       - 更新 unread_chapter_count
       - 发送通知（本地或远程）
    6. 打印汇总日志
    """
    # 1. 读取所有追更记录，同时获取系列信息用于模式检测
    stmt = select(UserMangaFollow, MangaSeriesLocal).join(
        MangaSeriesLocal, UserMangaFollow.series_id == MangaSeriesLocal.id
    ).order_by(UserMangaFollow.series_id, UserMangaFollow.user_id)
    result = await db.execute(stmt)
    follow_records = result.all()

    if not follow_records:
        logger.info("当前没有任何漫画追更记录 (user_manga_follow 为空)")
        return

    # 按系列分组
    series_to_follows: Dict[int, List[UserMangaFollow]] = defaultdict(list)
    series_info: Dict[int, MangaSeriesLocal] = {}
    
    for follow, series in follow_records:
        series_to_follows[follow.series_id].append(follow)
        series_info[follow.series_id] = series

    total_series = len(series_to_follows)
    total_follows = len(follow_records)
    local_series_count = 0
    remote_series_count = 0
    
    logger.info(f"开始漫画追更同步: 共发现 {total_series} 个追更中的系列, 总追更关系 {total_follows} 条")

    total_new_chapters = 0
    updated_follows = 0

    # 2. 针对每个系列执行同步
    for series_id, series_follows in series_to_follows.items():
        series = series_info[series_id]
        
        # 检测同步模式
        is_remote = (
            series.downloaded_chapters == 0 and 
            series.source_id is not None and 
            series.remote_series_id is not None
        )
        
        try:
            if is_remote:
                # 远程模式：仅检查更新，不下载章节
                remote_series_count += 1
                logger.info(f"系列《{series.title}》(ID: {series_id}) 使用远程同步模式")
                
                new_count = await _sync_remote_series(db, series, series_follows)
                
            else:
                # 本地模式：下载章节到本地
                local_series_count += 1
                logger.info(f"系列《{series.title}》(ID: {series_id}) 使用本地同步模式")
                
                sync_result = await sync_series_from_remote(
                    session=db,
                    series_id=series_id,
                    download_new=False,
                )

                # sync_series_from_remote 可能返回 int 或 dict，这里统一取 new_chapters
                if isinstance(sync_result, dict):
                    new_count = int(sync_result.get("new_chapters", 0) or 0)
                else:
                    new_count = int(sync_result or 0)

                if new_count > 0:
                    # 本地模式需要更新 last_synced_chapter_id
                    chapter_stmt = (
                        select(MangaChapterLocal)
                        .where(MangaChapterLocal.series_id == series_id)
                        .order_by(MangaChapterLocal.id.desc())
                        .limit(1)
                    )
                    chapter_result = await db.execute(chapter_stmt)
                    latest_chapter = chapter_result.scalar_one_or_none()
                    latest_chapter_id = latest_chapter.id if latest_chapter else None

                    # 更新所有追更该系列的记录
                    for follow in series_follows:
                        follow.last_synced_chapter_id = latest_chapter_id
                        follow.unread_chapter_count = (follow.unread_chapter_count or 0) + new_count
                        updated_follows += 1

                        # 发送本地更新通知
                        try:
                            from app.schemas.notification_reading import create_manga_updated_payload
                            
                            # 获取新章节标题列表
                            new_chapters_query = select(MangaChapterLocal).where(
                                MangaChapterLocal.series_id == series.id,
                                MangaChapterLocal.id > (follow.last_synced_chapter_id or 0)
                            ).order_by(MangaChapterLocal.id).limit(new_count)
                            
                            new_chapters_result = await db.execute(new_chapters_query)
                            new_chapters = new_chapters_result.scalars().all()
                            new_chapter_titles = [chapter.title for chapter in new_chapters]
                            
                            # 创建标准化 payload
                            payload = create_manga_updated_payload(
                                series_id=series.id,
                                title=series.title,
                                cover_url=series.cover_url,
                                new_chapters=new_chapter_titles,
                                latest_chapter_id=latest_chapter_id,
                                is_remote=False,
                            )
                            
                            await notify_manga_updated_for_user(
                                session=db,
                                user_id=follow.user_id,
                                payload=payload.dict(),
                            )
                        except Exception as notify_err:
                            logger.error(f"为用户 {follow.user_id} 发送漫画更新通知失败: {notify_err}")

            if new_count > 0:
                total_new_chapters += new_count
                updated_follows += len(series_follows)
                logger.info(f"系列《{series.title}》新增 {new_count} 个章节")
            else:
                logger.info(f"系列《{series.title}》无新增章节")

            # 提交本系列的更新
            await db.commit()

        except Exception as e:
            logger.error(f"同步追更系列 {series_id} 时发生错误: {e}", exc_info=True)
            await db.rollback()

    logger.info(
        f"漫画追更同步完成: 处理系列 {total_series} 个 (本地 {local_series_count} 个, 远程 {remote_series_count} 个), "
        f"更新追更记录 {updated_follows} 条, 新增章节总数 {total_new_chapters} 个"
    )


async def main() -> None:
    """Runner 主入口（单次执行）。"""
    async with runner_context("manga_follow_sync", runner_type="scheduled", recommended_interval_min=5):
        logger.info("=" * 60)
        logger.info("VabHub Manga Follow Sync Runner")
        logger.info("=" * 60)

        async with AsyncSessionLocal() as db:
            await _sync_followed_manga_once(db)


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
