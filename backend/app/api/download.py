"""
下载相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from loguru import logger

from app.core.database import get_db
from app.modules.download.service import DownloadService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class DownloadTaskResponse(BaseModel):
    """下载任务响应"""
    id: str
    title: str
    status: str
    progress: float
    size_gb: float
    downloaded_gb: float
    speed_mbps: Optional[float] = None
    eta: Optional[int] = None  # 秒
    media_type: Optional[str] = None
    extra_metadata: Optional[dict] = None
    created_at: datetime
    
    # 扩展字段 - DOWNLOAD-CENTER-UI-1
    download_speed: Optional[float] = None  # MB/s
    upload_speed: Optional[float] = None    # MB/s
    site_name: Optional[str] = None         # 站点名称
    tracker_alias: Optional[str] = None     # 跟踪器别名
    hr_level: Optional[str] = None          # NONE/H&R/HR/H3/H5
    is_short_drama: bool = False            # 短剧标记
    labels: List[str] = []                  # 下载器标签列表
    added_at: Optional[datetime] = None     # 添加时间
    
    # Local Intel 状态字段（Phase 8）
    intel_hr_status: Optional[str] = None  # SAFE, RISK, ACTIVE, UNKNOWN
    intel_site_status: Optional[str] = None  # OK, THROTTLED, ERROR, UNKNOWN
    
    # DOWNLOAD-CENTER-UI-2 新增字段
    is_vabhub_managed: bool = False      # 是否为VabHub管理的任务（计算属性）
    organize_status: str = "NONE"        # 整理状态: NONE, AUTO_OK, AUTO_FAILED, MANUAL_PENDING, MANUAL_DONE
    
    class Config:
        from_attributes = True


@router.get("/", response_model=BaseResponse)
async def list_downloads(
    status: Optional[str] = Query(None, description="状态过滤: downloading, completed, paused, error"),
    vabhub_only: bool = Query(True, description="只显示带VABHUB标签的任务（包括用户手动添加的）"),
    hide_organized: bool = Query(True, description="隐藏已整理完成的任务（AUTO_OK, MANUAL_DONE），DOWNLOAD-CENTER-UI-2默认开启自动退场"),
    recent_hours: Optional[int] = Query(None, ge=1, le=168, description="最近完成任务时间范围（小时），DOWNLOAD-CENTER-UI-2新增"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取下载列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [DownloadTaskResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        
        # DOWNLOAD-CENTER-UI-1: 更新状态过滤逻辑
        # 默认返回 all_active (downloading + queued + error)
        if not status:
            status = "all_active"
        
        downloads = await service.list_downloads(
        status=status, 
        vabhub_only=vabhub_only, 
        hide_organized=hide_organized,
        recent_hours=recent_hours
    )
        
        # 批量查询 Local Intel 状态（Phase 8）
        from app.core.config import settings
        if settings.INTEL_ENABLED:
            try:
                from app.core.intel_local.repo import SqlAlchemyHRCasesRepository
                from app.core.intel_local.models import HRStatus
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import select, func
                from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
                from datetime import datetime, timedelta
                
                # 收集所有任务的 site_id 和 torrent_id
                site_torrent_pairs = []
                for download in downloads:
                    extra_meta = download.get("extra_metadata") or {}
                    site_id = extra_meta.get("site_id") or extra_meta.get("site")
                    torrent_id = extra_meta.get("torrent_id")
                    if site_id and torrent_id:
                        site_torrent_pairs.append((site_id, torrent_id))
                
                # 批量查询 HR 状态
                hr_status_map = {}  # {(site, torrent_id): status}
                if site_torrent_pairs:
                    hr_repo = SqlAlchemyHRCasesRepository(AsyncSessionLocal)
                    # 按站点分组查询
                    sites_set = {site for site, _ in site_torrent_pairs}
                    for site in sites_set:
                        async for hr_case in hr_repo.list_active_for_site(site):  # type: ignore[attr-defined]
                            key = (hr_case.site, hr_case.torrent_id)
                            if key not in hr_status_map:
                                # 判断 HR 状态
                                if hr_case.hr_status in (HRStatus.NONE, HRStatus.FINISHED, HRStatus.FAILED):
                                    hr_status_map[key] = "SAFE"
                                elif hr_case.hr_status in (HRStatus.ACTIVE, HRStatus.UNKNOWN):
                                    # 检查是否过期或已满足要求
                                    now = datetime.utcnow()
                                    if hr_case.deadline and now >= hr_case.deadline:
                                        hr_status_map[key] = "SAFE"
                                    elif (
                                        hr_case.required_seed_hours
                                        and hr_case.seeded_hours
                                        and hr_case.seeded_hours >= hr_case.required_seed_hours
                                    ):
                                        hr_status_map[key] = "SAFE"
                                    else:
                                        # 判断风险等级
                                        if hr_case.deadline:
                                            remaining = (hr_case.deadline - now).total_seconds() / 3600
                                            if remaining < 24:
                                                hr_status_map[key] = "RISK"
                                            else:
                                                hr_status_map[key] = "ACTIVE"
                                        else:
                                            hr_status_map[key] = "ACTIVE"
                
                # 批量查询站点健康状态
                site_status_map = {}  # {site: status}
                if sites_set:
                    async with AsyncSessionLocal() as session:
                        # 查询最近的风控事件
                        for site in sites_set:
                            guard_query = select(SiteGuardEventModel).where(
                                SiteGuardEventModel.site == site
                            ).order_by(SiteGuardEventModel.created_at.desc()).limit(1)
                            guard_result = await session.execute(guard_query)
                            guard_event = guard_result.scalar_one_or_none()
                            
                            if guard_event:
                                # 判断站点状态
                                now = datetime.utcnow()
                                if guard_event.event_type in ("THROTTLE", "BAN"):
                                    if guard_event.created_at and (now - guard_event.created_at).days < 7:
                                        site_status_map[site] = "THROTTLED"
                                    else:
                                        site_status_map[site] = "OK"
                                else:
                                    site_status_map[site] = "OK"
                            else:
                                site_status_map[site] = "OK"
                
                # 将 Local Intel 状态添加到下载任务中
                for download in downloads:
                    extra_meta = download.get("extra_metadata") or {}
                    site_id = extra_meta.get("site_id") or extra_meta.get("site")
                    torrent_id = extra_meta.get("torrent_id")
                    
                    if site_id and torrent_id:
                        key = (site_id, torrent_id)
                        download["intel_hr_status"] = hr_status_map.get(key, "UNKNOWN")
                        download["intel_site_status"] = site_status_map.get(site_id, "UNKNOWN")
                    else:
                        download["intel_hr_status"] = "UNKNOWN"
                        download["intel_site_status"] = "UNKNOWN"
            except Exception as e:
                logger.warning(f"查询 Local Intel 状态失败: {e}，所有任务状态设为 UNKNOWN")
                for download in downloads:
                    download["intel_hr_status"] = "UNKNOWN"
                    download["intel_site_status"] = "UNKNOWN"
        else:
            # Local Intel 未启用，所有任务状态设为 UNKNOWN
            for download in downloads:
                download["intel_hr_status"] = "UNKNOWN"
                download["intel_site_status"] = "UNKNOWN"
        
        # DOWNLOAD-CENTER-UI-1: 使用数据增强方法
        enriched_downloads = await service.enrich_download_data(downloads)
        
        # 将字典转换为Pydantic模型
        download_responses = [
            DownloadTaskResponse(**download) for download in enriched_downloads
        ]
        
        # 计算分页
        total = len(download_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = download_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=[item.model_dump() for item in paginated_items],
            total=total,
            page=page,
            page_size=page_size,
            meta={"simulation_mode": await service.detect_simulation_mode()},
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取下载列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取下载列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{task_id}", response_model=BaseResponse)
async def get_download(
    task_id: str,
    db = Depends(get_db)
):
    """
    获取下载详情
    
    支持 task_id 和 download_id 两种参数名（兼容性）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": DownloadTaskResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        download = await service.get_download(task_id)
        if not download:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"下载任务不存在 (ID: {task_id})"
                ).model_dump()
            )
        # 将字典转换为Pydantic模型（service返回的是字典）
        download_response = DownloadTaskResponse(**download)
        return success_response(data=download_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取下载详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取下载详情时发生错误: {str(e)}"
            ).model_dump()
        )
    # 注意：FastAPI路由参数名不影响URL匹配，/{task_id} 和 /{download_id} 在URL层面是一样的
    # 因此 /api/downloads/{task_id} 和 /api/downloads/{download_id} 都能正常工作


