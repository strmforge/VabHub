"""
统一用户通知总线
NOTIFY-CORE 实现（含 NOTIFY-UX-1 偏好支持）

所有用户级通知都通过这个服务发送：
1. 评估用户偏好（静音/Snooze/渠道开关）
2. 写入 UserNotification 表（Web 通知列表）
3. 推送到用户配置的外部渠道（Telegram/Webhook/Bark）
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.models.user_notification import UserNotification
from app.models.enums.notification_type import NotificationType
from app.models.enums.alert_severity import AlertSeverity
from app.models.enums.reading_media_type import ReadingMediaType
from app.models.enums.user_notify_channel_type import UserNotifyChannelType
from app.schemas.user_notification import UserNotificationCreate
from app.services.user_notify_channel_service import get_enabled_channels_for_user
from app.modules.user_notify_channels import send_user_channel_message


async def notify_user(
    session: AsyncSession,
    user: User,
    *,
    title: str,
    message: str,
    level: Optional[AlertSeverity] = None,
    url: Optional[str] = None,
    event_type: Optional[NotificationType] = None,
    media_type: Optional[str] = None,
    target_id: Optional[int] = None,
    payload: Optional[dict[str, Any]] = None,
    skip_web: bool = False,
    skip_external: bool = False,
    actions: Optional[list[dict[str, Any]]] = None,
) -> None:
    """
    统一用户通知入口
    
    Args:
        session: 数据库会话
        user: 目标用户
        title: 通知标题
        message: 通知内容
        level: 告警级别（可选，用于某些场景）
        url: 相关链接（可选）
        event_type: 通知类型（用于写入 Web 通知）
        media_type: 媒体类型（可选，ReadingMediaType 字符串）
        target_id: 目标资源 ID（可选）
        payload: 额外数据（可选）
        skip_web: 是否跳过 Web 通知
        skip_external: 是否跳过外部渠道
        actions: 操作按钮列表（用于 Telegram 等渠道）
    """
    # 0. 评估用户偏好
    from app.services.notify_preference_service import evaluate_notification_delivery
    
    decision = None
    if event_type:
        try:
            # 转换 media_type 字符串为枚举
            reading_media_type = None
            if media_type:
                try:
                    reading_media_type = ReadingMediaType(media_type.upper())
                except (ValueError, AttributeError):
                    pass
            
            decision = await evaluate_notification_delivery(
                session,
                user_id=user.id,
                notification_type=event_type,
                media_type=reading_media_type,
                target_id=target_id,
            )
            
            if decision.reason:
                logger.debug(f"[notify-user] delivery decision for user {user.id}: {decision.reason}")
        except Exception as e:
            logger.warning(f"[notify-user] failed to evaluate delivery: {e}")
            # 评估失败时使用默认行为（全部允许）
    
    # 1. 写入 Web 通知（UserNotification 表）
    should_store = decision.store_in_user_notification if decision else True
    should_send_web = decision.allowed_web if decision else True
    
    if not skip_web and should_store:
        try:
            notification = UserNotification(
                user_id=user.id,
                type=event_type.value if event_type else "SYSTEM_MESSAGE",
                media_type=media_type,
                target_id=target_id,
                title=title,
                message=message,
                payload=payload,
            )
            session.add(notification)
            await session.flush()
            logger.debug(f"[notify-user] created web notification for user {user.id}")
        except Exception as e:
            logger.warning(f"[notify-user] failed to create web notification: {e}")
    
    # 2. 推送到外部渠道（基于用户偏好）
    if not skip_external:
        try:
            channels = await get_enabled_channels_for_user(session, user.id)
            
            if channels:
                success_count = 0
                for channel in channels:
                    # 检查该渠道是否被用户偏好允许
                    if decision:
                        channel_allowed = _is_channel_allowed(channel.channel_type, decision)
                        if not channel_allowed:
                            logger.debug(f"[notify-user] skipped channel {channel.id} due to user preference")
                            continue
                    
                    try:
                        ok = await send_user_channel_message(
                            channel,
                            message=message,
                            title=title,
                            url=url,
                            extra=payload,
                            actions=actions,
                        )
                        if ok:
                            success_count += 1
                    except Exception as e:
                        logger.warning(f"[notify-user] send to channel {channel.id} failed: {e}")
                
                logger.info(f"[notify-user] sent to {success_count}/{len(channels)} channels for user {user.id}")
        except Exception as e:
            logger.warning(f"[notify-user] failed to send to external channels: {e}")


def _is_channel_allowed(
    channel_type: UserNotifyChannelType,
    decision: "NotificationDeliveryDecision",
) -> bool:
    """检查某渠道是否被用户偏好允许"""
    from app.schemas.notify_preferences import NotificationDeliveryDecision
    
    match channel_type:
        case UserNotifyChannelType.TELEGRAM_BOT:
            return decision.allowed_telegram
        case UserNotifyChannelType.WEBHOOK:
            return decision.allowed_webhook
        case UserNotifyChannelType.BARK:
            return decision.allowed_bark
        case _:
            # 未知渠道类型，默认允许
            return True


async def notify_user_by_id(
    session: AsyncSession,
    user_id: int,
    *,
    title: str,
    message: str,
    **kwargs,
) -> None:
    """
    通过用户 ID 发送通知（不需要加载完整 User 对象）
    """
    from app.models.user import User
    from sqlalchemy import select
    
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        await notify_user(session, user, title=title, message=message, **kwargs)
    else:
        logger.warning(f"[notify-user] user {user_id} not found")


async def notify_users(
    session: AsyncSession,
    user_ids: list[int],
    *,
    title: str,
    message: str,
    **kwargs,
) -> None:
    """
    向多个用户发送通知
    """
    for user_id in user_ids:
        await notify_user_by_id(session, user_id, title=title, message=message, **kwargs)
