from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .actions import LocalIntelAction, LocalIntelActionType, merge_actions
from .hr_policy import evaluate_hr_for_site, HRPolicyConfig
from .inbox_policy import actions_from_inbox_events, InboxPolicyConfig
from .repo import HRCasesRepository, SiteGuardRepository, InboxCursorRepository
from .site_profiles import IntelSiteProfile
from .hr_watcher import HRWatcher
from .inbox_watcher import InboxWatcher


@dataclass
class LocalIntelEngineConfig:
    """统一的本地智能大脑配置。"""

    hr: HRPolicyConfig = HRPolicyConfig()
    inbox: InboxPolicyConfig = InboxPolicyConfig()


class LocalIntelEngine:
    """把 Watcher + Repository + 策略胶合在一起的统一入口。"""

    def __init__(
        self,
        *,
        hr_repo: HRCasesRepository,
        site_guard_repo: SiteGuardRepository,
        inbox_cursor_repo: InboxCursorRepository,
        hr_watcher: HRWatcher,
        inbox_watcher: InboxWatcher,
        config: Optional[LocalIntelEngineConfig] = None,
    ) -> None:
        self._hr_repo = hr_repo
        self._site_guard_repo = site_guard_repo
        self._inbox_cursor_repo = inbox_cursor_repo
        self._hr_watcher = hr_watcher
        self._inbox_watcher = inbox_watcher
        self._config = config or LocalIntelEngineConfig()

    async def refresh_site(
        self,
        site: str,
        profile: IntelSiteProfile,
        *,
        now: datetime | None = None,
    ) -> List[LocalIntelAction]:
        """针对某个站点执行一次“本地智能刷新”。"""
        if now is None:
            now = datetime.utcnow()

        actions: list[LocalIntelAction] = []

        # 1. HR 刷新 & 评估
        try:
            await self._hr_watcher.refresh_site(site, profile)
        except Exception as exc:  # noqa
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.LOG_ONLY,
                    site=site,
                    title="HRWatcher 刷新失败",
                    message=str(exc),
                    level="error",
                    payload={"exception": repr(exc)},
                ).with_created_at(now)
            )
        else:
            hr_actions = await evaluate_hr_for_site(
                site=site,
                repo=self._hr_repo,
                now=now,
                config=self._config.hr,
            )
            for act in hr_actions:
                act.created_at = act.created_at or now
            actions.extend(hr_actions)

        # 2. 站内信刷新 & 评估
        inbox_events = await self._inbox_watcher.refresh_site(site, profile)
        inbox_actions = actions_from_inbox_events(
            site=site,
            events=inbox_events,
            now=now,
            config=self._config.inbox,
        )
        for act in inbox_actions:
            act.created_at = act.created_at or now
        actions.extend(inbox_actions)

        # TODO: 3. 可在此加入 SiteGuard 的节流/封禁状态评估，转为 LocalIntelAction

        return merge_actions(actions)

    async def is_move_safe(
        self,
        site: str,
        torrent_id: str,
        *,
        now: datetime | None = None,
    ) -> bool:
        """
        检查移动/删除源文件是否安全（Phase 5）。
        
        如果该种子有未完成的 HR 记录，返回 False（不安全，不应删除源文件）。
        否则返回 True（安全，可以删除）。
        
        Args:
            site: 站点标识
            torrent_id: 种子 ID
            now: 当前时间（可选）
        
        Returns:
            True 表示安全（可以删除），False 表示不安全（不应删除）
        """
        if now is None:
            now = datetime.utcnow()
        
        try:
            # 查询该种子的 HR 记录
            async for hr_case in self._hr_repo.list_active_for_site(site):  # type: ignore[attr-defined]
                if hr_case.torrent_id == str(torrent_id):
                    # 检查 HR 状态
                    from .models import HRStatus
                    
                    # 如果 HR 已完成或不存在，可以安全删除
                    if hr_case.hr_status in (HRStatus.NONE, HRStatus.FINISHED, HRStatus.FAILED):
                        return True
                    
                    # 如果 HR 是 ACTIVE 或 UNKNOWN，检查是否已过期
                    if hr_case.hr_status in (HRStatus.ACTIVE, HRStatus.UNKNOWN):
                        # 如果有截止时间且已过期，可以删除
                        if hr_case.deadline and now >= hr_case.deadline:
                            return True
                        
                        # 如果已满足保种要求（比例 >= 1.0），可以删除
                        if (
                            hr_case.required_seed_hours
                            and hr_case.seeded_hours
                            and hr_case.seeded_hours >= hr_case.required_seed_hours
                        ):
                            return True
                        
                        # 否则不安全，不应删除
                        return False
            
            # 没有找到 HR 记录，默认安全
            return True
            
        except Exception as e:
            # 查询失败时，为了安全起见，返回 False（不删除）
            from loguru import logger
            logger.warning(f"LocalIntel: 检查移动安全性失败 (site={site}, torrent_id={torrent_id}): {e}")
            return False  # 保守策略：失败时不删除
