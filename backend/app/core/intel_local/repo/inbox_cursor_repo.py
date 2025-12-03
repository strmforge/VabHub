from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol


@dataclass
class InboxCursorRecord:
    site: str
    last_message_id: Optional[str]
    last_checked_at: Optional[datetime]


class InboxCursorRepository(Protocol):
    async def get(self, site: str) -> InboxCursorRecord:
        ...

    async def save(self, cursor: InboxCursorRecord) -> None:
        ...

