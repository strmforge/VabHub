"""
统一收件箱运行日志模型

用于记录每次 run-once 的执行结果，供健康检查使用。
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base


class InboxRunLog(Base):
    """
    统一收件箱运行日志
    
    记录每次 /api/dev/inbox/run-once 的执行结果。
    """
    __tablename__ = "inbox_run_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=False, index=True)  # 开始时间
    finished_at = Column(DateTime, nullable=True, index=True)  # 结束时间
    status = Column(String(20), nullable=False, index=True)  # 状态：success / partial / failed / empty
    total_items = Column(Integer, nullable=False, default=0, server_default="0")  # 本次扫描到的文件数
    handled_items = Column(Integer, nullable=False, default=0, server_default="0")  # 成功处理/导入的数
    skipped_items = Column(Integer, nullable=False, default=0, server_default="0")  # 跳过的数（如某 media_type disabled）
    failed_items = Column(Integer, nullable=False, default=0, server_default="0")  # 失败的数
    message = Column(Text, nullable=True)  # 总结性信息
    details = Column(JSON, nullable=True)  # 预留，存一些结构化信息（如每个 media_type 的统计）
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # 记录创建时间
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保默认值在 Python 层也生效
        if self.total_items is None:
            self.total_items = 0
        if self.handled_items is None:
            self.handled_items = 0
        if self.skipped_items is None:
            self.skipped_items = 0
        if self.failed_items is None:
            self.failed_items = 0