@router.post("/{task_id}/pause", response_model=BaseResponse)
async def pause_download(
    task_id: str,
    db = Depends(get_db)
):
    """
    暂停下载
    
    返回统一响应格式：
    {
        "success": true,
        "message": "暂停成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.pause_download(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"下载任务不存在 (ID: {task_id})"
                ).model_dump()
            )
        return success_response(message="暂停成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停下载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"暂停下载时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{task_id}/resume", response_model=BaseResponse)
async def resume_download(
    task_id: str,
    db = Depends(get_db)
):
    """
    恢复下载
    
    返回统一响应格式：
    {
        "success": true,
        "message": "恢复成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.resume_download(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"下载任务不存在 (ID: {task_id})"
                ).model_dump()
            )
        return success_response(message="恢复成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复下载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"恢复下载时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{task_id}", response_model=BaseResponse)
async def delete_download(
    task_id: str,
    db = Depends(get_db)
):
    """
    删除下载
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        
        # P3-2: SafetyPolicyEngine 删除前检查
        try:
            from app.modules.safety.engine import get_safety_policy_engine
            from app.modules.safety.models import SafetyContext
            from app.modules.hr_case.repository import get_hr_repository
            
            safety_engine = get_safety_policy_engine()
            hr_repo = get_hr_repository()
            
            # 获取下载任务信息
            task = await service.get_download_by_id(task_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=NotFoundResponse(
                        error_code="NOT_FOUND",
                        error_message=f"下载任务不存在 (ID: {task_id})"
                    ).model_dump()
                )
            
            # 查找HR案例
            hr_case = None
            if hasattr(task, 'site_key') and hasattr(task, 'torrent_id'):
                hr_case = await hr_repo.get_by_site_and_torrent(task.site_key, task.torrent_id)
            
            # 创建安全上下文
            safety_ctx = SafetyContext(
                action="delete",
                site_key=getattr(task, 'site_key', None),
                torrent_id=getattr(task, 'torrent_id', None),
                trigger="user_web",
                hr_case=hr_case
            )
            
            # 执行安全策略评估
            safety_decision = await safety_engine.evaluate(safety_ctx)
            
            if safety_decision.decision == "DENY":
                return error_response(
                    error_code="SAFETY_BLOCKED",
                    error_message=f"安全策略阻止删除: {safety_decision.message}"
                )
            elif safety_decision.decision == "REQUIRE_CONFIRM":
                return error_response(
                    error_code="SAFETY_REQUIRE_CONFIRM", 
                    error_message=f"需要用户确认: {safety_decision.message}"
                )
                
        except Exception as e:
            logger.warning(f"安全策略检查失败，允许删除: {e}")
        
        success = await service.delete_download(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"下载任务不存在 (ID: {task_id})"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除下载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除下载时发生错误: {str(e)}"
            ).model_dump()
        )


class CreateDownloadRequest(BaseModel):
    """创建下载任务请求"""
    title: str
    magnet_link: Optional[str] = None
    torrent_url: Optional[str] = None
    downloader: str = "qBittorrent"  # qBittorrent, transmission
    save_path: Optional[str] = None
    subscription_id: Optional[int] = None
    size_gb: Optional[float] = None


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_download(
    request: CreateDownloadRequest,
    db = Depends(get_db)
):
    """
    创建下载任务
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": DownloadTaskResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        
        if not request.magnet_link and not request.torrent_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="VALIDATION_ERROR",
                    error_message="必须提供磁力链接或种子URL"
                ).model_dump()
            )
        
        result = await service.create_download(request.model_dump())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CREATE_FAILED",
                    error_message="创建下载任务失败"
                ).model_dump()
            )
        simulation_mode = result.pop("simulation_mode", False)
        download_response = DownloadTaskResponse(**result)
        payload = download_response.model_dump()
        if simulation_mode:
            payload["simulation_mode"] = True
        message = "创建成功（模拟模式）" if simulation_mode else "创建成功"
        return success_response(data=payload, message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建下载任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建下载任务时发生错误: {str(e)}"
            ).model_dump()
        )


