"""
转移历史记录模型
参考MoviePilot的TransferHistory实现
"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class TransferHistory(Base):
    """转移历史记录"""
    __tablename__ = "transfer_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 源路径
    src = Column(String(1000), nullable=False, index=True)
    # 源存储
    src_storage = Column(String(50), nullable=False, default="local")
    # 源文件项（JSON）
    src_fileitem = Column(JSON, default=dict)
    
    # 目标路径
    dest = Column(String(1000), nullable=False)
    # 目标存储
    dest_storage = Column(String(50), nullable=False, default="local")
    # 目标文件项（JSON）
    dest_fileitem = Column(JSON, default=dict)
    
    # 转移模式 move/copy/link/softlink
    mode = Column(String(50), nullable=False, default="move")
    
    # 媒体信息
    type = Column(String(50), nullable=True)  # movie/tv
    category = Column(String(100), nullable=True)  # 二级分类（如：日番、国港、综艺等）
    title = Column(String(500), nullable=True, index=True)
    year = Column(String(10), nullable=True)
    tmdbid = Column(Integer, nullable=True, index=True)
    imdbid = Column(String(50), nullable=True)
    tvdbid = Column(Integer, nullable=True)
    doubanid = Column(String(50), nullable=True)
    seasons = Column(String(50), nullable=True)  # S01
    episodes = Column(String(50), nullable=True)  # E01
    episode_group = Column(String(100), nullable=True)  # 剧集组
    
    # 文件信息
    files = Column(JSON, default=list)  # 文件清单
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    
    # 海报
    image = Column(String(1000), nullable=True)
    
    # 下载器信息
    downloader = Column(String(50), nullable=True)
    download_hash = Column(String(100), nullable=True, index=True)
    
    # 转移状态
    status = Column(Boolean, default=True, nullable=False)  # True=成功, False=失败
    errmsg = Column(String(1000), nullable=True)  # 错误信息
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    date = Column(String(50), nullable=True, index=True)  # 格式化的日期字符串，用于查询
    
    # 索引
    __table_args__ = (
        Index('idx_transfer_history_title', 'title'),
        Index('idx_transfer_history_date', 'date'),
        Index('idx_transfer_history_status', 'status'),
        Index('idx_transfer_history_src', 'src'),
    )

