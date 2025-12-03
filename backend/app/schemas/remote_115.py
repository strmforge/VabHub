"""
115 远程播放相关 Schema
"""
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class Remote115VideoQuality(BaseModel):
    """115 视频清晰度"""
    id: str
    title: str
    height: int
    width: int
    url: str  # 使用 str 而不是 HttpUrl，因为可能是 m3u8 等协议


class Remote115Subtitle(BaseModel):
    """115 视频字幕"""
    sid: str
    language: str
    title: str
    url: str  # 使用 str 而不是 HttpUrl
    is_default: bool


class Remote115VideoProgress(BaseModel):
    """115 视频观看进度"""
    position: int  # 秒数


class Remote115VideoPlayOptions(BaseModel):
    """115 视频播放选项"""
    work_id: int
    pick_code: str
    file_name: str
    duration: int
    qualities: List[Remote115VideoQuality]
    subtitles: List[Remote115Subtitle]
    progress: Optional[Remote115VideoProgress] = None


class Update115VideoProgressRequest(BaseModel):
    """更新 115 视频观看进度请求"""
    position: int = Field(..., ge=0, description="已播放秒数")
    finished: bool = Field(default=False, description="是否播放完成")

