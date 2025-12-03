"""
站内信监控器 (Phase 2)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, Mapping, Optional, Any

from loguru import logger

from app.core.config import settings
from .events import InboxEvent, InboxEventType
from .hr_state import get_hr_state_for_torrent, mark_penalized, mark_torrent_deleted
from .site_guard import record_block_event
from .site_profiles import (
    IntelSiteProfile,
    get_all_site_profiles,
    get_site_profile,
)
from .http_clients import get_http_client_registry
from .parsers.inbox_html_parser import (
    ParsedInboxMessage,
    parse_inbox_page_generic,
    parse_inbox_page_ttg,
)
from .repo import InboxCursorRepository, InboxCursorRecord

INBOX_PARSERS = {
    "ttg": parse_inbox_page_ttg,
}


@dataclass
class InboxMessage:
    """站内信基础结构，由主项目的 HTTP/解析层提供。"""

    message_id: str
    subject: str
    body: str
    created_at: Optional[datetime] = None
    url: Optional[str] = None


class InboxWatcher:
    """解析站内信事件，更新 HR 状态与 SiteGuard。"""

    def __init__(
        self,
        site_profiles: Optional[Mapping[str, IntelSiteProfile]] = None,
        inbox_cursor_repo: InboxCursorRepository | None = None,
    ) -> None:
        self._profiles: Dict[str, IntelSiteProfile] = dict(site_profiles or get_all_site_profiles())
        self._inbox_cursor_repo = inbox_cursor_repo

    def refresh_profiles(self) -> None:
        """外部可调用以刷新站点配置映射。"""
        self._profiles = dict(get_all_site_profiles())

    async def handle_site(self, site: str) -> Dict[str, Any]:
        events = await self.refresh_site(site)
        return {
            "success": True,
            "site": site,
            "processed_count": len(events),
        }

    async def refresh_site(
        self,
        site: str,
        profile: Optional[IntelSiteProfile] = None,
    ) -> list[InboxEvent]:
        profile = profile or self._profiles.get(site) or get_site_profile(site)
        if not profile or not profile.inbox.enabled:
            logger.debug(f"站点 {site} 的站内信监控未启用，跳过")
            return []

        messages = await self.fetch_new_messages(site, profile)

        cursor_record: InboxCursorRecord | None = None
        if self._inbox_cursor_repo:
            cursor_record = await self._inbox_cursor_repo.get(site)

        cutoff_id = cursor_record.last_message_id if cursor_record else None
        new_messages: list[InboxMessage] = []
        for msg in messages:
            if cutoff_id and msg.message_id == cutoff_id:
                break
            new_messages.append(msg)

        events: list[InboxEvent] = []
        now = datetime.utcnow()

        for msg in new_messages:
            event = self._classify_message(site, profile, msg)
            if not event:
                continue
            events.append(event)

            if event.type is InboxEventType.HR_PENALTY and event.torrent_id:
                state = get_hr_state_for_torrent(site, event.torrent_id)
                mark_penalized(state, now=now)

            elif event.type is InboxEventType.TORRENT_DELETED and event.torrent_id:
                state = get_hr_state_for_torrent(site, event.torrent_id)
                mark_torrent_deleted(state, now=now)
                
                # Phase 9: 标记 TorrentIndex 中的种子为已删除
                try:
                    from .repo import SqlAlchemyTorrentIndexRepository
                    from app.core.database import AsyncSessionLocal
                    index_repo = SqlAlchemyTorrentIndexRepository(AsyncSessionLocal)
                    await index_repo.mark_deleted(site, event.torrent_id, deleted_at=now)
                    logger.info(
                        f"LocalIntel: 已标记种子 {site}/{event.torrent_id} 为已删除（来自站内信）"
                    )
                except Exception as e:
                    logger.warning(f"LocalIntel: 标记种子删除失败: {e}")

            elif event.type is InboxEventType.SITE_THROTTLED:
                block_until = event.throttle_until or (now + timedelta(hours=12))
                record_block_event(
                    site=site,
                    block_until=block_until,
                    cause="pm_throttle_notice",
                    scan_minutes_before_block=None,
                    scan_pages_before_block=None,
                    now=now,
                )

        if self._inbox_cursor_repo:
            latest_id = messages[0].message_id if messages else cutoff_id
            await self._inbox_cursor_repo.save(
                InboxCursorRecord(
                    site=site,
                    last_message_id=latest_id,
                    last_checked_at=now,
                )
            )

        return events

    async def fetch_new_messages(
        self,
        site: str,
        profile: IntelSiteProfile,
    ) -> Iterable[InboxMessage]:
        registry = get_http_client_registry()
        try:
            client = registry.get(site)
        except KeyError:
            logger.debug(f"LocalIntel: 未注册站点 {site} 的 HTTP 客户端，跳过站内信抓取")
            return []

        html = await client.fetch_inbox_page(profile, page=1)
        parser = INBOX_PARSERS.get(site, parse_inbox_page_generic)
        parsed_messages: Iterable[ParsedInboxMessage] = parser(site=site, html=html, profile=profile)

        inbox_messages: list[InboxMessage] = []
        for msg in parsed_messages:
            inbox_messages.append(
                InboxMessage(
                    message_id=msg.message_id,
                    subject=msg.subject or "",
                    body=msg.body or "",
                    created_at=msg.created_at,
                )
            )
        return inbox_messages

    def _classify_message(
        self,
        site: str,
        profile: IntelSiteProfile,
        msg: InboxMessage,
    ) -> Optional[InboxEvent]:
        """基于关键词的粗分类。"""
        keywords = profile.inbox.pm_keywords or {}

        subject = (msg.subject or "").lower()
        body = (msg.body or "").lower()

        def contains_any(words: Iterable[str]) -> bool:
            return any(word.lower() in subject or word.lower() in body for word in words)

        event_type: Optional[InboxEventType] = None

        if contains_any(keywords.get("penalty", [])):
            event_type = InboxEventType.HR_PENALTY
        elif contains_any(keywords.get("delete", [])):
            event_type = InboxEventType.TORRENT_DELETED
        elif contains_any(keywords.get("throttle", [])):
            event_type = InboxEventType.SITE_THROTTLED

        if not event_type:
            if not keywords:
                logger.debug(f"站点 {site} 未配置站内信关键词，跳过分类")
            return None

        # TODO: 解析 torrent_id（各站点格式差异大，需要主项目实现具体规则）
        torrent_id: Optional[str] = None

        # TODO: 若为 THROTTLE，可尝试从 body 中解析解除时间
        throttle_until: Optional[datetime] = None

        return InboxEvent(
            site=site,
            type=event_type,
            raw_subject=msg.subject,
            raw_body=msg.body,
            title=msg.subject,
            message=msg.body,
            torrent_id=torrent_id,
            created_at=msg.created_at,
            throttle_until=throttle_until,
            message_id=msg.message_id,
            message_url=msg.url,
        )

    async def handle_all_sites(self) -> Dict[str, Any]:
        """便利函数：遍历所有启用站内信的站点。"""
        if not settings.INTEL_ENABLED:
            logger.debug("LocalIntel 未启用，跳过站内信监控")
            return {"success": False, "reason": "not_enabled"}

        if not self._profiles:
            self.refresh_profiles()

        enabled_sites = [
            site for site, profile in self._profiles.items() if profile.inbox.enabled
        ]
        if not enabled_sites:
            logger.debug("没有启用站内信监控的站点")
            return {"success": True, "processed": 0}

        results = []
        for site in enabled_sites:
            try:
                result = await self.handle_site(site)
                results.append(result)
            except NotImplementedError:
                raise
            except Exception as exc:
                logger.error(f"处理站点 {site} 的站内信失败: {exc}", exc_info=True)
                results.append({"success": False, "site": site, "error": str(exc)})

        success_count = sum(1 for r in results if r.get("success"))
        return {
            "success": True,
            "processed": len(results),
            "success_count": success_count,
            "results": results,
        }


# 全局单例
_inbox_watcher: Optional[InboxWatcher] = None


def get_inbox_watcher() -> InboxWatcher:
    """获取 Inbox Watcher 单例"""
    global _inbox_watcher
    if _inbox_watcher is None:
        _inbox_watcher = InboxWatcher()
    else:
        _inbox_watcher.refresh_profiles()
    return _inbox_watcher

