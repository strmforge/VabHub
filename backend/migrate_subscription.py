"""
订阅模型字段迁移脚本
添加新的订阅规则字段
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine, init_db, close_db
from app.core.config import settings


async def migrate_subscription():
    """迁移订阅表，添加新字段"""
    print("=" * 60)
    print("订阅模型字段迁移")
    print("=" * 60)
    
    # 初始化数据库（确保表存在）
    await init_db()
    
    async with engine.begin() as conn:
        try:
            # 检查表是否存在
            if settings.DATABASE_URL.startswith("sqlite"):
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
                )
            else:
                result = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='subscriptions'")
                )
            
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                print("\n[信息] subscriptions表不存在，将创建新表")
                await close_db()
                await init_db()
                print("[成功] 表已创建")
                return
            
            print("\n[信息] 开始迁移订阅表...")
            
            # SQLite迁移
            if settings.DATABASE_URL.startswith("sqlite"):
                # 检查字段是否已存在
                result = await conn.execute(
                    text("PRAGMA table_info(subscriptions)")
                )
                columns = {row[1] for row in result.fetchall()}
                
                # 添加新字段（如果不存在）
                new_fields = {
                    'quality': 'TEXT',
                    'resolution': 'TEXT',
                    'effect': 'TEXT',
                    'sites': 'TEXT',  # JSON存储为TEXT
                    'downloader': 'TEXT',
                    'save_path': 'TEXT',
                    'best_version': 'INTEGER DEFAULT 0',
                    'search_imdbid': 'INTEGER DEFAULT 0',
                    'include': 'TEXT',
                    'exclude': 'TEXT',
                    'filter_groups': 'TEXT'  # JSON存储为TEXT
                }
                
                for field_name, field_type in new_fields.items():
                    if field_name not in columns:
                        try:
                            await conn.execute(
                                text(f"ALTER TABLE subscriptions ADD COLUMN {field_name} {field_type}")
                            )
                            print(f"  [成功] 添加字段: {field_name}")
                        except Exception as e:
                            print(f"  [警告] 添加字段 {field_name} 失败: {e}")
                    else:
                        print(f"  [跳过] 字段 {field_name} 已存在")
            
            # PostgreSQL迁移
            else:
                # 检查字段是否已存在
                result = await conn.execute(
                    text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='subscriptions'
                    """)
                )
                columns = {row[0] for row in result.fetchall()}
                
                # 添加新字段（如果不存在）
                new_fields = {
                    'quality': 'VARCHAR(50)',
                    'resolution': 'VARCHAR(50)',
                    'effect': 'VARCHAR(50)',
                    'sites': 'JSONB',
                    'downloader': 'VARCHAR(50)',
                    'save_path': 'VARCHAR(500)',
                    'best_version': 'BOOLEAN DEFAULT FALSE',
                    'search_imdbid': 'BOOLEAN DEFAULT FALSE',
                    'include': 'TEXT',
                    'exclude': 'TEXT',
                    'filter_groups': 'JSONB'
                }
                
                for field_name, field_type in new_fields.items():
                    if field_name not in columns:
                        try:
                            await conn.execute(
                                text(f"ALTER TABLE subscriptions ADD COLUMN {field_name} {field_type}")
                            )
                            print(f"  [成功] 添加字段: {field_name}")
                        except Exception as e:
                            print(f"  [警告] 添加字段 {field_name} 失败: {e}")
                    else:
                        print(f"  [跳过] 字段 {field_name} 已存在")
            
            print("\n[成功] 迁移完成！")
            
        except Exception as e:
            print(f"\n[错误] 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(migrate_subscription())

