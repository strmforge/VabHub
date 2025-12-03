"""
CookieCloud API路由
提供CookieCloud设置管理、同步控制、状态查询等API端点
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.schemas.cookiecloud import (
    CookieCloudSettingsRead, 
    CookieCloudSettingsUpdate,
    CookieCloudSyncResult,
    CookieCloudTestResult,
    CookieCloudSiteSyncResult
)
from app.modules.cookiecloud.service import CookieCloudSyncService
from app.models.cookiecloud import CookieCloudSettings
from app.schemas.common import ApiResponse, PaginationResponse

router = APIRouter(prefix="/cookiecloud", tags=["CookieCloud"])

# 速率限制存储（简单内存实现，生产环境建议使用Redis）
_sync_rate_limit = {}

def check_rate_limit(user_id: str = "default", max_requests: int = 1, window_minutes: int = 1) -> bool:
    """检查速率限制"""
    now = datetime.utcnow()
    key = f"sync_{user_id}"
    
    if key not in _sync_rate_limit:
        _sync_rate_limit[key] = []
    
    # 清理过期的请求记录
    _sync_rate_limit[key] = [
        req_time for req_time in _sync_rate_limit[key] 
        if now - req_time < timedelta(minutes=window_minutes)
    ]
    
    # 检查是否超过限制
    if len(_sync_rate_limit[key]) >= max_requests:
        return False
    
    # 记录新请求
    _sync_rate_limit[key].append(now)
    return True


@router.get("/settings", response_model=ApiResponse[CookieCloudSettingsRead])
async def get_cookiecloud_settings(
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(get_current_user)
):
    """获取CookieCloud设置"""
    try:
        sync_service = CookieCloudSyncService(db)
        settings = await sync_service._get_settings()
        
        if not settings:
            # 返回默认设置
            default_settings = CookieCloudSettingsRead(
                enabled=False,
                host="",
                uuid="",
                password="",
                sync_interval_minutes=60,
                safe_host_whitelist="[]",
                last_sync_at=None,
                last_status="NEVER",
                last_error=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            return ApiResponse(success=True, data=default_settings, message="获取默认设置")
        
        settings_read = CookieCloudSettingsRead.from_orm(settings)
        # 隐藏密码信息
        settings_read.password = "***" if settings_read.password else ""
        
        return ApiResponse(success=True, data=settings_read, message="获取设置成功")
        
    except Exception as e:
        logger.error(f"获取CookieCloud设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取设置失败: {e}")


@router.put("/settings", response_model=ApiResponse[CookieCloudSettingsRead])
async def update_cookiecloud_settings(
    settings_update: CookieCloudSettingsUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(get_current_user)
):
    """更新CookieCloud设置"""
    try:
        sync_service = CookieCloudSyncService(db)
        
        # 获取现有设置
        existing_settings = await sync_service._get_settings()
        
        if not existing_settings:
            # 创建新设置
            new_settings = CookieCloudSettings(
                enabled=settings_update.enabled,
                host=settings_update.host,
                uuid=settings_update.uuid,
                password=settings_update.password,
                sync_interval_minutes=settings_update.sync_interval_minutes or 60,
                safe_host_whitelist=settings_update.safe_host_whitelist or "[]",
                last_status="NEVER",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_settings)
        else:
            # 更新现有设置
            update_data = settings_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            # 如果密码是***，保持原密码不变
            if settings_update.password == "***":
                update_data.pop("password", None)
            
            for field, value in update_data.items():
                setattr(existing_settings, field, value)
        
        await db.commit()
        
        # 更新定时任务
        try:
            from app.core.scheduler import get_scheduler
            scheduler = get_scheduler()
            
            if settings_update.enabled and settings_update.sync_interval_minutes:
                # 启用定时任务
                scheduler.update_cookiecloud_sync_job(
                    user_id=current_user.id if hasattr(current_user, 'id') else 1,
                    interval_minutes=settings_update.sync_interval_minutes
                )
            else:
                # 禁用定时任务
                scheduler.remove_cookiecloud_sync_job(
                    user_id=current_user.id if hasattr(current_user, 'id') else 1
                )
        except Exception as e:
            logger.warning(f"更新CookieCloud定时任务失败: {e}")
        
        # 获取更新后的设置
        updated_settings = await sync_service._get_settings()
        settings_read = CookieCloudSettingsRead.from_orm(updated_settings)
        settings_read.password = "***" if settings_read.password else ""
        
        return ApiResponse(success=True, data=settings_read, message="设置更新成功")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"更新CookieCloud设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新设置失败: {e}")


@router.post("/sync", response_model=ApiResponse[CookieCloudSyncResult])
async def trigger_cookiecloud_sync(
    background_tasks: BackgroundTasks,
    user_id: str = "default",
    batch_size: Optional[int] = 10,
    site_timeout: Optional[int] = 30,
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(get_current_user)
):
    """触发CookieCloud同步（带速率限制）"""
    try:
        # 检查速率限制
        if not check_rate_limit(user_id, max_requests=1, window_minutes=1):
            raise HTTPException(
                status_code=429, 
                detail="同步请求过于频繁，请稍后再试（每分钟最多1次）"
            )
        
        # 检查配置
        sync_service = CookieCloudSyncService(db)
        settings = await sync_service._get_settings()
        
        if not settings or not settings.enabled:
            raise HTTPException(status_code=400, detail="CookieCloud未启用")
        
        if not settings.host or not settings.uuid or not settings.password:
            raise HTTPException(status_code=400, detail="CookieCloud配置不完整")
        
        # 添加后台同步任务
        background_tasks.add_task(
            _background_sync, 
            db, 
            batch_size or 10, 
            site_timeout or 30
        )
        
        return ApiResponse(
            success=True, 
            data=CookieCloudSyncResult(
                success=True,
                total_sites=0,
                synced_sites=0,
                unmatched_sites=0,
                error_sites=0,
                errors=["同步任务已启动，正在后台执行"]
            ),
            message="同步任务已启动"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发CookieCloud同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"触发同步失败: {e}")


@router.post("/sync-immediate", response_model=ApiResponse[CookieCloudSyncResult])
async def trigger_cookiecloud_sync_immediate(
    batch_size: Optional[int] = 10,
    site_timeout: Optional[int] = 30,
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(get_current_user)
):
    """立即触发CookieCloud同步（同步执行，用于测试）"""
    try:
        sync_service = CookieCloudSyncService(db)
        result = await sync_service.sync_all_sites(
            batch_size=batch_size or 10,
            site_timeout=site_timeout or 30
        )
        
        return ApiResponse(success=True, data=result, message="同步完成")
        
    except Exception as e:
        logger.error(f"立即同步CookieCloud失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {e}")


@router.post("/sync-site/{site_id}", response_model=ApiResponse[CookieCloudSiteSyncResult])
async def trigger_site_cookiecloud_sync(
    site_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(get_current_user)
):
    """触发单个站点的CookieCloud同步"""
    try:
        # 检查站点是否存在
        from app.models.site import Site
        from sqlalchemy import select
        
        result = await db.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        
        if not site:
            raise HTTPException(status_code=404, detail=f"站点 {site_id} 不存在")
        
        if not site.enabled:
            raise HTTPException(status_code=400, detail=f"站点 {site.name} 已禁用")
        
        # 添加后台同步任务
        background_tasks.add_task(_background_sync_site, db, site_id)
        
        return ApiResponse(
            success=True,
            data=CookieCloudSiteSyncResult(
                site_id=site_id,
                site_name=site.name,
                success=True,
                cookie_updated=False,
                error_message="同步任务已启动，正在后台执行"
            ),
            message="站点同步任务已启动"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发站点CookieCloud同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"触发站点同步失败: {e}")


@router.post("/test-connection", response_model=ApiResponse[CookieCloudTestResult])
async def test_cookiecloud_connection(
    db: AsyncSession = Depends(get_async_session)
):
    """测试CookieCloud连接"""
    try:
        sync_service = CookieCloudSyncService(db)
        connection_ok = await sync_service.test_connection()
        
        test_result = CookieCloudTestResult(
            success=connection_ok,
            message="连接成功" if connection_ok else "连接失败",
            details={
                "timestamp": datetime.utcnow().isoformat(),
                "test_type": "connection_test"
            }
        )
        
        return ApiResponse(success=True, data=test_result, message="连接测试完成")
        
    except Exception as e:
        logger.error(f"测试CookieCloud连接失败: {e}")
        test_result = CookieCloudTestResult(
            success=False,
            message="连接测试异常",
            details={"error": str(e)}
        )
        return ApiResponse(success=False, data=test_result, message=f"连接测试失败: {e}")


@router.get("/status", response_model=ApiResponse[Dict[str, Any]])
async def get_cookiecloud_status(
    db: AsyncSession = Depends(get_async_session)
):
    """获取CookieCloud状态概览"""
    try:
        sync_service = CookieCloudSyncService(db)
        settings = await sync_service._get_settings()
        
        if not settings:
            status_data = {
                "enabled": False,
                "configured": False,
                "last_sync_at": None,
                "last_status": "NEVER",
                "last_error": None,
                "total_sites": 0,
                "cookiecloud_sites": 0
            }
        else:
            # 统计站点信息
            from app.models.site import Site
            from app.schemas.cookiecloud import CookieSource
            from sqlalchemy import select, func
            
            total_sites_result = await db.execute(
                select(func.count(Site.id)).where(Site.enabled == True)
            )
            total_sites = total_sites_result.scalar() or 0
            
            cookiecloud_sites_result = await db.execute(
                select(func.count(Site.id)).where(
                    Site.enabled == True,
                    Site.cookie_source == CookieSource.COOKIECLOUD
                )
            )
            cookiecloud_sites = cookiecloud_sites_result.scalar() or 0
            
            status_data = {
                "enabled": settings.enabled,
                "configured": bool(settings.host and settings.uuid and settings.password),
                "last_sync_at": settings.last_sync_at.isoformat() if settings.last_sync_at else None,
                "last_status": settings.last_status,
                "last_error": settings.last_error,
                "sync_interval_minutes": settings.sync_interval_minutes,
                "total_sites": total_sites,
                "cookiecloud_sites": cookiecloud_sites,
                "safe_domains": len(settings.safe_host_whitelist or "[]") - 2 if settings.safe_host_whitelist else 0  # 简单计算
            }
        
        return ApiResponse(success=True, data=status_data, message="状态获取成功")
        
    except Exception as e:
        logger.error(f"获取CookieCloud状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {e}")


@router.get("/sync-history", response_model=ApiResponse[PaginationResponse[CookieCloudSyncHistory]])
async def get_cookiecloud_sync_history(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_async_session)
):
    """获取同步历史记录（简化实现）"""
    try:
        # 这里简化实现，实际应该有专门的同步历史表
        settings = await CookieCloudSyncService(db)._get_settings()
        
        history_items = []
        if settings and settings.last_sync_at:
            history_items.append({
                "id": 1,
                "sync_at": settings.last_sync_at.isoformat(),
                "status": settings.last_status,
                "error": settings.last_error,
                "total_sites": 0,  # 需要从日志或历史表获取
                "synced_sites": 0,
                "duration_seconds": 0
            })
        
        # 简单分页
        start = (page - 1) * size
        end = start + size
        paginated_items = history_items[start:end]
        
        pagination_data = PaginationResponse(
            items=paginated_items,
            total=len(history_items),
            page=page,
            size=size,
            pages=(len(history_items) + size - 1) // size
        )
        
        return ApiResponse(success=True, data=pagination_data, message="历史记录获取成功")
        
    except Exception as e:
        logger.error(f"获取同步历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {e}")


# 后台任务函数
async def _background_sync(db: AsyncSession, batch_size: int, site_timeout: int):
    """后台同步任务"""
    try:
        # 创建新的数据库会话
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as new_db:
            sync_service = CookieCloudSyncService(new_db)
            result = await sync_service.sync_all_sites(
                batch_size=batch_size,
                site_timeout=site_timeout
            )
            
            logger.info(f"后台CookieCloud同步完成: 成功 {result.synced_sites}, "
                       f"无匹配 {result.unmatched_sites}, 错误 {result.error_sites}")
            
    except Exception as e:
        logger.error(f"后台CookieCloud同步失败: {e}")


async def _background_sync_site(db: AsyncSession, site_id: int):
    """后台单站点同步任务"""
    try:
        # 创建新的数据库会话
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as new_db:
            sync_service = CookieCloudSyncService(new_db)
            result = await sync_service.sync_site(site_id)
            
            if result.success:
                logger.info(f"后台站点 {site_id} CookieCloud同步完成")
            else:
                logger.error(f"后台站点 {site_id} CookieCloud同步失败: {result.error_message}")
                
    except Exception as e:
        logger.error(f"后台站点 {site_id} CookieCloud同步异常: {e}")
