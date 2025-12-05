"""
统一数据库迁移脚本。

用法示例：
    python backend/scripts/migrate.py
    python backend/scripts/migrate.py --dry-run
    python backend/scripts/migrate.py --limit 1 --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any, Dict


from app.core.migrations import run_migrations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 VabHub 数据库迁移")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印准备执行的迁移步骤，不实际执行",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制执行的迁移步骤数量（从第一步开始）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="输出更详细的日志",
    )
    return parser.parse_args()


async def main_async(args: argparse.Namespace) -> Dict[str, Any]:
    results = await run_migrations(
        dry_run=args.dry_run,
        limit=args.limit,
        verbose=args.verbose,
    )
    status = "ok"
    for item in results:
        if item.get("status") == "error":
            status = "error"
            break
    return {
        "status": status,
        "dry_run": args.dry_run,
        "executed_at": datetime.utcnow().isoformat(),
        "results": results,
    }


def main() -> None:
    args = parse_args()
    summary = asyncio.run(main_async(args))

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if summary["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


