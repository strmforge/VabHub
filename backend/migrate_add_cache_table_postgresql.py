"""
添加缓存表迁移脚本（PostgreSQL版本）
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings
from loguru import logger


async def migrate():
    """执行迁移"""
    # 检查是否使用PostgreSQL
    if settings.DATABASE_URL.startswith("sqlite"):
        logger.warning("当前使用SQLite，此脚本适用于PostgreSQL")
        logger.info("SQLite版本请使用 migrate_add_cache_table.py")
        return
    
    async with engine.begin() as conn:
        # 创建缓存表（PostgreSQL）
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                id SERIAL PRIMARY KEY,
                key VARCHAR(500) NOT NULL UNIQUE,
                value TEXT NOT NULL,
                ttl INTEGER NOT NULL DEFAULT 3600,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL
            )
        """))
        
        # 创建索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(key)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache_entries(expires_at)
        """))
        
        # 创建更新时间触发器函数（PostgreSQL）
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        
        # 创建触发器（如果不存在）
        await conn.execute(text("""
            DROP TRIGGER IF EXISTS update_cache_entries_updated_at ON cache_entries;
            CREATE TRIGGER update_cache_entries_updated_at
                BEFORE UPDATE ON cache_entries
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """))
        
        logger.info("PostgreSQL缓存表迁移完成")


if __name__ == "__main__":
    asyncio.run(migrate())

