#!/usr/bin/env python3
"""
检查数据库表是否存在
"""

import sys
import asyncio
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.append('.')

from app.core.database import engine

async def check_tables():
    """检查数据库表"""
    async with engine.begin() as conn:
        # 检查所有表
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = result.scalars().all()
        
        print("数据库中的表:")
        for table in tables:
            print(f"  - {table}")
        
        # 检查特定表是否存在
        notifications_exists = "notifications" in tables
        user_notifications_exists = "user_notifications" in tables
        
        print(f"\nnotifications表存在: {notifications_exists}")
        print(f"user_notifications表存在: {user_notifications_exists}")

if __name__ == "__main__":
    asyncio.run(check_tables())