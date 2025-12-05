"""
Local Intel 数据库迁移脚本
创建 hr_cases、site_guard_profiles、inbox_events 表
"""

from __future__ import annotations

import asyncio
from typing import Dict, Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def create_hr_cases_table(session: AsyncSession) -> Dict[str, Any]:
    """创建 hr_cases 表"""
    try:
        # 检查表是否已存在
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='hr_cases'")
        )
        if result.scalar():
            logger.info("表 hr_cases 已存在，跳过创建")
            return {"status": "skipped", "reason": "table_exists"}
        
        # 创建表
        await session.execute(text("""
            CREATE TABLE hr_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site VARCHAR(100) NOT NULL,
                torrent_id VARCHAR(100) NOT NULL,
                hr_status VARCHAR(20) NOT NULL DEFAULT 'none',
                life_status VARCHAR(20) NOT NULL DEFAULT 'alive',
                required_seed_hours REAL,
                seeded_hours REAL DEFAULT 0.0,
                deadline DATETIME,
                first_seen_at DATETIME,
                last_seen_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_hr_cases_site ON hr_cases(site)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_hr_cases_torrent_id ON hr_cases(torrent_id)
        """))
        await session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_hr_cases_site_torrent 
            ON hr_cases(site, torrent_id)
        """))
        
        await session.commit()
        logger.info("表 hr_cases 创建成功")
        return {"status": "created"}
    except Exception as e:
        await session.rollback()
        logger.error(f"创建表 hr_cases 失败: {e}")
        return {"status": "error", "error": str(e)}


async def create_site_guard_profiles_table(session: AsyncSession) -> Dict[str, Any]:
    """创建 site_guard_profiles 表"""
    try:
        # 检查表是否已存在
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='site_guard_profiles'")
        )
        if result.scalar():
            logger.info("表 site_guard_profiles 已存在，跳过创建")
            return {"status": "skipped", "reason": "table_exists"}
        
        # 创建表
        await session.execute(text("""
            CREATE TABLE site_guard_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site VARCHAR(100) NOT NULL UNIQUE,
                last_block_start DATETIME,
                last_block_end DATETIME,
                last_block_cause VARCHAR(255),
                last_full_scan_minutes INTEGER,
                last_full_scan_pages INTEGER,
                safe_scan_minutes INTEGER DEFAULT 10,
                safe_pages_per_hour INTEGER DEFAULT 200,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_site_guard_profiles_site 
            ON site_guard_profiles(site)
        """))
        
        await session.commit()
        logger.info("表 site_guard_profiles 创建成功")
        return {"status": "created"}
    except Exception as e:
        await session.rollback()
        logger.error(f"创建表 site_guard_profiles 失败: {e}")
        return {"status": "error", "error": str(e)}


async def create_inbox_events_table(session: AsyncSession) -> Dict[str, Any]:
    """创建 inbox_events 表"""
    try:
        # 检查表是否已存在
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='inbox_events'")
        )
        if result.scalar():
            logger.info("表 inbox_events 已存在，跳过创建")
            return {"status": "skipped", "reason": "table_exists"}
        
        # 创建表
        await session.execute(text("""
            CREATE TABLE inbox_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site VARCHAR(100) NOT NULL,
                message_hash VARCHAR(64) NOT NULL,
                message_text TEXT,
                event_type VARCHAR(50) NOT NULL,
                torrent_id VARCHAR(100),
                message_time DATETIME,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_inbox_events_site ON inbox_events(site)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_inbox_events_message_hash 
            ON inbox_events(message_hash)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_inbox_events_event_type 
            ON inbox_events(event_type)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_inbox_events_torrent_id 
            ON inbox_events(torrent_id)
        """))
        await session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_inbox_events_site_hash 
            ON inbox_events(site, message_hash)
        """))
        
        await session.commit()
        logger.info("表 inbox_events 创建成功")
        return {"status": "created"}
    except Exception as e:
        await session.rollback()
        logger.error(f"创建表 inbox_events 失败: {e}")
        return {"status": "error", "error": str(e)}


async def create_site_guard_events_table(session: AsyncSession) -> Dict[str, Any]:
    """创建 site_guard_events 表"""
    try:
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='site_guard_events'")
        )
        if result.scalar():
            logger.info("表 site_guard_events 已存在，跳过创建")
            return {"status": "skipped", "reason": "table_exists"}

        await session.execute(text("""
            CREATE TABLE site_guard_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site VARCHAR(100) NOT NULL,
                event_type VARCHAR(50) NOT NULL DEFAULT 'block',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                block_until DATETIME,
                scan_minutes_before_block INTEGER,
                scan_pages_before_block INTEGER,
                cause VARCHAR(255)
            )
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_site_guard_events_site
            ON site_guard_events(site)
        """))

        await session.commit()
        logger.info("表 site_guard_events 创建成功")
        return {"status": "created"}
    except Exception as e:
        await session.rollback()
        logger.error(f"创建表 site_guard_events 失败: {e}")
        return {"status": "error", "error": str(e)}


