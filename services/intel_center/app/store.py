from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .config import settings


class IntelDataStore:
    """简单的文件存储实现（示例）。"""

    def __init__(self) -> None:
        base = Path(settings.DATA_DIR)
        base.mkdir(parents=True, exist_ok=True)
        self.alias_file = base / "aliases.json"
        self.index_file = base / "index.json"
        self.rules_file = base / "rules.json"

        self.aliases = self._load_json(self.alias_file, default={})
        self.index = self._load_json(self.index_file, default={})
        self.rules = self._load_json(self.rules_file, default={"version": 1, "rules": []})

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[IntelStore] 加载 {path} 失败: {e!r}")
            return default

    def search_alias(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        results: List[Dict[str, Any]] = []
        for key, data in self.aliases.items():
            if q in key:
                results.append(data)
        return results

    def resolve_alias(self, query: str) -> Optional[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            return None

        direct = self.aliases.get(q)
        if direct:
            return direct

        normalized = q.replace(" ", "")
        for key, data in self.aliases.items():
            if key.replace(" ", "") == normalized:
                return data
        return None

    def get_release_index(self, release_key: str) -> Dict[str, Any]:
        return self.index.get(release_key, {"release_key": release_key, "sites": []})

    def get_rules_latest(self) -> Dict[str, Any]:
        return self.rules

