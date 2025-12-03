"""
RSSHub表迁移脚本
创建RSSHub相关的数据库表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.core.database import engine, AsyncSessionLocal, init_db
from app.core.config import settings
from loguru import logger


async def migrate_rsshub_tables():
    """迁移RSSHub相关表"""
    print("=" * 60)
    print("RSSHub表迁移")
    print("=" * 60)
    
    # 初始化数据库（确保表存在）
    await init_db()
    
    async with engine.begin() as conn:
        try:
            # 检查表是否已存在
            if settings.DATABASE_URL.startswith("sqlite"):
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='rsshub_source'")
                )
            else:
                result = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='rsshub_source'")
                )
            
            table_exists = result.fetchone() is not None
            
            if table_exists:
                print("\n[信息] RSSHub相关表已存在，无需迁移")
                return
            
            print("\n[信息] RSSHub相关表不存在，将创建新表")
            
            # 重新初始化数据库以创建所有表
            await close_db()
            await init_db()
            
            print("[成功] RSSHub相关表已创建")
            
            # 验证表创建
            if settings.DATABASE_URL.startswith("sqlite"):
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'rsshub%'")
                )
            else:
                result = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'rsshub%'")
                )
            
            tables = [row[0] for row in result.fetchall()]
            print(f"[验证] 创建的RSSHub相关表: {tables}")
            
        except Exception as e:
            print(f"[错误] 迁移失败: {e}")
            raise


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()


async def main():
    """主函数"""
    try:
        await migrate_rsshub_tables()
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n[错误] 迁移失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())