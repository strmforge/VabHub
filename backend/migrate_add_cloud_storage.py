"""
数据库迁移：添加云存储相关表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
backend_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.database import engine, Base
from loguru import logger


async def migrate():
    """执行迁移"""
    try:
        logger.info("开始创建云存储相关表...")
        
        # 导入所有模型以确保它们被注册
        
        # 创建表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ 云存储相关表创建成功")
        logger.info("   - cloud_storages (云存储配置表)")
        logger.info("   - cloud_storage_auths (云存储认证记录表)")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())

