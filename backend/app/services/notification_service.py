"""
用户通知服务
PLUGIN-SDK-1 扩展：EventBus 事件发布
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.models.user_notification import UserNotification
from app.schemas.user_notification import UserNotificationCreate
from app.models.enums.notification_type import NotificationType
from app.models.enums.reading_media_type import ReadingMediaType
from app.models.user_favorite_media import UserFavoriteMedia


class NotificationService:
    """通知服务类"""

    @staticmethod
    async def list_notifications(
        session: AsyncSession,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[UserNotification], int, int]:
        """
        获取用户通知列表
        
        Args:
            session: 数据库会话
            user_id: 用户ID
            is_read: 是否已读筛选
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            (通知列表, 总数, 未读数量)
        """
        # 构建查询条件
        conditions = [UserNotification.user_id == user_id]
        if is_read is not None:
            conditions.append(UserNotification.is_read == is_read)
        
        # 获取通知列表
        stmt = (
            select(UserNotification)
            .where(*conditions)
            .order_by(UserNotification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        notifications = result.scalars().all()
        
        # 获取总数
        count_stmt = (
            select(func.count(UserNotification.id))
            .where(*conditions)
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()
        
        # 获取未读数量
        unread_stmt = (
            select(func.count(UserNotification.id))
            .where(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False
            )
        )
        unread_result = await session.execute(unread_stmt)
        unread_count = unread_result.scalar_one()
        
        return notifications, total, unread_count

    @staticmethod
    async def create_notification(
        session: AsyncSession,
        notification_data: UserNotificationCreate
    ) -> UserNotification:
        """
        创建通知
        
        Args:
            session: 数据库会话
            notification_data: 通知数据
            
        Returns:
            创建的通知对象
        """
        notification = UserNotification(**notification_data.dict())
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification

    @staticmethod
    async def mark_notification_read(
        session: AsyncSession,
        user_id: int,
        notification_id: int
    ) -> bool:
        """
        标记通知为已读
        
        Args:
            session: 数据库会话
            user_id: 用户ID
            notification_id: 通知ID
            
        Returns:
            是否成功标记
        """
        from datetime import datetime
        
        stmt = (
            update(UserNotification)
            .where(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
                UserNotification.is_read == False
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount > 0

    @staticmethod
    async def mark_all_read(
        session: AsyncSession,
        user_id: int
    ) -> int:
        """
        标记所有通知为已读
        
        Args:
            session: 数据库会话
            user_id: 用户ID
            
        Returns:
            更新的通知数量
        """
        from datetime import datetime
        
        stmt = (
            update(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount


# 兼容性函数别名
list_notifications = NotificationService.list_notifications
mark_notification_read = NotificationService.mark_notification_read
mark_all_read = NotificationService.mark_all_read


async def get_user_ids_for_manga_series(
    session: AsyncSession,
    series_id: int
) -> List[int]:
    """
    获取收藏了特定漫画系列的用户ID列表
    
    Args:
        session: 数据库会话
        series_id: 漫画系列ID
        
    Returns:
        用户ID列表
    """
    stmt = select(UserFavoriteMedia.user_id).where(
        UserFavoriteMedia.media_type == ReadingMediaType.MANGA,
        UserFavoriteMedia.target_id == series_id
    )
    
    result = await session.execute(stmt)
    user_ids = result.scalars().all()
    
    return list(user_ids)


# TTS专用的helper方法
async def notify_tts_job_completed(
    session: AsyncSession,
    *,
    user_id: int,
    job_id: int,
    ebook_id: int,
    ebook_title: str,
    audiobook_id: Optional[int] = None
) -> UserNotification:
    """
    TTS 任务完成时调用：为 user 创建一条 TTS_JOB_COMPLETED + AUDIOBOOK_READY 类型的通知。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        job_id: TTS任务ID
        ebook_id: 电子书ID
        ebook_title: 电子书标题
        audiobook_id: 有声书ID（可选）
        
    Returns:
        创建的通知对象
    """
    title = f"有声书《{ebook_title}》已生成"
    message = "TTS 任务已完成，可以开始收听。"
    payload = {
        "route_name": "AudiobookDetail",
        "route_params": {"audiobook_id": audiobook_id or ebook_id},
        "job_id": job_id,
        "ebook_id": ebook_id,
    }
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.TTS_JOB_COMPLETED,
        media_type=ReadingMediaType.AUDIOBOOK,
        target_id=audiobook_id or ebook_id,
        sub_target_id=job_id,
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # NOTIFY-CORE: 推送到外部渠道
    try:
        from app.services.notify_user_service import notify_user_by_id
        await notify_user_by_id(
            session,
            user_id,
            title=title,
            message=message,
            event_type=NotificationType.TTS_JOB_COMPLETED,
            media_type="audiobook",
            target_id=audiobook_id or ebook_id,
            payload=payload,
            skip_web=True,
        )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push TTS completed to external: {e}")
    
    # PLUGIN-SDK-1: 发布事件到 EventBus
    try:
        from app.plugin_sdk.events import publish_event, EventType
        await publish_event(
            EventType.AUDIOBOOK_TTS_FINISHED,
            {
                "job_id": job_id,
                "ebook_id": ebook_id,
                "ebook_title": ebook_title,
                "audiobook_id": audiobook_id,
                "user_id": user_id,
            },
            source="notification_service"
        )
    except Exception as e:
        from loguru import logger
        logger.debug(f"[notify] event bus publish error (non-critical): {e}")
    
    return notification


# 漫画更新专用的helper方法
async def notify_manga_updated(
    session: AsyncSession,
    *,
    user_id: int,
    series_id: int,
    series_title: str,
    new_chapters: int,
    latest_chapter_id: Optional[int] = None
) -> UserNotification:
    """
    漫画更新时调用：为 user 创建一条 MANGA_UPDATED 类型的通知。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        series_id: 漫画系列ID
        series_title: 漫画系列标题
        new_chapters: 新章节数量
        latest_chapter_id: 最新章节ID（可选）
        
    Returns:
        创建的通知对象
    """
    title = f"《{series_title}》更新了 {new_chapters} 话"
    message = f"漫画系列有新章节更新，快去看看吧！"
    
    payload = {
        "route_name": "MangaReader",
        "route_params": {
            "series_id": series_id,
            "chapter_id": latest_chapter_id
        },
        "series_id": series_id,
        "new_chapters": new_chapters,
        "latest_chapter_id": latest_chapter_id
    }
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.MANGA_UPDATED,
        media_type=ReadingMediaType.MANGA,
        target_id=series_id,
        sub_target_id=latest_chapter_id,
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # NOTIFY-CORE: 推送到外部渠道
    try:
        from app.services.notify_user_service import notify_user_by_id
        await notify_user_by_id(
            session,
            user_id,
            title=title,
            message=message,
            event_type=NotificationType.MANGA_UPDATED,
            media_type="manga",
            target_id=series_id,
            payload=payload,
            skip_web=True,  # 已经写入了
        )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push manga update to external: {e}")
    
    # PLUGIN-SDK-1: 发布事件到 EventBus
    try:
        from app.plugin_sdk.events import publish_event, EventType
        await publish_event(
            EventType.MANGA_UPDATED,
            {
                "series_id": series_id,
                "series_title": series_title,
                "new_chapters": new_chapters,
                "latest_chapter_id": latest_chapter_id,
                "user_id": user_id,
            },
            source="notification_service"
        )
    except Exception as e:
        from loguru import logger
        logger.debug(f"[notify] event bus publish error (non-critical): {e}")
    
    return notification


async def notify_manga_sync_failed(
    session: AsyncSession,
    *,
    user_id: int,
    series_id: int,
    series_title: str,
    error_message: str
) -> UserNotification:
    """
    漫画同步失败时调用：为 user 创建一条 MANGA_SYNC_FAILED 类型的通知。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        series_id: 漫画系列ID
        series_title: 漫画系列标题
        error_message: 错误信息
        
    Returns:
        创建的通知对象
    """
    title = f"《{series_title}》同步失败"
    message = f"漫画同步失败：{error_message}"
    
    payload = {
        "route_name": "MangaDetail",
        "route_params": {"series_id": series_id},
        "series_id": series_id,
        "error_message": error_message
    }
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.MANGA_SYNC_FAILED,
        media_type=ReadingMediaType.MANGA,
        target_id=series_id,
        title=title,
        message=message,
        payload=payload,
    )
    
    return await NotificationService.create_notification(session, notification_data)


async def notify_tts_job_failed(
    session: AsyncSession,
    *,
    user_id: int,
    job_id: int,
    ebook_id: int,
    ebook_title: Optional[str] = None,
    error_message: Optional[str] = None
) -> UserNotification:
    """
    TTS 任务失败时调用：为 user 创建一条 TTS_JOB_FAILED 通知。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        job_id: TTS任务ID
        ebook_id: 电子书ID
        ebook_title: 电子书标题（可选）
        error_message: 错误信息（可选）
        
    Returns:
        创建的通知对象
    """
    title = "有声书 TTS 任务失败"
    if ebook_title:
        title = f"有声书《{ebook_title}》生成失败"

    message = error_message or "TTS 任务执行失败，请查看任务详情日志。"

    payload = {
        "route_name": "AudiobookDetail",  # 先指向有声书详情页
        "route_params": {"audiobook_id": ebook_id},
        "job_id": job_id,
        "ebook_id": ebook_id,
        "extra": {"error_message": error_message},
    }

    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.TTS_JOB_FAILED,
        media_type=ReadingMediaType.AUDIOBOOK,
        target_id=ebook_id,
        sub_target_id=job_id,
        title=title,
        message=message,
        payload=payload,
    )

    return await NotificationService.create_notification(session, notification_data)


# 有声书专用的helper方法
async def notify_audiobook_ready(
    session: AsyncSession,
    *,
    user_id: int,
    audiobook_id: int,
    audiobook_title: str,
    source_type: str = "tts"  # "tts" | "import" | "download"
) -> UserNotification:
    """
    有声书就绪时调用：为 user 创建一条 AUDIOBOOK_READY 类型的通知。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        audiobook_id: 有声书ID
        audiobook_title: 有声书标题
        source_type: 来源类型（"tts" | "import" | "download"）
        
    Returns:
        创建的通知对象
    """
    # 根据来源类型构建不同的消息
    if source_type == "tts":
        title = f"有声书《{audiobook_title}》已生成"
        message = "TTS 任务已完成，可以开始收听。"
    elif source_type == "import":
        title = f"有声书《{audiobook_title}》已导入"
        message = "有声书文件已成功导入到媒体库。"
    elif source_type == "download":
        title = f"有声书《{audiobook_title}》下载完成"
        message = "有声书文件已下载完成，可以开始收听。"
    else:
        title = f"有声书《{audiobook_title}》已就绪"
        message = "有声书已准备就绪，可以开始收听。"
    
    payload = {
        "route_name": "AudiobookDetail",
        "route_params": {"audiobook_id": audiobook_id},
        "source_type": source_type,
    }
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.AUDIOBOOK_READY,
        media_type=ReadingMediaType.AUDIOBOOK,
        target_id=audiobook_id,
        title=title,
        message=message,
        payload=payload,
    )
    
    # PLUGIN-SDK-1: 发布事件到 EventBus
    notification = await NotificationService.create_notification(session, notification_data)
    
    try:
        from app.plugin_sdk.events import publish_event, EventType
        await publish_event(
            EventType.AUDIOBOOK_READY,
            {
                "audiobook_id": audiobook_id,
                "audiobook_title": audiobook_title,
                "source_type": source_type,
                "user_id": user_id,
            },
            source="notification_service"
        )
    except Exception as e:
        from loguru import logger
        logger.debug(f"[notify] event bus publish error (non-critical): {e}")
    
    return notification


async def create_notifications_for_users(
    session: AsyncSession,
    user_ids: List[int],
    type: NotificationType,
    media_type: Optional[str] = None,
    target_id: Optional[int] = None,
    title: str = "",
    message: str = "",
    payload: Optional[Dict[str, Any]] = None
) -> List[UserNotification]:
    """
    为多个用户创建通知
    
    Args:
        session: 数据库会话
        user_ids: 用户ID列表
        type: 通知类型
        media_type: 媒体类型
        target_id: 目标ID
        title: 通知标题
        message: 通知内容
        payload: 额外数据
        
    Returns:
        创建的通知列表
    """
    notifications = []
    for user_id in user_ids:
        notification_data = UserNotificationCreate(
            user_id=user_id,
            type=type,
            media_type=media_type,
            target_id=target_id,
            title=title,
            message=message,
            payload=payload,
        )
        notification = await NotificationService.create_notification(session, notification_data)
        notifications.append(notification)
    
    return notifications


# 阅读通知统一 Helper 方法
async def notify_manga_updated_for_user(
    session: AsyncSession,
    *,
    user_id: int,
    payload: dict,
) -> UserNotification:
    """
    漫画更新通知的统一入口，使用标准化的 payload 结构。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        payload: MangaUpdatedPayload 序列化后的字典
        
    Returns:
        创建的通知对象
    """
    title = f"《{payload['title']}》更新了 {payload['total_new_count']} 话"
    message = f"你追更的漫画有新章节更新，快去看看吧！"
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.MANGA_UPDATED,
        media_type=ReadingMediaType.MANGA,
        target_id=payload['series_id'],
        sub_target_id=payload.get('latest_chapter_id'),
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # 推送到外部渠道（TG 等）
    try:
        from app.services.notify_user_service import notify_user_by_id
        await notify_user_by_id(
            session,
            user_id,
            title=title,
            message=message,
            event_type=NotificationType.MANGA_UPDATED,
            media_type="manga",
            target_id=payload['series_id'],
            payload=payload,
            skip_web=True,  # 已经写入了
        )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push manga update to external: {e}")
    
    return notification


async def notify_ebook_imported(
    session: AsyncSession,
    *,
    user_id: int,
    payload: dict,
) -> UserNotification:
    """
    电子书导入完成通知。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        payload: EbookImportedPayload 序列化后的字典
        
    Returns:
        创建的通知对象
    """
    title = f"《{payload['title']}》已就绪"
    message = "新电子书已导入，可以开始阅读了！"
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.READING_EBOOK_IMPORTED,
        media_type=ReadingMediaType.NOVEL,
        target_id=payload['ebook_id'],
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # 推送到外部渠道（TG 等）
    try:
        from app.services.notify_user_service import notify_user_by_id
        await notify_user_by_id(
            session,
            user_id,
            title=title,
            message=message,
            event_type=NotificationType.READING_EBOOK_IMPORTED,
            media_type="novel",
            target_id=payload['ebook_id'],
            payload=payload,
            skip_web=True,  # 已经写入了
        )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push ebook imported to external: {e}")
    
    return notification


async def notify_audiobook_ready_for_user(
    session: AsyncSession,
    *,
    user_id: int,
    payload: dict,
) -> UserNotification:
    """
    有声书就绪通知的统一入口，使用标准化的 payload 结构。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        payload: AudiobookReadyPayload 序列化后的字典
        
    Returns:
        创建的通知对象
    """
    title = f"《{payload['title']}》有声书已生成"
    message = "有声书已生成完成，可以开始收听了！"
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.AUDIOBOOK_READY,
        media_type=ReadingMediaType.AUDIOBOOK,
        target_id=payload['audiobook_id'],
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # 推送到外部渠道（TG 等）
    try:
        from app.services.notify_user_service import notify_user_by_id
        await notify_user_by_id(
            session,
            user_id,
            title=title,
            message=message,
            event_type=NotificationType.AUDIOBOOK_READY,
            media_type="audiobook",
            target_id=payload['audiobook_id'],
            payload=payload,
            skip_web=True,  # 已经写入了
        )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push audiobook ready to external: {e}")
    
    return notification


# 下载通知统一 Helper 方法
async def notify_download_subscription_matched_for_user(
    session: AsyncSession,
    *,
    user_id: int,
    payload: dict,
) -> UserNotification:
    """
    订阅命中通知的统一入口，使用标准化的 payload 结构。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        payload: DownloadSubscriptionMatchedPayload 序列化后的字典
        
    Returns:
        创建的通知对象
    """
    title = f"订阅命中：{payload['title']}"
    message = f"订阅规则「{payload['subscription_name']}」已为你创建下载任务"
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.DOWNLOAD_SUBSCRIPTION_MATCHED,
        media_type=None,  # 下载通知跨媒体类型，不指定具体类型
        target_id=payload.get('task_id') or payload.get('torrent_id'),
        sub_target_id=payload.get('subscription_id'),
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # 推送到外部渠道（TG 等）- 基于环境变量控制
    try:
        from app.services.notify_user_service import notify_user_by_id
        from app.core.config import get_settings
        settings = get_settings()
        
        if settings.NOTIFY_TELEGRAM_DOWNLOAD_SUBSCRIPTION:
            await notify_user_by_id(
                session,
                user_id,
                title=title,
                message=message,
                event_type=NotificationType.DOWNLOAD_SUBSCRIPTION_MATCHED,
                media_type="download",
                target_id=payload.get('task_id'),
                payload=payload,
                skip_web=True,  # 已经写入了
            )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push download subscription matched to external: {e}")
    
    return notification


async def notify_download_task_completed_for_user(
    session: AsyncSession,
    *,
    user_id: int,
    payload: dict,
) -> UserNotification:
    """
    下载任务完成通知的统一入口，使用标准化的 payload 结构。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        payload: DownloadTaskCompletedPayload 序列化后的字典
        
    Returns:
        创建的通知对象
    """
    success = payload.get('success', False)
    if success:
        title = f"下载完成：{payload['title']}"
        message = "下载任务已完成并成功入库到媒体库"
    else:
        title = f"下载完成：{payload['title']}"
        message = "下载任务已完成，但入库失败，请检查日志"
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.DOWNLOAD_TASK_COMPLETED,
        media_type=None,  # 下载通知跨媒体类型，不指定具体类型
        target_id=payload.get('task_id'),
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # 推送到外部渠道（TG 等）- 基于环境变量控制
    try:
        from app.services.notify_user_service import notify_user_by_id
        from app.core.config import get_settings
        settings = get_settings()
        
        if settings.NOTIFY_TELEGRAM_DOWNLOAD_COMPLETION:
            await notify_user_by_id(
                session,
                user_id,
                title=title,
                message=message,
                event_type=NotificationType.DOWNLOAD_TASK_COMPLETED,
                media_type="download",
                target_id=payload.get('task_id'),
                payload=payload,
                skip_web=True,  # 已经写入了
            )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push download task completed to external: {e}")
    
    return notification


async def notify_download_hr_risk_for_user(
    session: AsyncSession,
    *,
    user_id: int,
    payload: dict,
) -> UserNotification:
    """
    HR 风险预警通知的统一入口，使用标准化的 payload 结构。
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        payload: DownloadHrRiskPayload 序列化后的字典
        
    Returns:
        创建的通知对象
    """
    risk_level = payload.get('risk_level', 'WARN')
    title = f"HR 风险提醒：{payload['title']}"
    
    # 根据风险等级构建不同的消息
    if risk_level == 'H&R':
        message = f"站点标记为 H&R，请避免删除原始数据并保持做种"
    elif risk_level == 'HR':
        message = f"需要保种 {payload.get('min_seed_time_hours', 72)} 小时，请勿删除原始数据"
    elif risk_level in ['H3', 'H5']:
        message = f"站点特殊要求（{risk_level}），请查看具体保种规则"
    else:
        message = f"下载任务存在保种要求，请注意及时处理"
    
    if payload.get('reason'):
        message += f"\n原因：{payload['reason']}"
    
    notification_data = UserNotificationCreate(
        user_id=user_id,
        type=NotificationType.DOWNLOAD_HR_RISK,
        media_type=None,  # 下载通知跨媒体类型，不指定具体类型
        target_id=payload.get('task_id'),
        title=title,
        message=message,
        payload=payload,
    )
    
    notification = await NotificationService.create_notification(session, notification_data)
    
    # 推送到外部渠道（TG 等）- 基于环境变量控制
    try:
        from app.services.notify_user_service import notify_user_by_id
        from app.core.config import get_settings
        settings = get_settings()
        
        if settings.NOTIFY_TELEGRAM_DOWNLOAD_HR_RISK:
            await notify_user_by_id(
                session,
                user_id,
                title=title,
                message=message,
                event_type=NotificationType.DOWNLOAD_HR_RISK,
                media_type="download",
                target_id=payload.get('task_id'),
                payload=payload,
                skip_web=True,  # 已经写入了
            )
    except Exception as e:
        from loguru import logger
        logger.warning(f"[notify] failed to push download HR risk to external: {e}")
    
    return notification
