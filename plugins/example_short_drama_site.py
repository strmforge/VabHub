"""
官方示例插件：短剧 PT 站点样板。

提供：
- 结构化默认配置（站点信息、分类映射、订阅 / 下载偏好）
- 快速构造短剧订阅/下载 payload 的辅助函数
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, Optional

from app.core.plugins.spec import PluginContext, PluginHooks, PluginMetadata

SHORT_DRAMA_MEDIA_TYPE = "short_drama"

PLUGIN_METADATA = PluginMetadata(
    id="example_short_drama_site",
    name="示例短剧站",
    version="0.1.0",
    description="演示短剧插件的配置结构与订阅/下载辅助函数。",
    author="VabHub",
    tags=["short_drama", "demo", "pt"],
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "site_name": "Demo Short Drama Station",
    "site_url": "https://short-drama.example.com",
    "auth": {
        "cookie": "pt_session=__PLACEHOLDER__",
        "token": "",
    },
    "category_mapping": {
        "vertical": {
            "search_tags": ["竖屏", "短剧"],
            "default_quality": "WEB-DL",
            "default_resolution": "1080p",
        },
        "urban_romance": {
            "search_tags": ["都市", "恋爱"],
            "default_quality": "WEB-DL",
            "default_resolution": "4K",
        },
    },
    "subscription_defaults": {
        "downloader": "qBittorrent",
        "quality": "WEB-DL",
        "resolution": "1080p",
        "auto_download": True,
        "min_seeders": 5,
    },
    "download_defaults": {
        "downloader": "qBittorrent",
        "save_path": "/downloads/short_drama",
    },
}


def register(context: PluginContext) -> PluginHooks:
    """在加载阶段写入默认配置，并输出站点信息。"""
    config = _ensure_nested_defaults(context, DEFAULT_CONFIG)
    context.logger.info(
        "[short-drama] 插件已加载：site=%s url=%s categories=%s",
        config.get("site_name"),
        config.get("site_url"),
        ", ".join(sorted(config.get("category_mapping", {}).keys())),
    )

    def _on_startup(ctx: PluginContext) -> None:
        cfg = ctx.config.all()
        ctx.logger.info(
            "[short-drama] on_startup -> downloader=%s save_path=%s",
            cfg.get("download_defaults", {}).get("downloader"),
            cfg.get("download_defaults", {}).get("save_path"),
        )

    def _on_shutdown(ctx: PluginContext) -> None:
        ctx.logger.info("[short-drama] on_shutdown -> 已卸载")

    return PluginHooks(on_startup=_on_startup, on_shutdown=_on_shutdown)


def create_subscription_payload(
    series_title: str,
    *,
    config: Optional[Dict[str, Any]] = None,
    season: int = 1,
    total_episodes: int = 20,
    episode_duration_min: int = 8,
    site_category: str = "vertical",
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    构建一个 `SubscriptionService.create_subscription` 可直接使用的 payload。
    """
    cfg = config or DEFAULT_CONFIG
    category_cfg = cfg.get("category_mapping", {}).get(site_category, {})
    defaults = cfg.get("subscription_defaults", {})

    short_meta = {
        "episode_duration": episode_duration_min * 60,
        "duration_unit": "second",
        "total_episodes": total_episodes,
        "format_tag": site_category,
        "source_category": category_cfg.get("search_tags", []),
    }

    payload = {
        **defaults,
        "title": series_title,
        "original_title": series_title,
        "media_type": SHORT_DRAMA_MEDIA_TYPE,
        "season": season,
        "episode_group": f"{_slugify(series_title)}-S{season:02d}",
        "short_drama_metadata": short_meta,
        "include": ",".join(category_cfg.get("search_tags", [])),
        "description": description or "",
    }
    return payload


def create_download_payload(
    release_title: str,
    *,
    magnet_link: Optional[str] = None,
    torrent_url: Optional[str] = None,
    size_gb: float = 1.0,
    episode_span: str = "E01-E10",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    构建 `DownloadService.create_download` 可使用的 payload，确保 media_type=short_drama。
    """
    cfg = config or DEFAULT_CONFIG
    download_defaults = cfg.get("download_defaults", {})

    payload = {
        **download_defaults,
        "title": release_title,
        "magnet_link": magnet_link,
        "torrent_url": torrent_url,
        "size_gb": size_gb,
        "media_type": SHORT_DRAMA_MEDIA_TYPE,
        "extra_metadata": {
            "short_drama": {
                "episode_span": episode_span,
                "site": cfg.get("site_name"),
            }
        },
    }
    return payload


def _ensure_nested_defaults(context: PluginContext, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """深度填充默认配置，保证升级时新增字段能写入 JSON。"""
    existing = context.config.all()
    merged = deepcopy(existing)
    changed = _merge_defaults(merged, defaults)
    if changed:
        context.config.set_all(merged or deepcopy(defaults))
        return merged or deepcopy(defaults)
    if not merged:
        context.config.set_all(deepcopy(defaults))
        return deepcopy(defaults)
    return merged


def _merge_defaults(target: Dict[str, Any], defaults: Dict[str, Any]) -> bool:
    changed = False
    for key, value in defaults.items():
        if key not in target:
            target[key] = deepcopy(value)
            changed = True
        elif isinstance(value, dict) and isinstance(target[key], dict):
            if _merge_defaults(target[key], value):
                changed = True
    return changed


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


__all__ = [
    "PLUGIN_METADATA",
    "register",
    "create_subscription_payload",
    "create_download_payload",
]

