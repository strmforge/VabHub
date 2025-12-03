from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Protocol

from app.core.intel_local.models import HRTorrentState, HRStatus, TorrentLife


@dataclass
class HRCasesRecord:
    id: int | None
    site: str
    torrent_id: str
    life: TorrentLife
    status: HRStatus
    required_seed_hours: float
    seeded_hours: float
    first_seen_at: datetime
    last_seen_at: datetime
    finished_at: Optional[datetime] = None
    penalized_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    raw_deadline: Optional[datetime] = None


class HRCasesRepository(Protocol):
    async def get(self, site: str, torrent_id: str) -> Optional[HRTorrentState]:
        ...

    async def upsert(self, state: HRTorrentState) -> HRTorrentState:
        ...

    async def list_active_for_site(self, site: str) -> Iterable[HRTorrentState]:
        ...

