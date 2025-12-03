"""
SITE-MANAGER-1 API 路由器
站点管理模块的REST API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response,
    NotFoundResponse
)
from app.modules.site_manager.service import SiteManagerService
from app.schemas.site_manager import (
    SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
    SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
    ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
)

router = APIRouter()


# === 基础CRUD API ===

@router.get("", response_model=BaseResponse)
async def list_sites(
    enabled: Optional[bool] = Query(None, description="启用状态过滤"),
    category: Optional[str] = Query(None, description="分类过滤"),
    health_status: Optional[HealthStatus] = Query(None, description="健康状态过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    tags: Optional[str] = Query(None, description="标签过滤（逗号分隔）"),
    priority_min: Optional[int] = Query(None, ge=0, description="最小优先级"),
    priority_max: Optional[int] = Query(None, ge=0, description="最大优先级"),
    db = Depends(get_db)
):
    """
    获取站点列表
    
    支持多种过滤条件：
    - enabled: 启用状态
    - category: 站点分类
    - health_status: 健康状态
    - keyword: 名称/域名关键词搜索
    - tags: 标签过滤
    - priority_min/max: 优先级范围
    """
    try:
        service = SiteManagerService(db)
        
        # 构建过滤器
        filters = SiteListFilter(
            enabled=enabled,
            category=category,
            health_status=health_status,
            keyword=keyword,
            tags=[tag.strip() for tag in tags.split(',')] if tags else None,
            priority_min=priority_min,
            priority_max=priority_max
        )
        
        sites = await service.list_sites(filters)
        
        return success_response(
            data=[site.dict() for site in sites],
            message=f"获取成功，共 {len(sites)} 个站点"
        )
        
    except Exception as e:
        logger.error(f"获取站点列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点列表失败: {str(e)}"
            ).model_dump()
        )


@router.get("/{site_id}", response_model=BaseResponse)
async def get_site_detail(
    site_id: int,
    db = Depends(get_db)
):
    """获取站点详细信息"""
    try:
        service = SiteManagerService(db)
        site = await service.get_site_detail(site_id)
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        return success_response(data=site.dict(), message="获取成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取站点详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点详情失败: {str(e)}"
            ).model_dump()
        )


@router.put("/{site_id}", response_model=BaseResponse)
async def update_site(
    site_id: int,
    payload: SiteUpdatePayload,
    db = Depends(get_db)
):
    """更新站点基本信息"""
    try:
        service = SiteManagerService(db)
        site = await service.update_site(site_id, payload)
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        return success_response(data=site.dict(), message="更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新站点失败: {str(e)}"
            ).model_dump()
        )


@router.delete("/{site_id}", response_model=BaseResponse)
async def delete_site(
    site_id: int,
    db = Depends(get_db)
):
    """删除站点（级联删除相关数据）"""
    try:
        service = SiteManagerService(db)
        success = await service.delete_site(site_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        return success_response(message="删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除站点失败: {str(e)}"
            ).model_dump()
        )


# === 访问配置API ===

@router.put("/{site_id}/access-config", response_model=BaseResponse)
async def update_site_access_config(
    site_id: int,
    payload: SiteAccessConfigPayload,
    db = Depends(get_db)
):
    """更新站点访问配置"""
    try:
        service = SiteManagerService(db)
        site = await service.update_site_access_config(site_id, payload)
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        return success_response(data=site.dict(), message="访问配置更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新站点访问配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新访问配置失败: {str(e)}"
            ).model_dump()
        )


# === 健康检查API ===

@router.post("/{site_id}/health-check", response_model=BaseResponse)
async def check_site_health(
    site_id: int,
    check_type: CheckType = Query(CheckType.BASIC, description="检查类型"),
    db = Depends(get_db)
):
    """执行站点健康检查"""
    try:
        service = SiteManagerService(db)
        result = await service.check_site_health(site_id, check_type)
        
        return success_response(data=result.dict(), message="健康检查完成")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="INVALID_REQUEST",
                error_message=str(e)
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"站点健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"健康检查失败: {str(e)}"
            ).model_dump()
        )


@router.post("/batch-health-check", response_model=BaseResponse)
async def batch_health_check(
    site_ids: List[int],
    background_tasks: BackgroundTasks,
    check_type: CheckType = Query(CheckType.BASIC, description="检查类型"),
    db = Depends(get_db)
):
    """
    批量健康检查
    
    注意：此操作可能耗时较长，建议使用后台任务
    """
    try:
        if len(site_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="TOO_MANY_SITES",
                    error_message="批量检查站点数量不能超过50个"
                ).model_dump()
            )
        
        service = SiteManagerService(db)
        result = await service.batch_health_check(site_ids, check_type)
        
        return success_response(data=result.dict(), message=result.message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量健康检查失败: {str(e)}"
            ).model_dump()
        )


# === 导入导出API ===

@router.post("/import", response_model=BaseResponse)
async def import_sites(
    sites_data: List[SiteImportItem],
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """导入站点配置"""
    try:
        if len(sites_data) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="TOO_MANY_SITES",
                    error_message="导入站点数量不能超过100个"
                ).model_dump()
            )
        
        service = SiteManagerService(db)
        result = await service.import_sites(sites_data)
        
        return success_response(data=result.dict(), message=result.message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"导入站点失败: {str(e)}"
            ).model_dump()
        )


@router.get("/export", response_model=BaseResponse)
async def export_sites(
    site_ids: Optional[str] = Query(None, description="站点ID列表，逗号分隔"),
    db = Depends(get_db)
):
    """导出站点配置"""
    try:
        service = SiteManagerService(db)
        
        # 解析站点ID列表
        ids_list = None
        if site_ids:
            try:
                ids_list = [int(id.strip()) for id in site_ids.split(',')]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(
                        error_code="INVALID_SITE_IDS",
                        error_message="站点ID格式错误"
                    ).model_dump()
                )
        
        export_data = await service.export_sites(ids_list)
        
        return success_response(
            data=[site.dict() for site in export_data],
            message=f"导出成功，共 {len(export_data)} 个站点"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"导出站点失败: {str(e)}"
            ).model_dump()
        )


# === 统计和分类API ===

@router.get("/categories/list", response_model=BaseResponse)
async def list_categories(
    db = Depends(get_db)
):
    """获取站点分类列表"""
    try:
        from sqlalchemy import select
        from app.models.site import SiteCategory
        
        query = select(SiteCategory).where(SiteCategory.enabled == True).order_by(SiteCategory.sort_order)
        result = await db.execute(query)
        categories = result.scalars().all()
        
        return success_response(
            data=[{
                "key": cat.key,
                "name": cat.name,
                "description": cat.description,
                "icon": cat.icon,
                "sort_order": cat.sort_order
            } for cat in categories],
            message=f"获取成功，共 {len(categories)} 个分类"
        )
        
    except Exception as e:
        logger.error(f"获取站点分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点分类失败: {str(e)}"
            ).model_dump()
        )


@router.get("/stats/summary", response_model=BaseResponse)
async def get_stats_summary(
    db = Depends(get_db)
):
    """获取站点统计摘要"""
    try:
        from sqlalchemy import select, func
        from app.models.site import Site, SiteStats
        
        # 总站点数
        total_query = select(func.count(Site.id))
        total_result = await db.execute(total_query)
        total_sites = total_result.scalar()
        
        # 启用站点数
        enabled_query = select(func.count(Site.id)).where(Site.is_active == True)
        enabled_result = await db.execute(enabled_query)
        enabled_sites = enabled_result.scalar()
        
        # 健康状态统计
        health_query = select(
            SiteStats.health_status,
            func.count(SiteStats.id).label('count')
        ).group_by(SiteStats.health_status)
        health_result = await db.execute(health_query)
        health_stats = {row.health_status: row.count for row in health_result}
        
        # 分类统计
        category_query = select(
            Site.category,
            func.count(Site.id).label('count')
        ).where(Site.category.isnot(None)).group_by(Site.category)
        category_result = await db.execute(category_query)
        category_stats = {row.category: row.count for row in category_result}
        
        summary = {
            "total_sites": total_sites,
            "enabled_sites": enabled_sites,
            "disabled_sites": total_sites - enabled_sites,
            "health_stats": health_stats,
            "category_stats": category_stats
        }
        
        return success_response(data=summary, message="统计摘要获取成功")
        
    except Exception as e:
        logger.error(f"获取统计摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取统计摘要失败: {str(e)}"
            ).model_dump()
        )
