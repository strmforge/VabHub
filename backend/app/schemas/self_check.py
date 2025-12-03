"""
自检 Schema
QA-1 实现

定义自检结果的数据模型
"""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SelfCheckStatus(str, Enum):
    """自检状态"""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIPPED = "skipped"


class SelfCheckItemResult(BaseModel):
    """单个自检项结果"""
    code: str = Field(..., description="检查项代码，如 db.migrations")
    name: str = Field(..., description="人类可读名称")
    status: SelfCheckStatus = Field(..., description="检查状态")
    message: Optional[str] = Field(None, description="状态消息")
    details: Optional[dict[str, Any]] = Field(None, description="详细信息")
    duration_ms: Optional[int] = Field(None, description="执行耗时(毫秒)")


class SelfCheckGroupResult(BaseModel):
    """自检分组结果"""
    code: str = Field(..., description="分组代码: core/novel_tts/manga/music/notify/bot/runners")
    name: str = Field(..., description="分组名称")
    status: SelfCheckStatus = Field(..., description="分组整体状态")
    items: list[SelfCheckItemResult] = Field(default_factory=list, description="分组内的检查项")
    
    def compute_status(self) -> SelfCheckStatus:
        """根据子项计算分组状态"""
        if not self.items:
            return SelfCheckStatus.SKIPPED
        
        has_fail = any(i.status == SelfCheckStatus.FAIL for i in self.items)
        has_warn = any(i.status == SelfCheckStatus.WARN for i in self.items)
        
        if has_fail:
            return SelfCheckStatus.FAIL
        if has_warn:
            return SelfCheckStatus.WARN
        return SelfCheckStatus.PASS


class SelfCheckRunResult(BaseModel):
    """完整自检运行结果"""
    started_at: datetime = Field(..., description="开始时间")
    finished_at: datetime = Field(..., description="结束时间")
    overall_status: SelfCheckStatus = Field(..., description="整体状态")
    groups: list[SelfCheckGroupResult] = Field(default_factory=list, description="各分组结果")
    environment: dict[str, Any] = Field(default_factory=dict, description="环境信息")
    
    def compute_overall_status(self) -> SelfCheckStatus:
        """根据各组计算整体状态"""
        if not self.groups:
            return SelfCheckStatus.SKIPPED
        
        has_fail = any(g.status == SelfCheckStatus.FAIL for g in self.groups)
        has_warn = any(g.status == SelfCheckStatus.WARN for g in self.groups)
        
        if has_fail:
            return SelfCheckStatus.FAIL
        if has_warn:
            return SelfCheckStatus.WARN
        return SelfCheckStatus.PASS
    
    @property
    def duration_ms(self) -> int:
        """总耗时(毫秒)"""
        delta = self.finished_at - self.started_at
        return int(delta.total_seconds() * 1000)
    
    @property
    def summary(self) -> dict[str, int]:
        """按状态统计"""
        counts = {s.value: 0 for s in SelfCheckStatus}
        for group in self.groups:
            for item in group.items:
                counts[item.status.value] += 1
        return counts


# ============== 辅助异常 ==============

class SelfCheckWarning(Exception):
    """自检警告异常，用于标记 WARN 状态"""
    pass


class SelfCheckSkip(Exception):
    """自检跳过异常，用于标记 SKIPPED 状态"""
    pass
