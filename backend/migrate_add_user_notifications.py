"""
数据库迁移脚本：创建用户通知表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal
from app.core.config import settings
from loguru import logger


async def migrate():
    """执行数据库迁移"""
    logger.info("开始迁移：创建用户通知表")
    
    async with engine.begin() as conn:
        # 检查表是否已存在
        if settings.DATABASE_URL.startswith("sqlite"):
            check_table_sql = text("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='user_notifications'
            """)
        else:
            check_table_sql = text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_notifications'
            """)
        
        result = await conn.execute(check_table_sql)
        table_exists = result.scalar() > 0
        
        if table_exists:
            logger.info("表 user_notifications 已存在，跳过创建")
            return
        
        # 创建用户通知表
        if settings.DATABASE_URL.startswith("sqlite"):
            # SQLite
            create_table_sql = text("""
                CREATE TABLE user_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    media_type VARCHAR(20),
                    target_id INTEGER,
                    sub_target_id INTEGER,
                    title VARCHAR(256) NOT NULL,
                    message TEXT,
                    payload JSON,
                    is_read BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    read_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # 创建索引
            create_indexes_sql = [
                text("CREATE INDEX idx_user_notifications_user_id ON user_notifications(user_id)"),
                text("CREATE INDEX idx_user_notifications_type ON user_notifications(type)"),
                text("CREATE INDEX idx_user_notifications_is_read ON user_notifications(is_read)"),
                text("CREATE INDEX idx_user_notifications_created_at ON user_notifications(created_at)"),
                text("CREATE INDEX idx_user_notifications_media_type ON user_notifications(media_type)"),
                text("CREATE INDEX idx_user_notifications_target_id ON user_notifications(target_id)")
            ]
        else:
            # PostgreSQL
            create_table_sql = text("""
                CREATE TABLE user_notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    media_type VARCHAR(20),
                    target_id INTEGER,
                    sub_target_id INTEGER,
                    title VARCHAR(256) NOT NULL,
                    message TEXT,
                    payload JSONB,
                    is_read BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP WITH TIME ZONE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # 创建索引
            create_indexes_sql = [
                text("CREATE INDEX idx_user_notifications_user_id ON user_notifications(user_id)"),
                text("CREATE INDEX idx_user_notifications_type ON user_notifications(type)"),
                text("CREATE INDEX idx_user_notifications_is_read ON user_notifications(is_read)"),
                text("CREATE INDEX idx_user_notifications_created_at ON user_notifications(created_at)"),
                text("CREATE INDEX idx_user_notifications_media_type ON user_notifications(media_type)"),
                text("CREATE INDEX idx_user_notifications_target_id ON user_notifications(target_id)")
            ]
        
        # 执行创建表
        await conn.execute(create_table_sql)
        logger.info("表 user_notifications 已创建")
        
        # 创建索引
        for idx_sql in create_indexes_sql:
            await conn.execute(idx_sql)
        logger.info("索引已创建")
        
        await conn.commit()
    
    logger.info("迁移完成：用户通知表已创建")


async def downgrade():
    """回滚迁移"""
    logger.info("开始回滚：删除用户通知表")
    
    async with engine.begin() as conn:
        if settings.DATABASE_URL.startswith("sqlite"):
            drop_table_sql = text("DROP TABLE IF EXISTS user_notifications")
        else:
            drop_table_sql = text("DROP TABLE IF EXISTS user_notifications")
        
        await conn.execute(drop_table_sql)
        await conn.commit()
    
    logger.info("回滚完成：用户通知表已删除")


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