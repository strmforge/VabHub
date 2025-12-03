"""
用户通知渠道服务
NOTIFY-CORE 实现
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.models.user_notify_channel import UserNotifyChannel
from app.models.enums.user_notify_channel_type import UserNotifyChannelType
from app.schemas.user_notify_channel import UserNotifyChannelCreate, UserNotifyChannelUpdate


# ============== CRUD 操作 ==============

async def list_channels_for_user(
    session: AsyncSession,
    user: User,
) -> list[UserNotifyChannel]:
    """获取用户的所有通知渠道"""
    result = await session.execute(
        select(UserNotifyChannel)
        .where(UserNotifyChannel.user_id == user.id)
        .order_by(UserNotifyChannel.created_at.desc())
    )
    return list(result.scalars().all())


async def get_channel_by_id(
    session: AsyncSession,
    channel_id: int,
) -> Optional[UserNotifyChannel]:
    """获取单个渠道"""
    result = await session.execute(
        select(UserNotifyChannel).where(UserNotifyChannel.id == channel_id)
    )
    return result.scalar_one_or_none()


async def get_channel_for_user(
    session: AsyncSession,
    user: User,
    channel_id: int,
) -> Optional[UserNotifyChannel]:
    """获取用户的单个渠道（验证归属）"""
    result = await session.execute(
        select(UserNotifyChannel).where(
            UserNotifyChannel.id == channel_id,
            UserNotifyChannel.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def create_channel_for_user(
    session: AsyncSession,
    user: User,
    data: UserNotifyChannelCreate,
) -> UserNotifyChannel:
    """为用户创建通知渠道"""
    channel = UserNotifyChannel(
        user_id=user.id,
        channel_type=data.channel_type,
        display_name=data.display_name,
        config=data.config,
        is_enabled=data.is_enabled,
        is_verified=False,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    logger.info(f"[user-notify] created channel for user {user.id}: {channel.channel_type}")
    return channel


async def update_channel_for_user(
    session: AsyncSession,
    user: User,
    channel_id: int,
    data: UserNotifyChannelUpdate,
) -> Optional[UserNotifyChannel]:
    """更新用户的通知渠道"""
    channel = await get_channel_for_user(session, user, channel_id)
    if not channel:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)

    await session.commit()
    await session.refresh(channel)
    logger.info(f"[user-notify] updated channel {channel_id} for user {user.id}")
    return channel


async def delete_channel_for_user(
    session: AsyncSession,
    user: User,
    channel_id: int,
) -> bool:
    """删除用户的通知渠道"""
    channel = await get_channel_for_user(session, user, channel_id)
    if not channel:
        return False

    await session.delete(channel)
    await session.commit()
    logger.info(f"[user-notify] deleted channel {channel_id} for user {user.id}")
    return True


# ============== 测试渠道 ==============

async def test_channel(
    session: AsyncSession,
    channel: UserNotifyChannel,
) -> bool:
    """
    测试通知渠道
    
    调用适配器发送测试消息，更新 last_test_* 字段。
    不抛异常，出错返回 False。
    """
    from app.modules.user_notify_channels import send_user_channel_message
    
    try:
        success = await send_user_channel_message(
            channel,
            title="VabHub 测试通知",
            message="如果你收到这条消息，说明通知渠道配置成功！✅",
        )
        
        channel.last_test_at = datetime.utcnow()
        channel.last_test_ok = success
        channel.last_error = None if success else "发送失败"
        
        if success:
            channel.is_verified = True
        
        await session.commit()
        return success
        
    except Exception as e:
        logger.error(f"[user-notify] test channel {channel.id} failed: {e}")
        
        channel.last_test_at = datetime.utcnow()
        channel.last_test_ok = False
        channel.last_error = str(e)[:500]
        
        await session.commit()
        return False


# ============== 按用户获取启用的渠道 ==============

async def get_enabled_channels_for_user(
    session: AsyncSession,
    user_id: int,
) -> list[UserNotifyChannel]:
    """获取用户所有启用的通知渠道"""
    result = await session.execute(
        select(UserNotifyChannel).where(
            UserNotifyChannel.user_id == user_id,
            UserNotifyChannel.is_enabled == True,
        )
    )
    return list(result.scalars().all())


async def get_telegram_channel_by_chat_id(
    session: AsyncSession,
    chat_id: int,
) -> Optional[UserNotifyChannel]:
    """根据 Telegram chat_id 查找渠道"""
    # 需要搜索 config JSON 中的 chat_id
    result = await session.execute(
        select(UserNotifyChannel).where(
            UserNotifyChannel.channel_type == UserNotifyChannelType.TELEGRAM_BOT,
        )
    )
    channels = result.scalars().all()
    
    for channel in channels:
        if channel.config.get("chat_id") == chat_id:
            return channel
    
    return None
