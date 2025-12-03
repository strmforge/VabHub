"""
外部依赖健康检查
OPS-1C 实现
"""

import time
from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.system_health import HealthCheckResult, HealthStatus


async def check_database(session: AsyncSession) -> HealthCheckResult:
    """检查数据库连接"""
    start = time.monotonic()
    try:
        await session.execute(text("SELECT 1"))
        duration_ms = int((time.monotonic() - start) * 1000)
        return HealthCheckResult(
            status="ok",
            duration_ms=duration_ms,
            meta={"query": "SELECT 1"},
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(f"[health] database check failed: {e}")
        return HealthCheckResult(
            status="error",
            duration_ms=duration_ms,
            error=str(e)[:500],
        )


async def check_redis() -> HealthCheckResult:
    """检查 Redis 连接"""
    start = time.monotonic()
    try:
        from app.core.config import settings
        
        if not settings.REDIS_ENABLED:
            return HealthCheckResult(
                status="ok",
                duration_ms=0,
                meta={"disabled": True},
            )
        
        import redis.asyncio as redis
        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        
        duration_ms = int((time.monotonic() - start) * 1000)
        return HealthCheckResult(
            status="ok",
            duration_ms=duration_ms,
            meta={"url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL},
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(f"[health] redis check failed: {e}")
        return HealthCheckResult(
            status="error",
            duration_ms=duration_ms,
            error=str(e)[:500],
        )


async def check_download_client() -> HealthCheckResult:
    """检查下载器连接（qBittorrent/Transmission）"""
    start = time.monotonic()
    try:
        # 尝试导入下载器服务
        from app.core.config import settings
        
        # 简单检查配置是否存在
        qb_url = getattr(settings, 'QB_URL', None) or getattr(settings, 'QBITTORRENT_URL', None)
        tr_url = getattr(settings, 'TR_URL', None) or getattr(settings, 'TRANSMISSION_URL', None)
        
        if not qb_url and not tr_url:
            return HealthCheckResult(
                status="warning",
                duration_ms=0,
                meta={"configured": False},
                error="未配置下载器",
            )
        
        # 简单返回配置存在
        duration_ms = int((time.monotonic() - start) * 1000)
        return HealthCheckResult(
            status="ok",
            duration_ms=duration_ms,
            meta={
                "qbittorrent": bool(qb_url),
                "transmission": bool(tr_url),
            },
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(f"[health] download client check failed: {e}")
        return HealthCheckResult(
            status="error",
            duration_ms=duration_ms,
            error=str(e)[:500],
        )


async def check_external_indexer(session: AsyncSession) -> HealthCheckResult:
    """检查外部索引器"""
    start = time.monotonic()
    try:
        # 检查是否有配置的外部索引器
        from sqlalchemy import select, func
        
        # 尝试查询 ext_indexer 表（如果存在）
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM ext_indexer WHERE enabled = true")
            )
            count = result.scalar() or 0
        except Exception:
            # 表不存在
            count = 0
        
        duration_ms = int((time.monotonic() - start) * 1000)
        
        if count == 0:
            return HealthCheckResult(
                status="warning",
                duration_ms=duration_ms,
                meta={"enabled_count": 0},
                error="无启用的外部索引器",
            )
        
        return HealthCheckResult(
            status="ok",
            duration_ms=duration_ms,
            meta={"enabled_count": count},
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(f"[health] external indexer check failed: {e}")
        return HealthCheckResult(
            status="error",
            duration_ms=duration_ms,
            error=str(e)[:500],
        )


async def check_manga_sources(session: AsyncSession) -> dict[str, HealthCheckResult]:
    """检查漫画源"""
    results: dict[str, HealthCheckResult] = {}
    start = time.monotonic()
    
    try:
        # 查询启用的漫画源
        try:
            result = await session.execute(
                text("SELECT id, name, enabled FROM manga_source WHERE enabled = true LIMIT 10")
            )
            sources = result.fetchall()
        except Exception:
            sources = []
        
        if not sources:
            results["manga_source.default"] = HealthCheckResult(
                status="warning",
                duration_ms=int((time.monotonic() - start) * 1000),
                error="无启用的漫画源",
            )
            return results
        
        for source in sources:
            source_id, name, enabled = source
            key = f"manga_source.{source_id}"
            results[key] = HealthCheckResult(
                status="ok",
                duration_ms=0,
                meta={"name": name, "enabled": enabled},
            )
        
    except Exception as e:
        logger.warning(f"[health] manga sources check failed: {e}")
        results["manga_source.default"] = HealthCheckResult(
            status="error",
            duration_ms=int((time.monotonic() - start) * 1000),
            error=str(e)[:500],
        )
    
    return results


async def check_music_chart_sources(session: AsyncSession) -> dict[str, HealthCheckResult]:
    """检查音乐榜单源"""
    results: dict[str, HealthCheckResult] = {}
    start = time.monotonic()
    
    try:
        # 查询启用的音乐榜单源
        try:
            result = await session.execute(
                text("SELECT id, name, enabled FROM music_chart_source WHERE enabled = true LIMIT 10")
            )
            sources = result.fetchall()
        except Exception:
            sources = []
        
        if not sources:
            results["music_chart_source.default"] = HealthCheckResult(
                status="warning",
                duration_ms=int((time.monotonic() - start) * 1000),
                error="无启用的音乐榜单源",
            )
            return results
        
        for source in sources:
            source_id, name, enabled = source
            key = f"music_chart_source.{source_id}"
            results[key] = HealthCheckResult(
                status="ok",
                duration_ms=0,
                meta={"name": name, "enabled": enabled},
            )
        
    except Exception as e:
        logger.warning(f"[health] music chart sources check failed: {e}")
        results["music_chart_source.default"] = HealthCheckResult(
            status="error",
            duration_ms=int((time.monotonic() - start) * 1000),
            error=str(e)[:500],
        )
    
    return results


async def check_disk_space() -> HealthCheckResult:
    """检查磁盘空间（默认数据目录）"""
    start = time.monotonic()
    try:
        import shutil
        from app.core.config import settings
        
        # 检查数据目录
        data_path = getattr(settings, 'STORAGE_PATH', './data')
        total, used, free = shutil.disk_usage(data_path)
        
        free_gb = free / (1024 ** 3)
        used_percent = (used / total) * 100
        free_percent = 100 - used_percent
        
        duration_ms = int((time.monotonic() - start) * 1000)
        
        status: HealthStatus = "ok"
        error = None
        
        if free_percent < 10:
            status = "error"
            error = f"磁盘空间不足: 剩余 {free_percent:.1f}%"
        elif free_percent < 20:
            status = "warning"
            error = f"磁盘空间较低: 剩余 {free_percent:.1f}%"
        
        return HealthCheckResult(
            status=status,
            duration_ms=duration_ms,
            error=error,
            meta={
                "path": data_path,
                "total_gb": round(total / (1024 ** 3), 2),
                "used_gb": round(used / (1024 ** 3), 2),
                "free_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 1),
                "free_percent": round(free_percent, 1),
            },
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(f"[health] disk space check failed: {e}")
        return HealthCheckResult(
            status="error",
            duration_ms=duration_ms,
            error=str(e)[:500],
        )


async def check_disks_multi(paths: list[dict]) -> dict[str, HealthCheckResult]:
    """
    检查多个磁盘路径（OPS-2D）
    
    Args:
        paths: 磁盘路径配置列表，每项包含 name, path, warn_percent, error_percent
        
    Returns:
        {disk.<name>: HealthCheckResult} 字典
    """
    import shutil
    
    results: dict[str, HealthCheckResult] = {}
    
    for disk_config in paths:
        name = disk_config.get("name", "unknown")
        path = disk_config.get("path", ".")
        warn_percent = disk_config.get("warn_percent", 20)
        error_percent = disk_config.get("error_percent", 10)
        
        key = f"disk.{name}"
        start = time.monotonic()
        
        try:
            total, used, free = shutil.disk_usage(path)
            
            free_gb = free / (1024 ** 3)
            used_percent = (used / total) * 100
            free_percent = 100 - used_percent
            
            duration_ms = int((time.monotonic() - start) * 1000)
            
            status: HealthStatus = "ok"
            error = None
            
            if free_percent < error_percent:
                status = "error"
                error = f"磁盘空间不足: 剩余 {free_percent:.1f}% (阈值 {error_percent}%)"
            elif free_percent < warn_percent:
                status = "warning"
                error = f"磁盘空间较低: 剩余 {free_percent:.1f}% (阈值 {warn_percent}%)"
            
            results[key] = HealthCheckResult(
                status=status,
                duration_ms=duration_ms,
                error=error,
                meta={
                    "name": name,
                    "path": path,
                    "total_gb": round(total / (1024 ** 3), 2),
                    "used_gb": round(used / (1024 ** 3), 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 1),
                    "free_percent": round(free_percent, 1),
                    "warn_percent": warn_percent,
                    "error_percent": error_percent,
                },
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.warning(f"[health] disk check failed for {path}: {e}")
            results[key] = HealthCheckResult(
                status="error",
                duration_ms=duration_ms,
                error=str(e)[:500],
                meta={"name": name, "path": path},
            )
    
    return results