class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    task_ids: List[str]
    delete_files: Optional[bool] = False


@router.post("/batch/pause", response_model=BaseResponse)
async def batch_pause_downloads(
    request: BatchOperationRequest,
    db = Depends(get_db)
):
    """
    批量暂停下载
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量暂停成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.batch_pause(request.task_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BATCH_OPERATION_FAILED",
                    error_message="批量暂停失败"
                ).model_dump()
            )
        return success_response(message=f"已暂停 {len(request.task_ids)} 个任务")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量暂停失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量暂停时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/batch/resume", response_model=BaseResponse)
async def batch_resume_downloads(
    request: BatchOperationRequest,
    db = Depends(get_db)
):
    """
    批量恢复下载
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量恢复成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.batch_resume(request.task_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BATCH_OPERATION_FAILED",
                    error_message="批量恢复失败"
                ).model_dump()
            )
        return success_response(message=f"已恢复 {len(request.task_ids)} 个任务")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量恢复失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量恢复时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/batch/delete", response_model=BaseResponse)
async def batch_delete_downloads(
    request: BatchOperationRequest,
    db = Depends(get_db)
):
    """
    批量删除下载
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.batch_delete(request.task_ids, delete_files=request.delete_files)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BATCH_OPERATION_FAILED",
                    error_message="批量删除失败"
                ).model_dump()
            )
        return success_response(message=f"已删除 {len(request.task_ids)} 个任务")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量删除时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{task_id}/queue/up", response_model=BaseResponse)
async def queue_move_up(
    task_id: str,
    db = Depends(get_db)
):
    """
    队列上移
    
    返回统一响应格式：
    {
        "success": true,
        "message": "上移成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.queue_move_up(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="TASK_NOT_FOUND",
                    error_message=f"任务不存在或无法操作 (ID: {task_id})"
                ).model_dump()
            )
        return success_response(message="上移成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"队列上移失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"队列上移时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{task_id}/queue/down", response_model=BaseResponse)
