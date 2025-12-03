"""
数据库管理脚本
"""

import asyncio
from app.core.database import init_db, close_db


async def main():
    """初始化数据库"""
    await init_db()
    await close_db()
    print("数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())

