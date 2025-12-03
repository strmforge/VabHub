"""
音乐自动下载任务模型

记录从榜单订阅或关键字订阅触发的搜索/下载任务。
Phase 3 扩展：支持完整的 PT 搜索 → 下载 → 导入链路。
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, Float, Boolean, Enum
from datetime import datetime
from enum import Enum as PyEnum
from app.core.database import Base


class MusicDownloadJobSource(str, PyEnum):
    """音乐下载任务来源"""
    CHART = "chart"      # 榜单订阅
    KEYWORD = "keyword"  # 关键字订阅


class MusicDownloadJob(Base):
    """
    音乐下载任务
    
    记录从榜单订阅触发的搜索和下载任务。
    复用现有 DownloadTask 进行实际下载，这里只做关联和状态追踪。
    
    状态流转：
    pending → searching → found → submitted → downloading → importing → completed
                       ↘ not_found → failed
                                  ↘ skipped_duplicate
    """
    __tablename__ = "music_download_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 任务来源类型
    source_type = Column(
        Enum(MusicDownloadJobSource),
        default=MusicDownloadJobSource.CHART,
        nullable=False,
        index=True
    )
    
    # 关联的订阅
    subscription_id = Column(Integer, ForeignKey("user_music_subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 关联的榜单条目（仅CHART类型使用）
    chart_item_id = Column(Integer, ForeignKey("music_chart_items.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 用户 ID（冗余，方便查询）
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 搜索关键词
    search_query = Column(String(500), nullable=False)
    
    # 任务状态
    # pending: 等待 PT 搜索
    # searching: 正在搜索 PT
    # found: 找到资源，等待下载
    # not_found: 未找到资源
    # submitted: 已提交到下载器
    # downloading: 下载中
    # importing: 导入中
    # completed: 完成（已入库）
    # failed: 失败
    # skipped_duplicate: 跳过（本地已有相同或更好版本）
    status = Column(String(30), default="pending", index=True)
    
    # ========== PT 搜索结果 ==========
    # 匹配到的种子信息
    matched_site = Column(String(50), nullable=True)
    matched_torrent_id = Column(String(100), nullable=True)
    matched_torrent_name = Column(String(500), nullable=True)
    matched_torrent_size_bytes = Column(Integer, nullable=True)  # 字节
    matched_seeders = Column(Integer, nullable=True)
    matched_leechers = Column(Integer, nullable=True)
    matched_free_percent = Column(Integer, nullable=True)  # 0/50/100
    quality_score = Column(Float, nullable=True)  # 综合评分
    
    # 搜索时返回的候选数量（用于调试）
    search_candidates_count = Column(Integer, nullable=True)
    
    # ========== 下载相关 ==========
    # 下载器类型
    download_client = Column(String(30), nullable=True)  # qbittorrent / transmission
    
    # 关联的下载任务 ID（如果已发起下载）
    download_task_id = Column(Integer, ForeignKey("download_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 下载器内部 hash（用于状态同步）
    downloader_hash = Column(String(100), nullable=True)
    
    # 下载完成后的文件路径
    downloaded_path = Column(String(1000), nullable=True)
    
    # ========== 导入结果 ==========
    # 导入后关联的 MusicFile ID
    music_file_id = Column(Integer, ForeignKey("music_files.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 导入后关联的 Music（作品）ID
    music_id = Column(Integer, ForeignKey("musics.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 是否为重复文件（有更好版本存在）
    is_duplicate = Column(Boolean, default=False)
    
    # 重复时，指向已有的 MusicFile ID
    duplicate_of_file_id = Column(Integer, nullable=True)
    
    # ========== 错误和重试 ==========
    # 错误信息
    last_error = Column(Text, nullable=True)
    
    # 重试次数
    retry_count = Column(Integer, default=0)
    
    # 最大重试次数（可配置）
    max_retries = Column(Integer, default=3)
    
    # ========== 时间戳 ==========
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)  # 开始处理时间
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_music_download_jobs_status_created", "status", "created_at"),
        Index("ix_music_download_jobs_user_status", "user_id", "status"),
        Index("ix_music_download_jobs_downloader_hash", "downloader_hash"),
    )
