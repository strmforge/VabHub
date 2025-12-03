"""
Local Intel API（Phase 6）
提供 HR 任务、事件、站点健康状态的只读 API
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.core.database import AsyncSessionLocal
from app.core.intel_local.factory import build_local_intel_engine
from app.core.intel_local.models import HRStatus
from app.core.intel_local.repo import SqlAlchemyHRCasesRepository, SqlAlchemySiteGuardRepository
from app.models.intel_local import HRCase, SiteGuardEvent

router = APIRouter(prefix="/intel", tags=["Local Intel"])


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_local_intel_engine():
    """获取 LocalIntelEngine 实例"""
    try:
        return build_local_intel_engine()
    except Exception as e:
        logger.error(f"获取 LocalIntelEngine 失败: {e}")
        raise HTTPException(status_code=500, detail="LocalIntel 引擎未初始化")


@router.get("/hr-tasks")
async def get_hr_tasks(
    site: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取 HR 任务列表，按风险排序。
    
    Args:
        site: 站点过滤（可选）
        status: HR 状态过滤（可选：ACTIVE, FINISHED, FAILED, NONE, UNKNOWN）
    
    Returns:
        HR 任务列表
    """
    try:
        hr_repo = SqlAlchemyHRCasesRepository(AsyncSessionLocal)
        
        items = []
        async for hr_case in hr_repo.list_active_for_site(site or ""):  # type: ignore[attr-defined]
            if site and hr_case.site != site:
                continue
            
            if status:
                if hr_case.hr_status.value != status.upper():
                    continue
            
            # 计算风险等级
            risk_level = "low"
            if hr_case.hr_status == HRStatus.ACTIVE:
                if hr_case.deadline:
                    remaining = (hr_case.deadline - datetime.utcnow()).total_seconds() / 3600
                    if remaining < 0:
                        risk_level = "high"
                    elif remaining < 24:
                        risk_level = "high"
                    elif remaining < 72:
                        risk_level = "medium"
            
            # 格式化保种时长
            seeding_time_str = None
            if hr_case.seeded_hours:
                days = int(hr_case.seeded_hours // 24)
                hours = int(hr_case.seeded_hours % 24)
                if days > 0:
                    seeding_time_str = f"{days}d{hours}h"
                else:
                    seeding_time_str = f"{hours}h"
            
            items.append({
                "id": f"hr_{hr_case.id}",
                "site": hr_case.site,
                "torrent_id": hr_case.torrent_id,
                "title": getattr(hr_case, "title", None) or f"Torrent {hr_case.torrent_id}",
                "hr_status": hr_case.hr_status.value,
                "deadline": hr_case.deadline.isoformat() if hr_case.deadline else None,
                "seeding_time": seeding_time_str,
                "risk_level": risk_level,
            })
        
        # 按风险等级排序（high > medium > low）
        risk_order = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda x: (risk_order.get(x["risk_level"], 99), x.get("deadline") or ""))
        
        return {"items": items}
        
    except Exception as e:
        logger.error(f"获取 HR 任务列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_intel_events(
    site: Optional[str] = None,
    limit: int = 100,
    since: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取最近的智能事件（种子删除、HR 扣分、站点风控等）。
    
    Args:
        site: 站点过滤（可选）
        limit: 返回数量限制（默认 100）
        since: 时间起点（ISO 格式字符串，可选）
    
    Returns:
        事件列表（按时间倒序）
    """
    try:
        from sqlalchemy import select, or_, desc
        from app.models.intel_local import InboxEvent as InboxEventModel, SiteGuardEvent as SiteGuardEventModel
        from datetime import datetime
        
        items = []
        since_dt = None
        
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            except Exception:
                logger.warning(f"无效的时间格式: {since}，忽略 since 参数")
        
        # 1. 查询站内信事件（InboxEvent）
        inbox_query = select(InboxEventModel)
        if site:
            inbox_query = inbox_query.where(InboxEventModel.site == site)
        if since_dt:
            inbox_query = inbox_query.where(InboxEventModel.created_at >= since_dt)
        inbox_query = inbox_query.order_by(desc(InboxEventModel.created_at)).limit(limit)
        
        inbox_result = await db.execute(inbox_query)
        inbox_events = inbox_result.scalars().all()
        
        for event in inbox_events:
            # 映射事件类型
            event_type_map = {
                "penalty": "HR_PENALTY",
                "delete": "TORRENT_DELETED",
                "throttle": "SITE_THROTTLED",
                "other": "OTHER",
            }
            event_type = event_type_map.get(event.event_type, "OTHER")
            
            # 构建标题和消息
            title = f"{event.site}: {event_type}"
            message = event.message_text or f"事件类型: {event.event_type}"
            
            # 如果是删除事件，添加种子ID信息
            if event.torrent_id:
                message = f"种子 ID: {event.torrent_id}. {message}"
            
            items.append({
                "id": f"inbox_{event.id}",
                "site": event.site,
                "type": event_type,
                "title": title,
                "message": message,
                "torrent_id": event.torrent_id,
                "created_at": (event.message_time or event.created_at).isoformat(),
            })
        
        # 2. 查询站点风控事件（SiteGuardEvent）
        guard_query = select(SiteGuardEventModel)
        if site:
            guard_query = guard_query.where(SiteGuardEventModel.site == site)
        if since_dt:
            guard_query = guard_query.where(SiteGuardEventModel.created_at >= since_dt)
        guard_query = guard_query.order_by(desc(SiteGuardEventModel.created_at)).limit(limit)
        
        guard_result = await db.execute(guard_query)
        guard_events = guard_result.scalars().all()
        
        for event in guard_events:
            # 构建标题和消息
            title = f"{event.site}: 站点风控"
            message = f"站点被限流/封禁"
            if event.cause:
                message = f"{message}，原因: {event.cause}"
            if event.block_until:
                message = f"{message}，解除时间: {event.block_until.isoformat()}"
            
            items.append({
                "id": f"guard_{event.id}",
                "site": event.site,
                "type": "SITE_THROTTLED",
                "title": title,
                "message": message,
                "torrent_id": None,
                "created_at": event.created_at.isoformat(),
            })
        
        # 3. 合并排序（按时间倒序）
        items.sort(key=lambda x: x["created_at"], reverse=True)
        
        # 4. 限制返回数量
        items = items[:limit]
        
        return {"items": items}
        
    except Exception as e:
        logger.error(f"获取智能事件列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sites")
async def get_intel_sites(
    db: AsyncSession = Depends(get_db),
):
    """
    获取各站点当前的健康状态。
    
    Returns:
        站点健康状态列表
    """
    try:
        from app.core.intel_local.site_profiles import get_all_site_profiles
        from app.models.site import Site
        from sqlalchemy import select
        
        site_profiles = get_all_site_profiles()
        
        # 查询数据库中的站点
        result = await db.execute(select(Site).where(Site.is_active == True))
        sites = result.scalars().all()
        
        items = []
        for site in sites:
            # 匹配站点配置
            site_key = site.name.lower().replace(" ", "").replace("-", "")
            matched_profile = None
            for profile_site, profile in site_profiles.items():
                if (
                    profile_site.lower() == site_key
                    or profile_site.lower() in site_key
                    or site_key in profile_site.lower()
                ):
                    matched_profile = profile
                    break
            
            if not matched_profile:
                continue
            
            # 查询最近的事件
            from sqlalchemy import select, func, desc
            from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel, InboxEvent as InboxEventModel
            
            # 查询最近的成功时间（从 HR 刷新或站内信刷新推断）
            # 这里简化处理：如果有最近的 HR 记录或站内信记录，认为最近成功过
            hr_repo = SqlAlchemyHRCasesRepository(AsyncSessionLocal)
            last_hr_seen = None
            async for hr_case in hr_repo.list_active_for_site(matched_profile.site):  # type: ignore[attr-defined]
                if hr_case.last_seen_at:
                    if not last_hr_seen or hr_case.last_seen_at > last_hr_seen:
                        last_hr_seen = hr_case.last_seen_at
                    break  # 只取第一个
            
            # 查询最近的站内信事件（成功处理）
            inbox_query = select(InboxEventModel).where(
                InboxEventModel.site == matched_profile.site
            ).order_by(desc(InboxEventModel.created_at)).limit(1)
            inbox_result = await db.execute(inbox_query)
            last_inbox_event = inbox_result.scalar_one_or_none()
            last_ok = last_hr_seen or (last_inbox_event.created_at if last_inbox_event else None)
            
            # 查询最近的风控事件
            guard_query = select(SiteGuardEventModel).where(
                SiteGuardEventModel.site == matched_profile.site
            ).order_by(desc(SiteGuardEventModel.created_at)).limit(1)
            guard_result = await db.execute(guard_query)
            latest_guard_event = guard_result.scalar_one_or_none()
            
            is_throttled = False
            last_error = None
            if latest_guard_event:
                if latest_guard_event.block_until and latest_guard_event.block_until > datetime.utcnow():
                    is_throttled = True
                last_error = latest_guard_event.created_at
            
            # 统计错误次数（最近 24 小时内的风控事件）
            error_count_query = select(func.count(SiteGuardEventModel.id)).where(
                SiteGuardEventModel.site == matched_profile.site,
                SiteGuardEventModel.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
            error_count_result = await db.execute(error_count_query)
            error_count = error_count_result.scalar_one() or 0
            
            items.append({
                "id": matched_profile.site,
                "name": site.name,
                "last_ok": last_ok.isoformat() if last_ok else None,
                "last_error": last_error.isoformat() if last_error else None,
                "is_throttled": is_throttled,
                "error_count": error_count,
            })
        
        return {"items": items}
        
    except Exception as e:
        logger.error(f"获取站点健康状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Phase 8: Local Intel 配置 API
@router.get("/settings")
async def get_intel_settings(
    db: AsyncSession = Depends(get_db),
):
    """
    获取 Local Intel 配置
    
    Returns:
        配置对象，包含 intel_enabled, intel_hr_mode, intel_move_check_enabled, intel_subscription_respect_site_guard
    """
    try:
        from app.modules.settings.service import SettingsService
        
        settings_service = SettingsService(db)
        
        intel_enabled = await settings_service.get_setting("intel_enabled", True)
        intel_hr_mode = await settings_service.get_setting("intel_hr_mode", "strict")
        intel_move_check_enabled = await settings_service.get_setting("intel_move_check_enabled", True)
        intel_subscription_respect_site_guard = await settings_service.get_setting("intel_subscription_respect_site_guard", True)
        
        return {
            "intel_enabled": bool(intel_enabled) if intel_enabled is not None else True,
            "intel_hr_mode": str(intel_hr_mode) if intel_hr_mode else "strict",
            "intel_move_check_enabled": bool(intel_move_check_enabled) if intel_move_check_enabled is not None else True,
            "intel_subscription_respect_site_guard": bool(intel_subscription_respect_site_guard) if intel_subscription_respect_site_guard is not None else True,
        }
        
    except Exception as e:
        logger.error(f"获取 Local Intel 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_intel_settings(
    settings_data: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    更新 Local Intel 配置
    
    Args:
        settings_data: 配置对象，包含 intel_enabled, intel_hr_mode, intel_move_check_enabled, intel_subscription_respect_site_guard
    
    Returns:
        更新后的配置对象
    """
    try:
        from app.modules.settings.service import SettingsService
        from app.core.config import settings as app_settings
        
        settings_service = SettingsService(db)
        
        # 验证和更新配置
        if "intel_enabled" in settings_data:
            intel_enabled = bool(settings_data["intel_enabled"])
            await settings_service.set_setting("intel_enabled", intel_enabled)
            # 同步到全局配置（如果支持）
            app_settings.INTEL_ENABLED = intel_enabled
        
        if "intel_hr_mode" in settings_data:
            hr_mode = str(settings_data["intel_hr_mode"])
            if hr_mode not in ("strict", "relaxed"):
                raise HTTPException(status_code=400, detail="intel_hr_mode 必须是 'strict' 或 'relaxed'")
            await settings_service.set_setting("intel_hr_mode", hr_mode)
        
        if "intel_move_check_enabled" in settings_data:
            move_check_enabled = bool(settings_data["intel_move_check_enabled"])
            await settings_service.set_setting("intel_move_check_enabled", move_check_enabled)
        
        if "intel_subscription_respect_site_guard" in settings_data:
            subscription_respect_site_guard = bool(settings_data["intel_subscription_respect_site_guard"])
            await settings_service.set_setting("intel_subscription_respect_site_guard", subscription_respect_site_guard)
        
        # 返回更新后的配置
        return await get_intel_settings(db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 Local Intel 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

