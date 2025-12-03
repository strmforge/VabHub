"""
媒体识别历史记录模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base


class IdentificationHistory(Base):
    """媒体识别历史记录模型"""
    __tablename__ = "identification_history"
    
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(1000), nullable=False, index=True)  # 文件路径
    file_name = Column(String(500), nullable=True)  # 原始文件名
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    title = Column(String(500), nullable=True)  # 识别出的标题
    year = Column(Integer, nullable=True)  # 年份
    season = Column(Integer, nullable=True)  # 季数（电视剧）
    episode = Column(Integer, nullable=True)  # 集数（电视剧）
    media_type = Column(String(50), nullable=True)  # 媒体类型（movie, tv, unknown）
    confidence = Column(Float, default=0.0)  # 识别置信度
    source = Column(String(100), nullable=True)  # 识别来源（filename_parser, enhanced_identification等）
    success = Column(String(10), default="false")  # 是否成功（true, false）
    error = Column(Text, nullable=True)  # 错误信息
    raw_result = Column(JSON, nullable=True)  # 原始识别结果（JSON格式）
    identified_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)  # 识别时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