async def create_inbox_cursor_table(session: AsyncSession) -> Dict[str, Any]:
    """创建 inbox_cursor 表"""
    try:
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='inbox_cursor'")
        )
        if result.scalar():
            logger.info("表 inbox_cursor 已存在，跳过创建")
            return {"status": "skipped", "reason": "table_exists"}

        await session.execute(text("""
            CREATE TABLE inbox_cursor (
                site VARCHAR(100) PRIMARY KEY,
                last_message_id VARCHAR(255),
                last_checked_at DATETIME,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await session.commit()
        logger.info("表 inbox_cursor 创建成功")
        return {"status": "created"}
    except Exception as e:
        await session.rollback()
        logger.error(f"创建表 inbox_cursor 失败: {e}")
        return {"status": "error", "error": str(e)}


async def create_torrent_index_table(session: AsyncSession) -> Dict[str, Any]:
    """创建 torrent_index 表（Phase 9）"""
    try:
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='torrent_index'")
        )
        if result.scalar():
            logger.info("表 torrent_index 已存在，跳过创建")
            return {"status": "skipped", "reason": "table_exists"}

        await session.execute(text("""
            CREATE TABLE torrent_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id VARCHAR(100) NOT NULL,
                torrent_id VARCHAR(100) NOT NULL,
                title_raw TEXT NOT NULL,
                title_clean TEXT,
                category VARCHAR(50),
                is_hr INTEGER DEFAULT 0,
                is_free INTEGER DEFAULT 0,
                is_half_free INTEGER DEFAULT 0,
                size_bytes INTEGER,
                seeders INTEGER DEFAULT 0,
                leechers INTEGER DEFAULT 0,
                completed INTEGER,
                published_at DATETIME,
                last_seen_at DATETIME NOT NULL,
                is_deleted INTEGER DEFAULT 0,
                deleted_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 创建索引
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_torrent_index_site_id 
            ON torrent_index(site_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_torrent_index_torrent_id 
            ON torrent_index(torrent_id)
        """))
        await session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_torrent_index_site_torrent 
            ON torrent_index(site_id, torrent_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_torrent_index_title 
            ON torrent_index(title_raw)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_torrent_index_published 
            ON torrent_index(published_at)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_torrent_index_category 
            ON torrent_index(category)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_torrent_index_seeders 
            ON torrent_index(seeders)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_torrent_index_is_deleted 
            ON torrent_index(is_deleted)
        """))

        await session.commit()
        logger.info("表 torrent_index 创建成功")
        return {"status": "created"}
    except Exception as e:
        await session.rollback()
        logger.error(f"创建表 torrent_index 失败: {e}")
        return {"status": "error", "error": str(e)}


async def migrate_local_intel_schema() -> Dict[str, Any]:
    """
    执行 Local Intel 数据库迁移
    
    Returns:
        迁移结果字典
    """
    logger.info("开始 Local Intel 数据库迁移...")
    
    results = {
        "hr_cases": None,
        "site_guard_profiles": None,
        "site_guard_events": None,
        "inbox_events": None,
        "inbox_cursor": None,
        "torrent_index": None,  # Phase 9
    }
    
    async with AsyncSessionLocal() as session:
        # 创建 hr_cases 表
        results["hr_cases"] = await create_hr_cases_table(session)
        
        # 创建 site_guard_profiles 表
        results["site_guard_profiles"] = await create_site_guard_profiles_table(session)
        
        # 创建 inbox_events 表
        results["inbox_events"] = await create_inbox_events_table(session)

        # 创建 site_guard_events 表
        results["site_guard_events"] = await create_site_guard_events_table(session)

        # 创建 inbox_cursor 表
        results["inbox_cursor"] = await create_inbox_cursor_table(session)

        # 创建 torrent_index 表（Phase 9）
        results["torrent_index"] = await create_torrent_index_table(session)
    
    # 检查是否有错误
    has_error = any(r.get("status") == "error" for r in results.values())
    
    logger.info(f"Local Intel 数据库迁移完成，结果: {results}")
    
    return {
        "status": "error" if has_error else "ok",
        "results": results,
    }


def main() -> None:
    """主函数"""
    result = asyncio.run(migrate_local_intel_schema())
    
    if result["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
