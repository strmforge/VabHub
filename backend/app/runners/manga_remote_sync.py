"""远程漫画章节同步 Runner

只负责：
- 调用 manga_remote_sync_service，同步远程章节到本地 MangaChapterLocal

不直接处理：
- 用户追更状态
- 未读数
- 通知

这些由既有的 manga_follow_sync Runner 负责。
"""
from __future__ import annotations

import argparse
import asyncio

from loguru import logger

from app.core.database import AsyncSessionLocal
from app.services.manga_remote_sync_service import sync_all_remote_series
from app.services.runner_heartbeat import runner_context


async def _run_once(args: argparse.Namespace) -> None:
    async with AsyncSessionLocal() as session:
        results = await sync_all_remote_series(
            session,
            only_followed=not args.include_unfollowed,
            min_sync_interval_minutes=args.min_sync_interval,
            limit_per_run=args.limit,
        )

        if not results:
            logger.info("本次远程章节同步没有需要处理的系列")
            return

        for r in results:
            if r.had_error:
                logger.error(
                    "[SERIES {sid}] 同步失败: {msg} (source_id={src}, remote_series_id={rid})",
                    sid=r.series_id,
                    msg=r.error_message,
                    src=r.source_id,
                    rid=r.remote_series_id,
                )
            else:
                logger.info(
                    "[SERIES {sid}] 同步成功，新增章节 {cnt} 个 (source_id={src}, remote_series_id={rid})",
                    sid=r.series_id,
                    cnt=r.new_chapters_count,
                    src=r.source_id,
                    rid=r.remote_series_id,
                )


async def _main_async(args: argparse.Namespace) -> None:
    """异步主入口，带心跳上报"""
    recommended_interval = args.loop_interval // 60 if args.loop else 5
    
    async with runner_context("manga_remote_sync", runner_type="scheduled", recommended_interval_min=recommended_interval):
        if args.loop:
            while True:
                await _run_once(args)
                await asyncio.sleep(args.loop_interval)
        else:
            await _run_once(args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync remote manga series chapters")
    parser.add_argument(
        "--include-unfollowed",
        action="store_true",
        help="Also sync series without any user follows",
    )
    parser.add_argument(
        "--min-sync-interval",
        type=int,
        default=30,
        help="Minimum minutes between sync for the same series (default: 30)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max series per run (0 means unlimited)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run in loop mode",
    )
    parser.add_argument(
        "--loop-interval",
        type=int,
        default=300,
        help="Loop interval seconds when --loop is enabled (default: 300)",
    )
    args = parser.parse_args()

    if args.limit == 0:
        args.limit = None

    asyncio.run(_main_async(args))


if __name__ == "__main__":  # pragma: no cover
    main()
