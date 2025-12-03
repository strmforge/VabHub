"""
AI 整理顾问数据模型

FUTURE-AI-CLEANUP-ADVISOR-1 P2 实现
定义清理计划草案和相关的数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ==================== 枚举 ====================

class RiskLevel(str, Enum):
    """风险级别"""
    SAFE = "safe"       # 安全删除（已完成保种、重复低质量版本）
    CAUTION = "caution" # 需谨慎（可能仍有价值）
    RISKY = "risky"     # 高风险（仍在保种中）


class CleanupActionType(str, Enum):
    """清理操作类型"""
    DELETE = "delete"       # 删除
    ARCHIVE = "archive"     # 归档（移动到冷存储）
    TRANSCODE = "transcode" # 转码压缩
    REPLACE = "replace"     # 质量替换（删除低质量保留高质量）


class CleanupFocus(str, Enum):
    """清理聚焦"""
    ALL = "all"
    DOWNLOADS = "downloads"      # 已完成下载
    DUPLICATES = "duplicates"    # 重复媒体
    LOW_QUALITY = "low_quality"  # 低质量版本
    SEEDING = "seeding"          # 保种相关


# ==================== 清理操作 ====================

class CleanupAction(BaseModel):
    """清理操作"""
    id: str = Field(..., description="唯一标识")
    action_type: CleanupActionType = Field(..., description="操作类型")
    target_type: str = Field(..., description="目标类型: media_file / download_task / torrent")
    target_id: str = Field(..., description="目标 ID")
    target_title: str = Field(..., description="目标标题")
    target_path: Optional[str] = Field(None, description="文件路径")
    size_gb: float = Field(0.0, description="可释放空间 (GB)")
    reason: str = Field("", description="建议原因")
    risk_level: RiskLevel = Field(RiskLevel.CAUTION, description="风险级别")
    risk_notes: list[str] = Field(default_factory=list, description="风险提示")
    hr_status: Optional[str] = Field(None, description="保种状态: active / completed / none")


# ==================== 清理计划草案 ====================

class CleanupPlanDraft(BaseModel):
    """清理计划草案"""
    summary: str = Field("", description="总体说明")
    total_savable_gb: float = Field(0.0, description="预计可释放空间 (GB)")
    actions: list[CleanupAction] = Field(default_factory=list, description="建议操作列表")
    storage_context: dict[str, Any] = Field(
        default_factory=dict,
        description="存储背景信息"
    )
    warnings: list[str] = Field(default_factory=list, description="全局警告")
    generated_at: Optional[str] = Field(None, description="生成时间")
    
    @classmethod
    def fallback_draft(cls, error_message: str) -> "CleanupPlanDraft":
        """生成回退草案（解析失败时使用）"""
        return cls(
            summary=f"AI 输出解析失败: {error_message[:100]}",
            warnings=["清理计划生成失败，请稍后重试或检查 AI 服务状态。"],
            generated_at=datetime.now().isoformat(),
        )


# ==================== 请求/响应 ====================

class CleanupScope(BaseModel):
    """清理范围"""
    focus: CleanupFocus = Field(
        CleanupFocus.ALL,
        description="聚焦类型"
    )
    min_size_gb: Optional[float] = Field(
        None,
        description="最小文件大小过滤 (GB)"
    )
    include_risky: bool = Field(
        False,
        description="是否包含高风险项（仍在保种中）"
    )


class CleanupRequest(BaseModel):
    """清理建议请求"""
    prompt: Optional[str] = Field(
        None,
        description="用户自然语言描述（可选）"
    )
    focus: Optional[str] = Field(
        None,
        description="聚焦类型: all / downloads / duplicates / low_quality / seeding"
    )
    min_size_gb: Optional[float] = Field(
        None,
        description="最小文件大小过滤 (GB)"
    )
    include_risky: bool = Field(
        False,
        description="是否包含高风险项"
    )


class CleanupResponse(BaseModel):
    """清理建议响应"""
    success: bool = Field(True, description="是否成功")
    draft: Optional[CleanupPlanDraft] = Field(None, description="清理计划草案")
    error: Optional[str] = Field(None, description="错误信息")


class PresetCleanupPrompt(BaseModel):
    """预设清理提示词"""
    id: str
    title: str
    prompt: str
    description: str
    focus: Optional[str] = None


class PresetCleanupPromptsResponse(BaseModel):
    """预设清理提示词响应"""
    prompts: list[PresetCleanupPrompt] = Field(default_factory=list)


# ==================== 辅助函数 ====================

def risk_to_score(risk: RiskLevel) -> int:
    """风险级别转分数（用于排序）"""
    scores = {
        RiskLevel.SAFE: 0,
        RiskLevel.CAUTION: 1,
        RiskLevel.RISKY: 2,
    }
    return scores.get(risk, 1)
