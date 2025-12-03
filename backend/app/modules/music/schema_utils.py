"""
音乐模块的数据库结构自愈工具。
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings


def _build_sync_url(db_url: str) -> str:
    if db_url.startswith("sqlite+aiosqlite://"):
        return db_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return db_url


async def ensure_music_schema() -> None:
    """
    确保 music_subscriptions 表具备最新字段。
    当前仅需要自动补齐 subscription_id，可按需扩展。
    """

    sync_url = _build_sync_url(settings.DATABASE_URL)
    sync_engine: Engine = create_engine(sync_url, future=True)
    try:
        with sync_engine.connect() as conn:
            inspector = inspect(conn)
            columns = {col["name"] for col in inspector.get_columns("music_subscriptions")}

            statements = []
            if "subscription_id" not in columns:
                statements.append("ALTER TABLE music_subscriptions ADD COLUMN subscription_id INTEGER")

            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                    logger.info(f"[music] {stmt} 执行完成")
                except Exception as exc:
                    message = str(exc).lower()
                    if "duplicate column" in message:
                        logger.debug(f"[music] {stmt} 已存在，跳过")
                        continue
                    logger.warning(f"[music] 执行 {stmt} 失败: {exc}")
    except Exception as exc:
        logger.warning(f"[music] 检查 music_subscriptions 结构失败: {exc}")
    finally:
        sync_engine.dispose()


