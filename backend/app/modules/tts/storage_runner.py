"""
TTS 存储自动清理 Runner

提供定时自动清理 TTS 存储的功能，根据策略和配置决定是否执行清理。
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import Settings
from app.models.tts_storage_cleanup_log import TTSStorageCleanupLog
from app.modules.tts.storage_service import (
    scan_storage,
    build_overview,
    build_cleanup_plan_from_policy,
    execute_cleanup,
)
from app.modules.tts.storage_policy import get_default_storage_policy
from app.utils.time import utcnow


@dataclass
class TTSStorageAutoCleanupResult:
    """自动清理结果"""
    status: str  # "success" / "skipped" / "failed"
    reason: Optional[str]  # 跳过/失败原因
    deleted_files_count: int
    freed_bytes: int
    started_at: datetime
    finished_at: datetime
    dry_run: bool


def _compute_warning_level(overview, settings: Settings) -> str:
    """
    计算存储警告级别
    
    Args:
        overview: TTSStorageOverview 对象
        settings: 配置对象
    
    Returns:
        "ok" | "high_usage" | "critical" | "no_root" | "scan_error"
    """
    total_size_bytes = overview.total_size_bytes or 0
    size_gb = total_size_bytes / (1024**3) if total_size_bytes else 0
    warn_threshold = getattr(settings, 'SMART_TTS_STORAGE_WARN_SIZE_GB', 10.0)
    critical_threshold = getattr(settings, 'SMART_TTS_STORAGE_CRITICAL_SIZE_GB', 30.0)
    
    if size_gb >= critical_threshold:
        return "critical"
    elif size_gb >= warn_threshold:
        return "high_usage"
    else:
        return "ok"


def _interval_ok(last_finished_at: Optional[datetime], now: datetime, min_interval_hours: float) -> bool:
    """
    检查是否满足最小间隔要求
    
    Args:
        last_finished_at: 上次完成时间
        now: 当前时间
        min_interval_hours: 最小间隔（小时）
    
    Returns:
        True 表示可以执行，False 表示间隔太短
    """
    if last_finished_at is None:
        return True
    
    elapsed = (now - last_finished_at).total_seconds() / 3600
    return elapsed >= min_interval_hours


def _shorten_exception(e: Exception) -> str:
    """缩短异常信息，避免过长"""
    msg = str(e)
    if len(msg) > 500:
        return msg[:500] + "..."
    return msg


async def _get_last_auto_log(db: AsyncSession) -> Optional[TTSStorageCleanupLog]:
    """获取最近一次自动清理日志"""
    try:
        stmt = (
            select(TTSStorageCleanupLog)
            .where(TTSStorageCleanupLog.mode == "auto")
            .order_by(desc(TTSStorageCleanupLog.finished_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"Failed to get last auto cleanup log: {e}")
        return None


def _result_skipped(reason: str) -> TTSStorageAutoCleanupResult:
    """创建跳过结果"""
    now = utcnow()
    return TTSStorageAutoCleanupResult(
        status="skipped",
        reason=reason,
        deleted_files_count=0,
        freed_bytes=0,
        started_at=now,
        finished_at=now,
        dry_run=False
    )


async def run_scheduled_cleanup(
    db: AsyncSession,
    settings: Settings,
    dry_run_override: Optional[bool] = None,
    force: bool = False,
) -> TTSStorageAutoCleanupResult:
    """
    执行一次定时自动清理
    
    Args:
        db: 数据库会话
        settings: 配置对象
        dry_run_override: 覆盖配置中的 dry_run 设置
        force: 是否忽略间隔和警告级别检查
    
    Returns:
        清理结果
    """
    now = utcnow()
    
    # 1) 检查是否启用
    if not force and not getattr(settings, 'SMART_TTS_STORAGE_AUTO_ENABLED', False):
        return _result_skipped("auto_disabled")
    
    # 2) 检查最小间隔
    if not force:
        last_auto_log = await _get_last_auto_log(db)
        min_interval = getattr(settings, 'SMART_TTS_STORAGE_AUTO_MIN_INTERVAL_HOURS', 12.0)
        if last_auto_log and not _interval_ok(last_auto_log.finished_at, now, min_interval):
            return _result_skipped("too_soon")
    
    # 3) 扫描存储 & 判断 warning_level
    root = Path(settings.SMART_TTS_OUTPUT_ROOT)
    if not root.exists():
        return _result_skipped("no_root")
    
    try:
        files = scan_storage(root, max_files=None)
        overview = build_overview(files, root)
        warning_level = _compute_warning_level(overview, settings)
        
        # 检查警告级别
        if not force:
            only_when_above_warn = getattr(settings, 'SMART_TTS_STORAGE_AUTO_ONLY_WHEN_ABOVE_WARN', True)
            if only_when_above_warn and warning_level in ("ok", "no_root", "scan_error"):
                reason = "below_warn" if warning_level == "ok" else warning_level
                return _result_skipped(reason)
    except Exception as e:
        logger.error(f"Failed to scan storage: {e}", exc_info=True)
        return _result_skipped("scan_error")
    
    # 4) 基于 policy 计算清理计划
    try:
        policy = get_default_storage_policy(settings)
        plan = build_cleanup_plan_from_policy(files, root, policy)
        
        if len(plan.matched_files) <= 0:
            return _result_skipped("nothing_to_clean")
    except Exception as e:
        logger.error(f"Failed to build cleanup plan: {e}", exc_info=True)
        return _result_skipped("plan_error")
    
    # 确定 dry_run
    if dry_run_override is not None:
        dry_run = dry_run_override
    else:
        dry_run = getattr(settings, 'SMART_TTS_STORAGE_AUTO_DRY_RUN', True)
    
    # 5) 创建日志记录（started）
    log = TTSStorageCleanupLog(
        mode="auto",
        strategy="policy",
        scope="all",  # 策略模式总是 all
        started_at=now,
        dry_run=dry_run,
        status="running",
    )
    db.add(log)
    await db.flush()
    
    try:
        # 6) 执行清理
        exec_result = execute_cleanup(plan, dry_run=dry_run)
        
        log.finished_at = utcnow()
        log.deleted_files_count = exec_result.total_deleted_files
        log.freed_bytes = exec_result.total_freed_bytes
        
        if dry_run:
            log.status = "skipped"
            log.reason = "dry_run"
        else:
            log.status = "success"
            log.reason = None
        
        await db.commit()
        
        return TTSStorageAutoCleanupResult(
            status=log.status,
            reason=log.reason,
            deleted_files_count=log.deleted_files_count,
            freed_bytes=log.freed_bytes,
            started_at=log.started_at,
            finished_at=log.finished_at,
            dry_run=dry_run,
        )
    except Exception as e:
        logger.error(f"Failed to execute cleanup: {e}", exc_info=True)
        log.finished_at = utcnow()
        log.status = "failed"
        log.reason = "exception"
        log.error_message = _shorten_exception(e)
        await db.commit()
        
        return TTSStorageAutoCleanupResult(
            status="failed",
            reason="exception",
            deleted_files_count=0,
            freed_bytes=0,
            started_at=log.started_at,
            finished_at=log.finished_at,
            dry_run=dry_run,
        )

