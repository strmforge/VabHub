"""
修复 RSSHub 订阅中缺失外键 / 脏数据的辅助脚本。

功能特性：
- 支持 `--dry-run` 仅预览不写库；
- 支持 `--limit N` 限制最大修复条数；
- 支持 `--verbose` 输出详细记录。
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from typing import Dict, Tuple

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.rsshub import RSSHubSource, RSSHubComposite, UserRSSHubSubscription
from app.modules.rsshub.constants import LEGACY_SOURCE_ID, LEGACY_COMPOSITE_ID


async def _ensure_default_records(
    session: AsyncSession,
    *,
    dry_run: bool = False,
) -> Tuple[RSSHubSource, RSSHubComposite]:
    """确保存在默认 Source / Composite 记录"""
    default_source = await session.get(RSSHubSource, LEGACY_SOURCE_ID)
    if not default_source:
        default_source = RSSHubSource(
            id=LEGACY_SOURCE_ID,
            name="Legacy Default Source",
            url_path="/legacy/default",
            type="mixed",
            group="rank",
            description="用于接管历史遗留且无效的 RSSHub 订阅目标。",
            is_template=False,
            default_enabled=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        if not dry_run:
            session.add(default_source)

    default_composite = await session.get(RSSHubComposite, LEGACY_COMPOSITE_ID)
    if not default_composite:
        default_composite = RSSHubComposite(
            id=LEGACY_COMPOSITE_ID,
            name="Legacy Default Composite",
            type="mixed",
            description="用于接管历史遗留且无效的 RSSHub 组合订阅目标。",
            default_enabled=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        if not dry_run:
            session.add(default_composite)

    if not dry_run:
        await session.commit()

    return default_source, default_composite


async def fix_rsshub_subscriptions(
    *,
    dry_run: bool = False,
    limit: int | None = None,
    verbose: bool = False,
) -> None:
    async with AsyncSessionLocal() as session:
        default_source, default_composite = await _ensure_default_records(session, dry_run=dry_run)

        source_ids = set((await session.execute(select(RSSHubSource.id))).scalars().all())
        composite_ids = set((await session.execute(select(RSSHubComposite.id))).scalars().all())

        result = await session.execute(select(UserRSSHubSubscription))
        subscriptions = result.scalars().all()

        stats: Dict[str, int] = {
            "scanned": len(subscriptions),
            "fixed_sources": 0,
            "fixed_composites": 0,
            "disabled": 0,
            "skipped": 0,
        }

        for sub in subscriptions:
            if limit is not None and (stats["fixed_sources"] + stats["fixed_composites"]) >= limit:
                logger.info(f"达到限制 {limit}，提前终止修复。")
                break

            needs_fix = False
            fallback_kind = "source"
            fallback_id = default_source.id

            if sub.target_type == "source":
                if not sub.target_id or sub.target_id not in source_ids:
                    needs_fix = True
                    fallback_kind = "source"
                    fallback_id = default_source.id
            elif sub.target_type == "composite":
                if not sub.target_id or sub.target_id not in composite_ids:
                    needs_fix = True
                    fallback_kind = "composite"
                    fallback_id = default_composite.id
            else:
                needs_fix = True
                fallback_kind = "source"
                fallback_id = default_source.id

            if not needs_fix:
                stats["skipped"] += 1
                continue

            if fallback_kind == "source":
                stats["fixed_sources"] += 1
            else:
                stats["fixed_composites"] += 1
            stats["disabled"] += 1

            if verbose:
                logger.info(
                    f"[RSSHub-FIX] user={sub.user_id} target={sub.target_id} "
                    f"type={sub.target_type} -> fallback={fallback_id}"
                )

            if dry_run:
                continue

            sub.target_id = fallback_id
            sub.target_type = fallback_kind
            sub.enabled = False
            sub.updated_at = datetime.utcnow()

        if dry_run:
            await session.rollback()
        else:
            await session.commit()

        logger.info(
            "[RSSHub-FIX] Summary: "
            + json.dumps(
                {
                    "dry_run": dry_run,
                    "limit": limit,
                    **stats,
                },
                ensure_ascii=False,
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="修复 RSSHub 订阅中的无效外键记录")
    parser.add_argument("--dry-run", action="store_true", help="仅预览将要修复的记录，不写入数据库")
    parser.add_argument("--limit", type=int, help="限制本次修复的最大记录数")
    parser.add_argument("--verbose", action="store_true", help="输出详细的修复记录")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.dry_run:
        logger.info("以 dry-run 模式运行，不会写入数据库")
    asyncio.run(
        fix_rsshub_subscriptions(
            dry_run=args.dry_run,
            limit=args.limit,
            verbose=args.verbose,
        )
    )


if __name__ == "__main__":
    main()

