"""
OCR统计模型
记录OCR识别历史、成功率等信息
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON
from datetime import datetime
from app.core.database import Base


class OCRRecord(Base):
    """OCR识别记录"""
    __tablename__ = "ocr_records"
    
    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String(100), nullable=True, index=True)  # 站点名称
    site_url = Column(String(500), nullable=True)  # 站点URL
    image_hash = Column(String(64), nullable=True, index=True)  # 图片hash（用于缓存）
    image_url = Column(String(1000), nullable=True)  # 图片URL
    original_text = Column(String(100), nullable=True)  # 原始识别结果
    cleaned_text = Column(String(100), nullable=True)  # 清理后的识别结果
    expected_length = Column(Integer, nullable=True)  # 期望长度（如6位验证码）
    success = Column(Boolean, default=False, index=True)  # 是否成功
    confidence = Column(Float, nullable=True)  # 置信度
    engine = Column(String(50), nullable=True)  # OCR引擎（paddleocr/external）
    retry_count = Column(Integer, default=0)  # 重试次数
    duration_ms = Column(Integer, nullable=True)  # 识别耗时（毫秒）
    error_message = Column(Text, nullable=True)  # 错误信息
    extra_metadata = Column(JSON, nullable=True)  # 额外元数据（避免使用metadata保留字）
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class OCRStatistics(Base):
    """OCR统计信息（按站点汇总）"""
    __tablename__ = "ocr_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String(100), nullable=True, unique=True, index=True)  # 站点名称
    total_attempts = Column(Integer, default=0)  # 总尝试次数
    success_count = Column(Integer, default=0)  # 成功次数
    failure_count = Column(Integer, default=0)  # 失败次数
    success_rate = Column(Float, default=0.0)  # 成功率
    avg_retry_count = Column(Float, default=0.0)  # 平均重试次数
    avg_duration_ms = Column(Float, default=0.0)  # 平均耗时（毫秒）
    last_success_at = Column(DateTime, nullable=True)  # 最后成功时间
    last_failure_at = Column(DateTime, nullable=True)  # 最后失败时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

