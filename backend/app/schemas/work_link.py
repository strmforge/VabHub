"""
作品关联（Work Link）Schema
"""

from typing import Literal
from datetime import datetime
from pydantic import BaseModel


class WorkLinkBase(BaseModel):
    """作品关联基础 Schema"""
    ebook_id: int
    target_type: Literal["video", "comic", "music"]
    target_id: int
    relation: Literal["include", "exclude"]


class WorkLinkCreate(WorkLinkBase):
    """创建作品关联"""
    pass


class WorkLinkUpdate(BaseModel):
    """更新作品关联"""
    relation: Literal["include", "exclude"]


class WorkLinkResponse(WorkLinkBase):
    """作品关联响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

