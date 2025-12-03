"""
漫画源 Schema
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import AnyHttpUrl, BaseModel

from app.models.enums.manga_source_type import MangaSourceType


class MangaSourceBase(BaseModel):
    """漫画源基础 Schema"""
    name: str
    type: MangaSourceType
    base_url: AnyHttpUrl
    is_enabled: bool = True

    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None


class MangaSourceCreate(MangaSourceBase):
    """创建漫画源 Schema"""
    pass


class MangaSourceUpdate(BaseModel):
    """更新漫画源 Schema"""
    name: Optional[str] = None
    type: Optional[MangaSourceType] = None
    base_url: Optional[AnyHttpUrl] = None
    is_enabled: Optional[bool] = None

    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None


class MangaSourceRead(MangaSourceBase):
    """读取漫画源 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MangaLibraryInfo(BaseModel):
    """漫画库/书架简要信息，用于连接测试预览"""
    id: str
    name: str

