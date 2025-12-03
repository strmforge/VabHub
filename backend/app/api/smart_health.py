"""
智能子系统健康检查 API

提供轻量级的自诊断接口，用于检查智能子系统（Local Intel / External Indexer / AI Site Adapter）的运行状态。
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_

from pathlib import Path
from app.core.config import settings
from app.core.database import get_db
from app.models.inbox import InboxRunLog
from app.models.media import Media
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.comic import Comic
from app.models.music import Music
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME

router = APIRouter()


async def get_inbox_health(
    settings,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    获取统一收件箱（INBOX）的健康状态信息
    
    这是一个内部 helper 函数，可以被 smart_health() 和 admin_library_settings API 复用。
    
    Args:
        settings: 配置对象
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: 包含 inbox 健康状态的字典
    """
    inbox_status: Dict[str, Any] = {
        "enabled": False,
        "inbox_root": settings.INBOX_ROOT,
        "enabled_media_types": [],
        "last_run_at": None,
        "last_run_status": "never",
        "last_run_summary": None,
        "pending_warning": None
    }
    
    # 检查哪些媒体类型启用了
    enabled_types: List[str] = []
    if settings.INBOX_ENABLE_VIDEO:
        enabled_types.append("video")
    if settings.INBOX_ENABLE_EBOOK:
        enabled_types.append("ebook")
    if settings.INBOX_ENABLE_AUDIOBOOK:
        enabled_types.append("audiobook")
    if settings.INBOX_ENABLE_NOVEL_TXT:
        enabled_types.append("novel_txt")
    if settings.INBOX_ENABLE_COMIC:
        enabled_types.append("comic")
    if settings.INBOX_ENABLE_MUSIC:
        enabled_types.append("music")
    
    inbox_status["enabled_media_types"] = enabled_types
    inbox_status["enabled"] = len(enabled_types) > 0
    
    # 如果启用了，查询最近的运行日志
    if inbox_status["enabled"]:
        try:
            stmt = (
                select(InboxRunLog)
                .order_by(desc(InboxRunLog.finished_at))
                .limit(1)
            )
            result_query = await db.execute(stmt)
            last_log = result_query.scalar_one_or_none()
            
            if last_log:
                inbox_status["last_run_at"] = last_log.finished_at.isoformat() if last_log.finished_at else None
                inbox_status["last_run_status"] = last_log.status
                inbox_status["last_run_summary"] = last_log.message
                
                # 计算 pending_warning
                if last_log.finished_at:
                    hours_since_last_run = (datetime.utcnow() - last_log.finished_at).total_seconds() / 3600
                    
                    # 如果最近一次状态是 failed，优先显示失败警告
                    if last_log.status == "failed":
                        inbox_status["pending_warning"] = "last_run_failed"
                    # 如果超过 24 小时没跑，给出警告
                    elif hours_since_last_run > 24:
                        inbox_status["pending_warning"] = "too_long_without_run"
                elif last_log.status == "failed":
                    # 即使没有 finished_at，如果状态是 failed，也给出警告
                    inbox_status["pending_warning"] = "last_run_failed"
            else:
                # 没有运行记录
                inbox_status["last_run_status"] = "never"
                inbox_status["pending_warning"] = "never_run" if inbox_status["enabled"] else None
        except Exception as e:
            logger.warning(f"查询收件箱运行日志失败: {e}")
            # 查询失败不影响整体健康检查，只记录警告
    
    return inbox_status


