"""
外部索引桥接管理 API

提供外部索引的设置查看、状态查询等功能。
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.config import settings
from app.core.ext_indexer.registry import get_runtime

router = APIRouter(prefix="/api/ext-indexer", tags=["外部索引管理"])


@router.get("/settings")
async def get_settings():
    """
    获取外部索引设置（只读）
    
    Returns:
        当前生效的配置信息
    """
    try:
        # 读取 engine_base_url
        engine_base_url: Optional[str] = None
        try:
            from external_indexer_engine.config import get_engine_settings
            engine_settings = get_engine_settings()
            engine_base_url = engine_settings.base_url if engine_settings.base_url else None
        except Exception as e:
            logger.debug(f"无法读取 engine 配置: {e}")
            engine_base_url = None
        
        return {
            "enabled": settings.EXTERNAL_INDEXER_ENABLED,
            "module": settings.EXTERNAL_INDEXER_MODULE or "",
            "engine_base_url": engine_base_url,
            "timeout_seconds": settings.EXTERNAL_INDEXER_TIMEOUT_SECONDS,
            "min_results": settings.EXTERNAL_INDEXER_MIN_RESULTS,
        }
    except Exception as e:
        logger.error(f"获取外部索引设置失败: {e}")
        return {
            "error": "获取设置失败",
            "enabled": False,
            "module": "",
            "engine_base_url": None,
            "timeout_seconds": 15,
            "min_results": 20,
        }


@router.get("/status")
async def get_status():
    """
    获取外部索引运行状态
    
    Returns:
        运行状态信息
    """
    try:
        runtime = get_runtime()
        runtime_loaded = runtime is not None
        
        # 检查 external_indexer_engine.core 是否导入成功
        has_engine = False
        try:
            import external_indexer_engine.core
            has_engine = True
        except ImportError:
            has_engine = False
        except Exception:
            has_engine = False
        
        # 检查 runtime 是否真正加载成功
        if runtime_loaded and hasattr(runtime, "is_loaded"):
            runtime_loaded = runtime.is_loaded
        
        # 目前没有持久化的错误记录，先返回 null
        last_error: Optional[str] = None
        
        notes = "当前为只读配置，需要通过环境变量修改。"
        if not settings.EXTERNAL_INDEXER_ENABLED:
            notes += "外部索引功能已禁用。"
        elif not settings.EXTERNAL_INDEXER_MODULE:
            notes += "未配置外部索引模块路径。"
        elif not runtime_loaded:
            notes += "外部索引运行时加载失败，请检查模块路径和配置。"
        
        return {
            "enabled": settings.EXTERNAL_INDEXER_ENABLED,
            "runtime_loaded": runtime_loaded,
            "has_engine": has_engine,
            "last_error": last_error,
            "notes": notes,
        }
    except Exception as e:
        logger.error(f"获取外部索引状态失败: {e}")
        return {
            "error": "获取状态失败",
            "enabled": False,
            "runtime_loaded": False,
            "has_engine": False,
            "last_error": str(e),
            "notes": "状态查询失败",
        }


@router.get("/sites")
async def get_sites():
    """
    获取外部索引支持的站点列表
    
    Returns:
        站点 ID 列表
    """
    try:
        # 尝试从站点配置加载器获取站点列表
        try:
            from app.core.ext_indexer.site_importer import load_all_site_configs
            site_configs = load_all_site_configs()
            sites = [config.site_id for config in site_configs if config.enabled]
            return {
                "sites": sites,
                "count": len(sites),
            }
        except Exception as e:
            logger.debug(f"无法加载站点配置: {e}")
            # 如果加载失败，尝试从注册表获取
            try:
                from app.core.ext_indexer.registry import list_registered_sites
                sites = list_registered_sites()
                return {
                    "sites": sites,
                    "count": len(sites),
                }
            except Exception as e2:
                logger.debug(f"无法从注册表获取站点: {e2}")
                return {
                    "sites": [],
                    "count": 0,
                }
    except Exception as e:
        logger.error(f"获取站点列表失败: {e}")
        return {
            "error": "获取站点列表失败",
            "sites": [],
            "count": 0,
        }

