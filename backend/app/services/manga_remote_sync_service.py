"""远程漫画章节同步服务

专门负责：
- 从远程源获取最新章节列表
- 与本地 MangaChapterLocal 做 diff
- 创建缺失的本地章节记录（status=PENDING）
- 更新 MangaSeriesLocal 的统计和 last_sync_at

不负责：
- 未读数统计
- 通知发送
- 章节文件下载

这些交由现有的 manga_follow_sync Runner 及相关服务处理。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manga_chapter_local import MangaChapterLocal, MangaChapterStatus
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_source import MangaSource
from app.models.user_manga_follow import UserMangaFollow
from app.schemas.manga_remote import RemoteMangaChapter
from app.services.manga_remote_service import list_chapters


@dataclass
class SeriesSyncResult:
    """单个系列远程章节同步结果。"""

    series_id: int
    source_id: Optional[int]
    remote_series_id: Optional[str]
    new_chapters_count: int
    had_error: bool = False
    error_message: Optional[str] = None


async def sync_remote_series_once(
    session: AsyncSession,
    *,
    series: MangaSeriesLocal,
) -> SeriesSyncResult:
    """同步单个本地漫画系列的远程章节。

    不提交事务，也不做 rollback，由调用方或批量函数管理事务。
    """
    series_id = series.id
    source_id = series.source_id
    remote_series_id = series.remote_series_id

    if not source_id or not remote_series_id:
        # 无法关联远程源，视为无更新，但不算错误
        return SeriesSyncResult(
            series_id=series_id,
            source_id=source_id,
            remote_series_id=remote_series_id,
            new_chapters_count=0,
            had_error=False,
        )

    try:
        # 1. 获取源信息
        stmt = select(MangaSource).where(MangaSource.id == source_id, MangaSource.is_enabled == True)  # noqa: E712
        result = await session.execute(stmt)
        source = result.scalar_one_or_none()
        if not source:
            logger.warning("系列 {} 的源 {} 不存在或未启用，跳过远程同步", series_id, source_id)
            return SeriesSyncResult(
                series_id=series_id,
                source_id=source_id,
                remote_series_id=remote_series_id,
                new_chapters_count=0,
                had_error=False,
            )

        # 2. 获取远程章节列表
        remote_chapters: List[RemoteMangaChapter] = await list_chapters(
            session=session,
            source_id=source_id,
            remote_series_id=remote_series_id,
        )

        if not remote_chapters:
            logger.info("系列 {} 从远程源获取到 0 个章节", series_id)
            return SeriesSyncResult(
                series_id=series_id,
                source_id=source_id,
                remote_series_id=remote_series_id,
                new_chapters_count=0,
                had_error=False,
            )

        # 3. 获取本地已有章节的 remote_chapter_id 集合
        stmt = select(MangaChapterLocal.remote_chapter_id).where(
            MangaChapterLocal.series_id == series_id
        )
        result = await session.execute(stmt)
        local_ids = {row[0] for row in result.fetchall() if row[0] is not None}

        # 4. 找出新增章节
        new_remote_chapters: List[RemoteMangaChapter] = [
            ch for ch in remote_chapters if ch.remote_id not in local_ids
        ]

        if not new_remote_chapters:
            # 仍然更新总章节数和 last_sync_at
            series.total_chapters = len(remote_chapters)
            series.last_sync_at = datetime.utcnow()
            return SeriesSyncResult(
                series_id=series_id,
                source_id=source_id,
                remote_series_id=remote_series_id,
                new_chapters_count=0,
                had_error=False,
            )

        # 5. 按合理顺序排序新增章节（按卷/话号/发布时间）
        def _chapter_sort_key(ch: RemoteMangaChapter):
            # None 排到最后
            vol = ch.volume if ch.volume is not None else 10**9
            num = ch.number if ch.number is not None else 10**9
            pub = ch.published_at or datetime.max
            return (vol, num, pub, ch.remote_id)

        new_remote_chapters.sort(key=_chapter_sort_key)

        # 6. 为新增章节创建本地记录
        new_count = 0
        for remote_chapter in new_remote_chapters:
            local_chapter = MangaChapterLocal(
                series_id=series_id,
                remote_chapter_id=remote_chapter.remote_id,
                title=remote_chapter.title,
                number=remote_chapter.number,
                volume=remote_chapter.volume,
                published_at=remote_chapter.published_at,
                status=MangaChapterStatus.PENDING,
            )
            # 如果模型后续增加了 source_id 等字段，可在此处一并填充
            if hasattr(local_chapter, "source_id"):
                setattr(local_chapter, "source_id", source_id)

            session.add(local_chapter)
            new_count += 1

        # 7. 更新系列统计信息
        series.total_chapters = len(remote_chapters)
        series.last_sync_at = datetime.utcnow()
        # new_chapter_count 字段在现有逻辑中用于“本轮新章节数”
        if hasattr(series, "new_chapter_count"):
            try:
                series.new_chapter_count = new_count
            except Exception:  # 容错，避免因为字段缺失导致失败
                pass

        logger.info(
            "系列《{}》(ID: {}) 远程同步完成，新增章节 {} 个，总章节 {} 个",
            series.title,
            series.id,
            new_count,
            series.total_chapters,
        )

        return SeriesSyncResult(
            series_id=series_id,
            source_id=source_id,
            remote_series_id=remote_series_id,
            new_chapters_count=new_count,
            had_error=False,
        )

    except Exception as e:  # noqa: BLE001
        logger.error(
            "同步系列 {} 的远程章节失败: {}",
            series_id,
            e,
            exc_info=True,
        )
        # 由调用方负责 rollback
        return SeriesSyncResult(
            series_id=series_id,
            source_id=source_id,
            remote_series_id=remote_series_id,
            new_chapters_count=0,
            had_error=True,
            error_message=str(e),
        )


async def sync_all_remote_series(
    session: AsyncSession,
    *,
    only_followed: bool = True,
    min_sync_interval_minutes: int = 30,
    limit_per_run: Optional[int] = None,
) -> List[SeriesSyncResult]:
    """批量同步远程章节。

    - 可选择只同步有追更记录的系列
    - 通过 last_sync_at 做简单节流
    - 按 last_sync_at 升序，优先同步长时间未更新的系列
    """
    # 1. 构造基础查询
    stmt = select(MangaSeriesLocal).where(
        and_(
            MangaSeriesLocal.source_id.isnot(None),
            MangaSeriesLocal.remote_series_id.isnot(None),
        )
    )

    if only_followed:
        stmt = stmt.join(
            UserMangaFollow,
            UserMangaFollow.series_id == MangaSeriesLocal.id,
        ).distinct()

    # 2. 根据 last_sync_at 做节流
    threshold = datetime.utcnow() - timedelta(minutes=min_sync_interval_minutes)
    stmt = stmt.where(
        or_(
            MangaSeriesLocal.last_sync_at.is_(None),
            MangaSeriesLocal.last_sync_at < threshold,
        )
    )

    # 3. 排序 + limit
    stmt = stmt.order_by(
        MangaSeriesLocal.last_sync_at.asc().nullsfirst(),
        MangaSeriesLocal.id.asc(),
    )

    if limit_per_run is not None and limit_per_run > 0:
        stmt = stmt.limit(limit_per_run)

    result = await session.execute(stmt)
    series_list: List[MangaSeriesLocal] = result.scalars().all()

    if not series_list:
        logger.info("没有需要执行远程章节同步的系列")
        return []

    logger.info(
        "开始远程章节同步: 计划处理系列 {} 个 (only_followed={}, min_interval={}min, limit={})",
        len(series_list),
        only_followed,
        min_sync_interval_minutes,
        limit_per_run,
    )

    results: List[SeriesSyncResult] = []

    for series in series_list:
        try:
            sync_result = await sync_remote_series_once(session, series=series)
            if sync_result.had_error:
                # 出错时回滚本系列的改动
                await session.rollback()
            else:
                await session.commit()
            results.append(sync_result)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "批量同步中处理系列 {} 时发生未捕获异常: {}",
                series.id,
                e,
                exc_info=True,
            )
            await session.rollback()
            results.append(
                SeriesSyncResult(
                    series_id=series.id,
                    source_id=series.source_id,
                    remote_series_id=series.remote_series_id,
                    new_chapters_count=0,
                    had_error=True,
                    error_message=str(e),
                )
            )

    logger.info("远程章节批量同步完成，共处理系列 {} 个", len(results))
    return results
