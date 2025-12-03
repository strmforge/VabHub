"""
订阅模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from datetime import datetime
from app.core.database import Base


class Subscription(Base):
    """订阅模型"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 订阅归属用户
    title = Column(String(255), nullable=False)
    original_title = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    media_type = Column(String(20), nullable=False)  # movie, tv
    tmdb_id = Column(Integer, nullable=True)
    tvdb_id = Column(Integer, nullable=True)
    imdb_id = Column(String(20), nullable=True)
    poster = Column(String(500), nullable=True)  # 海报图片URL
    backdrop = Column(String(500), nullable=True)  # 背景图片URL
    status = Column(String(20), default="active")  # active, paused, completed
    # 电视剧相关字段
    season = Column(Integer, nullable=True)  # 季数（电视剧专用）
    total_episode = Column(Integer, nullable=True)  # 总集数（电视剧专用）
    start_episode = Column(Integer, nullable=True)  # 起始集数（电视剧专用）
    episode_group = Column(String(100), nullable=True)  # 剧集组ID
    # 基础规则
    quality = Column(String(50), nullable=True)  # 质量：4K, 1080p, 720p等
    resolution = Column(String(50), nullable=True)  # 分辨率
    effect = Column(String(50), nullable=True)  # 特效：HDR, Dolby Vision等
    sites = Column(JSON, nullable=True)  # 订阅站点ID列表
    downloader = Column(String(50), nullable=True)  # 下载器
    save_path = Column(String(500), nullable=True)  # 保存路径
    min_seeders = Column(Integer, default=5)
    auto_download = Column(Boolean, default=True)
    best_version = Column(Boolean, default=False)  # 洗版
    search_imdbid = Column(Boolean, default=False)  # 使用IMDB ID搜索
    # 进阶规则
    include = Column(Text, nullable=True)  # 包含规则（关键字、正则式）
    exclude = Column(Text, nullable=True)  # 排除规则（关键字、正则式）
    filter_group_ids = Column(JSON, nullable=False, default=list)  # 过滤规则组ID列表
    # 其他
    search_rules = Column(JSON, nullable=True)  # 其他搜索规则
    extra_metadata = Column(JSON, nullable=True)  # 附加元数据（短剧等专用字段）
    # 安全策略字段
    allow_hr = Column(Boolean, default=False)  # 是否允许 HR/H&R
    allow_h3h5 = Column(Boolean, default=False)  # 是否允许 H3/H5 等扩展规则
    strict_free_only = Column(Boolean, default=False)  # 只下载 free/促销种
    
    # 运行状态字段
    last_check_at = Column(DateTime, nullable=True)  # 最后检查时间
    last_success_at = Column(DateTime, nullable=True)  # 最后成功时间
    last_error = Column(String(500), nullable=True)  # 最后错误信息
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_search = Column(DateTime, nullable=True)
    next_search = Column(DateTime, nullable=True)

