"""
AI 订阅工作流草案 Schema

FUTURE-AI-SUBS-WORKFLOW-1 P1 实现
定义订阅工作流草案的统一数据结构，用于 AI 生成的订阅规则建议。

设计说明：
- SubsWorkflowDraft 是 AI 生成的"草案"，不直接等同于真实订阅模型
- 草案需要经过验证和映射后，才能转换为真实的 Subscription / UserRSSHubSubscription
- 所有字段都设计为可选或有安全默认值，以容忍 LLM 输出的不完整性
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SubsTargetMediaType(str, Enum):
    """订阅目标媒体类型"""
    MOVIE = "movie"
    TV = "tv"
    ANIME = "anime"
    SHORT_DRAMA = "short_drama"
    MUSIC = "music"
    BOOK = "book"
    COMIC = "comic"


class SubsSourceType(str, Enum):
    """订阅来源类型"""
    RSSHUB = "rsshub"
    PT_SEARCH = "pt_search"
    RSS_URL = "rss_url"  # v2 预留


class SubsWorkflowSource(BaseModel):
    """
    订阅工作流来源配置
    
    描述订阅数据的来源，可以是 RSSHub 源或 PT 站点搜索。
    """
    type: SubsSourceType = Field(..., description="来源类型")
    id: Optional[str] = Field(None, description="来源 ID（RSSHub source_id 或站点 key）")
    name: Optional[str] = Field(None, description="来源名称（用于显示）")
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="额外参数")
    
    # 验证状态（由后端填充）
    valid: Optional[bool] = Field(None, description="是否验证通过（后端填充）")
    validation_message: Optional[str] = Field(None, description="验证信息（后端填充）")


class SubsFilterRule(BaseModel):
    """
    订阅过滤规则
    
    定义订阅的过滤条件，包括关键词、分辨率、HR 策略等。
    """
    include_keywords: List[str] = Field(default_factory=list, description="包含关键词列表")
    exclude_keywords: List[str] = Field(default_factory=list, description="排除关键词列表")
    
    # 质量相关
    min_resolution: Optional[str] = Field(None, description="最低分辨率：720p / 1080p / 2160p")
    preferred_resolution: Optional[str] = Field(None, description="首选分辨率")
    effect: Optional[str] = Field(None, description="特效偏好：HDR / Dolby Vision")
    
    # 安全策略
    hr_safe: Optional[bool] = Field(None, description="是否优先 HR 安全（True=不下载 HR 种）")
    free_only: Optional[bool] = Field(None, description="是否只下载 free/促销种")
    
    # 其他约束
    languages: List[str] = Field(default_factory=list, description="音轨/字幕语言偏好")
    min_seeders: Optional[int] = Field(None, description="最小做种数")
    other_constraints: Dict[str, Any] = Field(default_factory=dict, description="其他约束条件")


class SubsActionConfig(BaseModel):
    """
    订阅动作配置
    
    定义订阅匹配后的执行动作。
    """
    download_enabled: bool = Field(False, description="是否启用自动下载（v1 默认 False）")
    dry_run: bool = Field(True, description="仅预览模式（v1 默认 True）")
    target_library: Optional[str] = Field(None, description="目标媒体库路径/分类")
    notify_on_match: bool = Field(True, description="匹配时是否通知")
    downloader: Optional[str] = Field(None, description="指定下载器")
    
    # 洗版设置
    best_version: bool = Field(False, description="是否启用洗版")


class SubsWorkflowDraft(BaseModel):
    """
    订阅工作流草案
    
    AI 生成的订阅规则草案，包含完整的订阅配置建议。
    这是一个中间格式，需要经过验证和映射后才能应用到真实订阅模型。
    
    设计原则：
    - 所有字段都有合理的默认值，容忍 LLM 输出不完整
    - 包含 AI 解释文本，帮助用户理解草案内容
    - 包含验证状态字段，由后端填充
    """
    # 基础信息
    name: str = Field(..., description="订阅名称")
    description: Optional[str] = Field(None, description="订阅描述")
    media_type: SubsTargetMediaType = Field(..., description="媒体类型")
    
    # 来源配置
    sources: List[SubsWorkflowSource] = Field(default_factory=list, description="订阅来源列表")
    
    # 过滤规则
    filter_rule: SubsFilterRule = Field(default_factory=SubsFilterRule, description="过滤规则")
    
    # 动作配置
    action: SubsActionConfig = Field(default_factory=SubsActionConfig, description="动作配置")
    
    # AI 生成的解释
    ai_explanation: Optional[str] = Field(None, description="AI 对该草案的解释说明")
    
    # 验证状态（由后端填充）
    valid: Optional[bool] = Field(None, description="整体验证状态（后端填充）")
    validation_warnings: List[str] = Field(default_factory=list, description="验证警告列表（后端填充）")
    validation_errors: List[str] = Field(default_factory=list, description="验证错误列表（后端填充）")


class SubsWorkflowDraftList(BaseModel):
    """
    订阅工作流草案列表
    
    LLM 返回的完整草案响应，包含多个草案和总结信息。
    """
    drafts: List[SubsWorkflowDraft] = Field(default_factory=list, description="草案列表")
    summary: str = Field("", description="总结说明")
    notes: Optional[str] = Field(None, description="风险提示/注意事项")


# ==================== API 请求/响应模型 ====================

class SubsWorkflowPreviewRequest(BaseModel):
    """
    订阅工作流预览请求
    """
    prompt: str = Field(..., description="自然语言描述", min_length=1, max_length=1000)
    media_type_hint: Optional[SubsTargetMediaType] = Field(None, description="媒体类型提示")
    language_hint: Optional[str] = Field(None, description="语言偏好提示")
    force_dummy: bool = Field(False, description="强制使用 Dummy LLM（调试用）")


class SubsWorkflowPreviewResponse(BaseModel):
    """
    订阅工作流预览响应
    """
    success: bool = Field(..., description="是否成功")
    drafts: List[SubsWorkflowDraft] = Field(default_factory=list, description="草案列表")
    summary: str = Field("", description="总结说明")
    notes: Optional[str] = Field(None, description="风险提示/注意事项")
    
    # 调试信息
    orchestrator_plan: Optional[List[Dict[str, Any]]] = Field(None, description="Orchestrator 执行计划")
    error: Optional[str] = Field(None, description="错误信息")


class SubsWorkflowApplyRequest(BaseModel):
    """
    订阅工作流应用请求
    """
    draft: SubsWorkflowDraft = Field(..., description="要应用的草案")
    confirm: bool = Field(False, description="确认应用（必须为 True）")


class SubsWorkflowApplyResponse(BaseModel):
    """
    订阅工作流应用响应
    """
    success: bool = Field(..., description="是否成功")
    subscription_id: Optional[int] = Field(None, description="创建的订阅 ID")
    subscription_name: Optional[str] = Field(None, description="创建的订阅名称")
    rsshub_subscriptions_created: int = Field(0, description="创建的 RSSHub 订阅数")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    error: Optional[str] = Field(None, description="错误信息")


# ==================== 辅助函数 ====================

def resolution_to_quality(resolution: Optional[str]) -> Optional[str]:
    """
    将分辨率转换为质量标识
    
    Args:
        resolution: 分辨率字符串，如 "2160p", "1080p", "720p"
        
    Returns:
        质量标识，如 "4K", "1080p", "720p"
    """
    if not resolution:
        return None
    
    resolution_lower = resolution.lower()
    if "2160" in resolution_lower or "4k" in resolution_lower:
        return "4K"
    elif "1080" in resolution_lower:
        return "1080p"
    elif "720" in resolution_lower:
        return "720p"
    elif "480" in resolution_lower:
        return "480p"
    
    return resolution


def draft_to_subscription_dict(
    draft: SubsWorkflowDraft,
    user_id: int,
) -> Dict[str, Any]:
    """
    将草案转换为订阅创建字典
    
    Args:
        draft: 订阅工作流草案
        user_id: 用户 ID
        
    Returns:
        可用于 SubscriptionService.create_subscription() 的字典
    """
    # 收集 PT 站点 ID
    site_ids = []
    for source in draft.sources:
        if source.type == SubsSourceType.PT_SEARCH and source.id:
            try:
                site_ids.append(int(source.id))
            except ValueError:
                pass  # 非数字 ID，跳过
    
    # 构建 include/exclude 字符串
    include_parts = list(draft.filter_rule.include_keywords)
    if draft.filter_rule.languages:
        include_parts.extend(draft.filter_rule.languages)
    include_str = ",".join(include_parts) if include_parts else None
    
    exclude_str = ",".join(draft.filter_rule.exclude_keywords) if draft.filter_rule.exclude_keywords else None
    
    # 映射安全策略（hr_safe=True 意味着 allow_hr=False）
    allow_hr = not draft.filter_rule.hr_safe if draft.filter_rule.hr_safe is not None else False
    strict_free_only = draft.filter_rule.free_only if draft.filter_rule.free_only is not None else False
    
    return {
        "user_id": user_id,
        "title": draft.name,
        "media_type": draft.media_type.value,
        "quality": resolution_to_quality(draft.filter_rule.min_resolution),
        "resolution": draft.filter_rule.preferred_resolution,
        "effect": draft.filter_rule.effect,
        "sites": site_ids if site_ids else None,
        "downloader": draft.action.downloader,
        "save_path": draft.action.target_library,
        "min_seeders": draft.filter_rule.min_seeders or 5,
        "auto_download": draft.action.download_enabled,
        "best_version": draft.action.best_version,
        "include": include_str,
        "exclude": exclude_str,
        "allow_hr": allow_hr,
        "strict_free_only": strict_free_only,
        "status": "active" if draft.action.download_enabled else "paused",
    }
