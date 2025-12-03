"""
CookieCloud配置模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from app.core.database import Base


class CookieCloudSettings(Base):
    """CookieCloud全局配置表"""
    __tablename__ = "cookiecloud_settings"

    id = Column(Integer, primary_key=True, default=1)  # 永远只有一行
    enabled = Column(Boolean, default=False, nullable=False, comment="启用CookieCloud同步")

    host = Column(String(255), nullable=True, comment="CookieCloud服务器地址")
    uuid = Column(String(128), nullable=True, comment="CookieCloud UUID")
    password = Column(String(128), nullable=True, comment="CookieCloud密码，明文存储")

    sync_interval_minutes = Column(Integer, default=60, nullable=False, comment="同步间隔（分钟）")
    
    safe_host_whitelist = Column(Text, nullable=True, comment="安全域名白名单，JSON格式")
    
    last_sync_at = Column(DateTime, nullable=True, comment="上次同步时间")
    last_status = Column(String(32), nullable=True, comment="上次同步状态：SUCCESS/ERROR/PARTIAL")
    last_error = Column(Text, nullable=True, comment="上次同步错误信息")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CookieCloudSettings(id={self.id}, enabled={self.enabled}, host='{self.host}')>"
