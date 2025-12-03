"""
重置测试账号密码脚本
用于修复密码哈希问题
"""

import asyncio
from app.core.database import init_db, AsyncSessionLocal, close_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password


async def reset_passwords():
    """重置测试账号密码"""
    print("=" * 60)
    print("重置测试账号密码")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 测试账号列表
        test_users = [
            {"username": "admin", "password": "admin123"},
            {"username": "test", "password": "test123"},
            {"username": "demo", "password": "demo123"}
        ]
        
        updated_count = 0
        
        for user_data in test_users:
            username = user_data["username"]
            new_password = user_data["password"]
            
            # 查找用户
            user = await User.get_by_username(db, username)
            if not user:
                print(f"\n[跳过] 用户 '{username}' 不存在")
                continue
            
            # 检查当前密码是否正确
            current_correct = verify_password(new_password, user.hashed_password)
            
            if current_correct:
                print(f"\n[跳过] 用户 '{username}' 密码已正确，无需重置")
                continue
            
            # 重置密码
            try:
                new_hashed_password = get_password_hash(new_password)
                user.hashed_password = new_hashed_password
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                # 验证新密码
                if verify_password(new_password, user.hashed_password):
                    print(f"\n[成功] 重置用户 '{username}' 密码成功")
                    print(f"  新密码: {new_password}")
                    updated_count += 1
                else:
                    print(f"\n[警告] 重置用户 '{username}' 密码后验证失败")
            except Exception as e:
                print(f"\n[失败] 重置用户 '{username}' 密码失败: {e}")
                await db.rollback()
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print(f"完成！重置了 {updated_count} 个用户的密码")
        print("=" * 60)
        
        # 显示测试账号信息
        print("\n📋 测试账号信息：")
        print("-" * 60)
        for user_data in test_users:
            print(f"\n用户名: {user_data['username']}")
            print(f"密码: {user_data['password']}")
        print("-" * 60)
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(reset_passwords())

