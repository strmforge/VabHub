from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.core.plugins.config_store import PluginConfigStore
from app.core.plugins.graphql_builder import GraphQLSchemaBuilder

if TYPE_CHECKING:
    from fastapi import APIRouter


@dataclass
class PluginMetadata:
    """插件的元信息，用于在 UI / API 中展示。"""

    id: str
    name: str
    version: str
    description: str
    author: Optional[str] = None
    homepage: Optional[str] = None
    tags: List[str] = field(default_factory=list)


LifecycleCallable = Callable[["PluginContext"], None]


@dataclass
class PluginHooks:
    """插件返回的可选钩子。"""

    on_startup: Optional[LifecycleCallable] = None
    on_shutdown: Optional[LifecycleCallable] = None
    register_rest: Optional[Callable[["APIRouter"], None]] = None
    register_graphql: Optional[Callable[[GraphQLSchemaBuilder], None]] = None


class PluginContext:
    """传递给插件的上下文对象。"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(plugin=name)
        self.settings = settings
        self.config = PluginConfigStore(name)

    def emit_event(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """用于插件内部简单地记录关键事件。"""
        self.logger.info(f"[event={event}] payload={payload or {}}")


def metadata_from_object(raw: Any) -> PluginMetadata:
    if isinstance(raw, PluginMetadata):
        return raw
    if isinstance(raw, dict):
        return PluginMetadata(**raw)
    raise ValueError("插件需要导出 PLUGIN_METADATA（dict 或 PluginMetadata）")

