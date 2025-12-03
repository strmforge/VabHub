from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class HRStatus(str, Enum):
    NONE = "none"
    ACTIVE = "active"
    FINISHED = "finished"
    FAILED = "failed"
    UNKNOWN = "unknown"


class TorrentLife(str, Enum):
    ALIVE = "alive"
    DELETED = "deleted"


@dataclass
class HRTorrentState:
    site: str
    torrent_id: str

    hr_status: HRStatus = HRStatus.NONE
    life_status: TorrentLife = TorrentLife.ALIVE

    required_seed_hours: Optional[float] = None
    seeded_hours: float = 0.0

    deadline: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


@dataclass
class SiteGuardProfile:
    site: str

    last_block_start: Optional[datetime] = None
    last_block_end: Optional[datetime] = None
    last_block_cause: Optional[str] = None

    last_full_scan_minutes: Optional[int] = None
    last_full_scan_pages: Optional[int] = None

    safe_scan_minutes: int = 10
    safe_pages_per_hour: int = 200

    updated_at: Optional[datetime] = None

