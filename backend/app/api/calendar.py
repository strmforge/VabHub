"""
日历相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.modules.calendar.service import CalendarService
from app.core.schemas import (
    BaseResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class CalendarEvent(BaseModel):
    """日历事件"""
    id: str
    title: str
    date: datetime
    type: str  # subscription, download, media_update
    subscription_id: Optional[int] = None
    download_id: Optional[int] = None
    media_type: Optional[str] = None
    season: Optional[int] = None
    color: Optional[str] = None
    description: Optional[str] = None


@router.get("/", response_model=BaseResponse)
async def get_calendar_events(
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    event_types: Optional[List[str]] = Query(None, description="事件类型列表"),
    db = Depends(get_db)
):
    """
    获取日历事件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [CalendarEvent, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CalendarService(db)
        events = await service.get_calendar_events(
            start_date=start_date,
            end_date=end_date,
            event_types=event_types
        )
        return success_response(data=events, message="获取成功")
    except Exception as e:
        logger.error(f"获取日历事件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取日历事件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/subscription/{subscription_id}/ics")
async def get_subscription_calendar_ics(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    获取订阅的iCalendar格式日历
    
    返回iCalendar格式文件（特殊端点，不使用统一响应模型）
    """
    try:
        service = CalendarService(db)
        ics_content = await service.get_subscription_calendar_ics(subscription_id)
        
        if not ics_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"订阅不存在或无法生成日历 (ID: {subscription_id})"
                ).model_dump()
            )
        
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="subscription_{subscription_id}.ics"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订阅日历失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取订阅日历时发生错误: {str(e)}"
            ).model_dump()
        )

