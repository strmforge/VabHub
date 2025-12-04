"""
站点模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, BigInteger, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Site(Base):
    """PT站点模型 - 扩展版本 (SITE-MANAGER-1)"""
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    # SITE-MANAGER-1 新增字段
    key = Column(String(50), unique=True, index=True, nullable=True, comment="内部标识，如 hdhome")
    domain = Column(String(255), nullable=True, comment="主域名，如 hdhome.org")
    category = Column(String(50), nullable=True, comment="类型：PT/BT/小说/漫画/音乐")
    icon_url = Column(String(500), nullable=True, comment="站点图标URL")
    priority = Column(Integer, default=0, comment="优先级，越大越靠前")
    tags = Column(String(500), nullable=True, comment="自定义标签，逗号分隔")
    
    # 原有字段保持不变
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    cookie = Column(Text, nullable=True)
    cookiecloud_uuid = Column(String(100), nullable=True)
    cookiecloud_password = Column(String(100), nullable=True)
    cookiecloud_server = Column(String(500), nullable=True)  # CookieCloud服务器地址
    cookie_source = Column(String(32), nullable=True, default="MANUAL", comment="Cookie来源: MANUAL/COOKIECLOUD/API")
    last_cookiecloud_sync_at = Column(DateTime, nullable=True, comment="最近CookieCloud同步时间")
    is_active = Column(Boolean, default=True)  # 保持原字段，enabled作为别名
    user_data = Column(JSON, nullable=True)  # 用户数据（上传量、下载量等）
    last_checkin = Column(DateTime, nullable=True)  # 最后签到时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # SITE-MANAGER-1 关联关系
    stats = relationship("SiteStats", back_populates="site", uselist=False)
    access_config = relationship("SiteAccessConfig", back_populates="site", uselist=False)
    # hr_cases = relationship("HrCase", back_populates="site")  # 移除以避免外键关系问题
    
    @property
    def enabled(self) -> bool:
        """启用状态别名，保持API兼容性"""
        return self.is_active
    
    @enabled.setter
    def enabled(self, value: bool):
        """启用状态设置器，保持API兼容性"""
        self.is_active = value


class SiteStats(Base):
    """站点统计信息 (SITE-MANAGER-1)"""
    __tablename__ = "site_stats"
    
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, unique=True, comment="关联站点ID")
    
    # 流量统计
    upload_bytes = Column(BigInteger, default=0, comment="上传总量（字节）")
    download_bytes = Column(BigInteger, default=0, comment="下载总量（字节）")
    ratio = Column(Float, nullable=True, comment="分享率快照")
    
    # 健康状态
    last_seen_at = Column(DateTime, nullable=True, comment="最近成功访问时间")
    last_error_at = Column(DateTime, nullable=True, comment="最近错误时间")
    error_count = Column(Integer, default=0, comment="错误次数")
    health_status = Column(String(20), default="OK", comment="健康状态: OK/WARN/ERROR")
    
    # 连通性统计
    total_requests = Column(Integer, default=0, comment="总请求次数")
    successful_requests = Column(Integer, default=0, comment="成功请求次数")
    avg_response_time = Column(Float, nullable=True, comment="平均响应时间（毫秒）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    site = relationship("Site", back_populates="stats")


class SiteAccessConfig(Base):
    """站点访问配置 (SITE-MANAGER-1)"""
    __tablename__ = "site_access_configs"
    
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, unique=True, comment="关联站点ID")
    
    # 访问配置
    rss_url = Column(String(500), nullable=True, comment="RSS地址")
    api_key = Column(String(255), nullable=True, comment="API密钥")
    auth_header = Column(String(500), nullable=True, comment="认证头，如 Authorization: Bearer xxx")
    cookie = Column(Text, nullable=True, comment="Cookie（加密存储）")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    
    # 访问模式
    use_api_mode = Column(Boolean, default=False, comment="使用API模式")
    use_proxy = Column(Boolean, default=False, comment="使用代理")
    use_browser_emulation = Column(Boolean, default=False, comment="使用浏览器仿真")
    
    # 频率控制
    min_interval_seconds = Column(Integer, default=10, comment="请求最小间隔（秒）")
    max_concurrent_requests = Column(Integer, default=1, comment="最大并发请求数")
    
    # 高级配置
    timeout_seconds = Column(Integer, default=30, comment="请求超时时间（秒）")
    retry_count = Column(Integer, default=3, comment="重试次数")
    custom_headers = Column(JSON, nullable=True, comment="自定义请求头")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    site = relationship("Site", back_populates="access_config")


class SiteCategory(Base):
    """站点分类枚举表 (SITE-MANAGER-1)"""
    __tablename__ = "site_categories"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, index=True, comment="分类标识")
    name = Column(String(100), nullable=False, comment="分类名称")
    description = Column(String(500), nullable=True, comment="分类描述")
    icon = Column(String(100), nullable=True, comment="分类图标")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)


class SiteHealthCheck(Base):
    """站点健康检查记录 (SITE-MANAGER-1)"""
    __tablename__ = "site_health_checks"
    
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True, comment="关联站点ID")
    
    # 检查结果
    status = Column(String(20), nullable=False, comment="检查状态: OK/WARN/ERROR")
    response_time_ms = Column(Integer, nullable=True, comment="响应时间（毫秒）")
    error_message = Column(Text, nullable=True, comment="错误信息")
    http_status_code = Column(Integer, nullable=True, comment="HTTP状态码")
    
    # 检查类型
    check_type = Column(String(50), default="basic", comment="检查类型: basic/rss/api/login")
    
    # 时间戳
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关联关系
    site = relationship("Site")

