"""
Helper utilities for converting external indexer results into internal schemas.
"""

from typing import Dict, Any

from app.core.indexer_bridge.models import ExternalIndexerTorrentResult


def external_result_to_search_item(result: ExternalIndexerTorrentResult) -> Dict[str, Any]:
    """
    Convert an ExternalIndexerTorrentResult into a dict compatible with
    app.schemas.search.SearchResultItem.
    """

    magnet_link = None
    torrent_url = None
    if result.download_url:
        if result.download_url.startswith("magnet:"):
            magnet_link = result.download_url
        else:
            torrent_url = result.download_url

    return {
        "site_id": result.site_id,
        "torrent_id": result.torrent_id,
        "title_raw": result.title,
        "size_bytes": result.size_bytes,
        "size_gb": result.size_gb,
        "seeders": result.seeders,
        "leechers": result.leechers,
        "published_at": result.published_at,
        "is_hr": result.is_hr,
        "is_free": result.is_free,
        "is_half_free": result.is_half_free,
        "is_deleted": False,
        "category": result.category,
        "intel_site_status": None,
        "intel_hr_status": None,
        "magnet_link": magnet_link,
        "torrent_url": torrent_url,
        "source": "external_indexer",
    }

