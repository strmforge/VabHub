"""
短剧相关的数据库结构自检与自愈工具。

P11 要求在订阅、下载任务、媒资等核心表中补充短剧字段，
因此这里提供一个在应用启动阶段执行的轻量级 schema 检查器。
"""

from __future__ import annotations

from typing import Dict, Set, Tuple

from loguru import logger
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine

from app.core.config import settings


def _ensure_short_drama_columns_sync(conn: Connection) -> None:
    existing_columns: Dict[str, Set[str]] = {}
    inspector = inspect(conn)

    for table_name in ("download_tasks", "subscriptions", "media"):
        try:
            existing_columns[table_name] = {
                column["name"] for column in inspector.get_columns(table_name)
            }
        except Exception as exc:  # pragma: no cover
            logger.warning(f"[short-drama] 无法读取 {table_name} 结构: {exc}")
            existing_columns[table_name] = set()

    dialect_name = conn.dialect.name
    json_type = "JSON" if dialect_name != "sqlite" else "TEXT"

    column_defs: Dict[Tuple[str, str], str] = {
        ("download_tasks", "media_type"): "VARCHAR(32) DEFAULT 'unknown'",
        ("download_tasks", "extra_metadata"): json_type,
        ("subscriptions", "extra_metadata"): json_type,
        ("media", "extra_metadata"): json_type,
    }

    alter_statements = []
    for (table, column), ddl in column_defs.items():
        if column not in existing_columns.get(table, set()):
            alter_statements.append(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    if not alter_statements:
        logger.debug("[short-drama] 所有列已存在，无需迁移")
        return

    for stmt in alter_statements:
        try:
            conn.execute(text(stmt))
            logger.info(f"[short-drama] {stmt} 执行完成")
        except Exception as exc:
            logger.error(f"[short-drama] 执行 {stmt} 失败: {exc}")

    try:
        conn.execute(
            text(
                "UPDATE download_tasks SET media_type = 'unknown' "
                "WHERE media_type IS NULL OR media_type = ''"
            )
        )
    except Exception as exc:  # pragma: no cover
        logger.warning(f"[short-drama] 回填 download_tasks.media_type 失败: {exc}")


async def ensure_short_drama_columns() -> None:
    """
    检查并补充短剧相关字段：
    - download_tasks.media_type
    - download_tasks.extra_metadata
    - subscriptions.extra_metadata
    - media.extra_metadata
    """

    def _build_sync_url(db_url: str) -> str:
        if db_url.startswith("sqlite+aiosqlite://"):
            return db_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        if db_url.startswith("postgresql+asyncpg://"):
            return db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return db_url

    sync_url = _build_sync_url(settings.DATABASE_URL)
    sync_engine: Engine = create_engine(sync_url, future=True)
    try:
        with sync_engine.begin() as conn:
            _ensure_short_drama_columns_sync(conn)
    except Exception as exc:
        logger.warning(f"[short-drama] 列检查失败: {exc}")
    finally:
        sync_engine.dispose()


