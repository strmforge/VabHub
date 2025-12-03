from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

from app.core.intel_local.models import SiteGuardProfile


@dataclass
class SiteGuardEventRecord:
    id: int | None
    site: str
    event_type: str
    created_at: datetime
    block_until: Optional[datetime] = None
    scan_minutes_before_block: Optional[int] = None
    scan_pages_before_block: Optional[int] = None
    cause: Optional[str] = None


class SiteGuardRepository(Protocol):
    async def get_profile(self, site: str) -> SiteGuardProfile:
        ...

    async def save_profile(self, profile: SiteGuardProfile) -> None:
        ...

    async def record_block_event(
        self,
        site: str,
        block_until: datetime,
        cause: str,
        scan_minutes_before_block: Optional[int],
        scan_pages_before_block: Optional[int],
        now: Optional[datetime] = None,
    ) -> SiteGuardEventRecord:
        ...

    async def get_latest_block(self, site: str) -> Optional[SiteGuardEventRecord]:
        ...

