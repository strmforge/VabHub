"""
用户 Telegram 绑定 Schema
BOT-TELEGRAM 实现
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TelegramBindingRead(BaseModel):
    """Telegram 绑定信息"""
    id: int
    telegram_chat_id: int
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramBindingCodeResponse(BaseModel):
    """绑定码响应"""
    code: str
    expires_in: int  # 秒


class TelegramBindingStatusResponse(BaseModel):
    """绑定状态响应"""
    is_bound: bool
    binding: Optional[TelegramBindingRead] = None
