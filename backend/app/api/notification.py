"""
通知相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import json
from loguru import logger

from app.core.database import get_db
from app.modules.notification.service import NotificationService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class NotificationCreate(BaseModel):
    """创建通知请求"""
    title: str
    message: str
    type: str = "info"  # info, warning, error, success
    channels: List[str] = ["system"]  # system, telegram, email, wechat, webhook, push
    metadata: Optional[Dict] = None  # 渠道配置信息


class NotificationResponse(BaseModel):
    """通知响应"""
    id: int
    title: str
    message: str
    type: str
    channels: List[str]
    status: str
    is_read: bool
    read_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    
    @classmethod
    def from_orm(cls, notification):
        """从ORM对象创建响应"""
        return cls(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            type=notification.type,
            channels=json.loads(notification.channels) if isinstance(notification.channels, str) else notification.channels,
            status=notification.status,
            is_read=notification.is_read,
            read_at=notification.read_at,
            sent_at=notification.sent_at,
            created_at=notification.created_at
        )
    
    class Config:
        from_attributes = True


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    notification: NotificationCreate,
    db = Depends(get_db)
):
    """
    发送通知
    
    返回统一响应格式：
    {
        "success": true,
        "message": "发送成功",
        "data": NotificationResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        result = await service.send_notification(
            title=notification.title,
            message=notification.message,
            notification_type=notification.type,
            channels=notification.channels,
            metadata=notification.metadata
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="SEND_FAILED",
                    error_message="发送通知失败"
                ).model_dump()
            )
        return success_response(
            data=NotificationResponse.from_orm(result).model_dump(),
            message="发送成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"发送通知时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/", response_model=BaseResponse)
async def list_notifications(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    notification_type: Optional[str] = Query(None, description="通知类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    unread_only: bool = Query(False, description="是否只返回未读通知"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取通知列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [NotificationResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        notifications = await service.list_notifications(
            limit=limit,
            notification_type=notification_type,
            status=status,
            unread_only=unread_only
        )
        notification_responses = [NotificationResponse.from_orm(n).model_dump() for n in notifications]
        
        # 计算分页
        total = len(notification_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = notification_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取通知列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取通知列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{notification_id}", response_model=BaseResponse)
async def get_notification(
    notification_id: int,
    db = Depends(get_db)
):
    """
    获取通知详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": NotificationResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        notification = await service.get_notification(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"通知不存在 (ID: {notification_id})"
                ).model_dump()
            )
        return success_response(
            data=NotificationResponse.from_orm(notification).model_dump(),
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取通知详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取通知详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{notification_id}/read", response_model=BaseResponse)
async def mark_notification_as_read(
    notification_id: int,
    db = Depends(get_db)
):
    """
    标记通知为已读
    
    返回统一响应格式：
    {
        "success": true,
        "message": "标记成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        success = await service.mark_as_read(notification_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"通知不存在 (ID: {notification_id})"
                ).model_dump()
            )
        return success_response(message="标记成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记通知为已读失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"标记通知为已读时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{notification_id}", response_model=BaseResponse)
async def delete_notification(
    notification_id: int,
    db = Depends(get_db)
):
    """
    删除通知
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        success = await service.delete_notification(notification_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"通知不存在 (ID: {notification_id})"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除通知失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除通知时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/read-all", response_model=BaseResponse)
async def mark_all_notifications_as_read(
    notification_type: Optional[str] = Query(None, description="通知类型过滤"),
    db = Depends(get_db)
):
    """
    标记所有通知为已读
    
    返回统一响应格式：
    {
        "success": true,
        "message": "标记成功，已标记 X 条通知",
        "data": {
            "marked_count": 10
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        count = await service.mark_all_as_read(notification_type)
        return success_response(
            data={"marked_count": count},
            message=f"标记成功，已标记 {count} 条通知"
        )
    except Exception as e:
        logger.error(f"标记所有通知为已读失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"标记所有通知为已读时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/unread/count", response_model=BaseResponse)
async def get_unread_count(
    notification_type: Optional[str] = Query(None, description="通知类型过滤"),
    db = Depends(get_db)
):
    """
    获取未读通知数量
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "unread_count": 10
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        count = await service.get_unread_count(notification_type)
        return success_response(
            data={"unread_count": count},
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取未读通知数量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取未读通知数量时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/", response_model=BaseResponse)
async def delete_all_notifications(
    notification_type: Optional[str] = Query(None, description="通知类型过滤"),
    db = Depends(get_db)
):
    """
    删除所有通知
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功，已删除 X 条通知",
        "data": {
            "deleted_count": 10
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = NotificationService(db)
        count = await service.delete_all_notifications(notification_type)
        return success_response(
            data={"deleted_count": count},
            message=f"删除成功，已删除 {count} 条通知"
        )
    except Exception as e:
        logger.error(f"删除所有通知失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除所有通知时发生错误: {str(e)}"
            ).model_dump()
        )

