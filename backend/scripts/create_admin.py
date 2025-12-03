"""
创建管理员用户脚本
"""

import asyncio
import sys
from pathlib import Path
import getpass

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.database import AsyncSessionLocal, close_db
from app.models.user import User
from app.core.auth import get_password_hash
from loguru import logger


async def create_admin():
    """创建管理员用户"""
    logger.info("="*50)
    logger.info("创建管理员用户")
    logger.info("="*50)
    
    # 获取用户输入
    username = input("请输入用户名 (默认: admin): ").strip() or "admin"
    email = input("请输入邮箱 (默认: admin@vabhub.com): ").strip() or "admin@vabhub.com"
    password = getpass.getpass("请输入密码: ").strip()
    
    if not password:
        logger.error("密码不能为空")
        sys.exit(1)
    
    async with AsyncSessionLocal() as session:
        # 检查用户是否已存在
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"用户 {username} 已存在")
            update = input("是否更新密码? (y/n): ").strip().lower()
            if update == 'y':
                existing_user.hashed_password = get_password_hash(password)
                existing_user.is_active = True
                existing_user.is_superuser = True
                await session.commit()
                logger.info(f"✅ 用户 {username} 密码已更新")
            else:
                logger.info("取消操作")
        else:
            # 创建新用户
            new_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True
            )
            session.add(new_user)
            await session.commit()
            logger.info(f"✅ 管理员用户 {username} 创建成功")
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(create_admin())