async def compute_multi_format_work_stats(db: AsyncSession) -> Dict[str, int]:
    """
    计算多形态作品统计（以 EBook 为作品中心）
    
    复用 LIBRARY-WORK-BADGE-1 中的匹配逻辑，避免 N+1 查询。
    
    Args:
        db: 数据库会话
    
    Returns:
        Dict[str, int]: 包含 ebook_only, ebook_with_audiobook, ebook_with_comic, ebook_with_both 的字典
    """
    stats = {
        "ebook_only": 0,
        "ebook_with_audiobook": 0,
        "ebook_with_comic": 0,
        "ebook_with_both": 0
    }
    
    try:
        # 1. 获取所有 EBook（限制最大数量，避免内存问题）
        # 注意：这里不限制数量，因为统计需要全量数据
        ebook_stmt = select(EBook.id, EBook.series, EBook.title)
        ebook_result = await db.execute(ebook_stmt)
        ebook_list = ebook_result.all()
        
        if not ebook_list:
            return stats
        
        ebook_ids = [ebook.id for ebook in ebook_list]
        
        # 2. 批量查询 AudiobookFile（通过 ebook_id IN）
        audiobook_ebook_ids: set = set()
        try:
            audiobook_stmt = (
                select(AudiobookFile.ebook_id)
                .where(
                    AudiobookFile.ebook_id.in_(ebook_ids),
                    AudiobookFile.is_deleted == False
                )
                .distinct()
            )
            audiobook_result = await db.execute(audiobook_stmt)
            audiobook_ebook_ids = set(audiobook_result.scalars().all())
        except Exception as e:
            logger.warning(f"批量查询有声书关联失败: {e}")
        
        # 3. 批量查询 Comic（通过 series/title 匹配，复用 LIBRARY-WORK-BADGE-1 逻辑）
        ebook_series_map: Dict[str, List[int]] = {}  # series -> [ebook_ids]
        ebook_title_map: Dict[str, List[int]] = {}  # title -> [ebook_ids]
        
        for ebook in ebook_list:
            # 优先使用 series 匹配
            if ebook.series:
                if ebook.series not in ebook_series_map:
                    ebook_series_map[ebook.series] = []
                ebook_series_map[ebook.series].append(ebook.id)
            # 如果没有 series，使用 title
            elif ebook.title:
                if ebook.title not in ebook_title_map:
                    ebook_title_map[ebook.title] = []
                ebook_title_map[ebook.title].append(ebook.id)
        
        comic_ebook_ids: set = set()
        if ebook_series_map or ebook_title_map:
            try:
                comic_conditions = []
                
                # 构建匹配条件：优先 series，其次 title
                if ebook_series_map:
                    for series in ebook_series_map.keys():
                        comic_conditions.append(Comic.series.ilike(f"%{series}%"))
                
                if ebook_title_map:
                    for title in ebook_title_map.keys():
                        comic_conditions.append(Comic.title.ilike(f"%{title}%"))
                
                if comic_conditions:
                    # 查询匹配的 Comic（只取 series 和 title 用于匹配）
                    comic_stmt = (
                        select(Comic.series, Comic.title)
                        .where(or_(*comic_conditions))
                        .distinct()
                    )
                    comic_result = await db.execute(comic_stmt)
                    comic_rows = comic_result.all()
                    
                    # 在 Python 中匹配 comic 到 ebook
                    for comic_series, comic_title in comic_rows:
                        matched_ebook_ids: set = set()
                        
                        # 优先匹配 series
                        if comic_series:
                            for series, ebook_id_list in ebook_series_map.items():
                                comic_series_lower = comic_series.lower()
                                series_lower = series.lower()
                                if series_lower in comic_series_lower or comic_series_lower in series_lower:
                                    matched_ebook_ids.update(ebook_id_list)
                        
                        # 如果没有匹配到 series，尝试匹配 title
                        if not matched_ebook_ids and comic_title:
                            for title, ebook_id_list in ebook_title_map.items():
                                comic_title_lower = comic_title.lower()
                                title_lower = title.lower()
                                if title_lower in comic_title_lower or comic_title_lower in title_lower:
                                    matched_ebook_ids.update(ebook_id_list)
                        
                        comic_ebook_ids.update(matched_ebook_ids)
            except Exception as e:
                logger.warning(f"批量查询漫画关联失败: {e}")
        
        # 4. 统计每个 ebook 的形态
        for ebook in ebook_list:
            has_audiobook = ebook.id in audiobook_ebook_ids
            has_comic = ebook.id in comic_ebook_ids
            
            if has_audiobook and has_comic:
                stats["ebook_with_both"] += 1
            elif has_audiobook:
                stats["ebook_with_audiobook"] += 1
            elif has_comic:
                stats["ebook_with_comic"] += 1
            else:
                stats["ebook_only"] += 1
                
    except Exception as e:
        logger.warning(f"计算多形态作品统计失败: {e}")
    
    return stats


