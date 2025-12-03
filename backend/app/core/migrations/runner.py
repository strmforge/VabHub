from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from loguru import logger

from app.core.database import AsyncSessionLocal
from app.core.migrations.steps import MigrationStep, get_migration_steps


async def run_migrations(
    *,
    dry_run: bool = False,
    limit: Optional[int] = None,
    verbose: bool = False,
) -> List[dict]:
    """
    执行注册的迁移步骤。
    返回按照执行顺序的结果列表。
    """

    steps: List[MigrationStep] = get_migration_steps()
    if limit is not None:
        steps = steps[: limit]

    results: List[dict] = []
    for step in steps:
        result = {
            "id": step.id,
            "title": step.title,
            "description": step.description,
            "started_at": datetime.utcnow().isoformat(),
        }

        if dry_run:
            result["status"] = "skipped"
            result["message"] = "dry-run"
            results.append(result)
            if verbose:
                logger.info(f"[migrate] 跳过 {step.id} (dry-run)")
            continue

        try:
            if verbose:
                logger.info(f"[migrate] 执行 {step.id} ...")

            if step.requires_session:
                async with AsyncSessionLocal() as session:
                    detail = await step.runner(session)
            else:
                detail = await step.runner(None)

            result["status"] = "ok"
            if detail:
                result["detail"] = detail
            if verbose:
                logger.info(f"[migrate] {step.id} 完成")
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            logger.error(f"[migrate] {step.id} 失败: {exc}")
            results.append(result)
            break

        results.append(result)

    return results


