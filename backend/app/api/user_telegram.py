"""
用户 Telegram 绑定 API
BOT-TELEGRAM 实现
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user_telegram import (
    TelegramBindingRead,
    TelegramBindingCodeResponse,
    TelegramBindingStatusResponse,
)
from app.services import user_telegram_service

router = APIRouter(prefix="/api/notify/telegram", tags=["Telegram 绑定"])


@router.get("/status", response_model=TelegramBindingStatusResponse)
async def get_telegram_binding_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的 Telegram 绑定状态"""
    binding = await user_telegram_service.get_binding_by_user(session, current_user.id)
    
    if binding:
        return TelegramBindingStatusResponse(
            is_bound=True,
            binding=TelegramBindingRead.model_validate(binding),
        )
    else:
        return TelegramBindingStatusResponse(is_bound=False)


@router.post("/binding_code", response_model=TelegramBindingCodeResponse)
async def generate_binding_code(
    current_user: User = Depends(get_current_user),
):
    """生成 Telegram 绑定码"""
    code = await user_telegram_service.create_binding_code(current_user)
    
    return TelegramBindingCodeResponse(
        code=code,
        expires_in=user_telegram_service.BINDING_CODE_TTL,
    )


@router.delete("/unbind")
async def unbind_telegram(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """解除 Telegram 绑定"""
    success = await user_telegram_service.unbind_user(session, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail="未绑定 Telegram")
    
    return {"message": "解绑成功"}
