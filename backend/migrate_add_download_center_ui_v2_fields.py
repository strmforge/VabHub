#!/usr/bin/env python3
"""
DOWNLOAD-CENTER-UI-2 数据库迁移脚本
添加 organize_status 字段到 download_tasks 表
"""

import asyncio
import sys
from sqlalchemy import text
from loguru import logger

# 添加项目路径
sys.path.append('.')

from app.core.database import AsyncSessionLocal, engine


async def add_organize_status_column():
    """添加 organize_status 字段到 download_tasks 表"""
    
    async with engine.begin() as conn:
        try:
            # 使用异步兼容的方式检查字段是否已存在
            def check_columns(sync_conn):
                from sqlalchemy import inspect
                inspector = inspect(sync_conn)
                columns = inspector.get_columns("download_tasks")
                return [col["name"] for col in columns]
            
            column_names = await conn.run_sync(check_columns)
            field_exists = "organize_status" in column_names
            
            if field_exists:
                logger.info("organize_status 字段已存在，跳过添加")
                return
            
            # 添加 organize_status 字段
            await conn.execute(text("""
                ALTER TABLE download_tasks 
                ADD COLUMN organize_status VARCHAR(20) DEFAULT 'NONE'
            """))
            
            logger.success("✅ 成功添加 organize_status 字段")
            
        except Exception as e:
            logger.error(f"❌ 添加 organize_status 字段失败: {e}")
            raise


async def create_indexes():
    """创建相关索引优化查询性能"""
    
    async with engine.begin() as conn:
        try:
            # 为 organize_status 创建索引
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_download_tasks_organize_status 
                ON download_tasks(organize_status)
            """))
            
            logger.success("✅ 成功创建 organize_status 索引")
            
        except Exception as e:
            logger.warning(f"⚠️ 创建索引失败（可能已存在）: {e}")


async def update_existing_records():
    """更新现有记录的 organize_status 状态"""
    
    async with AsyncSessionLocal() as session:
        try:
            # 将已完成但没有整理状态的任务设为 NONE
            result = await session.execute(text("""
                UPDATE download_tasks 
                SET organize_status = 'NONE' 
                WHERE organize_status IS NULL OR organize_status = ''
            """))
            
            updated_count = result.rowcount
            await session.commit()
            
            logger.success(f"✅ 更新了 {updated_count} 条现有记录的状态")
            
        except Exception as e:
            logger.error(f"❌ 更新现有记录失败: {e}")
            await session.rollback()
            raise


async def verify_migration():
    """验证迁移结果"""
    
    async with AsyncSessionLocal() as session:
        try:
            # 检查表结构和数据
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN organize_status = 'NONE' THEN 1 END) as none_count,
                    COUNT(CASE WHEN organize_status = 'AUTO_OK' THEN 1 END) as auto_ok_count,
                    COUNT(CASE WHEN organize_status = 'AUTO_FAILED' THEN 1 END) as auto_failed_count,
                    COUNT(CASE WHEN organize_status = 'MANUAL_PENDING' THEN 1 END) as manual_pending_count,
                    COUNT(CASE WHEN organize_status = 'MANUAL_DONE' THEN 1 END) as manual_done_count
                FROM download_tasks
            """))
            
            stats = result.fetchone()
            
            logger.info("📊 迁移验证结果:")
            logger.info(f"  总任务数: {stats.total_count}")
            logger.info(f"  NONE 状态: {stats.none_count}")
            logger.info(f"  AUTO_OK 状态: {stats.auto_ok_count}")
            logger.info(f"  AUTO_FAILED 状态: {stats.auto_failed_count}")
            logger.info(f"  MANUAL_PENDING 状态: {stats.manual_pending_count}")
            logger.info(f"  MANUAL_DONE 状态: {stats.manual_done_count}")
            
            return stats.total_count > 0
            
        except Exception as e:
            logger.error(f"❌ 验证迁移失败: {e}")
            return False


async def main():
    """主迁移流程"""
    
    logger.info("🚀 开始 DOWNLOAD-CENTER-UI-2 数据库迁移...")
    
    try:
        # 步骤1: 添加字段
        await add_organize_status_column()
        
        # 步骤2: 创建索引
        await create_indexes()
        
        # 步骤3: 更新现有记录
        await update_existing_records()
        
        # 步骤4: 验证迁移
        success = await verify_migration()
        
        if success:
            logger.success("🎉 DOWNLOAD-CENTER-UI-2 数据库迁移完成！")
            logger.info("✨ 新增功能:")
            logger.info("  - organize_status 字段用于跟踪整理状态")
            logger.info("  - 支持自动退场逻辑")
            logger.info("  - 优化查询性能的索引")
        else:
            logger.error("❌ 迁移验证失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ 迁移过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 运行迁移
    asyncio.run(main())
