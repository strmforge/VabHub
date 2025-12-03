"""
用户通知API

基于Phase 7要求的用户通知中心功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.notification_service import (
    list_notifications,
    mark_notification_read,
    mark_all_read,
)
from app.schemas.notify import UserNotificationListResponse, UserNotificationItem
from app.models.user import User
from app.models.user_notification import UserNotification

router = APIRouter()


@router.get("/", response_model=UserNotificationListResponse)
async def get_user_notifications(
    is_read: Optional[bool] = Query(None, description="按已读状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的通知列表
    
    返回：UserNotificationListResponse（items + total + unread_count）
    """
    try:
        notifications, total, unread_count = await list_notifications(
            session=db,
            user_id=current_user.id,
            is_read=is_read,
            limit=limit,
            offset=offset,
        )
        
        # 将数据库模型转换为Schema对象
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
            
            items.append(UserNotificationItem(
                id=notif.id,
                type=notif.type,
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
        
        return UserNotificationListResponse(
            items=items,
            total=total,
            unread_count=unread_count
        )
        
    except Exception as e:
        logger.error(f"获取用户通知列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知列表失败: {str(e)}"
        )


@router.get("/unread_count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的未读通知数量
    
    返回：{"unread_count": number}
    """
    try:
        # 直接查询未读数量，避免调用list_notifications
        unread_stmt = (
            select(func.count(UserNotification.id))
            .where(
                UserNotification.user_id == current_user.id,
                UserNotification.is_read == False
            )
        )
        unread_result = await db.execute(unread_stmt)
        unread_count = unread_result.scalar_one() or 0
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        logger.error(f"获取未读通知数量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取未读通知数量失败: {str(e)}"
        )


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    标记单条通知为已读
    
    返回：{"ok": true}
    """
    try:
        await mark_notification_read(
            session=db,
            user_id=current_user.id,
            notification_id=notification_id,
        )
        
        return {"ok": True}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"标记通知为已读失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记通知为已读失败: {str(e)}"
        )


@router.post("/read_all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    标记当前用户所有通知为已读
    
    返回：{"updated": number}
    """
    try:
        updated_count = await mark_all_read(
            session=db,
            user_id=current_user.id,
        )
        
        return {"updated": updated_count}
        
    except Exception as e:
        logger.error(f"标记所有通知为已读失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记所有通知为已读失败: {str(e)}"
        )