"""
音乐订阅相关的查询生成工具
供 SubscriptionService / MusicService 等消费，避免循环依赖
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.models.subscription import Subscription


def _extract_music_rules(subscription: Subscription) -> Dict[str, Any]:
    """从订阅的 search_rules 中提取音乐规则"""
    rules = subscription.search_rules or {}
    if isinstance(rules, dict):
        return rules.get("music") or rules
    return {}


def build_music_keywords(subscription: Subscription) -> List[str]:
    """生成用于 PT 搜索的关键词列表"""
    rules = _extract_music_rules(subscription)
    keywords: List[str] = []

    title = rules.get("title") or rules.get("target_name") or subscription.title
    artist = rules.get("artist") or rules.get("target_name")
    album = rules.get("album")

    if artist and title:
        keywords.append(f"{artist} - {title}")
    elif title:
        keywords.append(title)

    if album:
        keywords.append(f"{title} {album}".strip())

    extra_keywords = rules.get("keywords") or []
    for kw in extra_keywords:
        if kw and kw not in keywords:
            keywords.append(kw)

    return [kw for kw in keywords if kw]


def build_music_search_params(subscription: Subscription) -> Tuple[Dict[str, Any], List[str]]:
    """构建音乐订阅的搜索参数及关键词"""
    keywords = build_music_keywords(subscription)
    search_query = keywords[0] if keywords else subscription.title

    params: Dict[str, Any] = {
        "query": search_query,
        "media_type": "music",
        "quality": subscription.quality,
        "min_seeders": subscription.min_seeders or 2,
    }

    if subscription.include:
        params["include"] = subscription.include
    if subscription.exclude:
        params["exclude"] = subscription.exclude
    if subscription.sites:
        params["sites"] = subscription.sites

    rules = _extract_music_rules(subscription)
    if rules.get("year"):
        params["year"] = rules["year"]

    return params, keywords


