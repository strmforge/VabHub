"""
站点 AI 适配数据库迁移脚本
创建 ai_site_adapters 表
"""

from __future__ import annotations

import asyncio
from typing import Dict, Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal


async def create_ai_site_adapters_table(session: AsyncSession) -> Dict[str, Any]:
    """创建 ai_site_adapters 表"""
    try:
        # 检查表是否已存在
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_site_adapters'")
        )
        table_exists = result.scalar()
        
        if not table_exists:
            # 创建表
            await session.execute(text("""
                CREATE TABLE ai_site_adapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id VARCHAR(100) NOT NULL UNIQUE,
                    engine VARCHAR(50) NOT NULL,
                    config_json TEXT NOT NULL,
                    raw_model_output TEXT,
                    version INTEGER NOT NULL DEFAULT 1,
                    disabled INTEGER NOT NULL DEFAULT 0,
                    manual_profile_preferred INTEGER NOT NULL DEFAULT 0,
                    confidence_score INTEGER,
                    last_error TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_ai_site_adapters_site_id 
                ON ai_site_adapters(site_id)
            """))
            
            await session.commit()
            logger.info("表 ai_site_adapters 创建成功")
            return {"status": "created"}
        else:
            # Phase AI-4: 表已存在，检查并添加新字段
            logger.info("表 ai_site_adapters 已存在，检查新字段...")
            
            # 检查现有列
            result = await session.execute(text("PRAGMA table_info(ai_site_adapters)"))
            existing_columns = {row[1] for row in result.fetchall()}
            
            columns_to_add = []
            if "disabled" not in existing_columns:
                columns_to_add.append(("disabled", "INTEGER NOT NULL DEFAULT 0"))
            if "manual_profile_preferred" not in existing_columns:
                columns_to_add.append(("manual_profile_preferred", "INTEGER NOT NULL DEFAULT 0"))
            if "confidence_score" not in existing_columns:
                columns_to_add.append(("confidence_score", "INTEGER"))
            if "last_error" not in existing_columns:
                columns_to_add.append(("last_error", "TEXT"))
            
            if columns_to_add:
                for col_name, col_def in columns_to_add:
                    try:
                        await session.execute(text(f"ALTER TABLE ai_site_adapters ADD COLUMN {col_name} {col_def}"))
                        logger.info(f"已添加列: {col_name}")
                    except Exception as e:
                        logger.warning(f"添加列 {col_name} 失败（可能已存在）: {e}")
                
                await session.commit()
                logger.info(f"表 ai_site_adapters 字段更新完成，新增 {len(columns_to_add)} 个字段")
                return {"status": "updated", "columns_added": len(columns_to_add)}
            else:
                logger.info("表 ai_site_adapters 字段已是最新，无需更新")
                return {"status": "skipped", "reason": "table_up_to_date"}
            
    except Exception as e:
        await session.rollback()
        logger.error(f"更新表 ai_site_adapters 失败: {e}")
        return {"status": "error", "error": str(e)}


async def main():
    """主函数"""
    logger.info("开始迁移站点 AI 适配数据库表...")
    
    async with AsyncSessionLocal() as session:
        result = await create_ai_site_adapters_table(session)
        logger.info(f"迁移结果: {result}")
    
    logger.info("迁移完成")


if __name__ == "__main__":
    asyncio.run(main())

