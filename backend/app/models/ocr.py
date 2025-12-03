"""
OCR统计模型
用于记录OCR识别历史、统计成功率等
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, Index
from datetime import datetime
from app.core.database import Base


class OCRRecord(Base):
    """OCR识别记录"""
    __tablename__ = "ocr_records"
    
    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String(100), nullable=True, index=True)  # 站点名称
    site_url = Column(String(500), nullable=True)  # 站点URL
    image_hash = Column(String(64), nullable=True, index=True)  # 图片MD5 hash（用于缓存）
    image_url = Column(String(1000), nullable=True)  # 图片URL
    original_text = Column(String(100), nullable=True)  # 原始识别结果
    cleaned_text = Column(String(100), nullable=True)  # 清理后的识别结果
    expected_length = Column(Integer, nullable=True)  # 期望长度
    success = Column(Boolean, default=False, index=True)  # 是否成功
    confidence = Column(Float, nullable=True)  # 置信度
    engine = Column(String(50), nullable=True, index=True)  # OCR引擎（paddleocr/external_service）
    retry_count = Column(Integer, default=0)  # 重试次数
    duration_ms = Column(Integer, nullable=True)  # 耗时（毫秒）
    error_message = Column(Text, nullable=True)  # 错误信息
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # 创建时间
    
    # 索引
    __table_args__ = (
        Index('idx_ocr_site_created', 'site_name', 'created_at'),
        Index('idx_ocr_hash_created', 'image_hash', 'created_at'),
        Index('idx_ocr_success_created', 'success', 'created_at'),
    )

