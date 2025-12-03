"""
CookieCloud数据表迁移脚本
添加cookiecloud_settings表和扩展sites表字段
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from loguru import logger


async def run_migration():
    """执行CookieCloud相关表迁移"""
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 创建cookiecloud_settings表
            logger.info("创建cookiecloud_settings表...")
            
            create_cookiecloud_settings_sql = """
            CREATE TABLE IF NOT EXISTS cookiecloud_settings (
                id INTEGER PRIMARY KEY,
                enabled BOOLEAN NOT NULL DEFAULT 0,
                host VARCHAR(255),
                uuid VARCHAR(128),
                password VARCHAR(128),
                sync_interval_minutes INTEGER NOT NULL DEFAULT 60,
                safe_host_whitelist TEXT,
                last_sync_at DATETIME,
                last_status VARCHAR(32),
                last_error TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            await db.execute(text(create_cookiecloud_settings_sql))
            logger.info("✅ cookiecloud_settings表创建成功")
            
            # 2. 检查并添加sites表新字段
            logger.info("检查并扩展sites表字段...")
            
            # 检查cookie_source字段是否存在
            check_cookie_source_sql = """
            SELECT COUNT(*) as count FROM pragma_table_info('sites') WHERE name = 'cookie_source'
            """
            
            result = await db.execute(text(check_cookie_source_sql))
            cookie_source_exists = result.scalar() > 0
            
            if not cookie_source_exists:
                logger.info("添加cookie_source字段...")
                await db.execute(text("""
                    ALTER TABLE sites ADD COLUMN cookie_source VARCHAR(32) DEFAULT 'MANUAL'
                """))
                logger.info("✅ cookie_source字段添加成功")
            else:
                logger.info("cookie_source字段已存在，跳过")
            
            # 检查last_cookiecloud_sync_at字段是否存在
            check_sync_at_sql = """
            SELECT COUNT(*) as count FROM pragma_table_info('sites') WHERE name = 'last_cookiecloud_sync_at'
            """
            
            result = await db.execute(text(check_sync_at_sql))
            sync_at_exists = result.scalar() > 0
            
            if not sync_at_exists:
                logger.info("添加last_cookiecloud_sync_at字段...")
                await db.execute(text("""
                    ALTER TABLE sites ADD COLUMN last_cookiecloud_sync_at DATETIME
                """))
                logger.info("✅ last_cookiecloud_sync_at字段添加成功")
            else:
                logger.info("last_cookiecloud_sync_at字段已存在，跳过")
            
            # 3. 插入默认CookieCloudSettings记录
            logger.info("插入默认CookieCloudSettings记录...")
            
            check_default_sql = """
            SELECT COUNT(*) as count FROM cookiecloud_settings WHERE id = 1
            """
            
            result = await db.execute(text(check_default_sql))
            default_exists = result.scalar() > 0
            
            if not default_exists:
                logger.info("插入默认配置记录...")
                await db.execute(text("""
                    INSERT INTO cookiecloud_settings (
                        id, enabled, host, uuid, password, sync_interval_minutes,
                        safe_host_whitelist, last_sync_at, last_status, last_error,
                        created_at, updated_at
                    ) VALUES (
                        1, 0, NULL, NULL, NULL, 60,
                        NULL, NULL, NULL, NULL,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """))
                logger.info("✅ 默认CookieCloudSettings记录插入成功")
            else:
                logger.info("默认CookieCloudSettings记录已存在，跳过")
            
            # 4. 创建索引优化查询性能
            logger.info("创建索引...")
            
            # 为sites表的cookie_source字段创建索引
            create_cookie_source_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_sites_cookie_source ON sites(cookie_source)
            """
            await db.execute(text(create_cookie_source_index_sql))
            logger.info("✅ sites表cookie_source索引创建成功")
            
            # 为sites表的last_cookiecloud_sync_at字段创建索引
            create_sync_at_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_sites_last_cookiecloud_sync_at ON sites(last_cookiecloud_sync_at)
            """
            await db.execute(text(create_sync_at_index_sql))
            logger.info("✅ sites表last_cookiecloud_sync_at索引创建成功")
            
            # 5. 验证表结构
            logger.info("验证表结构...")
            
            # 验证cookiecloud_settings表
            verify_cookiecloud_settings_sql = """
            SELECT COUNT(*) as count FROM cookiecloud_settings WHERE id = 1
            """
            result = await db.execute(text(verify_cookiecloud_settings_sql))
            settings_count = result.scalar()
            
            if settings_count == 1:
                logger.info("✅ cookiecloud_settings表验证通过")
            else:
                raise Exception(f"cookiecloud_settings表验证失败，期望1条记录，实际{settings_count}条")
            
            # 验证sites表新字段
            verify_sites_fields_sql = """
            SELECT COUNT(*) as count FROM pragma_table_info('sites') 
            WHERE name IN ('cookie_source', 'last_cookiecloud_sync_at')
            """
            result = await db.execute(text(verify_sites_fields_sql))
            fields_count = result.scalar()
            
            if fields_count == 2:
                logger.info("✅ sites表新字段验证通过")
            else:
                raise Exception(f"sites表新字段验证失败，期望2个字段，实际{fields_count}个")
            
            # 提交所有更改
            await db.commit()
            logger.info("🎉 CookieCloud数据表迁移完成！")
            
            # 6. 显示迁移结果
            logger.info("\n=== 迁移结果摘要 ===")
            logger.info("✅ 创建/验证 cookiecloud_settings 表")
            logger.info("✅ 扩展 sites 表添加 cookie_source 字段")
            logger.info("✅ 扩展 sites 表添加 last_cookiecloud_sync_at 字段")
            logger.info("✅ 插入默认 CookieCloudSettings 记录 (id=1)")
            logger.info("✅ 创建性能优化索引")
            logger.info("\n数据库已准备好支持CookieCloud同步功能！")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 迁移失败: {e}")
            raise


async def verify_migration():
    """验证迁移结果"""
    logger.info("开始验证迁移结果...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 验证cookiecloud_settings表
            result = await db.execute(text("SELECT COUNT(*) FROM cookiecloud_settings"))
            settings_count = result.scalar()
            logger.info(f"CookieCloudSettings记录数: {settings_count}")
            
            # 验证sites表新字段
            result = await db.execute(text("""
                SELECT COUNT(*) FROM sites 
                WHERE cookie_source IS NOT NULL
            """))
            sites_with_source = result.scalar()
            logger.info(f"有cookie_source标记的站点数: {sites_with_source}")
            
            # 显示表结构
            logger.info("\n=== cookiecloud_settings 表结构 ===")
            result = await db.execute(text("PRAGMA table_info(cookiecloud_settings)"))
            for row in result:
                logger.info(f"  {row[1]} ({row[2]})")
            
            logger.info("\n=== sites表新增字段 ===")
            result = await db.execute(text("""
                SELECT name, type, dflt_value FROM pragma_table_info('sites')
                WHERE name IN ('cookie_source', 'last_cookiecloud_sync_at')
            """))
            for row in result:
                logger.info(f"  {row[0]} ({row[1]}) 默认值: {row[2]}")
            
            logger.info("✅ 迁移验证完成")
            
        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            raise


if __name__ == "__main__":
    logger.info("开始CookieCloud数据表迁移...")
    
    try:
        asyncio.run(run_migration())
        asyncio.run(verify_migration())
        
        logger.info("\n🎊 CookieCloud迁移成功完成！")
        logger.info("现在可以开始实现CookieCloudClient和SyncService了。")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        sys.exit(1)
