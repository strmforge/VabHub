"""
漫画下载任务模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    ForeignKey,
    String,
    Text,
    Enum,
    func,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class DownloadJobMode(str, enum.Enum):
    """下载任务模式"""
    SERIES = "SERIES"  # 整部下载
    CHAPTER = "CHAPTER"  # 单章下载


class DownloadJobStatus(str, enum.Enum):
    """下载任务状态"""
    PENDING = "PENDING"  # 等待处理
    RUNNING = "RUNNING"  # 正在下载
    SUCCESS = "SUCCESS"  # 下载成功
    FAILED = "FAILED"  # 下载失败


class MangaDownloadJob(Base):
    """漫画下载任务"""
    __tablename__ = "manga_download_jobs"

    id = Column(Integer, primary_key=True)

    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 源信息
    source_id = Column(Integer, ForeignKey("manga_sources.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # "KOMGA"/"SUWAYOMI"/"OPDS"
    source_series_id = Column(String(100), nullable=False, index=True)
    source_chapter_id = Column(String(100), nullable=True, index=True)  # 整部下载时为空

    # 目标信息
    target_local_series_id = Column(Integer, ForeignKey("manga_series_local.id"), nullable=True, index=True)

    # 下载配置
    mode = Column(Enum(DownloadJobMode), nullable=False)
    status = Column(Enum(DownloadJobStatus), nullable=False, default=DownloadJobStatus.PENDING, index=True)
    priority = Column(Integer, nullable=False, default=0)  # 优先级，数字越大优先级越高
    error_msg = Column(Text, nullable=True)

    # 进度信息
    total_chapters = Column(Integer, nullable=True)  # 总章节数（整部下载时）
    downloaded_chapters = Column(Integer, nullable=False, default=0)  # 已下载章节数

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)  # 开始处理时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间

    # 关联关系
    user = relationship("User", back_populates="manga_download_jobs")
    source = relationship("MangaSource", back_populates="download_jobs")
    target_local_series = relationship("MangaSeriesLocal", back_populates="download_jobs")

    def __repr__(self):
        return (
            f"<MangaDownloadJob(id={self.id}, user_id={self.user_id}, "
            f"source={self.source_type}:{self.source_series_id}, "
            f"mode={self.mode}, status={self.status})>"
        )

    @property
    def is_active(self) -> bool:
        """是否为活跃任务（待处理或正在处理）"""
        return self.status in (DownloadJobStatus.PENDING, DownloadJobStatus.RUNNING)

    @property
    def is_finished(self) -> bool:
        """是否已完成（成功或失败）"""
        return self.status in (DownloadJobStatus.SUCCESS, DownloadJobStatus.FAILED)

    @property
    def progress_percent(self) -> float:
        """下载进度百分比"""
        if self.total_chapters and self.total_chapters > 0:
            return round(self.downloaded_chapters / self.total_chapters * 100, 1)
        return 0.0

    def mark_running(self):
        """标记为正在运行"""
        self.status = DownloadJobStatus.RUNNING
        self.started_at = func.now()

    def mark_success(self):
        """标记为成功完成"""
        self.status = DownloadJobStatus.SUCCESS
        self.completed_at = func.now()

    def mark_failed(self, error_msg: str):
        """标记为失败"""
        self.status = DownloadJobStatus.FAILED
        self.error_msg = error_msg
        self.completed_at = func.now()
