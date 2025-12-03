"""
数据库初始化脚本
创建数据库表和初始数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.database import init_db, close_db, engine
from app.core.config import settings
from app.core.cache import get_cache
from app.modules.settings.service import SettingsService
from app.core.database import AsyncSessionLocal
from loguru import logger


async def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    try:
        # 初始化数据库表
        await init_db()
        logger.info("数据库表创建完成")
        
        # 初始化默认设置
        async with AsyncSessionLocal() as session:
            settings_service = SettingsService(session)
            count = await settings_service.initialize_default_settings()
            logger.info(f"默认设置初始化完成，创建了 {count} 个设置项")
        
        # 初始化L3缓存表（如果使用PostgreSQL）
        if not settings.DATABASE_URL.startswith("sqlite"):
            try:
                from app.models.cache import CacheEntry
                async with AsyncSessionLocal() as session:
                    # 检查表是否已存在
                    from sqlalchemy import inspect
                    inspector = inspect(engine.sync_engine)
                    if 'cache_entries' not in inspector.get_table_names():
                        logger.info("创建L3缓存表...")
                        # 表会在init_db()中自动创建
                    else:
                        logger.info("L3缓存表已存在")
            except Exception as e:
                logger.warning(f"L3缓存表检查失败: {e}")
        
        logger.info("数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        await close_db()


async def check_database_connection():
    """检查数据库连接"""
    logger.info("检查数据库连接...")
    
    try:
        # 测试数据库连接
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info("数据库连接正常")
            return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        logger.error("请检查:")
        logger.error("1. 数据库服务是否运行")
        logger.error("2. DATABASE_URL配置是否正确")
        logger.error("3. 数据库用户权限是否足够")
        return False


async def main():
    """主函数"""
    logger.info("="*50)
    logger.info("VabHub 数据库初始化")
    logger.info("="*50)
    
    # 检查数据库连接
    if not await check_database_connection():
        sys.exit(1)
    
    # 初始化数据库
    await init_database()
    
    logger.info("="*50)
    logger.info("初始化完成！")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(main())

