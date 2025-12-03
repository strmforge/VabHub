"""
数据库索引优化脚本
为常用查询字段添加索引以提高查询性能
"""

import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 延迟导入以避免循环导入
from sqlalchemy import text


async def create_indexes():
    """创建数据库索引"""
    # 延迟导入logger以避免循环导入
    from loguru import logger
    from app.core.database import AsyncSessionLocal
    
    logger.info("="*60)
    logger.info("数据库索引优化")
    logger.info("="*60)
    
    indexes = [
        # 订阅表索引
        ("subscriptions", "user_id", "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)"),
        ("subscriptions", "media_type", "CREATE INDEX IF NOT EXISTS idx_subscriptions_media_type ON subscriptions(media_type)"),
        ("subscriptions", "status", "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)"),
        ("subscriptions", "created_at", "CREATE INDEX IF NOT EXISTS idx_subscriptions_created_at ON subscriptions(created_at)"),
        ("subscriptions", "user_id_status", "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status)"),
        
        # 下载任务表索引
        ("download_tasks", "status", "CREATE INDEX IF NOT EXISTS idx_download_tasks_status ON download_tasks(status)"),
        ("download_tasks", "downloader", "CREATE INDEX IF NOT EXISTS idx_download_tasks_downloader ON download_tasks(downloader)"),
        ("download_tasks", "created_at", "CREATE INDEX IF NOT EXISTS idx_download_tasks_created_at ON download_tasks(created_at)"),
        ("download_tasks", "downloader_hash", "CREATE INDEX IF NOT EXISTS idx_download_tasks_downloader_hash ON download_tasks(downloader_hash)"),
        
        # 站点表索引
        ("sites", "enabled", "CREATE INDEX IF NOT EXISTS idx_sites_enabled ON sites(enabled)"),
        ("sites", "site_type", "CREATE INDEX IF NOT EXISTS idx_sites_site_type ON sites(site_type)"),
        
        # 工作流表索引
        ("workflows", "enabled", "CREATE INDEX IF NOT EXISTS idx_workflows_enabled ON workflows(enabled)"),
        
        # 通知表索引
        ("notifications", "user_id", "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)"),
        ("notifications", "read", "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)"),
        ("notifications", "created_at", "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)"),
        ("notifications", "user_read", "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read)"),
        
        # 缓存表索引
        ("cache_entries", "key", "CREATE INDEX IF NOT EXISTS idx_cache_entries_key ON cache_entries(key)"),
        ("cache_entries", "expires_at", "CREATE INDEX IF NOT EXISTS idx_cache_entries_expires_at ON cache_entries(expires_at)"),
    ]
    
    try:
        async with AsyncSessionLocal() as db:
            created_count = 0
            skipped_count = 0
            
            for table, index_name, sql in indexes:
                try:
                    # 检查索引是否已存在
                    check_sql = f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name.split('_', 1)[-1]}'"
                    result = await db.execute(text(check_sql))
                    existing = result.scalar()
                    
                    if existing:
                        logger.info(f"索引 {index_name} 已存在，跳过")
                        skipped_count += 1
                        continue
                    
                    # 创建索引
                    await db.execute(text(sql))
                    await db.commit()
                    logger.info(f"✅ 索引 {index_name} 创建成功")
                    created_count += 1
                    
                except Exception as e:
                    logger.error(f"创建索引 {index_name} 失败: {e}")
                    await db.rollback()
            
            logger.info("="*60)
            logger.info(f"索引创建完成: 创建 {created_count} 个，跳过 {skipped_count} 个")
            logger.info("="*60)
            
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_indexes())

