"""
榜单数据提供者
"""

from app.modules.charts.providers.netflix_top10 import NetflixTop10Provider
from app.modules.charts.providers.imdb_datasets import IMDBDatasetsProvider

__all__ = ["NetflixTop10Provider", "IMDBDatasetsProvider"]

