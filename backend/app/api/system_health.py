"""
系统健康检查 API
OPS-1C + OPS-2B/2C 实现
"""

from typing import Literal
from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.system_health import SystemHealthSummary
from app.services.system_health_service import (
    get_health_summary,
    run_all_health_checks,
    get_runner_stats,
)
from app.services.system_health_report_service import generate_health_report

router = APIRouter(prefix="/api/admin/health", tags=["系统健康"])


@router.get("/summary", response_model=SystemHealthSummary)
async def get_system_health_summary(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """
    获取系统健康汇总
    
    返回所有健康检查项和 Runner 状态的汇总信息
    """
    return await get_health_summary(session)


@router.post("/run_once", response_model=SystemHealthSummary)
async def run_health_check_once(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """
    手动触发健康检查
    
    立即运行所有健康检查并返回结果
    """
    await run_all_health_checks(session)
    return await get_health_summary(session)


@router.get("/report")
async def get_health_report(
    format: Literal["json", "markdown"] = Query("json", description="报告格式"),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """
    生成健康体检报告
    
    支持 JSON 和 Markdown 两种格式
    """
    report = await generate_health_report(session, format=format)
    
    if format == "markdown":
        return PlainTextResponse(content=report, media_type="text/markdown")
    
    return report


@router.get("/runners")
async def list_runner_stats(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """
    获取 Runner 运行统计
    
    包括成功/失败次数、平均耗时等
    """
    return await get_runner_stats(session)


# ============== 磁盘监控配置 (OPS-2D) ==============

from app.schemas.disk_monitor import DiskPathConfig, DiskMonitorConfig
from app.services.health_checks import check_disks_multi

# 简单的内存存储，生产环境应该使用数据库或配置文件
_disk_monitor_config: list[dict] = []


@router.get("/disk-config", response_model=DiskMonitorConfig)
async def get_disk_monitor_config(
    _: User = Depends(get_current_admin_user),
):
    """获取磁盘监控配置"""
    return DiskMonitorConfig(paths=[DiskPathConfig(**p) for p in _disk_monitor_config])


@router.put("/disk-config", response_model=DiskMonitorConfig)
async def update_disk_monitor_config(
    config: DiskMonitorConfig,
    _: User = Depends(get_current_admin_user),
):
    """更新磁盘监控配置"""
    global _disk_monitor_config
    _disk_monitor_config = [p.model_dump() for p in config.paths]
    return config


@router.post("/disk-check")
async def check_disk_paths(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """
    检查配置的磁盘路径
    
    返回每个磁盘的健康状态
    """
    from app.services.system_health_service import upsert_check
    
    if not _disk_monitor_config:
        return {"message": "未配置磁盘监控路径", "results": {}}
    
    results = await check_disks_multi(_disk_monitor_config)
    
    # 写入数据库
    for key, result in results.items():
        await upsert_check(
            session,
            key=key,
            check_type="disk",
            status=result.status,
            duration_ms=result.duration_ms,
            error=result.error,
            meta=result.meta,
        )
    
    await session.commit()
    
    return {
        "message": f"检查了 {len(results)} 个磁盘路径",
        "results": {k: v.model_dump() for k, v in results.items()},
    }
