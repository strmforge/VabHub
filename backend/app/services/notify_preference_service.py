"""
通知偏好服务
NOTIFY-UX-1 实现

管理用户通知偏好、静音状态，并提供投递决策
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user_notify_preference import UserNotifyPreference
from app.models.user_notify_snooze import UserNotifySnooze
from app.models.enums.notification_type import NotificationType
from app.models.enums.reading_media_type import ReadingMediaType
from app.schemas.notify_preferences import (
    UserNotifyPreferenceCreate,
    UserNotifyPreferenceUpdate,
    UserNotifyPreferenceRead,
    UserNotifySnoozeRead,
    UserNotifySnoozeUpdate,
    UserNotifyPreferenceMatrix,
    NotificationTypeInfo,
    NotificationDeliveryDecision,
)


# ============== 通知类型元数据 ==============

NOTIFICATION_TYPE_INFO: dict[NotificationType, dict] = {
    # 漫画相关
    NotificationType.MANGA_NEW_CHAPTER: {
        "name": "漫画新章节",
        "description": "追更的漫画有新章节",
        "group": "manga",
        "is_critical": False,
    },
    NotificationType.MANGA_UPDATED: {
        "name": "漫画更新",
        "description": "追更漫画更新通知",
        "group": "manga",
        "is_critical": False,
    },
    NotificationType.MANGA_SYNC_FAILED: {
        "name": "漫画同步失败",
        "description": "漫画同步任务失败",
        "group": "manga",
        "is_critical": False,
    },
    # 小说/有声书相关
    NotificationType.NOVEL_NEW_CHAPTER: {
        "name": "小说新章节",
        "description": "订阅的小说有新章节",
        "group": "novel",
        "is_critical": False,
    },
    NotificationType.AUDIOBOOK_NEW_TRACK: {
        "name": "有声书新音轨",
        "description": "有声书有新章节音轨",
        "group": "novel",
        "is_critical": False,
    },
    NotificationType.TTS_JOB_COMPLETED: {
        "name": "TTS 任务完成",
        "description": "有声书 TTS 转换完成",
        "group": "novel",
        "is_critical": False,
    },
    NotificationType.TTS_JOB_FAILED: {
        "name": "TTS 任务失败",
        "description": "有声书 TTS 转换失败",
        "group": "novel",
        "is_critical": False,
    },
    NotificationType.AUDIOBOOK_READY: {
        "name": "有声书就绪",
        "description": "有声书整体就绪可收听",
        "group": "novel",
        "is_critical": False,
    },
    # 音乐相关
    NotificationType.MUSIC_CHART_UPDATED: {
        "name": "音乐榜单更新",
        "description": "订阅的音乐榜单已更新",
        "group": "music",
        "is_critical": False,
    },
    NotificationType.MUSIC_NEW_TRACKS_QUEUED: {
        "name": "音乐下载排队",
        "description": "新音乐已加入下载队列",
        "group": "music",
        "is_critical": False,
    },
    NotificationType.MUSIC_NEW_TRACKS_DOWNLOADING: {
        "name": "音乐下载中",
        "description": "新音乐正在下载",
        "group": "music",
        "is_critical": False,
    },
    NotificationType.MUSIC_NEW_TRACKS_READY: {
        "name": "音乐就绪",
        "description": "新音乐已下载完成",
        "group": "music",
        "is_critical": False,
    },
    # 下载相关
    NotificationType.DOWNLOAD_SUBSCRIPTION_MATCHED: {
        "name": "订阅命中",
        "description": "订阅规则匹配到新内容并创建下载任务",
        "group": "download",
        "is_critical": False,
    },
    NotificationType.DOWNLOAD_TASK_COMPLETED: {
        "name": "下载完成",
        "description": "下载任务完成并尝试入库",
        "group": "download",
        "is_critical": False,
    },
    NotificationType.DOWNLOAD_HR_RISK: {
        "name": "HR 风险提醒",
        "description": "下载任务存在保种要求或风险",
        "group": "download",
        "is_critical": True,
    },
    # 系统消息
    NotificationType.SYSTEM_MESSAGE: {
        "name": "系统消息",
        "description": "重要系统通知",
        "group": "system",
        "is_critical": True,
    },
}


def get_notification_type_info_list() -> list[NotificationTypeInfo]:
    """获取所有通知类型信息"""
    result = []
    for ntype, info in NOTIFICATION_TYPE_INFO.items():
        result.append(NotificationTypeInfo(
            type=ntype,
            name=info["name"],
            description=info["description"],
            group=info["group"],
            is_critical=info.get("is_critical", False),
        ))
    return result


def is_critical_notification(notification_type: NotificationType) -> bool:
    """判断是否为重要通知"""
    info = NOTIFICATION_TYPE_INFO.get(notification_type)
    return info.get("is_critical", False) if info else False


# ============== Snooze 服务 ==============

async def get_user_snooze(
    session: AsyncSession,
    user_id: int,
) -> Optional[UserNotifySnooze]:
    """获取用户静音状态"""
    result = await session.execute(
        select(UserNotifySnooze).where(UserNotifySnooze.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_snooze(
    session: AsyncSession,
    user_id: int,
) -> UserNotifySnooze:
    """获取或创建用户静音记录"""
    snooze = await get_user_snooze(session, user_id)
    if not snooze:
        snooze = UserNotifySnooze(user_id=user_id)
        session.add(snooze)
        await session.flush()
    return snooze


async def set_snooze(
    session: AsyncSession,
    user_id: int,
    *,
    muted: Optional[bool] = None,
    snooze_until: Optional[datetime] = None,
    allow_critical_only: Optional[bool] = None,
    duration_minutes: Optional[int] = None,
) -> UserNotifySnooze:
    """设置用户静音状态"""
    snooze = await get_or_create_snooze(session, user_id)
    
    if muted is not None:
        snooze.muted = muted
    
    if duration_minutes is not None:
        snooze.snooze_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    elif snooze_until is not None:
        snooze.snooze_until = snooze_until
    
    if allow_critical_only is not None:
        snooze.allow_critical_only = allow_critical_only
    
    await session.commit()
    logger.info(f"[notify-pref] set snooze for user {user_id}: muted={snooze.muted}, until={snooze.snooze_until}")
    return snooze


async def clear_snooze(
    session: AsyncSession,
    user_id: int,
) -> None:
    """清除用户静音状态"""
    snooze = await get_user_snooze(session, user_id)
    if snooze:
        snooze.muted = False
        snooze.snooze_until = None
        snooze.allow_critical_only = False
        await session.commit()
        logger.info(f"[notify-pref] cleared snooze for user {user_id}")


# ============== 偏好服务 ==============

async def get_user_preferences(
    session: AsyncSession,
    user_id: int,
) -> list[UserNotifyPreference]:
    """获取用户所有通知偏好"""
    result = await session.execute(
        select(UserNotifyPreference)
        .where(UserNotifyPreference.user_id == user_id)
        .order_by(UserNotifyPreference.notification_type)
    )
    return list(result.scalars().all())


async def get_preference(
    session: AsyncSession,
    user_id: int,
    notification_type: NotificationType,
    media_type: Optional[ReadingMediaType] = None,
    target_id: Optional[int] = None,
) -> Optional[UserNotifyPreference]:
    """获取特定偏好记录"""
    conditions = [
        UserNotifyPreference.user_id == user_id,
        UserNotifyPreference.notification_type == notification_type,
    ]
    
    if media_type is None:
        conditions.append(UserNotifyPreference.media_type.is_(None))
    else:
        conditions.append(UserNotifyPreference.media_type == media_type)
    
    if target_id is None:
        conditions.append(UserNotifyPreference.target_id.is_(None))
    else:
        conditions.append(UserNotifyPreference.target_id == target_id)
    
    result = await session.execute(
        select(UserNotifyPreference).where(and_(*conditions))
    )
    return result.scalar_one_or_none()


async def upsert_preference(
    session: AsyncSession,
    user_id: int,
    data: UserNotifyPreferenceCreate | UserNotifyPreferenceUpdate,
) -> UserNotifyPreference:
    """创建或更新通知偏好"""
    existing = await get_preference(
        session,
        user_id,
        data.notification_type,
        data.media_type,
        data.target_id,
    )
    
    if existing:
        # 更新
        update_data = data.model_dump(exclude_unset=True, exclude={"notification_type", "media_type", "target_id"})
        for key, value in update_data.items():
            if value is not None:
                setattr(existing, key, value)
        await session.commit()
        logger.debug(f"[notify-pref] updated preference {existing.id}")
        return existing
    else:
        # 创建
        pref = UserNotifyPreference(
            user_id=user_id,
            notification_type=data.notification_type,
            media_type=data.media_type,
            target_id=data.target_id,
            enable_web=getattr(data, "enable_web", True) if hasattr(data, "enable_web") and data.enable_web is not None else True,
            enable_telegram=getattr(data, "enable_telegram", True) if hasattr(data, "enable_telegram") and data.enable_telegram is not None else True,
            enable_webhook=getattr(data, "enable_webhook", True) if hasattr(data, "enable_webhook") and data.enable_webhook is not None else True,
            enable_bark=getattr(data, "enable_bark", True) if hasattr(data, "enable_bark") and data.enable_bark is not None else True,
            muted=getattr(data, "muted", False) if hasattr(data, "muted") and data.muted is not None else False,
            digest_only=getattr(data, "digest_only", False) if hasattr(data, "digest_only") and data.digest_only is not None else False,
        )
        session.add(pref)
        await session.commit()
        logger.info(f"[notify-pref] created preference for user {user_id}, type={data.notification_type}")
        return pref


async def delete_preference(
    session: AsyncSession,
    user_id: int,
    preference_id: int,
) -> bool:
    """删除通知偏好"""
    result = await session.execute(
        select(UserNotifyPreference).where(
            UserNotifyPreference.id == preference_id,
            UserNotifyPreference.user_id == user_id,
        )
    )
    pref = result.scalar_one_or_none()
    
    if pref:
        await session.delete(pref)
        await session.commit()
        logger.info(f"[notify-pref] deleted preference {preference_id}")
        return True
    return False


# ============== 聚合 Matrix ==============

async def get_user_matrix(
    session: AsyncSession,
    user_id: int,
) -> UserNotifyPreferenceMatrix:
    """获取用户完整偏好矩阵"""
    preferences = await get_user_preferences(session, user_id)
    snooze = await get_user_snooze(session, user_id)
    
    return UserNotifyPreferenceMatrix(
        preferences=[UserNotifyPreferenceRead.model_validate(p) for p in preferences],
        snooze=UserNotifySnoozeRead.model_validate(snooze) if snooze else None,
        available_notification_types=get_notification_type_info_list(),
    )


# ============== 投递决策（核心） ==============

async def evaluate_notification_delivery(
    session: AsyncSession,
    *,
    user_id: int,
    notification_type: NotificationType,
    media_type: Optional[ReadingMediaType] = None,
    target_id: Optional[int] = None,
) -> NotificationDeliveryDecision:
    """
    评估通知投递决策
    
    汇总：
    - 全局 snooze / muted
    - 针对 (notification_type) 的全局偏好
    - 针对 (notification_type, media_type, target_id) 的局部偏好
    
    Returns:
        NotificationDeliveryDecision: 各渠道是否允许发送
    """
    decision = NotificationDeliveryDecision()
    
    # 1. 检查全局静音/Snooze
    snooze = await get_user_snooze(session, user_id)
    if snooze:
        is_critical = is_critical_notification(notification_type)
        
        if snooze.muted:
            if snooze.allow_critical_only and is_critical:
                # 允许重要通知
                decision.reason = "全局静音但允许重要通知"
            else:
                # 静音所有
                decision.allowed_web = False
                decision.allowed_telegram = False
                decision.allowed_webhook = False
                decision.allowed_bark = False
                decision.store_in_user_notification = True  # 仍写入记录
                decision.reason = "全局静音"
                return decision
        
        if snooze.snooze_until and datetime.utcnow() < snooze.snooze_until:
            if snooze.allow_critical_only and is_critical:
                decision.reason = "Snooze中但允许重要通知"
            else:
                decision.allowed_web = False
                decision.allowed_telegram = False
                decision.allowed_webhook = False
                decision.allowed_bark = False
                decision.store_in_user_notification = True
                decision.reason = f"Snooze至 {snooze.snooze_until}"
                return decision
    
    # 2. 检查针对 (notification_type) 的全局偏好
    global_pref = await get_preference(
        session, user_id, notification_type, None, None
    )
    
    if global_pref:
        if global_pref.muted:
            decision.allowed_web = False
            decision.allowed_telegram = False
            decision.allowed_webhook = False
            decision.allowed_bark = False
            decision.store_in_user_notification = True
            decision.reason = f"静音通知类型 {notification_type.value}"
            return decision
        
        # 应用渠道设置
        decision.allowed_web = global_pref.enable_web
        decision.allowed_telegram = global_pref.enable_telegram
        decision.allowed_webhook = global_pref.enable_webhook
        decision.allowed_bark = global_pref.enable_bark
    
    # 3. 检查针对 (notification_type, media_type, target_id) 的局部偏好
    if media_type and target_id:
        local_pref = await get_preference(
            session, user_id, notification_type, media_type, target_id
        )
        
        if local_pref:
            if local_pref.muted:
                decision.allowed_web = False
                decision.allowed_telegram = False
                decision.allowed_webhook = False
                decision.allowed_bark = False
                decision.store_in_user_notification = True
                decision.reason = f"静音作品 {media_type.value}:{target_id}"
                return decision
            
            # 局部偏好覆盖全局偏好
            decision.allowed_web = local_pref.enable_web
            decision.allowed_telegram = local_pref.enable_telegram
            decision.allowed_webhook = local_pref.enable_webhook
            decision.allowed_bark = local_pref.enable_bark
    
    return decision


# ============== 批量操作（用于 Telegram Bot） ==============

# 虚拟分组到实际 NotificationType 的映射
NOTIFY_GROUPS: dict[str, list[NotificationType]] = {
    "manga": [
        NotificationType.MANGA_NEW_CHAPTER,
        NotificationType.MANGA_UPDATED,
        NotificationType.MANGA_SYNC_FAILED,
    ],
    "novel_tts": [
        NotificationType.NOVEL_NEW_CHAPTER,
        NotificationType.AUDIOBOOK_NEW_TRACK,
        NotificationType.TTS_JOB_COMPLETED,
        NotificationType.TTS_JOB_FAILED,
        NotificationType.AUDIOBOOK_READY,
    ],
    "music": [
        NotificationType.MUSIC_CHART_UPDATED,
        NotificationType.MUSIC_NEW_TRACKS_QUEUED,
        NotificationType.MUSIC_NEW_TRACKS_DOWNLOADING,
        NotificationType.MUSIC_NEW_TRACKS_READY,
    ],
    "system": [
        NotificationType.SYSTEM_MESSAGE,
    ],
}


async def get_group_enabled_status(
    session: AsyncSession,
    user_id: int,
    group: str,
) -> bool:
    """检查某分组是否启用（Telegram 渠道）"""
    ntypes = NOTIFY_GROUPS.get(group, [])
    if not ntypes:
        return True
    
    for ntype in ntypes:
        pref = await get_preference(session, user_id, ntype, None, None)
        if pref and (pref.muted or not pref.enable_telegram):
            return False
    
    return True


async def set_group_enabled(
    session: AsyncSession,
    user_id: int,
    group: str,
    enabled: bool,
) -> None:
    """设置某分组的启用状态（Telegram 渠道）"""
    ntypes = NOTIFY_GROUPS.get(group, [])
    
    for ntype in ntypes:
        data = UserNotifyPreferenceUpdate(
            notification_type=ntype,
            enable_telegram=enabled,
            muted=not enabled if not enabled else False,
        )
        await upsert_preference(session, user_id, data)
    
    logger.info(f"[notify-pref] set group {group} enabled={enabled} for user {user_id}")
