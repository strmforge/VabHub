from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class PluginConfigStore:
    """轻量级插件配置存储，使用 JSON 文件持久化。"""

    def __init__(self, plugin_name: str, base_dir: Optional[Path] = None) -> None:
        self.plugin_name = plugin_name
        self.base_dir = Path(base_dir or Path("data") / "plugin_configs")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.base_dir / f"{plugin_name}.json"

    def _read_raw(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {}
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - 仅日志
            logger.warning(f"[PluginConfigStore] 读取 {self.file_path} 失败: {exc}")
            return {}

    def _write_raw(self, data: Dict[str, Any]) -> None:
        try:
            tmp_path = self.file_path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_path.replace(self.file_path)
        except Exception as exc:  # pragma: no cover - 仅日志
            logger.error(f"[PluginConfigStore] 写入 {self.file_path} 失败: {exc}")

    def all(self) -> Dict[str, Any]:
        return self._read_raw()

    def set_all(self, values: Dict[str, Any]) -> Dict[str, Any]:
        self._write_raw(values)
        return values

    def get(self, key: str, default: Any = None) -> Any:
        data = self._read_raw()
        return data.get(key, default)

    def set(self, key: str, value: Any) -> Dict[str, Any]:
        data = self._read_raw()
        data[key] = value
        self._write_raw(data)
        return data

    def delete(self, key: str) -> Dict[str, Any]:
        data = self._read_raw()
        if key in data:
            data.pop(key)
            self._write_raw(data)
        return data

    def reset(self, defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = defaults or {}
        self._write_raw(payload)
        return payload

    def ensure_defaults(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        data = self._read_raw()
        updated = False
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
                updated = True
        if updated:
            self._write_raw(data)
        return data

