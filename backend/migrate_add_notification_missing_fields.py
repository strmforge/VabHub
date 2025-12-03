"""
添加notifications表缺失字段的迁移脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from loguru import logger
from app.core.database import AsyncSessionLocal


async def add_missing_fields():
    """添加notifications表缺失的字段"""
    
    logger.info("="*60)
    logger.info("开始添加notifications表缺失字段")
    logger.info("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查表是否存在
            result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.error("❌ notifications表不存在，无法添加字段")
                return False
            
            logger.info("✅ notifications表存在")
            
            # 检查表结构
            result = await db.execute(text("PRAGMA table_info(notifications)"))
            columns = result.fetchall()
            existing_fields = [col[1] for col in columns]
            
            # 需要添加的字段
            fields_to_add = [
                {
                    'name': 'level',
                    'type': 'VARCHAR(20)',
                    'nullable': 'NULL',
                    'default': None,
                    'description': '通知级别 (info, warning, error, critical)'
                },
                {
                    'name': 'is_read',
                    'type': 'BOOLEAN',
                    'nullable': 'NOT NULL',
                    'default': '0',
                    'description': '是否已读'
                },
                {
                    'name': 'read_at',
                    'type': 'DATETIME',
                    'nullable': 'NULL',
                    'default': None,
                    'description': '阅读时间'
                },
                {
                    'name': 'extra_metadata',
                    'type': 'JSON',
                    'nullable': 'NULL',
                    'default': None,
                    'description': '额外元数据'
                }
            ]
            
            added_count = 0
            skipped_count = 0
            
            for field in fields_to_add:
                if field['name'] in existing_fields:
                    logger.info(f"✅ 字段 {field['name']} 已存在，跳过")
                    skipped_count += 1
                    continue
                
                # 构建ALTER TABLE语句
                alter_sql = f"ALTER TABLE notifications ADD COLUMN {field['name']} {field['type']}"
                
                if field['nullable'] == 'NOT NULL':
                    alter_sql += " NOT NULL"
                
                if field['default']:
                    alter_sql += f" DEFAULT {field['default']}"
                
                try:
                    await db.execute(text(alter_sql))
                    await db.commit()
                    logger.info(f"✅ 字段 {field['name']} 添加成功: {field['description']}")
                    added_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ 添加字段 {field['name']} 失败: {e}")
                    await db.rollback()
                    return False
            
            # 添加索引
            if 'is_read' in existing_fields or 'is_read' in [f['name'] for f in fields_to_add if f['name'] not in existing_fields]:
                # 检查索引是否已存在
                result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_notifications_is_read'"))
                index_exists = result.scalar()
                
                if not index_exists:
                    try:
                        await db.execute(text("CREATE INDEX idx_notifications_is_read ON notifications(is_read)"))
                        await db.commit()
                        logger.info("✅ 索引 idx_notifications_is_read 创建成功")
                    except Exception as e:
                        logger.error(f"❌ 创建索引失败: {e}")
                        await db.rollback()
                else:
                    logger.info("✅ 索引 idx_notifications_is_read 已存在")
            
            logger.info("="*60)
            logger.info(f"迁移完成: 添加 {added_count} 个字段，跳过 {skipped_count} 个字段")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            await db.rollback()
            return False


async def verify_migration():
    """验证迁移结果"""
    
    logger.info("\n" + "="*60)
    logger.info("验证迁移结果")
    logger.info("="*60)
    
    async with AsyncSessionLocal() as db:
        # 检查表结构
        result = await db.execute(text("PRAGMA table_info(notifications)"))
        columns = result.fetchall()
        
        logger.info("📋 notifications表当前结构:")
        for col in columns:
            cid, name, type_, notnull, dflt_value, pk = col
            nullable = "NULL" if notnull == 0 else "NOT NULL"
            logger.info(f"  {name} | {type_} | {nullable}")
        
        # 检查模型字段是否都存在
        model_fields = [
            'id', 'title', 'message', 'type', 'level', 'channels', 
            'status', 'is_read', 'read_at', 'sent_at', 'created_at', 'extra_metadata'
        ]
        
        existing_fields = [col[1] for col in columns]
        missing_fields = [field for field in model_fields if field not in existing_fields]
        
        if missing_fields:
            logger.error(f"❌ 仍然缺失的字段: {missing_fields}")
            return False
        else:
            logger.info("✅ 所有模型字段都存在")
            return True


if __name__ == "__main__":
    logger.info("开始执行notifications表迁移...")
    
    # 执行迁移
    success = asyncio.run(add_missing_fields())
    
    if success:
        # 验证迁移结果
        verification_success = asyncio.run(verify_migration())
        
        if verification_success:
            logger.info("🎉 迁移验证成功！notifications表结构已与模型同步")
        else:
            logger.error("❌ 迁移验证失败，请检查表结构")
    else:
        logger.error("❌ 迁移执行失败")