"""
用户通知 API

提供用户通知的查询和管理接口
"""

from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from loguru import logger

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.notification_categories import get_notification_category
from app.schemas.notify import (
    UserNotificationListResponse,
    UserNotificationItem,
    UserNotificationListQuery,
    MarkReadRequest,
    MarkReadResponse,
    DeleteResponse,
    UnreadCountResponse
)
from app.models.user_notification import UserNotification
from app.models.user import User
from datetime import datetime

router = APIRouter()


@router.get("/recent", response_model=None)
async def get_recent_notifications(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取最近的通知列表
    
    返回最近 limit 条通知，按创建时间倒序
    """
    # 查询最近的通知
    notifications_result = await db.execute(
        select(UserNotification)
        .where(UserNotification.user_id == current_user.id)
        .order_by(desc(UserNotification.created_at))
        .limit(limit)
    )
    notifications = notifications_result.scalars().all()
    
    # 统计未读数量
    unread_count_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        )
    )
    unread_count = unread_count_result.scalar() or 0
    
    # 转换为响应格式
    items = []
    for notif in notifications:
        # 根据通知类型计算严重程度
        severity = "info"  # 默认值
        if notif.type == "TTS_JOB_COMPLETED":
            severity = "success"
        elif notif.type == "TTS_JOB_FAILED":
            severity = "error"
        elif notif.type == "AUDIOBOOK_READY":
            severity = "success"
        
        # 计算通知分类
        category = get_notification_category(notif.type)
        
        items.append(UserNotificationItem(
            id=notif.id,
            type=notif.type,
            category=category,  # 新增：通知分类
            media_type=notif.media_type,
            ebook_id=notif.ebook_id,
            tts_job_id=notif.tts_job_id,
            title=notif.title,
            message=notif.message,
            severity=severity,
            is_read=notif.is_read,
            created_at=notif.created_at,
            read_at=notif.read_at
        ))
    
    # 获取总数
    total_result = await db.execute(
        select(func.count(UserNotification.id))
    )
    total = total_result.scalar() or 0
    
    return UserNotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取未读通知数量
    
    用于顶部小红点轮询（当前用户）
    """
    result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        )
    )
    unread_count = result.scalar() or 0
    
    return UnreadCountResponse(unread_count=unread_count)


@router.get("/unread-count-by-category", response_model=dict)
async def get_unread_count_by_category(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取按分类统计的未读通知数量
    
    用于前端过滤侧栏的未读数量徽章
    """
    from app.core.notification_categories import NotificationCategory, get_types_by_category
    
    # 初始化各分类未读数量
    unread_by_category = {
        category.value: 0
        for category in NotificationCategory
    }
    
    # 统计各分类的未读数量
    for category in NotificationCategory:
        category_types = get_types_by_category(category)
        if category_types:
            result = await db.execute(
                select(func.count(UserNotification.id))
                .where(
                    UserNotification.user_id == current_user.id,
                    UserNotification.is_read == False,
                    UserNotification.type.in_([t.value for t in category_types])
                )
            )
            unread_by_category[category.value] = result.scalar() or 0
    
    return {
        "unread_by_category": unread_by_category,
        "total_unread": sum(unread_by_category.values())
    }


@router.get("/summary", response_model=dict)
async def get_notification_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取通知统计摘要（当前用户）
    
    返回未读通知的分布情况
    """
    # 获取未读总数（当前用户）
    total_unread_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        )
    )
    total_unread = total_unread_result.scalar() or 0
    
    # 按类型统计未读数量
    unread_by_level = {
        "error": 0,
        "warning": 0,
        "success": 0,
        "info": 0
    }
    
    # 统计错误类型未读（当前用户）
    error_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False,
            UserNotification.type == "TTS_JOB_FAILED"
        )
    )
    unread_by_level["error"] = error_result.scalar() or 0
    
    # 统计成功类型未读（当前用户）
    success_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False,
            UserNotification.type.in_(["TTS_JOB_COMPLETED", "AUDIOBOOK_READY"])
        )
    )
    unread_by_level["success"] = success_result.scalar() or 0
    
    # 统计警告类型未读（当前用户）
    warning_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False,
            UserNotification.type == "warning"
        )
    )
    unread_by_level["warning"] = warning_result.scalar() or 0
    
    # 统计信息类型未读（其他类型）（当前用户）
    info_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False,
            UserNotification.type.in_(["MANGA_NEW_CHAPTER", "NOVEL_NEW_CHAPTER", "AUDIOBOOK_NEW_TRACK", "SYSTEM_MESSAGE"])
        )
    )
    unread_by_level["info"] = info_result.scalar() or 0
    
    return {
        "total_unread": total_unread,
        "unread_by_level": unread_by_level
    }


