"""
SITE-MANAGER-1 Pydantic Schema 定义
站点管理模块的数据验证和响应模型
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class SiteCategory(str, Enum):
    """站点分类枚举"""
    PT = "pt"
    BT = "bt"
    NOVEL = "novel"
    COMIC = "comic"
    MUSIC = "music"
    MOVIE = "movie"
    GAME = "game"


class HealthStatus(str, Enum):
    """健康状态枚举"""
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"


class CheckType(str, Enum):
    """检查类型枚举"""
    BASIC = "basic"
    RSS = "rss"
    API = "api"
    LOGIN = "login"


# === 基础模型 ===

class SiteCategoryModel(BaseModel):
    """站点分类模型"""
    key: str = Field(..., description="分类标识")
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, description="分类图标")
    sort_order: int = Field(0, description="排序顺序")
    enabled: bool = Field(True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class SiteStatsModel(BaseModel):
    """站点统计模型"""
    id: int = Field(..., description="统计ID")
    site_id: int = Field(..., description="站点ID")
    
    # 流量统计
    upload_bytes: int = Field(0, description="上传总量（字节）")
    download_bytes: int = Field(0, description="下载总量（字节）")
    ratio: Optional[float] = Field(None, description="分享率")
    
    # 健康状态
    last_seen_at: Optional[datetime] = Field(None, description="最近成功访问时间")
    last_error_at: Optional[datetime] = Field(None, description="最近错误时间")
    error_count: int = Field(0, description="错误次数")
    health_status: HealthStatus = Field(HealthStatus.OK, description="健康状态")
    
    # 连通性统计
    total_requests: int = Field(0, description="总请求次数")
    successful_requests: int = Field(0, description="成功请求次数")
    avg_response_time: Optional[float] = Field(None, description="平均响应时间（毫秒）")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    @property
    def upload_gb(self) -> float:
        """上传量（GB）"""
        return round(self.upload_bytes / (1024**3), 2)
    
    @property
    def download_gb(self) -> float:
        """下载量（GB）"""
        return round(self.download_bytes / (1024**3), 2)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return round(self.successful_requests / self.total_requests * 100, 2)
    
    class Config:
        from_attributes = True


class SiteAccessConfigModel(BaseModel):
    """站点访问配置模型"""
    id: int = Field(..., description="配置ID")
    site_id: int = Field(..., description="站点ID")
    
    # 访问配置
    rss_url: Optional[str] = Field(None, description="RSS地址")
    api_key: Optional[str] = Field(None, description="API密钥")
    auth_header: Optional[str] = Field(None, description="认证头")
    cookie: Optional[str] = Field(None, description="Cookie（掩码显示）")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    # 访问模式
    use_api_mode: bool = Field(False, description="使用API模式")
    use_proxy: bool = Field(False, description="使用代理")
    use_browser_emulation: bool = Field(False, description="使用浏览器仿真")
    
    # 频率控制
    min_interval_seconds: int = Field(10, description="请求最小间隔（秒）")
    max_concurrent_requests: int = Field(1, description="最大并发请求数")
    
    # 高级配置
    timeout_seconds: int = Field(30, description="请求超时时间（秒）")
    retry_count: int = Field(3, description="重试次数")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class SiteHealthCheckModel(BaseModel):
    """站点健康检查记录模型"""
    id: int = Field(..., description="检查ID")
    site_id: int = Field(..., description="站点ID")
    
    # 检查结果
    status: HealthStatus = Field(..., description="检查状态")
    response_time_ms: Optional[int] = Field(None, description="响应时间（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    http_status_code: Optional[int] = Field(None, description="HTTP状态码")
    
    # 检查类型
    check_type: CheckType = Field(CheckType.BASIC, description="检查类型")
    
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        from_attributes = True


# === 站点模型 ===

class SiteBrief(BaseModel):
    """站点简要信息（列表用）"""
    id: int = Field(..., description="站点ID")
    key: Optional[str] = Field(None, description="内部标识")
    name: str = Field(..., description="站点名称")
    domain: Optional[str] = Field(None, description="主域名")
    category: Optional[str] = Field(None, description="站点分类")
    icon_url: Optional[str] = Field(None, description="站点图标URL")
    enabled: bool = Field(..., description="启用状态")
    priority: int = Field(0, description="优先级")
    tags: Optional[str] = Field(None, description="自定义标签")
    
    # 嵌入统计信息
    stats: Optional[SiteStatsModel] = Field(None, description="站点统计")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        """解析标签字符串"""
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v
    
    class Config:
        from_attributes = True


class SiteDetail(BaseModel):
    """站点详细信息（详情页用）"""
    id: int = Field(..., description="站点ID")
    key: Optional[str] = Field(None, description="内部标识")
    name: str = Field(..., description="站点名称")
    domain: Optional[str] = Field(None, description="主域名")
    category: Optional[str] = Field(None, description="站点分类")
    icon_url: Optional[str] = Field(None, description="站点图标URL")
    enabled: bool = Field(..., description="启用状态")
    priority: int = Field(0, description="优先级")
    tags: Optional[str] = Field(None, description="自定义标签")
    
    # 原有字段
    url: str = Field(..., description="站点URL")
    cookiecloud_uuid: Optional[str] = Field(None, description="CookieCloud UUID")
    cookiecloud_server: Optional[str] = Field(None, description="CookieCloud服务器")
    last_checkin: Optional[datetime] = Field(None, description="最后签到时间")
    
    # 嵌入完整信息
    stats: Optional[SiteStatsModel] = Field(None, description="站点统计")
    access_config: Optional[SiteAccessConfigModel] = Field(None, description="访问配置")
    
    # 健康检查历史（最近N次）
    recent_health_checks: Optional[List[SiteHealthCheckModel]] = Field(None, description="最近健康检查记录")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class SiteUpdatePayload(BaseModel):
    """站点更新请求载荷"""
    name: Optional[str] = Field(None, description="站点名称")
    domain: Optional[str] = Field(None, description="主域名")
    category: Optional[str] = Field(None, description="站点分类")
    icon_url: Optional[str] = Field(None, description="站点图标URL")
    enabled: Optional[bool] = Field(None, description="启用状态")
    priority: Optional[int] = Field(None, description="优先级")
    tags: Optional[str] = Field(None, description="自定义标签")
    url: Optional[str] = Field(None, description="站点URL")
    
    # CookieCloud配置
    cookiecloud_uuid: Optional[str] = Field(None, description="CookieCloud UUID")
    cookiecloud_password: Optional[str] = Field(None, description="CookieCloud密码")
    cookiecloud_server: Optional[str] = Field(None, description="CookieCloud服务器")


class SiteAccessConfigPayload(BaseModel):
    """站点访问配置更新请求载荷"""
    rss_url: Optional[str] = Field(None, description="RSS地址")
    api_key: Optional[str] = Field(None, description="API密钥")
    auth_header: Optional[str] = Field(None, description="认证头")
    cookie: Optional[str] = Field(None, description="Cookie")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    # 访问模式
    use_api_mode: Optional[bool] = Field(None, description="使用API模式")
    use_proxy: Optional[bool] = Field(None, description="使用代理")
    use_browser_emulation: Optional[bool] = Field(None, description="使用浏览器仿真")
    
    # 频率控制
    min_interval_seconds: Optional[int] = Field(None, ge=1, le=3600, description="请求最小间隔（秒）")
    max_concurrent_requests: Optional[int] = Field(None, ge=1, le=10, description="最大并发请求数")
    
    # 高级配置
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300, description="请求超时时间（秒）")
    retry_count: Optional[int] = Field(None, ge=0, le=10, description="重试次数")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="自定义请求头")


# === 导入导出模型 ===

class SiteImportItem(BaseModel):
    """站点导入项"""
    key: Optional[str] = Field(None, description="内部标识")
    name: str = Field(..., description="站点名称")
    domain: str = Field(..., description="主域名")
    category: Optional[str] = Field("pt", description="站点分类")
    icon_url: Optional[str] = Field(None, description="站点图标URL")
    enabled: bool = Field(True, description="启用状态")
    priority: int = Field(0, description="优先级")
    tags: Optional[str] = Field(None, description="自定义标签")
    url: str = Field(..., description="站点URL")
    
    # 访问配置
    rss_url: Optional[str] = Field(None, description="RSS地址")
    use_proxy: bool = Field(False, description="使用代理")
    use_browser_emulation: bool = Field(False, description="使用浏览器仿真")
    min_interval_seconds: int = Field(10, description="请求最小间隔（秒）")
    max_concurrent_requests: int = Field(1, description="最大并发请求数")


class SiteExportItem(BaseModel):
    """站点导出项"""
    key: Optional[str] = Field(None, description="内部标识")
    name: str = Field(..., description="站点名称")
    domain: str = Field(..., description="主域名")
    category: Optional[str] = Field(None, description="站点分类")
    icon_url: Optional[str] = Field(None, description="站点图标URL")
    enabled: bool = Field(..., description="启用状态")
    priority: int = Field(..., description="优先级")
    tags: Optional[str] = Field(None, description="自定义标签")
    url: str = Field(..., description="站点URL")
    
    # 访问配置
    rss_url: Optional[str] = Field(None, description="RSS地址")
    use_proxy: bool = Field(False, description="使用代理")
    use_browser_emulation: bool = Field(False, description="使用浏览器仿真")
    min_interval_seconds: int = Field(10, description="请求最小间隔（秒）")
    max_concurrent_requests: int = Field(1, description="最大并发请求数")


# === 健康检查模型 ===

class SiteHealthResult(BaseModel):
    """站点健康检查结果"""
    site_id: int = Field(..., description="站点ID")
    status: HealthStatus = Field(..., description="检查状态")
    response_time_ms: Optional[int] = Field(None, description="响应时间（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    http_status_code: Optional[int] = Field(None, description="HTTP状态码")
    check_type: CheckType = Field(CheckType.BASIC, description="检查类型")
    checked_at: datetime = Field(..., description="检查时间")


# === 列表和响应模型 ===

class SiteListFilter(BaseModel):
    """站点列表过滤器"""
    enabled: Optional[bool] = Field(None, description="启用状态过滤")
    category: Optional[str] = Field(None, description="分类过滤")
    health_status: Optional[HealthStatus] = Field(None, description="健康状态过滤")
    keyword: Optional[str] = Field(None, description="关键词搜索（名称/域名）")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    priority_min: Optional[int] = Field(None, ge=0, description="最小优先级")
    priority_max: Optional[int] = Field(None, ge=0, description="最大优先级")


class SiteListResponse(BaseModel):
    """站点列表响应"""
    items: List[SiteBrief] = Field(..., description="站点列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class ImportResult(BaseModel):
    """导入结果"""
    total: int = Field(..., description="总数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败项详情")
    message: str = Field(..., description="结果消息")


class BatchHealthCheckResult(BaseModel):
    """批量健康检查结果"""
    total: int = Field(..., description="总数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: List[SiteHealthResult] = Field(..., description="检查结果列表")
    message: str = Field(..., description="结果消息")
