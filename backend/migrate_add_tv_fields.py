"""
数据库迁移脚本：添加电视剧相关字段
"""
import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


async def migrate():
    """添加电视剧相关字段到subscriptions表"""
    # 创建异步引擎
    database_url = str(settings.DATABASE_URL)
    # 如果使用SQLite，需要转换为异步URL
    if database_url.startswith('sqlite'):
        database_url = database_url.replace('sqlite://', 'sqlite+aiosqlite://')
    
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        
        # 检查表是否存在
        if 'subscriptions' not in inspector.get_table_names():
            print("subscriptions表不存在，请先创建表")
            return
        
        # 检查并添加字段
        columns = inspector.get_columns('subscriptions')
        column_names = [col['name'] for col in columns]
        
        fields_to_add = [
            ('season', 'INTEGER'),
            ('total_episode', 'INTEGER'),
            ('start_episode', 'INTEGER'),
            ('episode_group', 'VARCHAR(100)'),
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in column_names:
                print(f"添加字段 {field_name}...")
                await conn.execute(text(f"""
                    ALTER TABLE subscriptions
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"{field_name} 字段添加成功。")
            else:
                print(f"{field_name} 字段已存在，跳过。")
        
        print("迁移完成！")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())

