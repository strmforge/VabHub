"""
添加缓存表迁移脚本
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine
from loguru import logger


async def migrate():
    """执行迁移"""
    async with engine.begin() as conn:
        # 创建缓存表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(500) NOT NULL UNIQUE,
                value TEXT NOT NULL,
                ttl INTEGER NOT NULL DEFAULT 3600,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL
            )
        """))
        
        # 创建索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(key)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache_entries(expires_at)
        """))
        
        logger.info("缓存表迁移完成")


if __name__ == "__main__":
    asyncio.run(migrate())

