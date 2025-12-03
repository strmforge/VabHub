"""
多模态分析性能指标数据模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Index, Text
from sqlalchemy.sql import func
from app.core.database import Base


class MultimodalPerformanceMetric(Base):
    """多模态分析性能指标历史记录"""
    __tablename__ = "multimodal_performance_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation = Column(String(50), nullable=False, index=True, comment="操作类型")
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True, comment="时间戳")
    
    # 性能指标
    cache_hit = Column(Boolean, default=False, comment="是否缓存命中")
    duration = Column(Float, nullable=False, comment="响应时间（秒）")
    error = Column(Boolean, default=False, comment="是否发生错误")
    concurrent = Column(Integer, default=0, comment="并发数")
    
    # 额外信息
    extra_metadata = Column(JSON, default=dict, comment="额外元数据（重命名以避免与SQLAlchemy保留字冲突）")
    
    # 索引
    __table_args__ = (
        Index('idx_operation_timestamp', 'operation', 'timestamp'),
    )


class MultimodalPerformanceAlert(Base):
    """多模态分析性能告警记录"""
    __tablename__ = "multimodal_performance_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation = Column(String(50), nullable=False, index=True, comment="操作类型")
    alert_type = Column(String(50), nullable=False, index=True, comment="告警类型")
    severity = Column(String(20), nullable=False, default="warning", comment="严重程度")
    message = Column(Text, nullable=False, comment="告警消息")
    threshold = Column(Float, comment="阈值")
    actual_value = Column(Float, comment="实际值")
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True, comment="时间戳")
    resolved = Column(Boolean, default=False, index=True, comment="是否已解决")
    resolved_at = Column(DateTime, comment="解决时间")
    resolved_by = Column(String(100), comment="解决人")
    
    # 额外信息
    extra_metadata = Column(JSON, default=dict, comment="额外元数据（重命名以避免与SQLAlchemy保留字冲突）")
    
    # 索引
    __table_args__ = (
        Index('idx_operation_alert_type', 'operation', 'alert_type'),
        Index('idx_timestamp_resolved', 'timestamp', 'resolved'),
    )


class MultimodalOptimizationHistory(Base):
    """多模态分析优化历史记录"""
    __tablename__ = "multimodal_optimization_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation = Column(String(50), nullable=False, index=True, comment="操作类型")
    optimization_type = Column(String(50), nullable=False, comment="优化类型（cache_ttl, concurrency）")
    old_value = Column(Float, comment="旧值")
    new_value = Column(Float, comment="新值")
    reason = Column(Text, comment="优化原因")
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True, comment="时间戳")
    
    # 优化效果
    improvement = Column(Float, comment="改进幅度（百分比）")
    before_metrics = Column(JSON, default=dict, comment="优化前指标")
    after_metrics = Column(JSON, default=dict, comment="优化后指标")
    
    # 额外信息
    extra_metadata = Column(JSON, default=dict, comment="额外元数据（重命名以避免与SQLAlchemy保留字冲突）")
    
    # 索引
    __table_args__ = (
        Index('idx_operation_optimization_type', 'operation', 'optimization_type'),
    )