@router.post("/mark-read", response_model=MarkReadResponse)
async def mark_notifications_read(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    标记通知为已读
    
    支持按 ID 列表或分类批量标记已读
    - 如果提供 ids，则只标记指定 ID 的通知
    - 如果提供 category，则只标记该分类的通知
    - 如果两者都提供，则标记同时满足 ID 和分类条件的通知
    - 如果两者都未提供，则标记所有未读通知
    """
    now = datetime.utcnow()
    
    # 构建查询条件
    conditions = [UserNotification.user_id == current_user.id, UserNotification.is_read == False]
    
    if request.ids is not None:
        # 按指定 ID 标记
        if not request.ids:
            return MarkReadResponse(success=True, updated=0)
        conditions.append(UserNotification.id.in_(request.ids))
    
    if request.category is not None:
        # 按分类标记
        from app.core.notification_categories import get_types_by_category
        category_types = get_types_by_category(request.category)
        if category_types:
            conditions.append(UserNotification.type.in_([t.value for t in category_types]))
    
    # 查询符合条件的未读通知
    result = await db.execute(
        select(UserNotification).where(and_(*conditions))
    )
    notifications = result.scalars().all()
    
    # 批量标记为已读
    updated = 0
    for notif in notifications:
        notif.is_read = True
        notif.read_at = now
        updated += 1
    
    await db.commit()
    
    logger.info(f"Marked {updated} notifications as read for user {current_user.id}")
    
    return MarkReadResponse(success=True, updated=updated)


@router.get("/", response_model=UserNotificationListResponse)
async def get_notifications(
    params: UserNotificationListQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取通知列表（支持分页和筛选）
    
    支持按类型、分类、媒体类型、已读状态筛选
    """
    # 构建查询条件
    conditions = [UserNotification.user_id == current_user.id]
    
    if params.type:
        conditions.append(UserNotification.type == params.type)
    if params.category:
        # 根据分类获取所有相关的通知类型
        from app.core.notification_categories import get_types_by_category
        category_types = get_types_by_category(params.category)
        if category_types:
            conditions.append(UserNotification.type.in_([t.value for t in category_types]))
    if params.media_type:
        conditions.append(UserNotification.media_type == params.media_type)
    if params.is_read is not None:
        conditions.append(UserNotification.is_read == params.is_read)
    if params.level:
        # 根据level筛选严重程度（基于type字段）
        if params.level == 'error':
            conditions.append(UserNotification.type.in_(['TTS_JOB_FAILED']))
        elif params.level == 'warning':
            conditions.append(UserNotification.type.in_(['warning']))
        elif params.level == 'success':
            conditions.append(UserNotification.type.in_(['TTS_JOB_COMPLETED', 'AUDIOBOOK_READY']))
        elif params.level == 'info':
            conditions.append(UserNotification.type.in_(['MANGA_NEW_CHAPTER', 'NOVEL_NEW_CHAPTER', 'AUDIOBOOK_NEW_TRACK', 'SYSTEM_MESSAGE']))
    
    # 查询通知列表
    query = select(UserNotification).order_by(desc(UserNotification.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    if params.limit:
        query = query.limit(params.limit)
    if params.offset:
        query = query.offset(params.offset)
    
    notifications_result = await db.execute(query)
    notifications = notifications_result.scalars().all()
    
    # 统计未读数量（当前用户）
    unread_count_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(
            UserNotification.user_id == current_user.id,
            UserNotification.is_read == False
        )
    )
    unread_count = unread_count_result.scalar() or 0
    
    # 转换为响应格式
    items = []
    for notif in notifications:
        # 根据通知类型计算严重程度
        severity = "info"  # 默认值
        if notif.type == "TTS_JOB_COMPLETED" or notif.type == "AUDIOBOOK_READY":
            severity = "success"
        elif notif.type == "TTS_JOB_FAILED":
            severity = "error"
        elif notif.type == "warning":
            severity = "warning"
        
        # 计算通知分类
        category = get_notification_category(notif.type)
        
        items.append(UserNotificationItem(
            id=notif.id,
            type=notif.type,
            category=category,  # 新增：通知分类
            media_type=notif.media_type,
            ebook_id=notif.ebook_id,
            tts_job_id=notif.tts_job_id,
            title=notif.title,
            message=notif.message,
            severity=severity,
            is_read=notif.is_read,
            created_at=notif.created_at,
            read_at=notif.read_at
        ))
    
    # 获取总数（当前用户）
    total_result = await db.execute(
        select(func.count(UserNotification.id))
        .where(UserNotification.user_id == current_user.id)
    )
    total = total_result.scalar() or 0
    
    return UserNotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count
    )


@router.delete("/batch", response_model=DeleteResponse)
async def delete_notifications_batch(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量删除通知（支持按ID和分类）
    
    Args:
        request: 包含ids列表或category的请求体
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        删除结果
        
    Logic:
    - 如果提供了ids，只删除指定的通知ID
    - 如果提供了category，删除该分类下的所有通知
    - 如果同时提供ids和category，只删除ids中属于该分类的通知
    - 如果都没提供，删除用户的所有通知
    """
    deleted = 0
    
    # 构建删除条件
    conditions = [UserNotification.user_id == current_user.id]
    
    if request.ids:
        # 按ID删除
        conditions.append(UserNotification.id.in_(request.ids))
    
    if request.category:
        # 按分类删除
        from app.core.notification_categories import get_types_by_category
        category_types = get_types_by_category(request.category)
        if category_types:
            type_values = [t.value for t in category_types]
            conditions.append(UserNotification.type.in_(type_values))
    
    # 执行删除
    query = select(UserNotification).where(and_(*conditions))
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    for notification in notifications:
        await db.delete(notification)
        deleted += 1
    
    await db.commit()
    
    logger.info(f"User {current_user.id} deleted {deleted} notifications by batch: ids={request.ids}, category={request.category}")
    
    return DeleteResponse(success=True, deleted=deleted)


@router.delete("/{notification_id}", response_model=DeleteResponse)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除单条通知
    """
    # 查找通知（确保属于当前用户）
    result = await db.execute(
        select(UserNotification).where(
            and_(UserNotification.id == notification_id, UserNotification.user_id == current_user.id)
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 删除通知
    await db.delete(notification)
    await db.commit()
    
    logger.info(f"User {current_user.id} deleted notification: {notification_id}")
    
    return DeleteResponse(success=True, deleted=1)


@router.delete("/", response_model=DeleteResponse)
async def delete_all_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户的所有通知
    """
    # 查询用户的所有通知
    result = await db.execute(
        select(UserNotification).where(UserNotification.user_id == current_user.id)
    )
    notifications = result.scalars().all()
    
    deleted = 0
    for notification in notifications:
        await db.delete(notification)
        deleted += 1
    
    await db.commit()
    
    logger.info(f"User {current_user.id} deleted all notifications: {deleted} items")
    
    return DeleteResponse(success=True, deleted=deleted)

