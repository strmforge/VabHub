"""
任务中心 Schema
TASK-1 实现
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel


TaskMediaType = Literal["movie", "series", "novel", "audiobook", "manga", "music", "other"]
TaskKind = Literal["download", "tts", "import", "subscription", "other"]
TaskStatus = Literal["pending", "running", "success", "failed", "skipped"]


class TaskCenterItem(BaseModel):
    """任务中心项"""
    id: str                     # 字符串 ID，来自不同表时可前缀，例如 "tts:123"
    kind: TaskKind
    media_type: TaskMediaType
    title: str
    sub_title: Optional[str] = None
    status: TaskStatus
    progress: Optional[float] = None  # 0-100
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_error: Optional[str] = None
    source: Optional[str] = None      # 如 "MusicSubscription", "TTSJob"
    route_name: Optional[str] = None
    route_params: Optional[dict] = None


class TaskCenterListResponse(BaseModel):
    """任务中心列表响应"""
    items: List[TaskCenterItem]
    total: int
