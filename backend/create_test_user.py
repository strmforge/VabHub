"""
创建测试账号脚本
"""

import asyncio
from app.core.database import init_db, AsyncSessionLocal, close_db
from app.models.user import User
from app.core.security import get_password_hash


async def create_test_users():
    """创建测试账号"""
    print("=" * 60)
    print("创建测试账号")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 测试账号列表
        test_users = [
            {
                "username": "admin",
                "email": "admin@vabhub.com",
                "password": "admin123",
                "full_name": "管理员",
                "is_superuser": True
            },
            {
                "username": "test",
                "email": "test@vabhub.com",
                "password": "test123",
                "full_name": "测试用户",
                "is_superuser": False
            },
            {
                "username": "demo",
                "email": "demo@vabhub.com",
                "password": "demo123",
                "full_name": "演示用户",
                "is_superuser": False
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        for user_data in test_users:
            username = user_data["username"]
            
            # 检查用户是否已存在
            existing_user = await User.get_by_username(db, username)
            if existing_user:
                print(f"\n[跳过] 用户 '{username}' 已存在")
                skipped_count += 1
                continue
            
            # 创建用户
            try:
                hashed_password = get_password_hash(user_data["password"])
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    full_name=user_data["full_name"],
                    is_superuser=user_data.get("is_superuser", False),
                    is_active=True
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                print(f"\n[成功] 创建用户: {username}")
                print(f"  邮箱: {user_data['email']}")
                print(f"  密码: {user_data['password']}")
                print(f"  管理员: {'是' if user_data.get('is_superuser') else '否'}")
                created_count += 1
            except Exception as e:
                print(f"\n[失败] 创建用户 '{username}' 失败: {e}")
                await db.rollback()
        
        print("\n" + "=" * 60)
        print(f"完成！创建了 {created_count} 个用户，跳过了 {skipped_count} 个已存在的用户")
        print("=" * 60)
        
        # 显示测试账号信息
        print("\n📋 测试账号信息：")
        print("-" * 60)
        for user_data in test_users:
            print(f"\n用户名: {user_data['username']}")
            print(f"密码: {user_data['password']}")
            print(f"邮箱: {user_data['email']}")
            if user_data.get('is_superuser'):
                print("角色: 管理员")
        print("-" * 60)
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(create_test_users())

