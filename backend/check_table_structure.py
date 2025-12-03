#!/usr/bin/env python3
"""
检查notifications表结构
"""

import sys
import asyncio
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.append('.')

from app.core.database import engine

async def check_table_structure():
    """检查notifications表结构"""
    async with engine.begin() as conn:
        # 检查notifications表结构
        result = await conn.execute(text("PRAGMA table_info(notifications)"))
        columns = result.fetchall()
        
        print("notifications表结构:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
        
        # 检查表中有多少数据
        result = await conn.execute(text("SELECT COUNT(*) FROM notifications"))
        count = result.scalar()
        print(f"\nnotifications表数据量: {count}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())