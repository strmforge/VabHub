"""
为 manga_series_local 表添加 new_chapter_count 字段
用于追踪未读新章节数量
"""

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
import asyncio

async def migrate():
    """执行数据库迁移"""
    async with AsyncSessionLocal() as db:
        try:
            # 检查字段是否已存在
            result = await db.execute(text("""
                PRAGMA table_info(manga_series_local)
            """))
            columns = [row[1] for row in result.fetchall()]
            
            if 'new_chapter_count' not in columns:
                # 添加字段
                await db.execute(text("""
                    ALTER TABLE manga_series_local 
                    ADD COLUMN new_chapter_count INTEGER DEFAULT 0 NOT NULL
                """))
                await db.commit()
                print("✅ 已添加 new_chapter_count 字段")
            else:
                print("✅ new_chapter_count 字段已存在")
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(migrate())