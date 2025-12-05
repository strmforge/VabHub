"""
数据库迁移脚本：添加通知未读标记字段
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings
from loguru import logger


async def migrate():
    """执行数据库迁移"""
    logger.info("开始迁移：添加通知未读标记字段")
    
    async with engine.begin() as conn:
        # 检查字段是否已存在
        if settings.DATABASE_URL.startswith("sqlite"):
            check_column_sql = text("""
                SELECT COUNT(*) FROM pragma_table_info('notifications') 
                WHERE name='is_read'
            """)
        else:
            check_column_sql = text("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'notifications' 
                AND column_name = 'is_read'
            """)
        
        result = await conn.execute(check_column_sql)
        column_exists = result.scalar() > 0
        
        if column_exists:
            logger.info("字段 is_read 和 read_at 已存在，跳过创建")
            return
        
        # 添加字段
        if settings.DATABASE_URL.startswith("sqlite"):
            # SQLite
            add_is_read_sql = text("""
                ALTER TABLE notifications 
                ADD COLUMN is_read BOOLEAN DEFAULT 0 NOT NULL
            """)
            
            add_read_at_sql = text("""
                ALTER TABLE notifications 
                ADD COLUMN read_at DATETIME
            """)
            
            create_index_sql = text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_is_read 
                ON notifications(is_read)
            """)
        else:
            # PostgreSQL
            add_is_read_sql = text("""
                ALTER TABLE notifications 
                ADD COLUMN is_read BOOLEAN DEFAULT FALSE NOT NULL
            """)
            
            add_read_at_sql = text("""
                ALTER TABLE notifications 
                ADD COLUMN read_at TIMESTAMP WITH TIME ZONE
            """)
            
            create_index_sql = text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_is_read 
                ON notifications(is_read)
            """)
        
        # 执行添加字段
        await conn.execute(add_is_read_sql)
        logger.info("字段 is_read 已添加")
        
        await conn.execute(add_read_at_sql)
        logger.info("字段 read_at 已添加")
        
        # 创建索引
        await conn.execute(create_index_sql)
        logger.info("索引已创建")
        
        await conn.commit()
    
    logger.info("迁移完成：通知未读标记字段已添加")


async def main():
    """主函数"""
    try:
        await migrate()
        logger.info("数据库迁移成功")
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

