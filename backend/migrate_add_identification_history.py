"""
数据库迁移脚本：添加媒体识别历史记录表
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
    logger.info("开始迁移：添加媒体识别历史记录表")
    
    async with engine.begin() as conn:
        # 检查表是否已存在
        if settings.DATABASE_URL.startswith("sqlite"):
            check_table_sql = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='identification_history'
            """)
        else:
            check_table_sql = text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'identification_history'
            """)
        
        result = await conn.execute(check_table_sql)
        table_exists = result.fetchone() is not None
        
        if table_exists:
            logger.info("表 identification_history 已存在，跳过创建")
            return
        
        # 创建表
        if settings.DATABASE_URL.startswith("sqlite"):
            create_table_sql = text("""
                CREATE TABLE identification_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path VARCHAR(1000) NOT NULL,
                    file_name VARCHAR(500),
                    file_size INTEGER,
                    title VARCHAR(500),
                    year INTEGER,
                    season INTEGER,
                    episode INTEGER,
                    media_type VARCHAR(50),
                    confidence FLOAT DEFAULT 0.0,
                    source VARCHAR(100),
                    success VARCHAR(10) DEFAULT 'false',
                    error TEXT,
                    raw_result TEXT,
                    identified_at DATETIME NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            create_index1_sql = text("""
                CREATE INDEX idx_identification_history_file_path ON identification_history(file_path)
            """)
            
            create_index2_sql = text("""
                CREATE INDEX idx_identification_history_identified_at ON identification_history(identified_at)
            """)
        else:
            # PostgreSQL
            create_table_sql = text("""
                CREATE TABLE identification_history (
                    id SERIAL PRIMARY KEY,
                    file_path VARCHAR(1000) NOT NULL,
                    file_name VARCHAR(500),
                    file_size INTEGER,
                    title VARCHAR(500),
                    year INTEGER,
                    season INTEGER,
                    episode INTEGER,
                    media_type VARCHAR(50),
                    confidence FLOAT DEFAULT 0.0,
                    source VARCHAR(100),
                    success VARCHAR(10) DEFAULT 'false',
                    error TEXT,
                    raw_result JSONB,
                    identified_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            
            create_index1_sql = text("""
                CREATE INDEX idx_identification_history_file_path ON identification_history(file_path)
            """)
            
            create_index2_sql = text("""
                CREATE INDEX idx_identification_history_identified_at ON identification_history(identified_at)
            """)
        
        # 执行创建表
        await conn.execute(create_table_sql)
        logger.info("表 identification_history 已创建")
        
        # 创建索引
        await conn.execute(create_index1_sql)
        await conn.execute(create_index2_sql)
        logger.info("索引已创建")
        
        await conn.commit()
    
    logger.info("迁移完成：媒体识别历史记录表已添加")


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

