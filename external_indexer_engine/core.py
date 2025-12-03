"""
外部索引引擎核心函数

导出 4 个异步函数，供 External Indexer Bridge 调用。
"""

import logging
from typing import Optional, List, Dict, Any

from external_indexer_engine.config import get_engine_settings
from external_indexer_engine.client import get_http_client
from external_indexer_engine.models import RemoteTorrentItem, RemoteTorrentDetail

logger = logging.getLogger(__name__)


async def search_torrents(
    site_id: str,
    keyword: str,
    media_type: Optional[str] = None,
    categories: Optional[List[str]] = None,
    page: int = 1,
) -> List[Dict[str, Any]]:
    """
    搜索种子
    
    Args:
        site_id: 站点 ID
        keyword: 搜索关键词
        media_type: 媒体类型（如 "movie" / "tv"）
        categories: 分类列表
        page: 页码（从 1 开始）
        
    Returns:
        搜索结果字典列表，字段对齐 ExternalTorrentResult
    """
    try:
        settings = get_engine_settings()
        
        # 如果未配置 base_url，直接返回空列表
        if not settings.base_url:
            logger.debug("外部索引引擎 base_url 未配置，跳过搜索")
            return []
        
        # 获取 HTTP 客户端
        client = get_http_client()
        
        # 调用客户端搜索
        items = await client.search_torrents(
            site_id=site_id,
            keyword=keyword,
            media_type=media_type,
            categories=categories,
            page=page,
        )
        
        # 转换为字典列表，字段对齐 ExternalTorrentResult
        result = []
        for item in items:
            item_dict = item.model_dump()
            
            # 提取标准字段
            torrent_dict = {
                "site_id": item_dict.get("site_id"),
                "torrent_id": item_dict.get("torrent_id"),
                "title": item_dict.get("title"),
                "size_bytes": item_dict.get("size_bytes"),
                "seeders": item_dict.get("seeders"),
                "leechers": item_dict.get("leechers"),
                "published_at": item_dict.get("published_at"),
                "categories": item_dict.get("categories", []),
                "tags": item_dict.get("tags", []),
                "is_hr": item_dict.get("is_hr", False),
                "free_percent": item_dict.get("free_percent"),
            }
            
            # 其余内容丢进 raw
            raw = {}
            for key, value in item_dict.items():
                if key not in torrent_dict:
                    raw[key] = value
            if item_dict.get("extra"):
                raw.update(item_dict["extra"])
            
            torrent_dict["raw"] = raw
            
            result.append(torrent_dict)
        
        return result
        
    except Exception as e:
        logger.warning(f"external indexer engine search_torrents failed: {e}", exc_info=True)
        return []


async def fetch_rss(
    site_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    获取 RSS 种子列表
    
    Args:
        site_id: 站点 ID
        limit: 返回数量限制
        
    Returns:
        RSS 种子字典列表，字段对齐 ExternalTorrentResult
    """
    try:
        settings = get_engine_settings()
        
        # 如果未配置 base_url，直接返回空列表
        if not settings.base_url:
            logger.debug("外部索引引擎 base_url 未配置，跳过 RSS")
            return []
        
        # 获取 HTTP 客户端
        client = get_http_client()
        
        # 调用客户端获取 RSS
        items = await client.fetch_rss(
            site_id=site_id,
            limit=limit,
        )
        
        # 转换为字典列表（与 search_torrents 相同的逻辑）
        result = []
        for item in items:
            item_dict = item.model_dump()
            
            torrent_dict = {
                "site_id": item_dict.get("site_id"),
                "torrent_id": item_dict.get("torrent_id"),
                "title": item_dict.get("title"),
                "size_bytes": item_dict.get("size_bytes"),
                "seeders": item_dict.get("seeders"),
                "leechers": item_dict.get("leechers"),
                "published_at": item_dict.get("published_at"),
                "categories": item_dict.get("categories", []),
                "tags": item_dict.get("tags", []),
                "is_hr": item_dict.get("is_hr", False),
                "free_percent": item_dict.get("free_percent"),
            }
            
            raw = {}
            for key, value in item_dict.items():
                if key not in torrent_dict:
                    raw[key] = value
            if item_dict.get("extra"):
                raw.update(item_dict["extra"])
            
            torrent_dict["raw"] = raw
            
            result.append(torrent_dict)
        
        return result
        
    except Exception as e:
        logger.warning(f"external indexer engine fetch_rss failed: {e}", exc_info=True)
        return []


async def get_detail(
    site_id: str,
    torrent_id: str,
) -> Optional[Dict[str, Any]]:
    """
    获取种子详细信息
    
    Args:
        site_id: 站点 ID
        torrent_id: 种子 ID
        
    Returns:
        种子详细信息字典，字段对齐 ExternalTorrentDetail，如果不存在则返回 None
    """
    try:
        settings = get_engine_settings()
        
        # 如果未配置 base_url，直接返回 None
        if not settings.base_url:
            logger.debug("外部索引引擎 base_url 未配置，跳过详情")
            return None
        
        # 获取 HTTP 客户端
        client = get_http_client()
        
        # 调用客户端获取详情
        detail = await client.get_detail(
            site_id=site_id,
            torrent_id=torrent_id,
        )
        
        if detail is None:
            return None
        
        # 转换为字典，字段对齐 ExternalTorrentDetail
        detail_dict = detail.model_dump()
        
        result = {
            "site_id": detail_dict.get("site_id"),
            "torrent_id": detail_dict.get("torrent_id"),
            "title": detail_dict.get("title"),
            "description_html": detail_dict.get("description_html"),
            "screenshots": detail_dict.get("screenshots", []),
            "media_info": detail_dict.get("media_info"),
            "tags": detail_dict.get("tags", []),
        }
        
        # 其余内容丢进 raw
        raw = {}
        for key, value in detail_dict.items():
            if key not in result:
                raw[key] = value
        if detail_dict.get("extra"):
            raw.update(detail_dict["extra"])
        
        result["raw"] = raw
        
        return result
        
    except Exception as e:
        logger.warning(f"external indexer engine get_detail failed: {e}", exc_info=True)
        return None


async def get_download_link(
    site_id: str,
    torrent_id: str,
) -> Optional[str]:
    """
    获取种子下载链接
    
    Args:
        site_id: 站点 ID
        torrent_id: 种子 ID
        
    Returns:
        下载链接字符串，如果获取失败则返回 None
    """
    try:
        settings = get_engine_settings()
        
        # 如果未配置 base_url，直接返回 None
        if not settings.base_url:
            logger.debug("外部索引引擎 base_url 未配置，跳过下载链接")
            return None
        
        # 获取 HTTP 客户端
        client = get_http_client()
        
        # 调用客户端获取下载链接
        link_dict = await client.get_download_link(
            site_id=site_id,
            torrent_id=torrent_id,
        )
        
        if link_dict is None:
            return None
        
        # 提取下载链接字符串
        if isinstance(link_dict, dict):
            # 优先使用 download_url 字段
            if "download_url" in link_dict:
                return link_dict["download_url"]
            # 如果没有 download_url，尝试其他可能的字段
            elif "url" in link_dict:
                return link_dict["url"]
            elif "link" in link_dict:
                return link_dict["link"]
            else:
                logger.warning(f"下载链接字典中未找到有效字段: {link_dict}")
                return None
        elif isinstance(link_dict, str):
            return link_dict
        else:
            logger.warning(f"意外的下载链接类型: {type(link_dict)}")
            return None
        
    except Exception as e:
        logger.warning(f"external indexer engine get_download_link failed: {e}", exc_info=True)
        return None

