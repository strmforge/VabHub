"""
有声书相关 Schema 定义
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UserAudiobookChapter(BaseModel):
    """用户有声书章节信息"""
    file_id: int
    title: str
    duration_seconds: Optional[int] = None
    is_tts_generated: bool = False
    tts_provider: Optional[str] = None
    order: int  # 用于排序展示


class UserWorkAudiobookStatus(BaseModel):
    """用户作品有声书状态"""
    has_audiobook: bool
    current_file_id: Optional[int] = None
    current_position_seconds: int = 0
    current_duration_seconds: Optional[int] = None
    progress_percent: Optional[float] = Field(None, ge=0, le=100)  # 0-100
    chapters: List[UserAudiobookChapter] = []


class UpdateAudiobookProgressRequest(BaseModel):
    """更新有声书进度请求"""
    audiobook_file_id: int
    position_seconds: int = Field(ge=0)
    duration_seconds: Optional[int] = Field(None, ge=0)


class AudiobookFileResponse(BaseModel):
    """有声书文件响应"""
    id: int
    ebook_id: int
    file_path: str
    file_size_bytes: Optional[int] = None
    file_size_mb: Optional[float] = None
    format: str
    duration_seconds: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    channels: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    narrator: Optional[str] = None
    is_tts_generated: bool = False
    tts_provider: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AudiobookDetailResponse(BaseModel):
    """有声书详情响应"""
    id: int
    ebook_id: int
    file_path: str
    file_size_bytes: Optional[int] = None
    file_size_mb: Optional[float] = None
    format: str
    duration_seconds: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    channels: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    narrator: Optional[str] = None
    is_tts_generated: bool = False
    tts_provider: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    work: Optional[dict] = None  # 关联的作品信息
    
    class Config:
        from_attributes = True


class AudiobookStatsResponse(BaseModel):
    """有声书统计响应"""
    audiobooks_total: int
    works_total: int
    total_size_mb: float
    total_duration_seconds: Optional[int] = None
