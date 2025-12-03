"""
用户 Telegram 绑定模型
BOT-TELEGRAM 实现
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserTelegramBinding(Base):
    """用户 Telegram 绑定"""
    __tablename__ = "user_telegram_binding"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Telegram 信息
    telegram_chat_id = Column(BigInteger, nullable=False, unique=True, index=True)
    telegram_username = Column(String(128), nullable=True)
    telegram_first_name = Column(String(128), nullable=True)
    telegram_last_name = Column(String(128), nullable=True)
    language_code = Column(String(16), nullable=True)
    
    # 状态
    is_blocked = Column(Boolean, default=False, nullable=False)  # 用户是否 block 了 bot
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserTelegramBinding user={self.user_id} chat={self.telegram_chat_id}>"
