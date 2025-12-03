"""漫画追更相关 Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserMangaFollowBase(BaseModel):
    """用户漫画追更基础字段"""

    user_id: int
    series_id: int
    last_synced_chapter_id: Optional[int] = None
    last_seen_chapter_id: Optional[int] = None
    unread_chapter_count: int = 0


class UserMangaFollowRead(UserMangaFollowBase):
    """用户漫画追更读取 Schema"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserMangaFollowUpdate(BaseModel):
    """更新追更状态时使用的 Schema

    注意：更新 API 会基于当前登录用户推断 user_id，因此这里不包含 user_id 字段。
    """

    last_synced_chapter_id: Optional[int] = None
    last_seen_chapter_id: Optional[int] = None
    unread_chapter_count: Optional[int] = None


class FollowedMangaItem(BaseModel):
    """追更中的漫画列表项

    用于前端展示用户当前追更的漫画系列及未读状态。
    """

    follow_id: int
    series_id: int
    series_title: str
    cover_url: Optional[str] = None
    source_id: int
    unread_chapter_count: int
    last_synced_chapter_id: Optional[int] = None
    last_seen_chapter_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
