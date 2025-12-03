"""
SafetyPolicyEngine 核心类型定义
实现安全策略评估的上下文和决策模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict
from app.modules.hr_case.models import HrCase


class SafetyContext(BaseModel):
    """安全策略评估上下文"""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # 操作信息
    action: Literal["download", "delete", "move", "upload_cleanup", "generate_strm"]
    site_key: Optional[str] = None
    torrent_id: Optional[str] = None
    infohash: Optional[str] = None
    
    # 文件路径信息
    path_from: Optional[str] = None
    path_to: Optional[str] = None
    changes_seeding_path: bool = False
    
    # 触发来源
    trigger: Literal["system_runner", "user_web", "user_telegram", "mobile_upload"]
    
    # 关联信息
    subscription_id: Optional[int] = None
    hr_case: Optional[HrCase] = None
    
    # 扩展字段
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SafetyDecision(BaseModel):
    """安全策略决策结果"""
    
    decision: Literal["ALLOW", "DENY", "REQUIRE_CONFIRM"]
    reason_code: str
    message: str
    suggested_alternative: Optional[str] = None
    hr_status_snapshot: Optional[Dict[str, Any]] = None
    
    # 决策元数据
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_user_action: bool = False
    auto_approve_after: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    
    # 关联配置快照（用于调试）
    settings_snapshot: Optional[Dict[str, Any]] = None


class GlobalSafetySettings(BaseModel):
    """全局安全设置"""
    
    mode: Literal["SAFE", "BALANCED", "AGGRESSIVE"] = "BALANCED"
    min_keep_hours: float = Field(default=24.0, ge=0.0)
    min_ratio_for_delete: float = Field(default=0.8, ge=0.0, le=10.0)
    prefer_copy_on_move_for_hr: bool = True
    enable_hr_protection: bool = True
    
    # 高级设置
    auto_approve_hours: float = Field(default=2.0, ge=0.0)  # 自动批准时间
    enable_telegram_integration: bool = True
    enable_notification_integration: bool = True
    
    # 性能设置
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    batch_check_enabled: bool = True


class SiteSafetySettings(BaseModel):
    """站点级安全设置"""
    
    site_key: str
    hr_sensitivity: Literal["normal", "sensitive", "highly_sensitive"] = "normal"
    min_keep_ratio: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    min_keep_time_hours: Optional[float] = Field(default=None, ge=0.0)
    
    # 站点特定设置
    enable_hr_download_block: bool = True
    enable_hr_delete_block: bool = True
    enable_hr_move_warning: bool = True
    
    # 站点元数据
    site_name: Optional[str] = None
    hr_rules_url: Optional[str] = None
    hr_description: Optional[str] = None


class SubscriptionSafetySettings(BaseModel):
    """订阅级安全设置"""
    
    allow_hr: bool = False
    allow_h3h5: bool = False
    strict_free_only: bool = False
    
    # 订阅特定设置
    enable_hr_warning: bool = True
    enable_hr_confirmation: bool = True
    auto_skip_hr: bool = False
    
    # 订阅元数据
    subscription_name: Optional[str] = None
    owner_id: Optional[int] = None


class SafetyAuditLog(BaseModel):
    """安全策略审计日志"""
    
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # 上下文信息
    action: str
    site_key: Optional[str] = None
    torrent_id: Optional[str] = None
    trigger: str
    
    # 决策信息
    decision: str
    reason_code: str
    message: str
    
    # 用户响应
    user_confirmed: bool = False
    user_id: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    
    # 元数据
    hr_status_snapshot: Optional[Dict[str, Any]] = None
    settings_snapshot: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None


class SafetyStats(BaseModel):
    """安全策略统计信息"""
    
    total_evaluations: int = 0
    allowed_count: int = 0
    denied_count: int = 0
    require_confirm_count: int = 0
    
    # 按操作类型统计
    download_stats: Dict[str, int] = Field(default_factory=dict)
    delete_stats: Dict[str, int] = Field(default_factory=dict)
    move_stats: Dict[str, int] = Field(default_factory=dict)
    cleanup_stats: Dict[str, int] = Field(default_factory=dict)
    
    # 按站点统计
    site_stats: Dict[str, int] = Field(default_factory=dict)
    
    # 时间范围
    stats_from: datetime = Field(default_factory=datetime.utcnow)
    stats_to: datetime = Field(default_factory=datetime.utcnow)
    
    # 性能统计
    avg_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0


class SafetyPolicyConfig(BaseModel):
    """安全策略配置（用于API传输）"""
    
    global_settings: GlobalSafetySettings
    site_settings: list[SiteSafetySettings] = Field(default_factory=list)
    subscription_settings: list[SubscriptionSafetySettings] = Field(default_factory=list)
    
    # 功能开关
    feature_enabled: bool = True
    debug_mode: bool = False
    
    # 版本信息
    config_version: str = "1.0"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# 枚举定义
class SafetyDecisionReason:
    """安全决策原因代码"""
    
    # 允许原因
    SAFE = "safe"
    HR_SAFE = "hr_safe"
    HR_FINISHED = "hr_finished"
    SUBSCRIPTION_ALLOWED = "subscription_allowed"
    USER_CONFIRMED = "user_confirmed"
    
    # 拒绝原因
    HR_ACTIVE_DOWNLOAD = "hr_active_download"
    HR_ACTIVE_DELETE = "hr_active_delete"
    HR_ACTIVE_MOVE = "hr_active_move"
    HR_ACTIVE_CLEANUP = "hr_active_cleanup"
    RATIO_TOO_LOW = "ratio_too_low"
    TIME_TOO_SHORT = "time_too_short"
    
    # 需要确认原因
    SUBSCRIPTION_NO_HR = "subscription_no_hr"
    SITE_HIGHLY_SENSITIVE = "site_highly_sensitive"
    HR_MOVE_SUGGEST_COPY = "hr_move_suggest_copy"
    LOW_RATIO_WARNING = "low_ratio_warning"
    
    # 系统原因
    UNKNOWN_ACTION = "unknown_action"
    ERROR_OCCURRED = "error_occurred"
    SETTINGS_DISABLED = "settings_disabled"


class SafetyActionType:
    """安全操作类型"""
    
    DOWNLOAD = "download"
    DELETE = "delete"
    MOVE = "move"
    UPLOAD_CLEANUP = "upload_cleanup"
    GENERATE_STRM = "generate_strm"


class SafetyTriggerType:
    """安全触发类型"""
    
    SYSTEM_RUNNER = "system_runner"
    USER_WEB = "user_web"
    USER_TELEGRAM = "user_telegram"
    MOBILE_UPLOAD = "mobile_upload"
