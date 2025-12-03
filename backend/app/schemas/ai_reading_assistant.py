"""
AI 阅读助手数据模型

FUTURE-AI-READING-ASSISTANT-1 P2 实现
定义阅读计划草案和相关的数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ==================== 枚举 ====================

class ReadingGoalType(str, Enum):
    """阅读目标类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SuggestionType(str, Enum):
    """建议类型"""
    CONTINUE = "continue"   # 继续阅读
    START = "start"         # 开始新书
    FINISH = "finish"       # 完成当前
    PAUSE = "pause"         # 暂停建议


class SuggestionPriority(str, Enum):
    """建议优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ==================== 阅读目标 ====================

class ReadingGoal(BaseModel):
    """阅读目标"""
    goal_type: ReadingGoalType = Field(..., description="目标类型")
    target_count: int = Field(1, description="目标数量")
    current_count: int = Field(0, description="当前进度")
    media_types: list[str] = Field(default_factory=list, description="适用媒体类型")
    deadline: Optional[str] = Field(None, description="截止日期")
    description: str = Field("", description="目标描述")


# ==================== 阅读建议 ====================

class ReadingSuggestion(BaseModel):
    """阅读建议"""
    suggestion_type: SuggestionType = Field(..., description="建议类型")
    media_type: str = Field(..., description="媒体类型: novel / manga / audiobook")
    item_id: Optional[int] = Field(None, description="书籍/漫画 ID")
    title: str = Field(..., description="标题")
    author: Optional[str] = Field(None, description="作者")
    reason: str = Field("", description="推荐理由")
    priority: SuggestionPriority = Field(SuggestionPriority.MEDIUM, description="优先级")
    estimated_time: Optional[str] = Field(None, description="预估阅读时间")
    current_progress: Optional[str] = Field(None, description="当前进度（如有）")


# ==================== 阅读计划草案 ====================

class ReadingPlanDraft(BaseModel):
    """阅读计划草案"""
    summary: str = Field("", description="总体说明")
    goals: list[ReadingGoal] = Field(default_factory=list, description="阅读目标")
    suggestions: list[ReadingSuggestion] = Field(default_factory=list, description="阅读建议")
    stats_context: dict[str, Any] = Field(default_factory=dict, description="统计背景")
    insights: list[str] = Field(default_factory=list, description="阅读洞察")
    generated_at: Optional[str] = Field(None, description="生成时间")
    
    @classmethod
    def fallback_draft(cls, error_message: str) -> "ReadingPlanDraft":
        """生成回退草案（解析失败时使用）"""
        return cls(
            summary=f"AI 输出解析失败: {error_message[:100]}",
            insights=["阅读计划生成失败，请稍后重试或检查 AI 服务状态。"],
            generated_at=datetime.now().isoformat(),
        )


# ==================== 请求/响应 ====================

class ReadingPlanRequest(BaseModel):
    """阅读计划请求"""
    prompt: Optional[str] = Field(
        None,
        description="用户自然语言描述（可选）"
    )
    focus: Optional[str] = Field(
        None,
        description="聚焦类型: all / novel / manga / audiobook"
    )
    goal_type: Optional[str] = Field(
        None,
        description="目标类型: daily / weekly / monthly"
    )


class ReadingPlanResponse(BaseModel):
    """阅读计划响应"""
    success: bool = Field(True, description="是否成功")
    plan: Optional[ReadingPlanDraft] = Field(None, description="阅读计划草案")
    error: Optional[str] = Field(None, description="错误信息")


class PresetReadingPrompt(BaseModel):
    """预设阅读提示词"""
    id: str
    title: str
    prompt: str
    description: str
    focus: Optional[str] = None


class PresetReadingPromptsResponse(BaseModel):
    """预设阅读提示词响应"""
    prompts: list[PresetReadingPrompt] = Field(default_factory=list)


# ==================== 辅助函数 ====================

def priority_to_score(priority: SuggestionPriority) -> int:
    """优先级转分数（用于排序）"""
    scores = {
        SuggestionPriority.HIGH: 0,
        SuggestionPriority.MEDIUM: 1,
        SuggestionPriority.LOW: 2,
    }
    return scores.get(priority, 1)
