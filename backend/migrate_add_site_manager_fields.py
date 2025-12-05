#!/usr/bin/env python3
"""
SITE-MANAGER-1 数据库迁移脚本
添加站点管理所需的新字段和新表
"""

import asyncio
import sys
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from loguru import logger

async def migrate_site_manager():
    """执行站点管理模块的数据库迁移"""
    
    async with AsyncSessionLocal() as db:
        try:
            # 使用SQLAlchemy的create_all方法创建新表（跨数据库兼容）
            logger.info("开始创建新表...")
            
            # 导入所有模型确保表被注册
            
            # 创建新表（如果不存在）
            async with db.begin():
                # 只创建新表，不修改现有表结构
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS site_stats (
                        id INTEGER PRIMARY KEY,
                        site_id INTEGER NOT NULL UNIQUE,
                        upload_bytes BIGINT DEFAULT 0,
                        download_bytes BIGINT DEFAULT 0,
                        ratio REAL,
                        last_seen_at DATETIME,
                        last_error_at DATETIME,
                        error_count INTEGER DEFAULT 0,
                        health_status VARCHAR(20) DEFAULT 'OK',
                        total_requests INTEGER DEFAULT 0,
                        successful_requests INTEGER DEFAULT 0,
                        avg_response_time REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (site_id) REFERENCES sites (id)
                    )
                """))
                
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS site_access_configs (
                        id INTEGER PRIMARY KEY,
                        site_id INTEGER NOT NULL UNIQUE,
                        rss_url VARCHAR(500),
                        api_key VARCHAR(255),
                        auth_header VARCHAR(500),
                        cookie TEXT,
                        user_agent VARCHAR(500),
                        use_api_mode BOOLEAN DEFAULT 0,
                        use_proxy BOOLEAN DEFAULT 0,
                        use_browser_emulation BOOLEAN DEFAULT 0,
                        min_interval_seconds INTEGER DEFAULT 10,
                        max_concurrent_requests INTEGER DEFAULT 1,
                        timeout_seconds INTEGER DEFAULT 30,
                        retry_count INTEGER DEFAULT 3,
                        custom_headers TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (site_id) REFERENCES sites (id)
                    )
                """))
                
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS site_categories (
                        id INTEGER PRIMARY KEY,
                        key VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        description VARCHAR(500),
                        icon VARCHAR(100),
                        sort_order INTEGER DEFAULT 0,
                        enabled BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS site_health_checks (
                        id INTEGER PRIMARY KEY,
                        site_id INTEGER NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        response_time_ms INTEGER,
                        error_message TEXT,
                        http_status_code INTEGER,
                        check_type VARCHAR(50) DEFAULT 'basic',
                        checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (site_id) REFERENCES sites (id)
                    )
                """))
            
            logger.info("✅ 新表创建完成")
            
            # 为现有Site表添加新字段（SQLite兼容方式）
            logger.info("开始迁移Site表...")
            
            # 添加新列到sites表（SQLite需要逐个添加）
            logger.info("添加新列到sites表...")
            new_columns = [
                "ALTER TABLE sites ADD COLUMN key VARCHAR(50)",
                "ALTER TABLE sites ADD COLUMN domain VARCHAR(255)",
                "ALTER TABLE sites ADD COLUMN category VARCHAR(50)",
                "ALTER TABLE sites ADD COLUMN icon_url VARCHAR(500)",
                "ALTER TABLE sites ADD COLUMN priority INTEGER DEFAULT 0",
                "ALTER TABLE sites ADD COLUMN tags VARCHAR(500)"
            ]
            
            for column_sql in new_columns:
                try:
                    await db.execute(text(column_sql))
                    logger.info(f"✅ 执行: {column_sql}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info(f"⚠️  列已存在，跳过: {column_sql}")
                    else:
                        logger.warning(f"⚠️  添加列失败: {column_sql}, 错误: {e}")
            
            # 检查现有站点并生成key和domain
            result = await db.execute(text("SELECT id, name, url FROM sites"))
            sites = result.fetchall()
            
            for site_id, name, url in sites:
                # 生成key（从name转换）
                key = name.lower().replace(' ', '').replace('-', '').replace('_', '')
                
                # 提取domain
                domain = url.replace('http://', '').replace('https://', '').split('/')[0]
                
                # 更新站点信息（使用SQLite的INSERT OR REPLACE语法）
                await db.execute(text("""
                    UPDATE sites 
                    SET key = COALESCE(key, :key), 
                        domain = COALESCE(domain, :domain), 
                        category = COALESCE(category, 'PT'),
                        priority = COALESCE(priority, 0)
                    WHERE id = :site_id
                """), {
                    "key": key,
                    "domain": domain,
                    "site_id": site_id
                })
            
            logger.info(f"✅ 已迁移 {len(sites)} 个站点的基础信息")
            
            # 3. 初始化默认分类
            logger.info("初始化站点分类...")
            
            default_categories = [
                ("pt", "PT站点", "Private Tracker站点", "mdi-server", 1),
                ("bt", "BT站点", "公共BT站点", "mdi-download", 2),
                ("novel", "小说站点", "网络小说站点", "mdi-book-open", 3),
                ("comic", "漫画站点", "漫画资源站点", "mdi-image", 4),
                ("music", "音乐站点", "音乐资源站点", "mdi-music", 5),
                ("movie", "影视站点", "影视资源站点", "mdi-movie", 6),
                ("game", "游戏站点", "游戏资源站点", "mdi-gamepad", 7),
            ]
            
            for key, name, description, icon, sort_order in default_categories:
                try:
                    await db.execute(text("""
                        INSERT OR IGNORE INTO site_categories (key, name, description, icon, sort_order, enabled)
                        VALUES (:key, :name, :description, :icon, :sort_order, 1)
                    """), {
                        "key": key,
                        "name": name,
                        "description": description,
                        "icon": icon,
                        "sort_order": sort_order
                    })
                except Exception as e:
                    logger.warning(f"⚠️  添加分类 {key} 失败: {e}")
            
            logger.info("✅ 已初始化默认站点分类")
            
            # 4. 为现有站点创建默认的stats和access_config记录
            logger.info("为现有站点创建默认记录...")
            
            result = await db.execute(text("SELECT id FROM sites"))
            site_ids = [row[0] for row in result.fetchall()]
            
            for site_id in site_ids:
                # 创建SiteStats记录
                try:
                    await db.execute(text("""
                        INSERT OR IGNORE INTO site_stats (site_id, upload_bytes, download_bytes, health_status)
                        VALUES (:site_id, 0, 0, 'OK')
                    """), {"site_id": site_id})
                except Exception as e:
                    logger.warning(f"⚠️  创建site_stats记录失败 (site_id={site_id}): {e}")
                
                # 创建SiteAccessConfig记录
                try:
                    await db.execute(text("""
                        INSERT OR IGNORE INTO site_access_configs (site_id)
                        VALUES (:site_id)
                    """), {"site_id": site_id})
                except Exception as e:
                    logger.warning(f"⚠️  创建site_access_configs记录失败 (site_id={site_id}): {e}")
            
            logger.info(f"✅ 已为 {len(site_ids)} 个站点创建默认记录")
            
            # 提交事务
            await db.commit()
            logger.info("🎉 SITE-MANAGER-1 数据库迁移完成！")
            
            return {
                "success": True,
                "message": "迁移完成",
                "migrated_sites": len(sites),
                "created_categories": len(default_categories)
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 数据库迁移失败: {e}")
            return {
                "success": False,
                "message": f"迁移失败: {str(e)}"
            }

async def main():
    """主函数"""
    logger.info("开始执行 SITE-MANAGER-1 数据库迁移...")
    
    result = await migrate_site_manager()
    
    if result["success"]:
        logger.info(f"✅ 迁移成功: {result['message']}")
        sys.exit(0)
    else:
        logger.error(f"❌ 迁移失败: {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
