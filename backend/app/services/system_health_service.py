"""
系统健康检查服务
OPS-1A 实现
"""

from datetime import datetime
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.system_health import SystemHealthCheck, SystemRunnerStatus
from app.schemas.system_health import (
    SystemHealthCheckRead,
    SystemRunnerStatusRead,
    SystemHealthSummary,
    HealthStatus,
)


async def upsert_check(
    session: AsyncSession,
    *,
    key: str,
    check_type: str,
    status: str,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> SystemHealthCheck:
    """
    更新或插入健康检查记录
    """
    result = await session.execute(
        select(SystemHealthCheck).where(SystemHealthCheck.key == key)
    )
    check = result.scalar_one_or_none()
    
    if check is None:
        check = SystemHealthCheck(
            key=key,
            check_type=check_type,
            status=status,
            last_checked_at=datetime.utcnow(),
            last_duration_ms=duration_ms,
            last_error=error,
            meta=meta,
        )
        session.add(check)
    else:
        check.check_type = check_type
        check.status = status
        check.last_checked_at = datetime.utcnow()
        check.last_duration_ms = duration_ms
        check.last_error = error
        check.meta = meta
    
    await session.flush()
    logger.debug(f"[health] upsert check: key={key} status={status}")
    return check


async def get_all_checks(session: AsyncSession) -> list[SystemHealthCheck]:
    """获取所有健康检查记录"""
    result = await session.execute(
        select(SystemHealthCheck).order_by(SystemHealthCheck.key)
    )
    return list(result.scalars().all())


async def get_all_runners(session: AsyncSession) -> list[SystemRunnerStatus]:
    """获取所有 Runner 状态"""
    result = await session.execute(
        select(SystemRunnerStatus).order_by(SystemRunnerStatus.name)
    )
    return list(result.scalars().all())


async def get_health_summary(session: AsyncSession) -> SystemHealthSummary:
    """获取健康汇总"""
    checks = await get_all_checks(session)
    runners = await get_all_runners(session)
    
    # 统计各状态数量
    ok_count = sum(1 for c in checks if c.status == "ok")
    warning_count = sum(1 for c in checks if c.status == "warning")
    error_count = sum(1 for c in checks if c.status == "error")
    unknown_count = sum(1 for c in checks if c.status == "unknown")
    
    # 计算整体状态
    if error_count > 0:
        overall_status: HealthStatus = "error"
    elif warning_count > 0:
        overall_status = "warning"
    elif ok_count > 0:
        overall_status = "ok"
    else:
        overall_status = "unknown"
    
    # 最近检查时间
    last_check_time = None
    if checks:
        times = [c.last_checked_at for c in checks if c.last_checked_at]
        if times:
            last_check_time = max(times)
    
    return SystemHealthSummary(
        overall_status=overall_status,
        total_checks=len(checks),
        ok_count=ok_count,
        warning_count=warning_count,
        error_count=error_count,
        unknown_count=unknown_count,
        checks=[SystemHealthCheckRead.model_validate(c) for c in checks],
        runners=[SystemRunnerStatusRead.model_validate(r) for r in runners],
        last_check_time=last_check_time,
    )


# ============== Runner 心跳相关 ==============

async def runner_heartbeat_start(
    session: AsyncSession,
    *,
    name: str,
    runner_type: str = "scheduled",
    recommended_interval_min: Optional[int] = None,
) -> SystemRunnerStatus:
    """
    Runner 开始执行时调用
    """
    result = await session.execute(
        select(SystemRunnerStatus).where(SystemRunnerStatus.name == name)
    )
    runner = result.scalar_one_or_none()
    
    if runner is None:
        runner = SystemRunnerStatus(
            name=name,
            runner_type=runner_type,
            last_started_at=datetime.utcnow(),
            recommended_interval_min=recommended_interval_min,
        )
        session.add(runner)
    else:
        runner.runner_type = runner_type
        runner.last_started_at = datetime.utcnow()
        if recommended_interval_min is not None:
            runner.recommended_interval_min = recommended_interval_min
    
    await session.flush()
    logger.info(f"[runner] started: {name}")
    return runner


async def runner_heartbeat_finish(
    session: AsyncSession,
    *,
    name: str,
    exit_code: int,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
) -> SystemRunnerStatus:
    """
    Runner 结束执行时调用
    """
    result = await session.execute(
        select(SystemRunnerStatus).where(SystemRunnerStatus.name == name)
    )
    runner = result.scalar_one_or_none()
    
    if runner is None:
        # 如果没有 start 记录，也创建一个
        runner = SystemRunnerStatus(
            name=name,
            runner_type="scheduled",
            last_finished_at=datetime.utcnow(),
            last_exit_code=exit_code,
            last_duration_ms=duration_ms,
            last_error=error,
            success_count=1 if exit_code == 0 else 0,
            failure_count=0 if exit_code == 0 else 1,
        )
        session.add(runner)
    else:
        runner.last_finished_at = datetime.utcnow()
        runner.last_exit_code = exit_code
        runner.last_error = error
        if duration_ms is not None:
            runner.last_duration_ms = duration_ms
        
        # OPS-2C: 更新成功/失败计数
        if exit_code == 0:
            runner.success_count = (runner.success_count or 0) + 1
            runner.last_error = None  # 成功时清除错误信息
        else:
            runner.failure_count = (runner.failure_count or 0) + 1
    
    await session.flush()
    status_str = "success" if exit_code == 0 else f"failed(code={exit_code})"
    logger.info(f"[runner] finished: {name} {status_str}")
    return runner


async def get_runner_status(
    session: AsyncSession,
    name: str,
) -> Optional[SystemRunnerStatus]:
    """获取指定 Runner 状态"""
    result = await session.execute(
        select(SystemRunnerStatus).where(SystemRunnerStatus.name == name)
    )
    return result.scalar_one_or_none()


async def get_runner_stats(session: AsyncSession) -> list[dict]:
    """
    获取所有 Runner 的统计信息（OPS-2C）
    """
    result = await session.execute(
        select(SystemRunnerStatus).order_by(SystemRunnerStatus.name)
    )
    runners = result.scalars().all()
    
    stats = []
    for runner in runners:
        total_runs = (runner.success_count or 0) + (runner.failure_count or 0)
        success_rate = (runner.success_count or 0) / total_runs * 100 if total_runs > 0 else 0
        
        stats.append({
            "name": runner.name,
            "runner_type": runner.runner_type,
            "last_started_at": runner.last_started_at.isoformat() if runner.last_started_at else None,
            "last_finished_at": runner.last_finished_at.isoformat() if runner.last_finished_at else None,
            "last_exit_code": runner.last_exit_code,
            "last_duration_ms": runner.last_duration_ms,
            "last_error": runner.last_error,
            "recommended_interval_min": runner.recommended_interval_min,
            "success_count": runner.success_count or 0,
            "failure_count": runner.failure_count or 0,
            "total_runs": total_runs,
            "success_rate": round(success_rate, 1),
        })
    
    return stats


# ============== 健康检查运行 ==============

async def run_all_health_checks(session: AsyncSession) -> list[SystemHealthCheck]:
    """
    运行所有健康检查并写入数据库
    """
    from app.services.health_checks import (
        check_database,
        check_redis,
        check_download_client,
        check_external_indexer,
        check_manga_sources,
        check_music_chart_sources,
        check_disk_space,
    )
    
    results: list[SystemHealthCheck] = []
    
    # 1. 数据库检查
    db_result = await check_database(session)
    check = await upsert_check(
        session,
        key="db.default",
        check_type="db",
        status=db_result.status,
        duration_ms=db_result.duration_ms,
        error=db_result.error,
        meta=db_result.meta,
    )
    results.append(check)
    
    # 2. Redis 检查
    redis_result = await check_redis()
    check = await upsert_check(
        session,
        key="service.redis",
        check_type="service",
        status=redis_result.status,
        duration_ms=redis_result.duration_ms,
        error=redis_result.error,
        meta=redis_result.meta,
    )
    results.append(check)
    
    # 3. 下载器检查
    dl_result = await check_download_client()
    check = await upsert_check(
        session,
        key="service.download_client",
        check_type="service",
        status=dl_result.status,
        duration_ms=dl_result.duration_ms,
        error=dl_result.error,
        meta=dl_result.meta,
    )
    results.append(check)
    
    # 4. 外部索引器检查
    indexer_result = await check_external_indexer(session)
    check = await upsert_check(
        session,
        key="external.indexer",
        check_type="external",
        status=indexer_result.status,
        duration_ms=indexer_result.duration_ms,
        error=indexer_result.error,
        meta=indexer_result.meta,
    )
    results.append(check)
    
    # 5. 漫画源检查
    manga_results = await check_manga_sources(session)
    for key, result in manga_results.items():
        check = await upsert_check(
            session,
            key=key,
            check_type="external",
            status=result.status,
            duration_ms=result.duration_ms,
            error=result.error,
            meta=result.meta,
        )
        results.append(check)
    
    # 6. 音乐榜单源检查
    music_results = await check_music_chart_sources(session)
    for key, result in music_results.items():
        check = await upsert_check(
            session,
            key=key,
            check_type="external",
            status=result.status,
            duration_ms=result.duration_ms,
            error=result.error,
            meta=result.meta,
        )
        results.append(check)
    
    # 7. 磁盘空间检查
    disk_result = await check_disk_space()
    check = await upsert_check(
        session,
        key="disk.data",
        check_type="disk",
        status=disk_result.status,
        duration_ms=disk_result.duration_ms,
        error=disk_result.error,
        meta=disk_result.meta,
    )
    results.append(check)
    
    await session.commit()
    logger.info(f"[health] completed {len(results)} health checks")
    return results
