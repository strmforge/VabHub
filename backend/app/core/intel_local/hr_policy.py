from __future__ import annotations

from datetime import datetime
from typing import List

from .actions import LocalIntelAction, LocalIntelActionType
from .models import HRTorrentState, HRStatus
from .repo import HRCasesRepository


class HRPolicyConfig:
    """HR 策略的可调参数。"""

    def __init__(
        self,
        risk_threshold_hours: float = 1.0,
        min_required_ratio_for_safe: float = 1.0,
    ) -> None:
        self.risk_threshold_hours = risk_threshold_hours
        self.min_required_ratio_for_safe = min_required_ratio_for_safe


async def evaluate_hr_for_site(
    *,
    site: str,
    repo: HRCasesRepository,
    now: datetime | None = None,
    config: HRPolicyConfig | None = None,
) -> List[LocalIntelAction]:
    """基于当前 hr_cases 表评估一个站点的 HR 风险/安全状况。"""
    if now is None:
        now = datetime.utcnow()
    if config is None:
        config = HRPolicyConfig()

    actions: list[LocalIntelAction] = []

    states = await repo.list_active_for_site(site)
    for state in states:
        ratio = None
        if state.required_seed_hours and state.required_seed_hours > 0:
            ratio = (state.seeded_hours or 0.0) / state.required_seed_hours

        actions.append(
            LocalIntelAction(
                type=LocalIntelActionType.HR_RECORD_PROGRESS,
                site=site,
                torrent_id=state.torrent_id,
                title=getattr(state, "title", None),
                message=None,
                level="info",
                payload={
                    "required_seed_hours": state.required_seed_hours,
                    "seeded_hours": state.seeded_hours,
                    "ratio": ratio,
                    "status": state.hr_status.value if isinstance(state.hr_status, HRStatus) else str(state.hr_status),
                    "deadline": state.deadline,
                },
            )
        )

        if state.hr_status in (HRStatus.NONE, HRStatus.FINISHED):
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.HR_MARK_SAFE,
                    site=site,
                    torrent_id=state.torrent_id,
                    title=getattr(state, "title", None),
                    message="HR 已达标或被站点移除",
                    level="info",
                )
            )
            continue

        deadline = state.deadline
        if deadline is None:
            continue

        if now >= deadline:
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.HR_MARK_RISK,
                    site=site,
                    torrent_id=state.torrent_id,
                    title=getattr(state, "title", None),
                    message="HR 截止时间已过，存在扣分风险",
                    level="error",
                    payload={"deadline": deadline},
                )
            )
            continue

        remaining = deadline - now
        remaining_hours = remaining.total_seconds() / 3600.0
        if remaining_hours <= config.risk_threshold_hours:
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.HR_MARK_RISK,
                    site=site,
                    torrent_id=state.torrent_id,
                    title=getattr(state, "title", None),
                    message=f"HR 即将到期（剩余约 {remaining_hours:.1f} 小时）",
                    level="warning",
                    payload={"deadline": deadline, "remaining_hours": remaining_hours},
                )
            )

    return actions
