"""
全局规则模块
SETTINGS-RULES-1: 全局 HR 策略、分辨率档位、三档模式实现
"""

from .service import GlobalRulesService
from .filter import filter_by_hr_policy, apply_global_quality_rules, resolve_file_move_behavior

__all__ = [
    "GlobalRulesService",
    "filter_by_hr_policy",
    "apply_global_quality_rules", 
    "resolve_file_move_behavior"
]
