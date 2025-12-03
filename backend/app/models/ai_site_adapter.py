"""
站点 AI 适配配置数据库模型

存储由 Cloudflare AI 服务生成的站点适配配置。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from datetime import datetime
from app.core.database import Base


class AISiteAdapter(Base):
    """站点 AI 适配配置表"""
    __tablename__ = "ai_site_adapters"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(100), nullable=False, index=True, unique=True)
    engine = Column(String(50), nullable=False)  # 如 "nexusphp", "gazelle" 等
    config_json = Column(JSON, nullable=False)  # 适配配置 JSON
    raw_model_output = Column(Text, nullable=True)  # 原始 LLM 输出（用于调试）
    version = Column(Integer, default=1, nullable=False)  # 配置版本号
    # Phase AI-4: 站点级别的 AI 适配控制
    disabled = Column(Boolean, default=False, nullable=False)  # 是否禁用本站点的 AI 适配
    manual_profile_preferred = Column(Boolean, default=False, nullable=False)  # 是否优先使用人工配置
    confidence_score = Column(Integer, nullable=True)  # AI 配置可信度分数（0-100）
    last_error = Column(Text, nullable=True)  # 最近一次 AI 调用失败摘要
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

