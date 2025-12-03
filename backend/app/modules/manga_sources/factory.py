"""
漫画源适配器工厂
"""
from app.models.manga_source import MangaSource
from app.models.enums.manga_source_type import MangaSourceType
from app.modules.manga_sources.adapter_base import BaseMangaSourceAdapter
from app.modules.manga_sources.opds_adapter import OpdsMangaSourceAdapter
from app.modules.manga_sources.suwayomi_adapter import SuwayomiMangaSourceAdapter
from app.modules.manga_sources.komga_adapter import KomgaMangaSourceAdapter
from app.modules.manga_sources.generic_http_adapter import GenericHttpMangaSourceAdapter


def get_manga_source_adapter(source: MangaSource) -> BaseMangaSourceAdapter:
    """根据源类型返回对应的适配器实例"""
    if source.type == MangaSourceType.OPDS:
        return OpdsMangaSourceAdapter(source)
    if source.type == MangaSourceType.SUWAYOMI:
        return SuwayomiMangaSourceAdapter(source)
    if source.type == MangaSourceType.KOMGA:
        return KomgaMangaSourceAdapter(source)
    if source.type == MangaSourceType.GENERIC_HTTP:
        return GenericHttpMangaSourceAdapter(source)
    raise ValueError(f"Unsupported manga source type: {source.type}")

