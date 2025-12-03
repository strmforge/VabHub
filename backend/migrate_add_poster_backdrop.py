"""
数据库迁移脚本：添加poster和backdrop字段到subscriptions表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def migrate():
    """执行迁移"""
    async with engine.begin() as conn:
        # 检查字段是否存在
        check_poster = text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('subscriptions')
            WHERE name = 'poster'
        """)
        
        check_backdrop = text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('subscriptions')
            WHERE name = 'backdrop'
        """)
        
        result_poster = await conn.execute(check_poster)
        result_backdrop = await conn.execute(check_backdrop)
        
        poster_exists = result_poster.scalar() > 0
        backdrop_exists = result_backdrop.scalar() > 0
        
        # 添加poster字段
        if not poster_exists:
            print("添加poster字段...")
            await conn.execute(text("""
                ALTER TABLE subscriptions
                ADD COLUMN poster VARCHAR(500)
            """))
            print("✅ poster字段已添加")
        else:
            print("ℹ️ poster字段已存在")
        
        # 添加backdrop字段
        if not backdrop_exists:
            print("添加backdrop字段...")
            await conn.execute(text("""
                ALTER TABLE subscriptions
                ADD COLUMN backdrop VARCHAR(500)
            """))
            print("✅ backdrop字段已添加")
        else:
            print("ℹ️ backdrop字段已存在")
        
        print("✅ 迁移完成")


if __name__ == "__main__":
    asyncio.run(migrate())

