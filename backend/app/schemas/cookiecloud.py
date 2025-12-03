"""
CookieCloud Pydantic Schema 定义
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class CookieCloudSettingsBase(BaseModel):
    """CookieCloud配置基础模型"""
    enabled: bool = Field(False, description="启用CookieCloud同步")
    host: Optional[str] = Field(None, description="CookieCloud服务器地址，如 https://cookiecloud.example.com")
    uuid: Optional[str] = Field(None, description="CookieCloud UUID")
    password: Optional[str] = Field(None, description="CookieCloud密码")
    sync_interval_minutes: int = Field(60, description="同步间隔（分钟）")
    safe_host_whitelist: Optional[List[str]] = Field(None, description="安全域名白名单")

    @validator('host')
    def validate_host(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('host必须以http://或https://开头')
        if v:
            v = v.rstrip('/')  # 去掉末尾斜杠
        return v

    @validator('uuid')
    def validate_uuid(cls, v):
        if v and len(v) < 8:
            raise ValueError('UUID长度不能少于8个字符')
        return v

    @validator('sync_interval_minutes')
    def validate_sync_interval(cls, v):
        if v < 5:
            raise ValueError('同步间隔不能少于5分钟')
        if v > 1440:  # 24小时
            raise ValueError('同步间隔不能超过24小时')
        return v


class CookieCloudSettingsRead(CookieCloudSettingsBase):
    """CookieCloud配置读取模型"""
    id: int
    last_sync_at: Optional[datetime] = Field(None, description="上次同步时间")
    last_status: Optional[str] = Field(None, description="上次同步状态")
    last_error: Optional[str] = Field(None, description="上次同步错误信息")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CookieCloudSettingsUpdate(BaseModel):
    """CookieCloud配置更新模型"""
    enabled: Optional[bool] = Field(None, description="启用CookieCloud同步")
    host: Optional[str] = Field(None, description="CookieCloud服务器地址")
    uuid: Optional[str] = Field(None, description="CookieCloud UUID")
    password: Optional[str] = Field(None, description="CookieCloud密码")
    sync_interval_minutes: Optional[int] = Field(None, description="同步间隔（分钟）")
    safe_host_whitelist: Optional[List[str]] = Field(None, description="安全域名白名单")

    @validator('host')
    def validate_host(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('host必须以http://或https://开头')
        if v:
            v = v.rstrip('/')
        return v

    @validator('uuid')
    def validate_uuid(cls, v):
        if v and len(v) < 8:
            raise ValueError('UUID长度不能少于8个字符')
        return v

    @validator('sync_interval_minutes')
    def validate_sync_interval(cls, v):
        if v is not None:
            if v < 5:
                raise ValueError('同步间隔不能少于5分钟')
            if v > 1440:
                raise ValueError('同步间隔不能超过24小时')
        return v


class CookieCloudSyncResult(BaseModel):
    """CookieCloud同步结果"""
    success: bool = Field(description="同步是否成功")
    total_sites: int = Field(description="总站点数")
    synced_sites: int = Field(description="成功同步的站点数")
    unmatched_sites: int = Field(description="无匹配Cookie的站点数")
    error_sites: int = Field(description="同步失败的站点数")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    sync_time: datetime = Field(default_factory=datetime.utcnow, description="同步时间")


class SiteCookieSyncResult(BaseModel):
    """单站点Cookie同步结果"""
    success: bool = Field(description="同步是否成功")
    site_id: int = Field(description="站点ID")
    site_name: str = Field(description="站点名称")
    domain: str = Field(description="站点域名")
    cookie_updated: bool = Field(description="Cookie是否已更新")
    error_message: Optional[str] = Field(None, description="错误信息")
    sync_time: datetime = Field(default_factory=datetime.utcnow, description="同步时间")


class CookieCloudSiteSyncResult(BaseModel):
    """CookieCloud单站点同步结果"""
    site_id: int = Field(description="站点ID")
    site_name: str = Field(description="站点名称")
    success: bool = Field(description="同步是否成功")
    cookie_updated: bool = Field(description="Cookie是否已更新")
    error_message: Optional[str] = Field(None, description="错误信息")
    duration_seconds: Optional[float] = Field(None, description="同步耗时（秒）")


class CookieCloudTestResult(BaseModel):
    """CookieCloud连接测试结果"""
    success: bool = Field(description="测试是否成功")
    message: str = Field(description="测试结果消息")
    details: Optional[dict] = Field(None, description="测试详细信息")


# Cookie来源枚举
class CookieSource(str):
    """Cookie来源枚举"""
    MANUAL = "MANUAL"  # 手动设置
    COOKIECLOUD = "COOKIECLOUD"  # CookieCloud同步
