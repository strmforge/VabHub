from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LocalIntelActionType(str, Enum):
    """本地智能大脑输出的统一动作类型。"""

    # HR 相关
    HR_MARK_SAFE = "hr_mark_safe"          # HR 任务已达标，可视为安全
    HR_MARK_RISK = "hr_mark_risk"          # 接近/已经超时，存在 HR 风险
    HR_RECORD_PROGRESS = "hr_record_progress"  # 更新本地 HR 进度统计

    # 种子生命周期
    TORRENT_DELETED_REMOTE = "torrent_deleted_remote"  # 远端站点已删种
    TORRENT_HR_PENALTY = "torrent_hr_penalty"          # 站内信确认 HR 扣分

    # 站点风控
    SITE_THROTTLED = "site_throttled"      # 站点疑似限流/封禁，建议降频或暂停
    SITE_RECOVERED = "site_recovered"      # 站点风控已解除

    # 提醒类
    USER_NOTIFICATION = "user_notification"  # 提醒用户（站内信/HR/删种等）
    LOG_ONLY = "log_only"                    # 仅记录日志，暂不提示用户


@dataclass
class LocalIntelAction:
    """单条动作。"""

    type: LocalIntelActionType
    site: str

    # 对于 HR/种子相关的动作
    torrent_id: Optional[str] = None

    # 用于 UI/日志展示
    title: Optional[str] = None
    message: Optional[str] = None
    level: str = "info"  # info / warning / error

    # 附加信息：任意结构化 payload（将来可用于调试/统计）
    payload: dict[str, Any] | None = None

    # 产生时间（可由调用方填入）
    created_at: Optional[datetime] = None

    def with_created_at(self, ts: datetime) -> "LocalIntelAction":
        self.created_at = ts
        return self


def merge_actions(actions: list[LocalIntelAction]) -> list[LocalIntelAction]:
    """简单的动作去重/合并策略。"""
    latest_progress: dict[tuple[str, str], LocalIntelAction] = {}
    others: list[LocalIntelAction] = []

    for act in actions:
        if act.type is LocalIntelActionType.HR_RECORD_PROGRESS and act.torrent_id:
            key = (act.site, act.torrent_id)
            latest_progress[key] = act
        else:
            others.append(act)

    return others + list(latest_progress.values())
