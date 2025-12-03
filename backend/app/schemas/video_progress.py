"""
视频播放进度相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class VideoProgressBase(BaseModel):
    """视频进度基础模型"""
    position_seconds: float = Field(..., ge=0, description="当前播放位置（秒）")
    duration_seconds: Optional[float] = Field(None, ge=0, description="视频总时长（秒）")
    progress_percent: float = Field(..., ge=0, le=100, description="进度百分比")
    is_finished: bool = Field(False, description="是否已看完")
    source_type: Optional[int] = Field(None, description="播放源类型：1=本地，2=115")
    last_play_url: Optional[str] = Field(None, description="最后播放的URL")
    tmdb_id: Optional[int] = Field(None, description="TMDB ID")


class VideoProgressUpdate(VideoProgressBase):
    """更新视频进度的请求模型"""
    pass


class VideoProgressResponse(VideoProgressBase):
    """视频进度响应模型"""
    work_id: int = Field(..., description="作品ID")
    has_progress: bool = Field(True, description="是否有进度记录")
    last_played_at: Optional[datetime] = Field(None, description="最近播放时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class VideoProgressListResponse(BaseModel):
    """视频进度列表响应模型"""
    items: List[VideoProgressResponse] = Field(..., description="进度列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")

    class Config:
        from_attributes = True
