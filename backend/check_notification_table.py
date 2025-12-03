"""
检查notifications表的详细结构
"""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_notification_table():
    """检查notifications表的详细结构"""
    async with AsyncSessionLocal() as db:
        # 检查表是否存在
        result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"))
        table_exists = result.scalar()
        
        if not table_exists:
            print("❌ notifications表不存在")
            return
        
        print("✅ notifications表存在")
        
        # 检查表结构
        result = await db.execute(text("PRAGMA table_info(notifications)"))
        columns = result.fetchall()
        
        print("\n📋 notifications表结构:")
        print("字段名 | 类型 | 是否可为空 | 默认值")
        print("-" * 50)
        for col in columns:
            cid, name, type_, notnull, dflt_value, pk = col
            nullable = "NULL" if notnull == 0 else "NOT NULL"
            default = dflt_value if dflt_value else "-"
            print(f"{name} | {type_} | {nullable} | {default}")
        
        # 检查是否有数据
        result = await db.execute(text("SELECT COUNT(*) FROM notifications"))
        count = result.scalar()
        print(f"\n📊 notifications表数据量: {count} 条记录")
        
        # 检查模型字段是否在表中存在
        model_fields = [
            'id', 'title', 'message', 'type', 'level', 'channels', 
            'status', 'is_read', 'read_at', 'sent_at', 'created_at', 'extra_metadata'
        ]
        
        existing_fields = [col[1] for col in columns]
        missing_fields = [field for field in model_fields if field not in existing_fields]
        
        if missing_fields:
            print(f"\n❌ 缺失的模型字段: {missing_fields}")
        else:
            print("\n✅ 所有模型字段都存在")

if __name__ == "__main__":
    asyncio.run(check_notification_table())