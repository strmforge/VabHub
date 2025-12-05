"""
修复脚本：确保数据库表已创建
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import engine, Base
from loguru import logger


async def ensure_tables_created():
    """确保所有数据库表已创建"""
    logger.info("=" * 60)
    logger.info("开始检查并创建数据库表")
    logger.info("=" * 60)
    
    try:
        # 导入所有模型以确保它们被注册到Base.metadata
        # 导入其他模型...
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ 数据库表检查完成，所有表已创建")
        
        # 验证cache_entries表是否存在
        from sqlalchemy import inspect
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            inspector = inspect(engine.sync_engine)
            tables = inspector.get_table_names()
            
            if "cache_entries" in tables:
                logger.info("✅ cache_entries表已存在")
            else:
                logger.warning("⚠️  cache_entries表不存在，尝试创建...")
                # 再次尝试创建
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ 已尝试创建cache_entries表")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    success = await ensure_tables_created()
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✅ 修复完成！")
        logger.info("=" * 60)
    else:
        logger.error("\n" + "=" * 60)
        logger.error("❌ 修复失败！")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

