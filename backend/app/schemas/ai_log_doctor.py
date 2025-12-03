"""
AI 故障医生数据模型

FUTURE-AI-LOG-DOCTOR-1 P2 实现
定义诊断报告和相关的数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ==================== 枚举 ====================

class DiagnosisSeverity(str, Enum):
    """诊断严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DiagnosisTimeWindow(str, Enum):
    """诊断时间窗口"""
    HOUR_1 = "1h"
    HOUR_24 = "24h"
    DAY_7 = "7d"


class DiagnosisFocus(str, Enum):
    """诊断聚焦组件"""
    ALL = "all"
    DOWNLOAD = "download"
    RSSHUB = "rsshub"
    SITE = "site"
    RUNNER = "runner"
    TELEGRAM = "telegram"
    STORAGE = "storage"


# ==================== 诊断项 ====================

class DiagnosisItem(BaseModel):
    """诊断项"""
    id: str = Field(..., description="唯一标识")
    severity: DiagnosisSeverity = Field(..., description="严重程度")
    title: str = Field(..., description="问题标题")
    description: str = Field(..., description="问题描述")
    evidence: list[str] = Field(default_factory=list, description="证据（日志片段/检查项摘要）")
    related_components: list[str] = Field(default_factory=list, description="相关组件标识")


class DiagnosisPlanStep(BaseModel):
    """建议操作步骤"""
    step: int = Field(..., description="步骤编号")
    title: str = Field(..., description="步骤标题")
    detail: str = Field(..., description="详细说明")
    is_safe: bool = Field(True, description="是否为安全操作（只读检查）")


# ==================== 诊断报告 ====================

class SystemDiagnosisReport(BaseModel):
    """系统诊断报告"""
    overall_status: DiagnosisSeverity = Field(
        DiagnosisSeverity.INFO,
        description="总体健康状态"
    )
    summary: str = Field("", description="一句话总结")
    items: list[DiagnosisItem] = Field(default_factory=list, description="诊断项列表")
    suggested_steps: list[DiagnosisPlanStep] = Field(
        default_factory=list,
        description="建议操作步骤"
    )
    raw_refs: dict[str, Any] = Field(
        default_factory=dict,
        description="原始数据引用（调试用）"
    )
    generated_at: Optional[str] = Field(None, description="生成时间")
    
    @classmethod
    def fallback_report(cls, error_message: str) -> "SystemDiagnosisReport":
        """生成回退报告（解析失败时使用）"""
        return cls(
            overall_status=DiagnosisSeverity.WARNING,
            summary=f"AI 输出解析失败: {error_message[:100]}",
            items=[
                DiagnosisItem(
                    id="parse_error",
                    severity=DiagnosisSeverity.WARNING,
                    title="诊断报告生成异常",
                    description="AI 返回的诊断结果无法解析，请检查 raw_refs 中的原始输出。",
                    evidence=[error_message[:200]],
                    related_components=["ai_orchestrator"],
                )
            ],
            suggested_steps=[
                DiagnosisPlanStep(
                    step=1,
                    title="检查 AI 服务状态",
                    detail="确认 AI Orchestrator 配置正确，LLM 服务可用。",
                    is_safe=True,
                )
            ],
            generated_at=datetime.now().isoformat(),
        )


# ==================== 请求/响应 ====================

class DiagnosisScope(BaseModel):
    """诊断范围"""
    time_window: DiagnosisTimeWindow = Field(
        DiagnosisTimeWindow.HOUR_24,
        description="时间窗口"
    )
    focus: DiagnosisFocus = Field(
        DiagnosisFocus.ALL,
        description="聚焦组件"
    )


class DiagnoseRequest(BaseModel):
    """诊断请求"""
    prompt: Optional[str] = Field(
        None,
        description="用户自然语言描述（可选）"
    )
    time_window: Optional[str] = Field(
        "24h",
        description="时间窗口: 1h / 24h / 7d"
    )
    focus: Optional[str] = Field(
        None,
        description="聚焦组件: download / rsshub / site / runner / telegram / storage"
    )


class DiagnoseResponse(BaseModel):
    """诊断响应"""
    success: bool = Field(True, description="是否成功")
    report: Optional[SystemDiagnosisReport] = Field(None, description="诊断报告")
    error: Optional[str] = Field(None, description="错误信息")


class PresetPrompt(BaseModel):
    """预设提示词"""
    id: str
    title: str
    prompt: str
    description: str
    focus: Optional[str] = None


class PresetPromptsResponse(BaseModel):
    """预设提示词响应"""
    prompts: list[PresetPrompt] = Field(default_factory=list)


# ==================== 辅助函数 ====================

def severity_to_score(severity: DiagnosisSeverity) -> int:
    """严重程度转分数（用于排序）"""
    scores = {
        DiagnosisSeverity.INFO: 0,
        DiagnosisSeverity.WARNING: 1,
        DiagnosisSeverity.ERROR: 2,
        DiagnosisSeverity.CRITICAL: 3,
    }
    return scores.get(severity, 0)


def get_overall_severity(items: list[DiagnosisItem]) -> DiagnosisSeverity:
    """根据诊断项计算总体严重程度"""
    if not items:
        return DiagnosisSeverity.INFO
    
    max_score = max(severity_to_score(item.severity) for item in items)
    
    if max_score >= 3:
        return DiagnosisSeverity.CRITICAL
    elif max_score >= 2:
        return DiagnosisSeverity.ERROR
    elif max_score >= 1:
        return DiagnosisSeverity.WARNING
    else:
        return DiagnosisSeverity.INFO
