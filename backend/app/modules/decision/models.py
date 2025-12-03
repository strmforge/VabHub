"""决策模块数据模型定义。"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DecisionReasonCode(str, Enum):
    """下载决策原因枚举。"""

    OK_NEW = "ok_new"
    OK_UPGRADE = "ok_upgrade"
    RULE_MISMATCH = "rule_mismatch"
    DUPLICATE_ACTIVE = "duplicate_active"
    QUALITY_INFERIOR = "quality_inferior"
    HNR_BLOCKED = "hnr_blocked"
    HNR_SUSPECTED = "hnr_suspected"
    SAFETY_BLOCKED = "safety_blocked"
    SAFETY_REQUIRE_CONFIRM = "safety_require_confirm"
    ERROR = "error"


class DecisionCandidate(BaseModel):
    """待评估的候选资源（通常对应一次搜索结果）。"""

    id: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    media_type: str
    quality: Optional[str] = None
    resolution: Optional[str] = None
    effect: Optional[str] = None
    size_gb: Optional[float] = None
    seeders: Optional[int] = 0
    site: Optional[str] = None
    release_group: Optional[str] = None
    hashes: Dict[str, str] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict)


class DecisionSubscriptionInfo(BaseModel):
    """与候选资源关联的订阅信息（简化版）。"""

    id: Optional[int] = None
    title: Optional[str] = None
    media_type: Optional[str] = None
    quality: Optional[str] = None
    resolution: Optional[str] = None
    effect: Optional[str] = None
    min_seeders: Optional[int] = None
    include: Optional[str] = None
    exclude: Optional[str] = None
    filter_groups: Optional[List[Dict[str, Any]]] = None
    search_rules: Optional[Dict[str, Any]] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionExistingItem(BaseModel):
    """用于比较的现有任务或库存项。"""

    title: str
    media_type: Optional[str] = None
    quality: Optional[str] = None
    resolution: Optional[str] = None
    effect: Optional[str] = None
    size_gb: Optional[float] = None
    status: Optional[str] = None  # downloading / seeding / completed
    source: Optional[str] = None  # download_task / library / subscription
    extra: Dict[str, Any] = Field(default_factory=dict)


class DecisionContext(BaseModel):
    """决策所需的上下文信息。"""

    subscription: DecisionSubscriptionInfo
    existing_items: List[DecisionExistingItem] = Field(default_factory=list)
    hnr_site: Optional[str] = None
    hnr_badges: Optional[str] = None
    hnr_html: Optional[str] = None
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    debug_enabled: bool = False


class DecisionResult(BaseModel):
    """决策结果。"""

    should_download: bool
    reason: DecisionReasonCode
    message: str
    score: float = 0.0
    selected_quality: Optional[str] = None
    normalized_quality: Optional[str] = None
    hnr_verdict: Optional[str] = None
    debug_context: Dict[str, Any] = Field(default_factory=dict)


