"""
音乐通知服务

发送音乐相关的用户通知。
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user_notification import UserNotification
from app.models.enums.notification_type import NotificationType


async def notify_music_chart_updated(
    session: AsyncSession,
    user_ids: List[int],
    chart_id: int,
    chart_name: str,
    new_count: int,
    subscription_id: Optional[int] = None,
):
    """
    发送音乐榜单更新通知
    
    Args:
        session: 数据库会话
        user_ids: 接收通知的用户 ID 列表
        chart_id: 榜单 ID
        chart_name: 榜单名称
        new_count: 新增曲目数
        subscription_id: 关联的订阅 ID（可选）
    """
    if not user_ids:
        return
    
    for user_id in user_ids:
        notification = UserNotification(
            user_id=user_id,
            type=NotificationType.MUSIC_CHART_UPDATED.value,
            media_type="music",
            target_id=chart_id,
            title=f"榜单更新: {chart_name}",
            message=f"榜单 {chart_name} 新增 {new_count} 首曲目",
            payload={
                "route_name": "MusicCenter",
                "route_params": {"tab": "charts"},
                "chart_id": chart_id,
                "new_count": new_count,
                "subscription_id": subscription_id,
            },
        )
        session.add(notification)
    
    await session.commit()
    logger.info(f"已发送榜单更新通知给 {len(user_ids)} 个用户")


async def notify_music_new_tracks_queued(
    session: AsyncSession,
    user_ids: List[int],
    chart_id: int,
    chart_name: str,
    track_count: int,
    subscription_id: Optional[int] = None,
):
    """
    发送新音乐任务已排队通知
    
    Args:
        session: 数据库会话
        user_ids: 接收通知的用户 ID 列表
        chart_id: 榜单 ID
        chart_name: 榜单名称
        track_count: 排队的曲目数
        subscription_id: 关联的订阅 ID（可选）
    """
    if not user_ids:
        return
    
    for user_id in user_ids:
        notification = UserNotification(
            user_id=user_id,
            type=NotificationType.MUSIC_NEW_TRACKS_QUEUED.value,
            media_type="music",
            target_id=chart_id,
            title=f"新音乐任务已排队",
            message=f"来自 {chart_name} 的 {track_count} 首曲目已加入搜索队列",
            payload={
                "route_name": "MusicCenter",
                "route_params": {"tab": "tasks"},
                "chart_id": chart_id,
                "track_count": track_count,
                "subscription_id": subscription_id,
            },
        )
        session.add(notification)
    
    await session.commit()
    logger.info(f"已发送新音乐任务通知给 {len(user_ids)} 个用户")


async def notify_music_new_tracks_ready(
    session: AsyncSession,
    user_ids: List[int],
    chart_id: int,
    chart_name: str,
    track_titles: List[str],
    subscription_id: Optional[int] = None,
):
    """
    发送新音乐已就绪通知
    
    Args:
        session: 数据库会话
        user_ids: 接收通知的用户 ID 列表
        chart_id: 榜单 ID
        chart_name: 榜单名称
        track_titles: 已就绪的曲目标题列表
        subscription_id: 关联的订阅 ID（可选）
    """
    if not user_ids:
        return
    
    track_count = len(track_titles)
    tracks_preview = ", ".join(track_titles[:3])
    if track_count > 3:
        tracks_preview += f" 等 {track_count} 首"
    
    for user_id in user_ids:
        notification = UserNotification(
            user_id=user_id,
            type=NotificationType.MUSIC_NEW_TRACKS_READY.value,
            media_type="music",
            target_id=chart_id,
            title=f"新音乐已就绪",
            message=f"{tracks_preview} 已下载完成",
            payload={
                "route_name": "MusicCenter",
                "route_params": {"tab": "library"},
                "chart_id": chart_id,
                "track_titles": track_titles,
                "subscription_id": subscription_id,
            },
        )
        session.add(notification)
    
    await session.commit()
    logger.info(f"已发送新音乐就绪通知给 {len(user_ids)} 个用户")
