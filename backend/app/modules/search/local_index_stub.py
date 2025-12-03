from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class LocalIndexHit:
    site: str
    torrent_id: str
    title: str
    score: float


class LocalIndexService:
    async def index_torrent(self, site: str, torrent_id: str, title: str) -> None:
        raise NotImplementedError

    async def search(self, query: str, limit: int = 50) -> Iterable[LocalIndexHit]:
        raise NotImplementedError

