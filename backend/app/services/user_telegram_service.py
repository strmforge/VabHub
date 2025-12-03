"""
用户 Telegram 绑定服务
BOT-TELEGRAM 实现
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.models.user_telegram_binding import UserTelegramBinding
from app.models.user_notify_channel import UserNotifyChannel
from app.models.enums.user_notify_channel_type import UserNotifyChannelType
from app.core.config import settings


# ============== 白名单校验 ==============

# 解析并缓存白名单配置
_allowed_users_cache: Optional[set[str]] = None

def _parse_allowed_users() -> set[str]:
    """解析允许绑定的用户白名单"""
    global _allowed_users_cache
    
    if not settings.TELEGRAM_BOT_ALLOWED_USERS:
        _allowed_users_cache = set()
        return _allowed_users_cache
    
    # 解析逗号分隔的用户列表
    users = set()
    for user in settings.TELEGRAM_BOT_ALLOWED_USERS.split(','):
        user = user.strip()
        if user:
            # 标准化：去除@符号，转为小写
            normalized = user.lstrip('@').lower()
            users.add(normalized)
    
    _allowed_users_cache = users
    logger.info(f"[telegram] parsed allowed users: {len(users)} entries")
    return users

def is_user_allowed(chat_id: int, username: Optional[str] = None) -> bool:
    """
    检查用户是否在白名单中
    
    Args:
        chat_id: Telegram Chat ID
        username: Telegram 用户名（可选）
        
    Returns:
        True if allowed, False otherwise
    """
    # 如果没有配置白名单，允许所有用户
    if not settings.TELEGRAM_BOT_ALLOWED_USERS:
        return True
    
    # 获取解析后的白名单
    allowed_users = _parse_allowed_users()
    if not allowed_users:
        return True
    
    # 检查用户ID（转为字符串）
    if str(chat_id) in allowed_users:
        return True
    
    # 检查用户名
    if username:
        normalized_username = username.lstrip('@').lower()
        if normalized_username in allowed_users:
            return True
    
    return False

# ============== 绑定码存储（简单内存实现） ==============
# 生产环境建议使用 Redis

_binding_codes: dict[str, tuple[int, datetime]] = {}  # code -> (user_id, expires_at)
BINDING_CODE_TTL = 600  # 10 分钟


def _cleanup_expired_codes():
    """清理过期的绑定码"""
    now = datetime.utcnow()
    expired = [code for code, (_, expires_at) in _binding_codes.items() if expires_at < now]
    for code in expired:
        del _binding_codes[code]


async def create_binding_code(user: User) -> str:
    """
    生成绑定码
    
    Args:
        user: 用户对象
        
    Returns:
        32 位随机绑定码
    """
    _cleanup_expired_codes()
    
    # 生成随机码
    code = secrets.token_urlsafe(24)[:32].upper()
    expires_at = datetime.utcnow() + timedelta(seconds=BINDING_CODE_TTL)
    
    _binding_codes[code] = (user.id, expires_at)
    
    logger.info(f"[telegram] created binding code for user {user.id}")
    return code


def verify_binding_code(code: str) -> Optional[int]:
    """
    验证绑定码
    
    Args:
        code: 绑定码
        
    Returns:
        用户 ID，如果验证失败返回 None
    """
    _cleanup_expired_codes()
    
    if code not in _binding_codes:
        return None
    
    user_id, expires_at = _binding_codes[code]
    
    if datetime.utcnow() > expires_at:
        del _binding_codes[code]
        return None
    
    # 使用后删除
    del _binding_codes[code]
    return user_id


# ============== 绑定操作 ==============

async def get_binding_by_user(
    session: AsyncSession,
    user_id: int,
) -> Optional[UserTelegramBinding]:
    """获取用户的 Telegram 绑定"""
    result = await session.execute(
        select(UserTelegramBinding).where(UserTelegramBinding.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_binding_by_chat_id(
    session: AsyncSession,
    chat_id: int,
) -> Optional[UserTelegramBinding]:
    """根据 chat_id 获取绑定"""
    result = await session.execute(
        select(UserTelegramBinding).where(UserTelegramBinding.telegram_chat_id == chat_id)
    )
    return result.scalar_one_or_none()


async def bind_user_with_code(
    session: AsyncSession,
    code: str,
    telegram_chat_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    language_code: Optional[str] = None,
) -> Optional[UserTelegramBinding]:
    """
    使用绑定码绑定用户
    
    Args:
        session: 数据库会话
        code: 绑定码
        telegram_chat_id: Telegram Chat ID
        username: Telegram 用户名
        first_name: 名
        last_name: 姓
        language_code: 语言代码
        
    Returns:
        绑定对象，如果失败返回 None
    """
    # 验证绑定码
    user_id = verify_binding_code(code)
    if user_id is None:
        logger.warning(f"[telegram] invalid binding code: {code[:8]}...")
        return None
    
    # 检查是否已绑定其他用户
    existing = await get_binding_by_chat_id(session, telegram_chat_id)
    if existing:
        if existing.user_id == user_id:
            logger.info(f"[telegram] user {user_id} already bound to {telegram_chat_id}")
            return existing
        else:
            logger.warning(f"[telegram] chat {telegram_chat_id} already bound to user {existing.user_id}")
            return None
    
    # 删除用户的旧绑定
    old_binding = await get_binding_by_user(session, user_id)
    if old_binding:
        await session.delete(old_binding)
    
    # 创建新绑定
    binding = UserTelegramBinding(
        user_id=user_id,
        telegram_chat_id=telegram_chat_id,
        telegram_username=username,
        telegram_first_name=first_name,
        telegram_last_name=last_name,
        language_code=language_code,
    )
    session.add(binding)
    
    # 同时创建/更新 UserNotifyChannel
    await _ensure_telegram_notify_channel(session, user_id, telegram_chat_id, username)
    
    await session.commit()
    await session.refresh(binding)
    
    logger.info(f"[telegram] bound user {user_id} to chat {telegram_chat_id}")
    return binding


async def _ensure_telegram_notify_channel(
    session: AsyncSession,
    user_id: int,
    chat_id: int,
    username: Optional[str] = None,
):
    """确保用户有 Telegram 通知渠道"""
    # 查找现有渠道
    result = await session.execute(
        select(UserNotifyChannel).where(
            UserNotifyChannel.user_id == user_id,
            UserNotifyChannel.channel_type == UserNotifyChannelType.TELEGRAM_BOT,
        )
    )
    channel = result.scalar_one_or_none()
    
    if channel:
        # 更新配置
        channel.config = {
            "chat_id": chat_id,
            "username": username,
        }
        channel.is_verified = True
        channel.is_enabled = True
    else:
        # 创建新渠道
        channel = UserNotifyChannel(
            user_id=user_id,
            channel_type=UserNotifyChannelType.TELEGRAM_BOT,
            display_name=f"Telegram @{username}" if username else "Telegram",
            config={
                "chat_id": chat_id,
                "username": username,
            },
            is_enabled=True,
            is_verified=True,
        )
        session.add(channel)


async def unbind_user(
    session: AsyncSession,
    user_id: int,
) -> bool:
    """解除用户的 Telegram 绑定"""
    binding = await get_binding_by_user(session, user_id)
    if not binding:
        return False
    
    await session.delete(binding)
    
    # 同时禁用通知渠道
    result = await session.execute(
        select(UserNotifyChannel).where(
            UserNotifyChannel.user_id == user_id,
            UserNotifyChannel.channel_type == UserNotifyChannelType.TELEGRAM_BOT,
        )
    )
    channel = result.scalar_one_or_none()
    if channel:
        channel.is_enabled = False
        channel.is_verified = False
    
    await session.commit()
    logger.info(f"[telegram] unbound user {user_id}")
    return True


async def get_user_by_chat_id(
    session: AsyncSession,
    chat_id: int,
) -> Optional[User]:
    """根据 Telegram chat_id 获取用户"""
    binding = await get_binding_by_chat_id(session, chat_id)
    if not binding:
        return None
    
    result = await session.execute(
        select(User).where(User.id == binding.user_id)
    )
    return result.scalar_one_or_none()
