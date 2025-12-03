#!/usr/bin/env python3
"""
简单检查表结构
"""

import sys
import asyncio
from sqlalchemy import text

sys.path.append('.')

from app.core.database import engine

async def check_table():
    async with engine.begin() as conn:
        # 检查notifications表结构
        result = await conn.execute(text("PRAGMA table_info(notifications)"))
        columns = result.fetchall()
        
        print("notifications表结构:")
        for col in columns:
            nullable = "NOT NULL" if col[3] else "NULLABLE"
            print(f"  {col[1]} ({col[2]}) - {nullable}")

if __name__ == "__main__":
    asyncio.run(check_table())