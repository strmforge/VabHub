"""
数据库迁移脚本：添加 downloader_hash 字段到 download_tasks 表
"""

import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from loguru import logger


async def migrate():
    """执行迁移"""
    logger.info("="*60)
    logger.info("数据库迁移：添加 downloader_hash 字段")
    logger.info("="*60)
    
    try:
        # 直接使用sqlite3连接，因为SQLAlchemy的text()在处理PRAGMA时可能有问题
        import sqlite3
        from app.core.config import settings
        import os
        
        # 从数据库URL中提取数据库文件路径
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            if not os.path.isabs(db_path):
                # 相对路径，需要转换为绝对路径
                backend_dir = Path(__file__).parent.parent
                db_path = backend_dir / db_path
        else:
            logger.error(f"不支持的数据库URL: {db_url}")
            return
        
        logger.info(f"数据库文件路径: {db_path}")
        
        # 检查文件是否存在
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            return
        
        # 使用sqlite3直接操作
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(download_tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'downloader_hash' in columns:
            logger.info("字段 downloader_hash 已存在，跳过迁移")
            conn.close()
            return
        
        # 添加字段
        logger.info("开始添加字段 downloader_hash...")
        cursor.execute("ALTER TABLE download_tasks ADD COLUMN downloader_hash VARCHAR(100) NULL")
        conn.commit()
        conn.close()
        
        logger.info("✅ 字段 downloader_hash 添加成功")
            
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(migrate())

