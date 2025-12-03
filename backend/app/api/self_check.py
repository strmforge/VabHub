"""
自检 API
QA-1 实现

提供 Web 端触发自检的能力
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_session
from app.core.auth import require_admin
from app.models.user import User
from app.schemas.self_check import SelfCheckRunResult
from app.services.self_check_service import run_full_self_check


router = APIRouter(prefix="/admin/self_check", tags=["self-check"])


@router.post("/run", response_model=SelfCheckRunResult)
async def run_self_check(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    运行完整自检
    
    仅管理员可调用。返回 SelfCheckRunResult，包含各组检查结果。
    """
    logger.info(f"[self-check] triggered by user {current_user.id}")
    
    try:
        result = await run_full_self_check(session)
        return result
    except Exception as e:
        logger.error(f"[self-check] failed: {e}")
        raise HTTPException(status_code=500, detail=f"自检运行失败: {e}")


@router.get("/summary")
async def get_self_check_summary(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    获取自检摘要（快速版本，不运行完整自检）
    
    返回各组的状态概览
    """
    # 这里可以返回最近一次自检结果（如果有持久化）
    # 目前只返回一个占位响应
    return {
        "message": "请使用 POST /run 触发完整自检",
        "groups": [
            "core",
            "novel_tts",
            "manga",
            "music",
            "notify",
            "bot",
            "runners",
        ],
    }
