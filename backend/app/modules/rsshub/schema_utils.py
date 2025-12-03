"""
RSSHub 相关表的动态结构校验与修复
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_subscription_schema_checked = False


async def ensure_subscription_health_columns(db: AsyncSession) -> None:
    """
    确保 user_rsshub_subscription 表包含健康检查所需的列。
    """
    global _subscription_schema_checked
    if _subscription_schema_checked:
        return

    async_engine = getattr(db, "bind", None)
    if async_engine is None:
        return

    statements = [
        "ALTER TABLE user_rsshub_subscription ADD COLUMN last_error_code VARCHAR(64)",
        "ALTER TABLE user_rsshub_subscription ADD COLUMN last_error_message TEXT",
        "ALTER TABLE user_rsshub_subscription ADD COLUMN last_error_at DATETIME",
    ]

    try:
        async with async_engine.begin() as conn:
            for stmt in statements:
                try:
                    await conn.execute(text(stmt))
                except Exception as exc:  # pragma: no cover - SQLite重复列等
                    message = str(exc).lower()
                    if "duplicate column name" in message:
                        continue
                    logger.warning(f"执行 `{stmt}` 失败: {exc}")
                    return
        logger.info("user_rsshub_subscription 健康字段已自动补充")
    except Exception as exc:  # pragma: no cover - 防御性
        logger.warning(f"自动补充 user_rsshub_subscription 健康字段失败: {exc}")
        return

    _subscription_schema_checked = True