async def queue_move_down(
    task_id: str,
    db = Depends(get_db)
):
    """
    队列下移
    
    返回统一响应格式：
    {
        "success": true,
        "message": "下移成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.queue_move_down(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="TASK_NOT_FOUND",
                    error_message=f"任务不存在或无法操作 (ID: {task_id})"
                ).model_dump()
            )
        return success_response(message="下移成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"队列下移失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"队列下移时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{task_id}/queue/top", response_model=BaseResponse)
async def queue_move_top(
    task_id: str,
    db = Depends(get_db)
):
    """
    队列置顶
    
    返回统一响应格式：
    {
        "success": true,
        "message": "置顶成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.queue_move_top(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="TASK_NOT_FOUND",
                    error_message=f"任务不存在或无法操作 (ID: {task_id})"
                ).model_dump()
            )
        return success_response(message="置顶成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"队列置顶失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"队列置顶时发生错误: {str(e)}"
            ).model_dump()
        )


class SpeedLimitRequest(BaseModel):
    """速度限制请求"""
    download_limit: Optional[float] = None  # MB/s，None表示不限制
    upload_limit: Optional[float] = None  # MB/s，None表示不限制


@router.put("/speed-limit/global", response_model=BaseResponse)
async def set_global_speed_limit(
    request: SpeedLimitRequest,
    downloader: str = Query(..., description="下载器名称: qBittorrent 或 Transmission"),
    db = Depends(get_db)
):
    """
    设置全局速度限制
    
    返回统一响应格式：
    {
        "success": true,
        "message": "设置成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        if downloader not in ["qBittorrent", "Transmission"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="VALIDATION_ERROR",
                    error_message="下载器名称必须是 qBittorrent 或 Transmission"
                ).model_dump()
            )
        
        service = DownloadService(db)
        success = await service.set_global_speed_limit(
            downloader=downloader,
            download_limit=request.download_limit,
            upload_limit=request.upload_limit
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="SPEED_LIMIT_FAILED",
                    error_message="设置全局速度限制失败"
                ).model_dump()
            )
        
        return success_response(
            message=f"全局速度限制设置成功: 下载={request.download_limit if request.download_limit else '无限制'}MB/s, 上传={request.upload_limit if request.upload_limit else '无限制'}MB/s"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置全局速度限制失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"设置全局速度限制时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/speed-limit/global", response_model=BaseResponse)
async def get_global_speed_limit(
    downloader: str = Query(..., description="下载器名称: qBittorrent 或 Transmission"),
    db = Depends(get_db)
):
    """
    获取全局速度限制
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "download_limit": 10.0,  # MB/s，None表示无限制
            "upload_limit": 5.0  # MB/s，None表示无限制
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        if downloader not in ["qBittorrent", "Transmission"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="VALIDATION_ERROR",
                    error_message="下载器名称必须是 qBittorrent 或 Transmission"
                ).model_dump()
            )
        
        service = DownloadService(db)
        limits = await service.get_global_speed_limit(downloader=downloader)
        
        if limits is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="GET_SPEED_LIMIT_FAILED",
                    error_message="获取全局速度限制失败"
                ).model_dump()
            )
        
        return success_response(data=limits, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取全局速度限制失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取全局速度限制时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{task_id}/speed-limit", response_model=BaseResponse)
async def set_task_speed_limit(
    task_id: str,
    request: SpeedLimitRequest,
    db = Depends(get_db)
):
    """
    设置单个任务的速度限制
    
    返回统一响应格式：
    {
        "success": true,
        "message": "设置成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.set_task_speed_limit(
            task_id=task_id,
            download_limit=request.download_limit,
            upload_limit=request.upload_limit
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="SPEED_LIMIT_FAILED",
                    error_message="设置任务速度限制失败，任务可能不存在"
                ).model_dump()
            )
        
        return success_response(
            message=f"任务速度限制设置成功: 下载={request.download_limit if request.download_limit else '无限制'}MB/s, 上传={request.upload_limit if request.upload_limit else '无限制'}MB/s"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置任务速度限制失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"设置任务速度限制时发生错误: {str(e)}"
            ).model_dump()
        )


class BatchSpeedLimitRequest(BaseModel):
    """批量速度限制请求"""
    task_ids: List[str]
    download_limit: Optional[float] = None
    upload_limit: Optional[float] = None


@router.post("/batch/speed-limit", response_model=BaseResponse)
async def batch_set_speed_limit(
    request: BatchSpeedLimitRequest,
    db = Depends(get_db)
):
    """
    批量设置任务速度限制
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量设置成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.batch_set_speed_limit(
            task_ids=request.task_ids,
            download_limit=request.download_limit,
            upload_limit=request.upload_limit
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BATCH_SPEED_LIMIT_FAILED",
                    error_message="批量设置速度限制失败"
                ).model_dump()
            )
        
        return success_response(
            message=f"已为 {len(request.task_ids)} 个任务设置速度限制: 下载={request.download_limit if request.download_limit else '无限制'}MB/s, 上传={request.upload_limit if request.upload_limit else '无限制'}MB/s"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量设置速度限制失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量设置速度限制时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/batch/queue/up", response_model=BaseResponse)
async def batch_queue_up(
    request: BatchOperationRequest,
    db = Depends(get_db)
):
    """
    批量队列上移
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量上移成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.batch_queue_up(request.task_ids)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BATCH_QUEUE_OPERATION_FAILED",
                    error_message="批量队列上移失败"
                ).model_dump()
            )
        
        return success_response(message=f"已上移 {len(request.task_ids)} 个任务")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量队列上移失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量队列上移时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/batch/queue/down", response_model=BaseResponse)
async def batch_queue_down(
    request: BatchOperationRequest,
    db = Depends(get_db)
):
    """
    批量队列下移
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量下移成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.batch_queue_down(request.task_ids)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BATCH_QUEUE_OPERATION_FAILED",
                    error_message="批量队列下移失败"
                ).model_dump()
            )
        
        return success_response(message=f"已下移 {len(request.task_ids)} 个任务")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量队列下移失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量队列下移时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/batch/queue/top", response_model=BaseResponse)
async def batch_queue_top(
    request: BatchOperationRequest,
    db = Depends(get_db)
):
    """
    批量队列置顶
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量置顶成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DownloadService(db)
        success = await service.batch_queue_top(request.task_ids)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BATCH_QUEUE_OPERATION_FAILED",
                    error_message="批量队列置顶失败"
                ).model_dump()
            )
        
        return success_response(message=f"已置顶 {len(request.task_ids)} 个任务")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量队列置顶失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量队列置顶时发生错误: {str(e)}"
            ).model_dump()
        )

