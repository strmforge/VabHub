"""
Site discovery helpers for the Indexer Bridge.

The current implementation acts as a stub – it can later be wired into a real
external configuration source. Returning an empty list keeps the surrounding
code paths operational without forcing users to configure a backend.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from app.core.indexer_bridge.models import ExternalIndexerSiteConfig


@dataclass
class ImportedExternalSite:
    site_id: str
    name: str
    framework: str
    raw_config: Dict[str, Any]


async def discover_external_sites() -> List[ImportedExternalSite]:
    return []


async def import_nexusphp_sites_from_external() -> List[ExternalIndexerSiteConfig]:
    sites = await discover_external_sites()
    configs: List[ExternalIndexerSiteConfig] = []
    for site in sites:
        if site.framework.lower() != "nexusphp":
            continue
        configs.append(
            ExternalIndexerSiteConfig(
                site_id=site.site_id,
                name=site.name,
                raw_config=site.raw_config,
            )
        )
    return configs

