"""
Onboarding API
LAUNCH-1 L2-1 实现

首次启动向导状态管理
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.system_state import SystemState
from app.schemas.response import BaseResponse, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/onboarding", tags=["Onboarding"])


class OnboardingStatusResponse(BaseModel):
    """Onboarding 状态响应"""
    completed: bool
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None


async def get_or_create_system_state(db: AsyncSession) -> SystemState:
    """获取或创建系统状态记录"""
    result = await db.execute(select(SystemState).where(SystemState.id == 1))
    state = result.scalar_one_or_none()
    
    if state is None:
        state = SystemState(id=1, onboarding_completed=False)
        db.add(state)
        await db.commit()
        await db.refresh(state)
    
    return state


@router.get("/status", response_model=BaseResponse, summary="获取 Onboarding 状态")
async def get_onboarding_status(
    db: AsyncSession = Depends(get_db),
):
    """
    获取 Onboarding 状态
    
    此接口不需要登录，用于前端判断是否需要显示 Onboarding 向导
    """
    try:
        state = await get_or_create_system_state(db)
        
        return success_response(
            data=OnboardingStatusResponse(
                completed=state.onboarding_completed,
                completed_at=state.onboarding_completed_at,
                completed_by=state.onboarding_completed_by
            ).model_dump(),
            message="获取 Onboarding 状态成功"
        )
    except Exception as e:
        logger.error(f"获取 Onboarding 状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Onboarding 状态失败: {str(e)}"
        )


@router.post("/complete", response_model=BaseResponse, summary="完成 Onboarding")
async def complete_onboarding(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    标记 Onboarding 完成
    
    需要登录用户调用，最好是管理员
    """
    try:
        state = await get_or_create_system_state(db)
        
        if state.onboarding_completed:
            return success_response(
                data={"completed": True},
                message="Onboarding 已完成"
            )
        
        state.onboarding_completed = True
        state.onboarding_completed_at = datetime.utcnow()
        state.onboarding_completed_by = current_user.username
        
        await db.commit()
        
        logger.info(f"Onboarding 已由用户 {current_user.username} 完成")
        
        return success_response(
            data={"completed": True},
            message="Onboarding 完成"
        )
    except Exception as e:
        logger.error(f"完成 Onboarding 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"完成 Onboarding 失败: {str(e)}"
        )


@router.post("/skip", response_model=BaseResponse, summary="跳过 Onboarding")
async def skip_onboarding(
    db: AsyncSession = Depends(get_db),
):
    """
    跳过 Onboarding（不需要登录）
    
    用于用户选择跳过向导的情况
    """
    try:
        state = await get_or_create_system_state(db)
        
        if not state.onboarding_completed:
            state.onboarding_completed = True
            state.onboarding_completed_at = datetime.utcnow()
            state.onboarding_completed_by = "skipped"
            await db.commit()
        
        return success_response(
            data={"completed": True},
            message="已跳过 Onboarding"
        )
    except Exception as e:
        logger.error(f"跳过 Onboarding 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"跳过 Onboarding 失败: {str(e)}"
        )
