"""
用户收藏媒体 Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums.reading_media_type import ReadingMediaType


class UserFavoriteMediaBase(BaseModel):
    """用户收藏媒体基础"""
    media_type: ReadingMediaType
    target_id: int


class UserFavoriteMediaCreate(UserFavoriteMediaBase):
    """用户收藏媒体创建"""
    pass


class UserFavoriteMediaRead(UserFavoriteMediaBase):
    """用户收藏媒体读取"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True