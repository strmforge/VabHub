"""
检查现有用户脚本
"""

import asyncio
from app.core.database import init_db, AsyncSessionLocal, close_db
from app.models.user import User


async def check_users():
    """检查现有用户"""
    print("=" * 60)
    print("检查现有用户")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        # 获取所有用户
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("\n[信息] 数据库中没有用户")
        else:
            print(f"\n[信息] 找到 {len(users)} 个用户：\n")
            print("-" * 60)
            for user in users:
                print(f"ID: {user.id}")
                print(f"用户名: {user.username}")
                print(f"邮箱: {user.email}")
                print(f"全名: {user.full_name or 'N/A'}")
                print(f"管理员: {'是' if user.is_superuser else '否'}")
                print(f"激活: {'是' if user.is_active else '否'}")
                print(f"创建时间: {user.created_at}")
                print("-" * 60)
        
        # 检查测试账号
        test_usernames = ["admin", "test", "demo"]
        print("\n测试账号状态：")
        print("-" * 60)
        for username in test_usernames:
            user = await User.get_by_username(db, username)
            if user:
                status = "✅ 已存在"
                if not user.is_active:
                    status += " (已禁用)"
                print(f"{username:10} {status}")
            else:
                print(f"{username:10} ❌ 不存在")
        print("-" * 60)
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(check_users())

