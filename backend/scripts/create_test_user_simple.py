"""
创建测试用户
用于功能测试
"""

import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


async def create_test_user():
    """创建测试用户"""
    username = "test_user"
    email = "test@example.com"
    password = "test_password_123"
    
    async with AsyncSessionLocal() as db:
        # 检查用户是否已存在
        existing_user = await User.get_by_username(db, username)
        if existing_user:
            print(f"[INFO] 用户 {username} 已存在")
            return existing_user
        
        # 创建新用户
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name="Test User",
            is_active=True
        )
        
        await user.save(db)
        print("[OK] 测试用户创建成功")
        print(f"     用户名: {username}")
        print(f"     邮箱: {email}")
        print(f"     密码: {password}")
        return user


if __name__ == "__main__":
    asyncio.run(create_test_user())

