"""
Authentication helpers for the Indexer Bridge.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol
from loguru import logger


@dataclass
class ExternalIndexerSessionState:
    site_id: str
    is_logged_in: bool
    last_check: Optional[datetime]
    requires_challenge: bool = False
    message: Optional[str] = None


class ExternalIndexerAuthBridge(Protocol):
    async def ensure_logged_in(self, site_id: str) -> ExternalIndexerSessionState:
        ...

    async def refresh_session(self, site_id: str) -> ExternalIndexerSessionState:
        ...


class SimpleExternalIndexerAuthBridge:
    """
    Default no-op auth bridge that only reports unavailable status.
    """

    async def ensure_logged_in(self, site_id: str) -> ExternalIndexerSessionState:
        logger.debug("No auth backend configured for site_id=%s", site_id)
        return ExternalIndexerSessionState(
            site_id=site_id,
            is_logged_in=False,
            last_check=datetime.utcnow(),
            message="External auth bridge not configured",
        )

    async def refresh_session(self, site_id: str) -> ExternalIndexerSessionState:
        return await self.ensure_logged_in(site_id)

