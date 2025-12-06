"""
初始管理员自动创建模块

首次启动时自动创建管理员账号：
- 若数据库中已有任何 is_superuser=True 的用户，则跳过
- 若设置了 SUPERUSER_PASSWORD 环境变量，使用指定密码
- 若未设置密码，自动生成随机密码并输出到日志
"""

import os
import secrets
import string
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash


def generate_random_password(length: int = 16) -> str:
    """
    生成随机密码
    
    Args:
        length: 密码长度，默认16位
    
    Returns:
        包含大小写字母和数字的随机密码
    """
    alphabet = string.ascii_letters + string.digits
    # 确保至少有一个大写、一个小写、一个数字
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    # 填充剩余字符
    password.extend(secrets.choice(alphabet) for _ in range(length - 3))
    # 打乱顺序
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return ''.join(password_list)


async def has_any_superuser(db: AsyncSession) -> bool:
    """
    检查数据库中是否已有超级管理员
    
    Args:
        db: 数据库会话
    
    Returns:
        是否已有超级管理员
    """
    result = await db.execute(
        select(func.count(User.id)).where(User.is_superuser == True)
    )
    count = result.scalar_one()
    return count > 0


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    根据用户名获取用户
    
    Args:
        db: 数据库会话
        username: 用户名
    
    Returns:
        用户对象或 None
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def ensure_initial_superuser(db: AsyncSession) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    确保首次启动时存在初始管理员账号
    
    行为逻辑：
    1. 如果数据库中已有任何 is_superuser=True 的用户，直接返回
    2. 读取环境变量 SUPERUSER_NAME（默认 admin）和 SUPERUSER_PASSWORD
    3. 如果 SUPERUSER_PASSWORD 存在：
       - 创建指定用户名/密码的超级用户
    4. 如果 SUPERUSER_PASSWORD 不存在：
       - 生成随机密码
       - 创建 admin 超级用户
       - 在日志中输出密码
    
    Args:
        db: 数据库会话
    
    Returns:
        Tuple of (created: bool, username: Optional[str], password: Optional[str])
        - created: 是否创建了新用户
        - username: 创建的用户名（如果创建了）
        - password: 随机生成的密码（仅当使用随机密码时返回）
    """
    # 检查是否已有超级管理员
    if await has_any_superuser(db):
        logger.debug("数据库中已存在超级管理员，跳过初始用户创建")
        return False, None, None
    
    # 读取环境变量
    superuser_name = os.getenv("SUPERUSER_NAME", "admin").strip()
    superuser_password = os.getenv("SUPERUSER_PASSWORD", "").strip()
    
    # 确定密码
    password_is_random = False
    if not superuser_password:
        superuser_password = generate_random_password(16)
        password_is_random = True
        logger.info("未设置 SUPERUSER_PASSWORD 环境变量，将生成随机密码")
    
    # 检查用户名是否已存在（非超级管理员但同名）
    existing_user = await get_user_by_username(db, superuser_name)
    if existing_user:
        # 用户已存在但不是超级管理员 - 升级为超级管理员
        existing_user.is_superuser = True
        existing_user.is_active = True
        if password_is_random:
            # 如果是随机密码，也更新密码
            existing_user.hashed_password = get_password_hash(superuser_password)
        await db.commit()
        logger.info(f"用户 {superuser_name} 已存在，已升级为超级管理员")
        if password_is_random:
            return True, superuser_name, superuser_password
        return True, superuser_name, None
    
    # 创建新用户
    new_user = User(
        username=superuser_name,
        email=f"{superuser_name}@vabhub.local",
        hashed_password=get_password_hash(superuser_password),
        is_active=True,
        is_superuser=True,
    )
    db.add(new_user)
    await db.commit()
    
    if password_is_random:
        # 在日志中输出随机密码
        logger.info("=" * 60)
        logger.info("🔐 初始管理员账号已创建")
        logger.info(f"   用户名: {superuser_name}")
        logger.info(f"   密码: {superuser_password}")
        logger.info("⚠️  请尽快登录后修改密码！")
        logger.info("=" * 60)
        return True, superuser_name, superuser_password
    else:
        logger.info(f"✅ 初始管理员 {superuser_name} 已创建（使用环境变量设置的密码）")
        return True, superuser_name, None


async def initialize_superuser():
    """
    在应用启动时调用的初始化入口
    
    自动获取数据库会话并执行初始管理员创建
    """
    try:
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            created, username, password = await ensure_initial_superuser(db)
            if created:
                logger.info(f"初始管理员初始化完成: {username}")
            else:
                logger.debug("初始管理员已存在，无需创建")
    except Exception as e:
        logger.error(f"初始管理员创建失败: {e}")
        # 不抛出异常，避免阻断启动流程
