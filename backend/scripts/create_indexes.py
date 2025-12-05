"""
创建数据库索引脚本
优化查询性能
"""

import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
from sqlalchemy import text
from loguru import logger

from app.core.database import engine


async def create_indexes():
    """创建数据库索引"""
    # 使用全局引擎
    
    indexes = [
        # 下载任务表索引
        ("idx_download_tasks_status", "download_tasks", "status"),
        ("idx_download_tasks_created_at", "download_tasks", "created_at"),
        ("idx_download_tasks_downloader_hash", "download_tasks", "downloader_hash"),
        ("idx_download_tasks_downloader", "download_tasks", "downloader"),
        
        # 订阅表索引
        ("idx_subscriptions_status", "subscriptions", "status"),
        ("idx_subscriptions_media_type", "subscriptions", "media_type"),
        ("idx_subscriptions_created_at", "subscriptions", "created_at"),
        ("idx_subscriptions_enabled", "subscriptions", "enabled"),
        
        # 媒体文件表索引
        ("idx_media_files_tmdb_id", "media_files", "tmdb_id"),
        ("idx_media_files_media_type", "media_files", "media_type"),
        ("idx_media_files_file_path", "media_files", "file_path"),
        ("idx_media_files_quality", "media_files", "quality"),
        
        # RSS订阅表索引
        ("idx_rss_subscriptions_enabled", "rss_subscriptions", "enabled"),
        ("idx_rss_subscriptions_site_id", "rss_subscriptions", "site_id"),
        ("idx_rss_subscriptions_created_at", "rss_subscriptions", "created_at"),
        
        # 站点表索引
        ("idx_sites_enabled", "sites", "enabled"),
        ("idx_sites_site_type", "sites", "site_type"),
        
        # 任务表索引
        ("idx_tasks_status", "tasks", "status"),
        ("idx_tasks_task_type", "tasks", "task_type"),
        ("idx_tasks_created_at", "tasks", "created_at"),
    ]
    
    # 检查是否是异步引擎
    if hasattr(engine, 'begin'):
        # 异步引擎
        async with engine.begin() as conn:
            for index_name, table_name, column_name in indexes:
                try:
                    # 检查索引是否已存在
                    check_sql = text(f"""
                        SELECT name FROM sqlite_master 
                        WHERE type='index' AND name='{index_name}'
                    """)
                    result = await conn.execute(check_sql)
                    if result.scalar_one_or_none():
                        logger.info(f"索引 {index_name} 已存在，跳过")
                        continue
                    
                    # 创建索引
                    create_sql = text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name}({column_name})
                    """)
                    await conn.execute(create_sql)
                    logger.success(f"✓ 创建索引: {index_name} on {table_name}({column_name})")
                except Exception as e:
                    logger.error(f"✗ 创建索引失败 {index_name}: {e}")
    else:
        # 同步引擎
        with engine.begin() as conn:
            for index_name, table_name, column_name in indexes:
                try:
                    # 检查索引是否已存在
                    check_sql = text(f"""
                        SELECT name FROM sqlite_master 
                        WHERE type='index' AND name='{index_name}'
                    """)
                    result = conn.execute(check_sql)
                    if result.scalar_one_or_none():
                        logger.info(f"索引 {index_name} 已存在，跳过")
                        continue
                    
                    # 创建索引
                    create_sql = text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name}({column_name})
                    """)
                    conn.execute(create_sql)
                    logger.success(f"✓ 创建索引: {index_name} on {table_name}({column_name})")
                except Exception as e:
                    logger.error(f"✗ 创建索引失败 {index_name}: {e}")
    
    logger.info("数据库索引创建完成！")


async def main():
    """主函数"""
    logger.info("开始创建数据库索引...")
    await create_indexes()


if __name__ == "__main__":
    asyncio.run(main())
