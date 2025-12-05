"""
测试登录功能脚本
验证测试账号是否可以正常登录
"""

import asyncio
import httpx
from app.core.database import init_db, AsyncSessionLocal, close_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash

from scripts.api_test_config import API_BASE_URL, api_url


async def test_login():
    """测试登录功能"""
    print("=" * 60)
    print("测试登录功能")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 测试账号列表
        test_accounts = [
            {"username": "admin", "password": "admin123"},
            {"username": "test", "password": "test123"},
            {"username": "demo", "password": "demo123"}
        ]
        
        print("\n测试密码验证：")
        print("-" * 60)
        
        for account in test_accounts:
            username = account["username"]
            password = account["password"]
            
            # 查找用户
            user = await User.get_by_username(db, username)
            if not user:
                print(f"\n[失败] 用户 '{username}' 不存在")
                continue
            
            # 测试密码验证
            is_valid = verify_password(password, user.hashed_password)
            
            if is_valid:
                print(f"\n[✅] 用户 '{username}' 密码验证成功")
                print(f"  用户名: {username}")
                print(f"  密码: {password}")
                print(f"  邮箱: {user.email}")
                print(f"  激活: {'是' if user.is_active else '否'}")
            else:
                print(f"\n[❌] 用户 '{username}' 密码验证失败")
                print("  需要重置密码")
                
                # 尝试重置密码
                try:
                    new_hashed = get_password_hash(password)
                    user.hashed_password = new_hashed
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
                    
                    # 再次验证
                    if verify_password(password, user.hashed_password):
                        print("  [修复] 已重置密码，现在可以正常登录")
                    else:
                        print("  [错误] 重置后仍然无法验证")
                except Exception as e:
                    print(f"  [错误] 重置密码失败: {e}")
                    await db.rollback()
        
        print("\n" + "-" * 60)
    
    await close_db()
    
    # 测试API登录
    print("\n测试API登录：")
    print("-" * 60)
    
    BASE_URL = API_BASE_URL
    
    async with httpx.AsyncClient() as client:
        for account in test_accounts:
            username = account["username"]
            password = account["password"]
            
            try:
                response = await client.post(
                    api_url("/auth/login"),
                    data={
                        "username": username,
                        "password": password
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    print(f"\n[✅] API登录成功: {username}")
                    print(f"  Token: {token_data.get('access_token', '')[:50]}...")
                else:
                    print(f"\n[❌] API登录失败: {username}")
                    print(f"  状态码: {response.status_code}")
                    print(f"  响应: {response.text}")
            except Exception as e:
                print(f"\n[⚠️] API登录测试跳过: {username}")
                print("  原因: 后端服务可能未启动")
                print(f"  错误: {e}")
                break
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    print(f"\n请确保后端服务已启动 ({API_BASE_URL})")
    print("按 Enter 开始测试...")
    input()
    asyncio.run(test_login())

