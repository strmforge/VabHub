"""
数据库迁移：为 Plugin 表添加来源信息字段
PLUGIN-HUB-2 实现

新增字段：
- source: 来源类型（local/plugin_hub/manual_hub）
- hub_id: Plugin Hub 条目 ID
- repo_url: Git 仓库地址
- installed_ref: 当前安装的 commit/ref
- auto_update_enabled: 是否启用自动更新
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

from sqlalchemy import text
from app.core.database import engine
from loguru import logger


async def check_column_exists(conn, table: str, column: str) -> bool:
    """检查列是否存在"""
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    columns = [row[1] for row in result.fetchall()]
    return column in columns


async def migrate():
    """执行迁移"""
    try:
        logger.info("开始为 Plugin 表添加来源信息字段...")
        
        async with engine.begin() as conn:
            # 检查并添加 source 字段
            if not await check_column_exists(conn, "plugin", "source"):
                await conn.execute(text(
                    "ALTER TABLE plugin ADD COLUMN source VARCHAR(32) NOT NULL DEFAULT 'local'"
                ))
                logger.info("  ✅ 添加字段: source")
            else:
                logger.info("  ⏭️  字段已存在: source")
            
            # 检查并添加 hub_id 字段
            if not await check_column_exists(conn, "plugin", "hub_id"):
                await conn.execute(text(
                    "ALTER TABLE plugin ADD COLUMN hub_id VARCHAR(128)"
                ))
                logger.info("  ✅ 添加字段: hub_id")
            else:
                logger.info("  ⏭️  字段已存在: hub_id")
            
            # 检查并添加 repo_url 字段
            if not await check_column_exists(conn, "plugin", "repo_url"):
                await conn.execute(text(
                    "ALTER TABLE plugin ADD COLUMN repo_url VARCHAR(512)"
                ))
                logger.info("  ✅ 添加字段: repo_url")
            else:
                logger.info("  ⏭️  字段已存在: repo_url")
            
            # 检查并添加 installed_ref 字段
            if not await check_column_exists(conn, "plugin", "installed_ref"):
                await conn.execute(text(
                    "ALTER TABLE plugin ADD COLUMN installed_ref VARCHAR(128)"
                ))
                logger.info("  ✅ 添加字段: installed_ref")
            else:
                logger.info("  ⏭️  字段已存在: installed_ref")
            
            # 检查并添加 auto_update_enabled 字段
            if not await check_column_exists(conn, "plugin", "auto_update_enabled"):
                await conn.execute(text(
                    "ALTER TABLE plugin ADD COLUMN auto_update_enabled BOOLEAN NOT NULL DEFAULT 1"
                ))
                logger.info("  ✅ 添加字段: auto_update_enabled")
            else:
                logger.info("  ⏭️  字段已存在: auto_update_enabled")
        
        logger.info("✅ Plugin 表来源信息字段迁移完成")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())
