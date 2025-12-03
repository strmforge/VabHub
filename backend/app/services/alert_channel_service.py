"""
告警渠道服务
OPS-2A 实现
"""

import fnmatch
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.alert_channel import AlertChannel
from app.models.enums.alert_channel_type import AlertChannelType
from app.models.enums.alert_severity import AlertSeverity
from app.schemas.alert_channel import AlertChannelCreate, AlertChannelUpdate
from app.modules.alert_channels import get_alert_channel_adapter


# ============== CRUD 操作 ==============

async def list_channels(session: AsyncSession) -> list[AlertChannel]:
    """获取所有告警渠道"""
    result = await session.execute(select(AlertChannel).order_by(AlertChannel.id))
    return list(result.scalars().all())


async def get_channel(session: AsyncSession, channel_id: int) -> Optional[AlertChannel]:
    """获取单个告警渠道"""
    result = await session.execute(
        select(AlertChannel).where(AlertChannel.id == channel_id)
    )
    return result.scalar_one_or_none()


async def create_channel(
    session: AsyncSession,
    data: AlertChannelCreate,
) -> AlertChannel:
    """创建告警渠道"""
    channel = AlertChannel(
        name=data.name,
        channel_type=data.channel_type,
        is_enabled=data.is_enabled,
        min_severity=data.min_severity,
        config=data.config,
        include_checks=data.include_checks,
        exclude_checks=data.exclude_checks,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    logger.info(f"[alert-channel] created channel: {channel.name} ({channel.channel_type})")
    return channel


async def update_channel(
    session: AsyncSession,
    channel_id: int,
    data: AlertChannelUpdate,
) -> Optional[AlertChannel]:
    """更新告警渠道"""
    channel = await get_channel(session, channel_id)
    if not channel:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)

    await session.commit()
    await session.refresh(channel)
    logger.info(f"[alert-channel] updated channel: {channel.name}")
    return channel


async def delete_channel(session: AsyncSession, channel_id: int) -> bool:
    """删除告警渠道"""
    channel = await get_channel(session, channel_id)
    if not channel:
        return False

    await session.delete(channel)
    await session.commit()
    logger.info(f"[alert-channel] deleted channel: {channel.name}")
    return True


# ============== 路由匹配 ==============

def _severity_level(severity: AlertSeverity) -> int:
    """获取严重级别的数值（用于比较）"""
    levels = {
        AlertSeverity.INFO: 0,
        AlertSeverity.WARNING: 1,
        AlertSeverity.ERROR: 2,
    }
    return levels.get(severity, 0)


def _match_check_key(pattern: str, check_key: str) -> bool:
    """匹配检查项 key（支持通配符）"""
    # 支持 disk.* 这种前缀匹配
    return fnmatch.fnmatch(check_key, pattern)


def _should_send_to_channel(
    channel: AlertChannel,
    check_key: str,
    severity: AlertSeverity,
) -> bool:
    """判断是否应该发送到该渠道"""
    # 1. 检查是否启用
    if not channel.is_enabled:
        return False

    # 2. 检查严重级别
    if _severity_level(severity) < _severity_level(channel.min_severity):
        return False

    # 3. 检查白名单
    if channel.include_checks:
        matched = any(_match_check_key(p, check_key) for p in channel.include_checks)
        if not matched:
            return False

    # 4. 检查黑名单
    if channel.exclude_checks:
        excluded = any(_match_check_key(p, check_key) for p in channel.exclude_checks)
        if excluded:
            return False

    return True


async def get_active_channels_for_check(
    session: AsyncSession,
    check_key: str,
    severity: AlertSeverity,
) -> list[AlertChannel]:
    """
    获取应该发送告警的渠道列表
    
    Args:
        session: 数据库会话
        check_key: 检查项 key（如 "db.default"、"disk.data"）
        severity: 告警严重级别
        
    Returns:
        符合条件的渠道列表
    """
    channels = await list_channels(session)
    return [c for c in channels if _should_send_to_channel(c, check_key, severity)]


# ============== 发送告警 ==============

async def send_alert_to_channel(
    channel: AlertChannel,
    title: str,
    body: str,
) -> bool:
    """
    向单个渠道发送告警
    
    Returns:
        是否发送成功
    """
    try:
        adapter = get_alert_channel_adapter(channel)
        await adapter.send(title, body)
        return True
    except Exception as e:
        logger.error(f"[alert-channel] failed to send to {channel.name}: {e}")
        return False


async def send_test_message(
    session: AsyncSession,
    channel_id: int,
    message: Optional[str] = None,
) -> bool:
    """
    发送测试消息
    
    Args:
        session: 数据库会话
        channel_id: 渠道 ID
        message: 自定义消息（可选）
        
    Returns:
        是否发送成功
    """
    channel = await get_channel(session, channel_id)
    if not channel:
        return False

    title = "VabHub 测试告警"
    body = message or "如果你看到这条消息，说明告警渠道配置成功！✅"

    return await send_alert_to_channel(channel, title, body)


async def broadcast_alert(
    session: AsyncSession,
    check_key: str,
    severity: AlertSeverity,
    title: str,
    body: str,
) -> int:
    """
    广播告警到所有符合条件的渠道
    
    Returns:
        成功发送的渠道数量
    """
    channels = await get_active_channels_for_check(session, check_key, severity)
    
    if not channels:
        logger.debug(f"[alert-channel] no channels matched for {check_key} ({severity})")
        return 0

    success_count = 0
    for channel in channels:
        if await send_alert_to_channel(channel, title, body):
            success_count += 1

    logger.info(f"[alert-channel] broadcast alert to {success_count}/{len(channels)} channels")
    return success_count
