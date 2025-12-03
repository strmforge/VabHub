"""
漫画下载任务 Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.manga_download_job import DownloadJobMode, DownloadJobStatus


class MangaDownloadJobBase(BaseModel):
    """下载任务基础信息"""
    source_id: int = Field(..., description="源 ID")
    source_type: str = Field(..., description="源类型")
    source_series_id: str = Field(..., description="远程系列 ID")
    source_chapter_id: Optional[str] = Field(None, description="远程章节 ID")
    target_local_series_id: Optional[int] = Field(None, description="目标本地系列 ID")
    mode: DownloadJobMode = Field(..., description="下载模式")
    priority: int = Field(0, description="优先级")


class MangaDownloadJobCreate(MangaDownloadJobBase):
    """创建下载任务请求"""
    pass


class MangaDownloadJobUpdate(BaseModel):
    """更新下载任务请求"""
    status: Optional[DownloadJobStatus] = None
    error_msg: Optional[str] = None
    downloaded_chapters: Optional[int] = None
    total_chapters: Optional[int] = None


class MangaDownloadJobRead(MangaDownloadJobBase):
    """下载任务响应"""
    id: int = Field(..., description="任务 ID")
    user_id: int = Field(..., description="用户 ID")
    status: DownloadJobStatus = Field(..., description="任务状态")
    error_msg: Optional[str] = Field(None, description="错误信息")
    total_chapters: Optional[int] = Field(None, description="总章节数")
    downloaded_chapters: int = Field(0, description="已下载章节数")
    progress_percent: float = Field(0.0, description="下载进度百分比")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 关联信息（可选）
    source_name: Optional[str] = Field(None, description="源名称")
    target_series_title: Optional[str] = Field(None, description="目标系列标题")
    
    class Config:
        from_attributes = True


class MangaDownloadJobList(BaseModel):
    """下载任务列表响应"""
    items: List[MangaDownloadJobRead] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页大小")
    total_pages: int = Field(..., description="总页数")


class MangaDownloadJobSummary(BaseModel):
    """下载任务统计信息"""
    total_jobs: int = Field(..., description="总任务数")
    pending_jobs: int = Field(..., description="待处理任务数")
    running_jobs: int = Field(..., description="正在运行任务数")
    completed_jobs: int = Field(..., description="已完成任务数")
    failed_jobs: int = Field(..., description="失败任务数")
