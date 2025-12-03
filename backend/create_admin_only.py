"""
仅创建admin管理员账号脚本
"""

import asyncio
from app.core.database import init_db, AsyncSessionLocal, close_db
from app.models.user import User
from app.core.security import get_password_hash


async def create_admin():
    """创建admin管理员账号"""
    print("=" * 60)
    print("创建admin管理员账号")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    async with AsyncSessionLocal() as db:
        username = "admin"
        
        # 检查用户是否已存在
        existing_user = await User.get_by_username(db, username)
        if existing_user:
            print(f"\n[信息] 用户 '{username}' 已存在")
            print(f"  邮箱: {existing_user.email}")
            print(f"  管理员: {'是' if existing_user.is_superuser else '否'}")
            print(f"  激活: {'是' if existing_user.is_active else '否'}")
            
            # 询问是否要更新密码
            print("\n[提示] 如果要重置密码，请先删除现有用户")
            return
        
        # 创建admin用户
        try:
            hashed_password = get_password_hash("admin123")
            user = User(
                username="admin",
                email="admin@vabhub.com",
                hashed_password=hashed_password,
                full_name="管理员",
                is_superuser=True,
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"\n[成功] 创建admin管理员账号成功！")
            print(f"  用户名: admin")
            print(f"  密码: admin123")
            print(f"  邮箱: admin@vabhub.com")
            print(f"  角色: 管理员")
        except Exception as e:
            print(f"\n[失败] 创建失败: {e}")
            await db.rollback()
            import traceback
            traceback.print_exc()
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(create_admin())

