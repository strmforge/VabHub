"""
外部索引桥接调试 API

提供调试接口，用于测试和验证外部索引桥接功能。
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from loguru import logger

from app.core.ext_indexer.registry import (
    get_runtime,
    list_registered_sites,
)
from app.core.ext_indexer.site_importer import (
    load_all_site_configs,
    get_site_config,
)
from app.core.ext_indexer.models import ExternalTorrentResult
from app.core.config import settings

router = APIRouter(prefix="/api/debug/ext-indexer", tags=["外部索引调试"])


@router.get("/sites")
async def list_sites():
    """
    列出所有外部站点配置和已注册的适配器
    
    Returns:
        {
            "sites": [...],  # 从配置文件加载的站点
            "registered": [...]  # 已注册的适配器站点 ID
        }
    """
    try:
        # 加载所有站点配置
        site_configs = load_all_site_configs()
        sites = [config.dict() for config in site_configs]
        
        # 获取已注册的适配器
        registered = list_registered_sites()
        
        return {
            "sites": sites,
            "registered": registered,
        }
    except Exception as e:
        logger.error(f"列出外部站点失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出站点失败: {str(e)}")


@router.get("/search")
async def debug_search(
    site: str = Query(..., description="站点 ID"),
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
):
    """
    调试搜索接口
    
    直接调用外部索引运行时进行搜索。
    """
    runtime = get_runtime()
    if not runtime:
        raise HTTPException(
            status_code=503,
            detail="外部索引运行时未初始化，请检查配置",
        )
    
    try:
        # 调用运行时搜索
        raw_results = await runtime.search_torrents(
            site_id=site,
            keyword=q,
            page=page,
        )
        
        # 转换为 ExternalTorrentResult
        results = []
        for raw_result in raw_results:
            try:
                result = ExternalTorrentResult(
                    site_id=site,
                    torrent_id=str(raw_result.get("torrent_id") or raw_result.get("id") or ""),
                    title=str(raw_result.get("title") or raw_result.get("name") or ""),
                    size_bytes=raw_result.get("size_bytes") or raw_result.get("size"),
                    seeders=raw_result.get("seeders") or raw_result.get("seeds") or 0,
                    leechers=raw_result.get("leechers") or raw_result.get("peers") or 0,
                    published_at=raw_result.get("published_at"),
                    categories=raw_result.get("categories") or [],
                    tags=raw_result.get("tags") or [],
                    is_hr=raw_result.get("is_hr") or False,
                    free_percent=raw_result.get("free_percent") or raw_result.get("free"),
                    raw=raw_result,
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"转换搜索结果失败: {e}")
                continue
        
        return {
            "site": site,
            "query": q,
            "page": page,
            "results": [result.dict() for result in results],
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"外部索引搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/status")
async def get_status():
    """
    获取外部索引桥接状态
    
    Returns:
        {
            "external_indexer_enabled": bool,
            "external_indexer_module": str | null,
            "runtime_loaded": bool
        }
    """
    runtime = get_runtime()
    
    return {
        "external_indexer_enabled": settings.EXTERNAL_INDEXER_ENABLED,
        "external_indexer_module": settings.EXTERNAL_INDEXER_MODULE,
        "runtime_loaded": runtime is not None and hasattr(runtime, "is_loaded") and runtime.is_loaded,
    }

