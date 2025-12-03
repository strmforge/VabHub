from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from .actions import LocalIntelAction, LocalIntelActionType
from .events import InboxEvent, InboxEventType


class InboxPolicyConfig:
    """站内信策略可调参数。"""

    def __init__(
        self,
        treat_delete_as_error: bool = True,
        treat_hr_penalty_as_error: bool = True,
    ) -> None:
        self.treat_delete_as_error = treat_delete_as_error
        self.treat_hr_penalty_as_error = treat_hr_penalty_as_error


def actions_from_inbox_events(
    *,
    site: str,
    events: Iterable[InboxEvent],
    now: datetime | None = None,
    config: InboxPolicyConfig | None = None,
) -> List[LocalIntelAction]:
    """把 InboxEvent 转换为 LocalIntelAction 列表。"""
    if now is None:
        now = datetime.utcnow()
    if config is None:
        config = InboxPolicyConfig()

    actions: list[LocalIntelAction] = []

    for ev in events:
        if ev.type is InboxEventType.HR_PENALTY:
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.TORRENT_HR_PENALTY,
                    site=site,
                    torrent_id=ev.torrent_id,
                    title=ev.title,
                    message=ev.message,
                    level="error" if config.treat_hr_penalty_as_error else "warning",
                    payload={
                        "raw_subject": ev.raw_subject,
                        "raw_body": ev.raw_body,
                    },
                )
            )
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.USER_NOTIFICATION,
                    site=site,
                    torrent_id=ev.torrent_id,
                    title="HR 扣分提醒",
                    message=ev.message or "收到站点 HR 扣分/处罚相关站内信，请尽快登录站点查看详情。",
                    level="error" if config.treat_hr_penalty_as_error else "warning",
                    payload={"inbox_event_id": getattr(ev, "id", None)},
                )
            )
            continue

        if ev.type is InboxEventType.TORRENT_DELETED:
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.TORRENT_DELETED_REMOTE,
                    site=site,
                    torrent_id=ev.torrent_id,
                    title=ev.title,
                    message=ev.message or "站点通知：已删除某个你曾下载/正在保种的种子。",
                    level="warning" if config.treat_delete_as_error else "info",
                    payload={
                        "raw_subject": ev.raw_subject,
                        "raw_body": ev.raw_body,
                    },
                )
            )
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.USER_NOTIFICATION,
                    site=site,
                    torrent_id=ev.torrent_id,
                    title="种子删除通知",
                    message=ev.message or "站点删除了你曾下载的资源，建议检查是否需要换源或清理任务。",
                    level="warning" if config.treat_delete_as_error else "info",
                    payload={"inbox_event_id": getattr(ev, "id", None)},
                )
            )
            continue

        if ev.type is InboxEventType.SITE_THROTTLED:
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.SITE_THROTTLED,
                    site=site,
                    torrent_id=None,
                    title="站点可能处于风控/限流状态",
                    message=ev.message or "站点通知存在异常或限制，建议降低扫描/访问频率。",
                    level="warning",
                    payload={"raw_subject": ev.raw_subject, "raw_body": ev.raw_body},
                )
            )
            actions.append(
                LocalIntelAction(
                    type=LocalIntelActionType.USER_NOTIFICATION,
                    site=site,
                    torrent_id=None,
                    title="站点风控提醒",
                    message=ev.message or "站点可能触发风控，请留意下载和访问行为。",
                    level="warning",
                    payload={"inbox_event_id": getattr(ev, "id", None)},
                )
            )
            continue

        actions.append(
            LocalIntelAction(
                type=LocalIntelActionType.LOG_ONLY,
                site=site,
                torrent_id=getattr(ev, "torrent_id", None),
                title=ev.title,
                message=ev.message,
                level="info",
                payload={
                    "raw_subject": ev.raw_subject,
                    "raw_body": ev.raw_body,
                    "event_type": ev.type.value if hasattr(ev.type, "value") else str(ev.type),
                },
            )
        )

    return actions