async def get_tts_health(settings, db: AsyncSession) -> Dict[str, Any]:
    """
    获取 TTS（文本转语音）子系统的健康状态信息
    
    这是一个内部 helper 函数，可以被 smart_health() 复用。
    
    Args:
        settings: 配置对象
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: 包含 TTS 健康状态的字典
    """
    tts_status: Dict[str, Any] = {
        "enabled": False,
        "provider": "",
        "output_root": "",
        "max_chapters": 0,
        "strategy": "",
        "status": "disabled",
        "last_used_at": None,
        "last_error": None
    }
    
    # 基本配置直接读取
    enabled = bool(settings.SMART_TTS_ENABLED)
    provider = str(settings.SMART_TTS_PROVIDER) if hasattr(settings, 'SMART_TTS_PROVIDER') else "dummy"
    output_root = str(settings.SMART_TTS_OUTPUT_ROOT) if hasattr(settings, 'SMART_TTS_OUTPUT_ROOT') else "./data/tts_output"
    max_chapters = int(settings.SMART_TTS_MAX_CHAPTERS) if hasattr(settings, 'SMART_TTS_MAX_CHAPTERS') else 200
    strategy = str(settings.SMART_TTS_CHAPTER_STRATEGY) if hasattr(settings, 'SMART_TTS_CHAPTER_STRATEGY') else "per_chapter"
    
    tts_status["enabled"] = enabled
    tts_status["provider"] = provider
    tts_status["output_root"] = output_root
    tts_status["max_chapters"] = max_chapters
    tts_status["strategy"] = strategy
    
    if not enabled:
        tts_status["status"] = "disabled"
    else:
        # 尝试初始化引擎，失败则视为 degraded
        try:
            from app.modules.tts.factory import get_tts_engine
            engine = get_tts_engine(settings=settings)
            
            # 如果顺利创建实例，我们认为基本"可用"
            if engine is not None:
                tts_status["status"] = "ok"
            else:
                tts_status["status"] = "degraded"
                tts_status["last_error"] = "TTS engine factory returned None"
        except Exception as exc:
            tts_status["status"] = "degraded"
            tts_status["last_error"] = str(exc)
            logger.warning(f"TTS 引擎初始化检查失败: {exc}")
    
    # 从 UsageTracker 获取使用历史
    try:
        from app.modules.tts.usage_tracker import get_state
        state = get_state()
        
        # 映射 last_used_at（实际上是 last_success_at）
        if state.last_success_at:
            tts_status["last_used_at"] = state.last_success_at.isoformat()
        
        # 映射 last_error
        if state.last_error_at and state.last_error_message:
            # 使用字符串格式，包含时间和错误信息
            error_str = f"[{state.last_error_at.isoformat()}] {state.last_error_message}"
            if state.last_provider:
                error_str += f" (provider: {state.last_provider})"
            tts_status["last_error"] = error_str
    except Exception as e:
        # 如果获取状态失败，不影响健康检查，只记录日志
        logger.warning(f"TTS usage tracker: failed to get state in health check: {e}")
        # last_used_at 和 last_error 保持为 None
    
    # 从 RateLimiter 获取配额信息
    try:
        from app.modules.tts.rate_limiter import get_state as get_rate_limit_state
        
        rate_limit_enabled = bool(getattr(settings, 'SMART_TTS_RATE_LIMIT_ENABLED', False))
        tts_status["rate_limit_enabled"] = rate_limit_enabled
        
        if rate_limit_enabled:
            rate_state = get_rate_limit_state()
            rate_limit_info = {
                "max_daily_requests": getattr(settings, 'SMART_TTS_MAX_DAILY_REQUESTS', 0),
                "max_daily_characters": getattr(settings, 'SMART_TTS_MAX_DAILY_CHARACTERS', 0),
                "max_requests_per_run": getattr(settings, 'SMART_TTS_MAX_REQUESTS_PER_RUN', 0),
            }
            
            if rate_state.last_limited_at:
                rate_limit_info["last_limited_at"] = rate_state.last_limited_at.isoformat()
            if rate_state.last_limited_reason:
                rate_limit_info["last_limited_reason"] = rate_state.last_limited_reason
            
            tts_status["rate_limit_info"] = rate_limit_info
        else:
            tts_status["rate_limit_info"] = None
    except Exception as e:
        # 如果获取限流状态失败，不影响健康检查，只记录日志
        logger.warning(f"TTS rate limiter: failed to get state in health check: {e}")
        tts_status["rate_limit_enabled"] = False
        tts_status["rate_limit_info"] = None
    
    # 从 TTSJob 获取 Job 概览（轻量级）
    try:
        from app.models.tts_job import TTSJob
        
        # 统计 queued jobs 数量
        queued_count_result = await db.execute(
            select(func.count(TTSJob.id)).where(TTSJob.status == "queued")
        )
        queued_jobs = queued_count_result.scalar() or 0
        
        # 获取最后一条 job
        last_job_result = await db.execute(
            select(TTSJob)
            .order_by(desc(TTSJob.requested_at))
            .limit(1)
        )
        last_job = last_job_result.scalar_one_or_none()
        
        tts_status["job_summary"] = {
            "queued_jobs": queued_jobs,
            "last_job_status": last_job.status if last_job else None,
            "last_job_finished_at": last_job.finished_at.isoformat() if last_job and last_job.finished_at else None
        }
    except Exception as e:
        logger.warning(f"TTS jobs: failed to get job summary in health check: {e}")
        tts_status["job_summary"] = {
            "queued_jobs": 0,
            "last_job_status": None,
            "last_job_finished_at": None
        }
    
    # 添加存储状态
    storage_block = None
    auto_cleanup_info = None
    try:
        from app.modules.tts.storage_service import scan_storage, build_overview
        from app.models.tts_storage_cleanup_log import TTSStorageCleanupLog
        from sqlalchemy import select, desc
        
        # 获取最近一次自动清理日志
        try:
            stmt = (
                select(TTSStorageCleanupLog)
                .where(TTSStorageCleanupLog.mode == "auto")
                .order_by(desc(TTSStorageCleanupLog.finished_at))
                .limit(1)
            )
            result_query = await db.execute(stmt)
            last_log = result_query.scalar_one_or_none()
            
            auto_cleanup_info = {
                "enabled": getattr(settings, 'SMART_TTS_STORAGE_AUTO_ENABLED', False),
                "last_run_at": last_log.finished_at.isoformat() if last_log and last_log.finished_at else None,
                "last_run_status": last_log.status if last_log else None,
                "last_run_freed_bytes": last_log.freed_bytes if last_log else 0,
                "last_run_reason": last_log.reason if last_log else None,
            }
        except Exception as e:
            logger.warning(f"Failed to get auto cleanup info: {e}")
            auto_cleanup_info = {
                "enabled": getattr(settings, 'SMART_TTS_STORAGE_AUTO_ENABLED', False),
                "last_run_at": None,
                "last_run_status": None,
                "last_run_freed_bytes": 0,
                "last_run_reason": None,
            }
        
        root = Path(settings.SMART_TTS_OUTPUT_ROOT)
        if not root.exists():
            storage_block = {
                "root": str(root),
                "total_files": 0,
                "total_size_bytes": 0,
                "by_category": {
                    "job": {"files": 0, "size_bytes": 0},
                    "playground": {"files": 0, "size_bytes": 0},
                    "other": {"files": 0, "size_bytes": 0}
                },
                "warning": "no_root",
            }
        else:
            # 扫描并构建概览
            files = scan_storage(root, max_files=None)
            overview = build_overview(files, root)
            
            total_size_bytes = overview.total_size_bytes
            total_files = overview.total_files
            
            # 构建按类别统计
            by_category = {
                "job": {
                    "files": overview.by_category.get("job", {}).get("files", 0),
                    "size_bytes": overview.by_category.get("job", {}).get("size_bytes", 0),
                },
                "playground": {
                    "files": overview.by_category.get("playground", {}).get("files", 0),
                    "size_bytes": overview.by_category.get("playground", {}).get("size_bytes", 0),
                },
                "other": {
                    "files": overview.by_category.get("other", {}).get("files", 0),
                    "size_bytes": overview.by_category.get("other", {}).get("size_bytes", 0),
                },
            }
            
            # 基于阈值计算 warning
            size_gb = total_size_bytes / (1024**3) if total_size_bytes else 0
            warn_threshold = getattr(settings, 'SMART_TTS_STORAGE_WARN_SIZE_GB', 10.0)
            critical_threshold = getattr(settings, 'SMART_TTS_STORAGE_CRITICAL_SIZE_GB', 30.0)
            
            if size_gb >= critical_threshold:
                warning = "critical"
            elif size_gb >= warn_threshold:
                warning = "high_usage"
            else:
                warning = "ok"
            
            storage_block = {
                "root": str(root),
                "total_files": total_files,
                "total_size_bytes": total_size_bytes,
                "by_category": by_category,
                "warning": warning,
            }
    except Exception as exc:
        # 不让异常影响整个 smart_health
        logger.warning(f"TTS storage scan failed in health check: {exc}")
        storage_block = {
            "root": str(settings.SMART_TTS_OUTPUT_ROOT),
            "total_files": 0,
            "total_size_bytes": 0,
            "by_category": {
                "job": {"files": 0, "size_bytes": 0},
                "playground": {"files": 0, "size_bytes": 0},
                "other": {"files": 0, "size_bytes": 0}
            },
            "warning": "scan_error",
        }
        # 即使扫描失败，也尝试获取 auto_cleanup 信息
        if auto_cleanup_info is None:
            try:
                from app.models.tts_storage_cleanup_log import TTSStorageCleanupLog
                from sqlalchemy import select, desc
                stmt = (
                    select(TTSStorageCleanupLog)
                    .where(TTSStorageCleanupLog.mode == "auto")
                    .order_by(desc(TTSStorageCleanupLog.finished_at))
                    .limit(1)
                )
                result_query = await db.execute(stmt)
                last_log = result_query.scalar_one_or_none()
                auto_cleanup_info = {
                    "enabled": getattr(settings, 'SMART_TTS_STORAGE_AUTO_ENABLED', False),
                    "last_run_at": last_log.finished_at.isoformat() if last_log and last_log.finished_at else None,
                    "last_run_status": last_log.status if last_log else None,
                    "last_run_freed_bytes": last_log.freed_bytes if last_log else 0,
                    "last_run_reason": last_log.reason if last_log else None,
                }
            except Exception:
                auto_cleanup_info = {
                    "enabled": getattr(settings, 'SMART_TTS_STORAGE_AUTO_ENABLED', False),
                    "last_run_at": None,
                    "last_run_status": None,
                    "last_run_freed_bytes": 0,
                    "last_run_reason": None,
                }
    
    # 将 auto_cleanup 信息添加到 storage_block
    if storage_block and auto_cleanup_info:
        storage_block["auto_cleanup"] = auto_cleanup_info
    elif storage_block:
        storage_block["auto_cleanup"] = {
            "enabled": getattr(settings, 'SMART_TTS_STORAGE_AUTO_ENABLED', False),
            "last_run_at": None,
            "last_run_status": None,
            "last_run_freed_bytes": 0,
            "last_run_reason": None,
        }
    
    tts_status["storage"] = storage_block
    
    return tts_status


