"""
HNR检测相关模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base


class HNRDetection(Base):
    """HNR检测记录模型"""
    __tablename__ = "hnr_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    download_task_id = Column(Integer, ForeignKey("download_tasks.id"), nullable=True)
    title = Column(String(500), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    site_name = Column(String(100), nullable=True)
    verdict = Column(String(20), nullable=False)  # blocked, suspected, pass
    confidence = Column(Float, default=0.0)  # 置信度 0.0-1.0
    matched_rules = Column(Text, nullable=True)  # JSON字符串，匹配的规则列表
    category = Column(String(50), nullable=True)  # HNR类型
    penalties = Column(Text, nullable=True)  # JSON字符串，惩罚信息
    message = Column(Text, nullable=True)  # 检测消息
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class HNRTask(Base):
    """HNR监控任务模型"""
    __tablename__ = "hnr_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    download_task_id = Column(Integer, ForeignKey("download_tasks.id"), nullable=False)
    title = Column(String(500), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    site_name = Column(String(100), nullable=True)
    status = Column(String(20), default="monitoring")  # monitoring, completed, failed
    risk_score = Column(Float, default=0.0)  # 风险评分 0.0-1.0
    current_ratio = Column(Float, default=0.0)  # 当前分享率
    required_ratio = Column(Float, default=1.0)  # 要求分享率
    seed_time_hours = Column(Float, default=0.0)  # 做种时间（小时）
    required_seed_time_hours = Column(Float, default=0.0)  # 要求做种时间（小时）
    downloaded_gb = Column(Float, default=0.0)  # 已下载大小（GB）
    uploaded_gb = Column(Float, default=0.0)  # 已上传大小（GB）
    last_check = Column(DateTime, nullable=True)  # 最后检查时间
    next_check = Column(DateTime, nullable=True)  # 下次检查时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HNRSignature(Base):
    """HNR签名规则模型"""
    __tablename__ = "hnr_signatures"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    patterns = Column(Text, nullable=False)  # JSON字符串，匹配模式
    confidence = Column(Float, default=0.8)  # 置信度
    category = Column(String(50), nullable=True)  # 规则类别
    penalties = Column(Text, nullable=True)  # JSON字符串，惩罚信息
    is_active = Column(Boolean, default=True)
    site_ids = Column(Text, nullable=True)  # JSON字符串，适用的站点ID列表
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