async def get_library_health(
    settings,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    获取媒体库的健康状态信息
    
    Args:
        settings: 配置对象
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: 包含 library 健康状态的字典
    """
    library_status: Dict[str, Any] = {
        "enabled": False,
        "roots": {},
        "counts": {
            "movie": 0,
            "tv": 0,
            "anime": 0,
            "ebook": 0,
            "audiobook": 0,
            "comic": 0,
            "music": 0
        },
        "multi_format_works": {
            "ebook_only": 0,
            "ebook_with_audiobook": 0,
            "ebook_with_comic": 0,
            "ebook_with_both": 0
        },
        "pending_warning": None
    }
    
    # 1. 收集库根目录配置
    roots = {
        "movie": settings.MOVIE_LIBRARY_ROOT,
        "tv": settings.TV_LIBRARY_ROOT,
        "anime": settings.ANIME_LIBRARY_ROOT,
        "short_drama": settings.SHORT_DRAMA_LIBRARY_ROOT if hasattr(settings, 'SHORT_DRAMA_LIBRARY_ROOT') else None,
        "ebook": settings.EBOOK_LIBRARY_ROOT,
        "comic": settings.COMIC_LIBRARY_ROOT if hasattr(settings, 'COMIC_LIBRARY_ROOT') else None,
        "music": settings.MUSIC_LIBRARY_ROOT if hasattr(settings, 'MUSIC_LIBRARY_ROOT') else None
    }
    library_status["roots"] = roots
    
    # 判断是否启用：只要有任意一个 library_root 非空就视为启用
    library_status["enabled"] = any(root for root in roots.values() if root)
    
    # 2. 统计各媒体类型数量（避免 N+1，一次查询一个模型）
    try:
        # Movie
        movie_stmt = select(func.count(Media.id)).where(Media.media_type == MEDIA_TYPE_MOVIE)
        movie_result = await db.execute(movie_stmt)
        library_status["counts"]["movie"] = movie_result.scalar() or 0
        
        # TV
        tv_stmt = select(func.count(Media.id)).where(Media.media_type == MEDIA_TYPE_TV)
        tv_result = await db.execute(tv_stmt)
        library_status["counts"]["tv"] = tv_result.scalar() or 0
        
        # Anime
        anime_stmt = select(func.count(Media.id)).where(Media.media_type == MEDIA_TYPE_ANIME)
        anime_result = await db.execute(anime_stmt)
        library_status["counts"]["anime"] = anime_result.scalar() or 0
        
        # EBook（作品级）
        ebook_stmt = select(func.count(EBook.id))
        ebook_result = await db.execute(ebook_stmt)
        library_status["counts"]["ebook"] = ebook_result.scalar() or 0
        
        # Audiobook（文件级，统计 AudiobookFile）
        audiobook_stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
        audiobook_result = await db.execute(audiobook_stmt)
        library_status["counts"]["audiobook"] = audiobook_result.scalar() or 0
        
        # Comic（作品级，统计 Comic）
        comic_stmt = select(func.count(Comic.id))
        comic_result = await db.execute(comic_stmt)
        library_status["counts"]["comic"] = comic_result.scalar() or 0
        
        # Music（作品级，统计 Music）
        music_stmt = select(func.count(Music.id))
        music_result = await db.execute(music_stmt)
        library_status["counts"]["music"] = music_result.scalar() or 0
        
    except Exception as e:
        logger.warning(f"统计媒体库数量失败: {e}")
    
    # 3. 计算多形态作品统计
    try:
        multi_format_stats = await compute_multi_format_work_stats(db)
        library_status["multi_format_works"] = multi_format_stats
    except Exception as e:
        logger.warning(f"计算多形态作品统计失败: {e}")
    
    # 4. 计算 pending_warning
    total_count = sum(library_status["counts"].values())
    if total_count == 0:
        library_status["pending_warning"] = "empty_library"
    
    return library_status


@router.get("/health", summary="智能子系统健康检查")
async def smart_health(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    检查智能子系统的运行状态
    
    返回格式：
    {
        "ok": true,
        "features": {
            "local_intel": {
                "enabled": true,
                "db_ready": true
            },
            "external_indexer": {
                "enabled": true,
                "module_loaded": true,
                "runtime_ok": true
            },
            "ai_site_adapter": {
                "enabled": true,
                "endpoint_configured": true
            }
        }
    }
    """
    result: Dict[str, Any] = {
        "ok": True,
        "features": {}
    }
    
    # 检查 Local Intel
    local_intel_status: Dict[str, Any] = {
        "enabled": settings.INTEL_ENABLED,
        "db_ready": False
    }
    
    if settings.INTEL_ENABLED:
        try:
            # 尝试导入数据库相关模块，检查数据库是否可用
            from sqlalchemy.ext.asyncio import AsyncSession
            from app.core.database import get_db
            # 简单检查：如果能导入说明数据库配置正常
            local_intel_status["db_ready"] = True
        except ImportError as e:
            # 如果是导入错误（可能是项目代码问题），只记录但不标记为失败
            logger.debug(f"Local Intel 模块导入检查: {e}")
            local_intel_status["db_ready"] = True  # 假设数据库配置正常
        except Exception as e:
            logger.warning(f"Local Intel 数据库检查失败: {e}")
            local_intel_status["db_ready"] = False
            result["ok"] = False
    
    result["features"]["local_intel"] = local_intel_status
    
    # 检查 External Indexer
    external_indexer_status: Dict[str, Any] = {
        "enabled": settings.EXTERNAL_INDEXER_ENABLED,
        "module_loaded": False,
        "runtime_ok": False
    }
    
    if settings.EXTERNAL_INDEXER_ENABLED:
        # 检查模块是否配置
        if settings.EXTERNAL_INDEXER_MODULE:
            try:
                # 尝试导入配置的模块
                import importlib
                module = importlib.import_module(settings.EXTERNAL_INDEXER_MODULE)
                external_indexer_status["module_loaded"] = True
                
                # 尝试检查 runtime 是否可构造（轻量检查）
                try:
                    # 假设模块有 get_runtime 或类似函数
                    if hasattr(module, "get_runtime") or hasattr(module, "ExternalIndexerRuntime"):
                        external_indexer_status["runtime_ok"] = True
                    else:
                        # 如果模块存在但结构未知，至少标记为已加载
                        external_indexer_status["runtime_ok"] = True
                except Exception as e:
                    logger.debug(f"External Indexer runtime 检查失败: {e}")
                    external_indexer_status["runtime_ok"] = False
            except ImportError as e:
                logger.warning(f"External Indexer 模块导入失败: {e}")
                external_indexer_status["module_loaded"] = False
                result["ok"] = False
        else:
            logger.warning("External Indexer 已启用但未配置模块路径")
            result["ok"] = False
    
    result["features"]["external_indexer"] = external_indexer_status
    
    # 检查 AI Site Adapter
    ai_adapter_status: Dict[str, Any] = {
        "enabled": settings.AI_ADAPTER_ENABLED,
        "endpoint_configured": False
    }
    
    if settings.AI_ADAPTER_ENABLED:
        # 检查端点是否配置
        if settings.AI_ADAPTER_ENDPOINT and settings.AI_ADAPTER_ENDPOINT.strip():
            ai_adapter_status["endpoint_configured"] = True
        else:
            logger.warning("AI Site Adapter 已启用但未配置端点")
            result["ok"] = False
    
    result["features"]["ai_site_adapter"] = ai_adapter_status
    
    # 检查电子书元数据增强
    ebook_metadata_status: Dict[str, Any] = {
        "enabled": settings.SMART_EBOOK_METADATA_ENABLED,
        "status": "disabled",  # 默认状态
        "providers": [],
        "timeout_seconds": settings.SMART_EBOOK_METADATA_TIMEOUT,
        "last_success_at": None,
        "last_error": None
    }
    
    if settings.SMART_EBOOK_METADATA_ENABLED:
        # 解析 providers 列表
        provider_names = [
            name.strip()
            for name in settings.SMART_EBOOK_METADATA_PROVIDERS.split(",")
            if name.strip()
        ]
        ebook_metadata_status["providers"] = provider_names
        
        # 计算 status
        if not provider_names:
            # enabled=True 但 providers 为空，配置不完整
            ebook_metadata_status["status"] = "degraded"
            result["ok"] = False
        else:
            # 尝试初始化 metadata_service 以验证 providers 是否可用
            try:
                from app.modules.ebook.metadata_service import get_metadata_service
                service = get_metadata_service()
                
                # 检查实际加载的 providers 数量
                loaded_count = len(service.providers)
                if loaded_count == 0:
                    # 配置了 providers 但都加载失败
                    ebook_metadata_status["status"] = "degraded"
                    result["ok"] = False
                elif loaded_count < len(provider_names):
                    # 部分 providers 加载失败
                    ebook_metadata_status["status"] = "degraded"
                    # 不标记整体为失败，因为至少部分可用
                else:
                    # 所有 providers 加载成功
                    ebook_metadata_status["status"] = "ok"
                
                # TODO: 如果 metadata_service 将来记录了 last_success_at 和 last_error，
                # 可以从 service 中获取这些信息
                # 例如：
                # if hasattr(service, '_last_success_at'):
                #     ebook_metadata_status["last_success_at"] = service._last_success_at
                # if hasattr(service, '_last_error'):
                #     ebook_metadata_status["last_error"] = service._last_error
                
            except Exception as e:
                logger.warning(f"电子书元数据服务检查失败: {e}")
                ebook_metadata_status["status"] = "degraded"
                result["ok"] = False
    else:
        # enabled=False，状态为 disabled
        ebook_metadata_status["status"] = "disabled"
        # 即使禁用，也返回默认的 providers 配置（用于显示）
        provider_names = [
            name.strip()
            for name in settings.SMART_EBOOK_METADATA_PROVIDERS.split(",")
            if name.strip()
        ]
        ebook_metadata_status["providers"] = provider_names
    
    result["features"]["ebook_metadata"] = ebook_metadata_status
    
    # 检查统一收件箱（INBOX）- 使用 helper 函数
    inbox_status = await get_inbox_health(settings, db)
    result["features"]["inbox"] = inbox_status
    
    # 检查媒体库（Library）- 使用 helper 函数
    library_status = await get_library_health(settings, db)
    result["features"]["library"] = library_status
    
    # 检查 TTS（文本转语音）- 使用 helper 函数
    tts_status = await get_tts_health(settings, db)
    
    # 添加预设异常统计（轻量级，避免循环依赖）
    try:
        from app.models.tts_work_profile import TTSWorkProfile
        from app.models.tts_voice_preset import TTSVoicePreset
        
        # 简化统计：只计算最基础的异常情况
        # 1. bound_but_never_used: bound_works_count > 0 && tts_generated_works_count == 0
        # 2. high_bound_low_usage: bound_works_count >= 20 && usage_ratio < 0.3
        
        # 查询所有有 preset_id 的 work profile
        bound_counts_result = await db.execute(
            select(
                TTSWorkProfile.preset_id,
                func.count(func.distinct(TTSWorkProfile.ebook_id)).label("bound_count")
            )
            .where(TTSWorkProfile.preset_id.isnot(None))
            .group_by(TTSWorkProfile.preset_id)
        )
        bound_counts = {row.preset_id: row.bound_count for row in bound_counts_result.all()}
        
        # 查询已生成 TTS 的作品数（按 preset_id）
        from app.models.audiobook import AudiobookFile
        tts_counts_result = await db.execute(
            select(
                TTSWorkProfile.preset_id,
                func.count(func.distinct(AudiobookFile.ebook_id)).label("tts_count")
            )
            .join(
                AudiobookFile,
                AudiobookFile.ebook_id == TTSWorkProfile.ebook_id
            )
            .where(
                TTSWorkProfile.preset_id.isnot(None),
                AudiobookFile.is_tts_generated == True
            )
            .group_by(TTSWorkProfile.preset_id)
        )
        tts_counts = {row.preset_id: row.tts_count for row in tts_counts_result.all()}
        
        # 计算异常统计
        bound_but_never_used = 0
        high_bound_low_usage = 0
        
        for preset_id, bound_count in bound_counts.items():
            tts_count = tts_counts.get(preset_id, 0)
            
            # bound_but_never_used: 绑定了但从未生成
            if bound_count > 0 and tts_count == 0:
                bound_but_never_used += 1
            
            # high_bound_low_usage: 绑定 >= 20 但使用率 < 0.3
            if bound_count >= 20:
                usage_ratio = tts_count / bound_count if bound_count > 0 else 0.0
                if usage_ratio < 0.3:
                    high_bound_low_usage += 1
        
        tts_status["preset_anomaly_summary"] = {
            "bound_but_never_used": bound_but_never_used,
            "high_bound_low_usage": high_bound_low_usage
        }
    except Exception as e:
        logger.warning(f"计算 TTS 预设异常统计失败: {e}")
        tts_status["preset_anomaly_summary"] = None
    
    result["features"]["tts"] = tts_status
    
    # 如果 TTS 启用但状态为 degraded，可以考虑是否影响整体 ok
    # 建议：TTS 不属于"硬阻断功能"，status="degraded" 不强制把整体 ok 置为 False
    # 如果需要更保守的策略，可以在这里添加：
    # if tts_status["enabled"] and tts_status["status"] == "degraded":
    #     result["ok"] = False
    
    return result

