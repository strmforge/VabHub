"""
站点管理相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db, AsyncSessionLocal
from app.modules.site.service import SiteService
from app.modules.site_icon.service import SiteIconService
from app.core.cookiecloud import CookieCloudClient
from app.core.site_ai_adapter import maybe_auto_analyze_site
from app.core.site_ai_adapter.status import get_ai_adapter_status_for_site  # Phase AI-3
from app.core.site_ai_adapter.settings import update_site_ai_settings  # Phase AI-4
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class SiteCreate(BaseModel):
    """创建站点请求"""
    name: str
    url: str
    cookie: Optional[str] = None
    cookiecloud_uuid: Optional[str] = None
    cookiecloud_password: Optional[str] = None
    cookiecloud_server: Optional[str] = None
    is_active: bool = True
    # Phase AI-4: 站点级别的 AI 控制字段
    ai_disabled: Optional[bool] = None  # 是否禁用本站点的 AI 适配
    ai_manual_profile_preferred: Optional[bool] = None  # 是否优先使用人工配置


class SiteResponse(BaseModel):
    """站点响应"""
    id: int
    name: str
    url: str
    is_active: bool
    cookiecloud_uuid: Optional[str] = None
    cookiecloud_server: Optional[str] = None
    user_data: Optional[dict] = None
    last_checkin: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Phase AI-3: AI 适配状态字段（只读）
    ai_adapter_enabled: Optional[bool] = None
    ai_config_present: Optional[bool] = None
    ai_config_last_analyzed_at: Optional[datetime] = None
    ai_effective_mode: Optional[str] = None
    # Phase AI-4: 站点级别的 AI 控制字段
    ai_disabled: Optional[bool] = None  # 是否禁用本站点的 AI 适配
    ai_manual_profile_preferred: Optional[bool] = None  # 是否优先使用人工配置
    ai_confidence_score: Optional[int] = None  # AI 配置可信度分数
    
    class Config:
        from_attributes = True


class CookieCloudSyncRequest(BaseModel):
    """CookieCloud同步请求"""
    server_url: str
    uuid: str
    password: Optional[str] = None
    site_ids: Optional[List[int]] = None  # 如果为空，同步所有站点


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site: SiteCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    创建站点
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": SiteResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        result = await service.create_site(site.model_dump())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CREATE_FAILED",
                    error_message="创建站点失败"
                ).model_dump()
            )
        
        # Phase AI-4: 保存站点级别的 AI 适配设置
        if site.ai_disabled is not None or site.ai_manual_profile_preferred is not None:
            try:
                await update_site_ai_settings(
                    str(result.id),
                    db,
                    disabled=site.ai_disabled,
                    manual_profile_preferred=site.ai_manual_profile_preferred,
                )
            except Exception as e:
                logger.warning(f"保存站点 AI 适配设置失败 (site_id: {result.id}): {e}")
        
        # 创建成功后，后台触发 AI 适配（不阻塞当前请求）
        # 注意：需要在后台任务中创建新的数据库会话
        async def analyze_in_background(site_id: int):
            """后台任务：使用新的数据库会话进行 AI 适配分析"""
            async with AsyncSessionLocal() as new_db:
                try:
                    await maybe_auto_analyze_site(str(site_id), new_db)
                except Exception as e:
                    logger.error(f"后台 AI 适配分析异常 (site_id: {site_id}): {e}", exc_info=True)
        
        background_tasks.add_task(analyze_in_background, result.id)
        
        # 将SQLAlchemy对象转换为Pydantic模型
        site_response = SiteResponse.model_validate(result)
        return success_response(data=site_response.model_dump(), message="创建成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建站点时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/", response_model=BaseResponse)
async def list_sites(
    active_only: bool = Query(False, description="是否只返回激活的站点"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取站点列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [SiteResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        sites = await service.list_sites(active_only=active_only)
        
        # 将SQLAlchemy对象转换为Pydantic模型
        site_responses = []
        for site in sites:
            site_dict = SiteResponse.model_validate(site).model_dump()
            # Phase AI-3/AI-4: 补充 AI 适配状态
            try:
                ai_status = await get_ai_adapter_status_for_site(str(site.id), db)
                site_dict.update({
                    "ai_adapter_enabled": ai_status.ai_adapter_enabled,
                    "ai_config_present": ai_status.ai_config_present,
                    "ai_config_last_analyzed_at": ai_status.ai_config_last_analyzed_at,
                    "ai_effective_mode": ai_status.ai_effective_mode,
                    # Phase AI-4
                    "ai_disabled": ai_status.disabled,
                    "ai_manual_profile_preferred": ai_status.manual_profile_preferred,
                    "ai_confidence_score": ai_status.confidence_score,
                })
            except Exception as e:
                logger.debug(f"获取站点 {site.id} 的 AI 状态失败: {e}")
                site_dict.update({
                    "ai_adapter_enabled": False,
                    "ai_config_present": False,
                    "ai_config_last_analyzed_at": None,
                    "ai_effective_mode": "none",
                    "ai_disabled": False,
                    "ai_manual_profile_preferred": False,
                    "ai_confidence_score": None,
                })
            site_responses.append(site_dict)
        
        # 计算分页
        total = len(site_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = site_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取站点列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{site_id}", response_model=BaseResponse)
async def get_site(
    site_id: int,
    db = Depends(get_db)
):
    """
    获取站点详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SiteResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        site = await service.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        site_dict = SiteResponse.model_validate(site).model_dump()
        # Phase AI-3/AI-4: 补充 AI 适配状态
        try:
            ai_status = await get_ai_adapter_status_for_site(str(site.id), db)
            site_dict.update({
                "ai_adapter_enabled": ai_status.ai_adapter_enabled,
                "ai_config_present": ai_status.ai_config_present,
                "ai_config_last_analyzed_at": ai_status.ai_config_last_analyzed_at,
                "ai_effective_mode": ai_status.ai_effective_mode,
                # Phase AI-4
                "ai_disabled": ai_status.disabled,
                "ai_manual_profile_preferred": ai_status.manual_profile_preferred,
                "ai_confidence_score": ai_status.confidence_score,
            })
        except Exception as e:
            logger.debug(f"获取站点 {site.id} 的 AI 状态失败: {e}")
            site_dict.update({
                "ai_adapter_enabled": False,
                "ai_config_present": False,
                "ai_config_last_analyzed_at": None,
                "ai_effective_mode": "none",
                "ai_disabled": False,
                "ai_manual_profile_preferred": False,
                "ai_confidence_score": None,
            })
        return success_response(data=site_dict, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取站点详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{site_id}", response_model=BaseResponse)
async def update_site(
    site_id: int,
    site: SiteCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    更新站点
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": SiteResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        result = await service.update_site(site_id, site.model_dump())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        # Phase AI-4: 保存站点级别的 AI 适配设置
        if site.ai_disabled is not None or site.ai_manual_profile_preferred is not None:
            try:
                await update_site_ai_settings(
                    str(result.id),
                    db,
                    disabled=site.ai_disabled,
                    manual_profile_preferred=site.ai_manual_profile_preferred,
                )
            except Exception as e:
                logger.warning(f"保存站点 AI 适配设置失败 (site_id: {result.id}): {e}")
        
        # 更新成功后，后台触发 AI 适配（不阻塞当前请求）
        # 注意：需要在后台任务中创建新的数据库会话
        async def analyze_in_background(site_id: int):
            """后台任务：使用新的数据库会话进行 AI 适配分析"""
            async with AsyncSessionLocal() as new_db:
                try:
                    await maybe_auto_analyze_site(str(site_id), new_db)
                except Exception as e:
                    logger.error(f"后台 AI 适配分析异常 (site_id: {site_id}): {e}", exc_info=True)
        
        background_tasks.add_task(analyze_in_background, result.id)
        
        # 将SQLAlchemy对象转换为Pydantic模型
        site_response = SiteResponse.model_validate(result)
        return success_response(data=site_response.model_dump(), message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新站点时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{site_id}", response_model=BaseResponse)
async def delete_site(
    site_id: int,
    db = Depends(get_db)
):
    """
    删除站点
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
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
                error_message=f"删除站点时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/sync-cookiecloud", response_model=BaseResponse)
async def sync_cookiecloud(
    request: CookieCloudSyncRequest,
    db = Depends(get_db)
):
    """
    同步CookieCloud
    
    返回统一响应格式：
    {
        "success": true,
        "message": "同步完成: 成功 X 个，失败 Y 个",
        "data": {
            "synced_count": 10,
            "failed_count": 2
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        
        # 获取要同步的站点列表
        if request.site_ids:
            sites = []
            for site_id in request.site_ids:
                site = await service.get_site(site_id)
                if site:
                    sites.append({
                        "id": site.id,
                        "name": site.name,
                        "url": site.url
                    })
        else:
            # 获取所有站点
            all_sites = await service.list_sites(active_only=True)
            sites = [{
                "id": site.id,
                "name": site.name,
                "url": site.url
            } for site in all_sites]
        
        # 创建CookieCloud客户端
        client = CookieCloudClient(
            server_url=request.server_url,
            uuid=request.uuid,
            password=request.password or ""
        )
        
        # 获取Cookie数据
        cookies = await client.get_cookies()
        
        if not cookies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="SYNC_FAILED",
                    error_message="未能从CookieCloud获取Cookie数据"
                ).model_dump()
            )
        
        # 同步Cookie到站点
        synced_count = 0
        failed_count = 0
        
        for site in sites:
            site_url = site["url"]
            site_id = site["id"]
            
            # 匹配域名
            matched_cookie = None
            for domain, cookie_string in cookies.items():
                domain_clean = domain.replace("http://", "").replace("https://", "").split("/")[0]
                site_domain = site_url.replace("http://", "").replace("https://", "").split("/")[0]
                
                if domain_clean in site_domain or site_domain in domain_clean:
                    matched_cookie = cookie_string
                    break
            
            if matched_cookie:
                # 更新站点Cookie
                await service.update_site(site_id, {
                    "cookie": matched_cookie,
                    "cookiecloud_uuid": request.uuid,
                    "cookiecloud_password": request.password
                })
                synced_count += 1
                logger.info(f"成功同步Cookie到站点: {site['name']}")
            else:
                failed_count += 1
                logger.warning(f"未找到匹配的Cookie: {site['name']}")
        
        await client.close()
        
        return success_response(
            data={
                "synced_count": synced_count,
                "failed_count": failed_count
            },
            message=f"同步完成: 成功 {synced_count} 个，失败 {failed_count} 个"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CookieCloud同步失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"CookieCloud同步失败: {str(e)}"
            ).model_dump()
        )


@router.post("/{site_id}/test", response_model=BaseResponse)
async def test_site(
    site_id: int,
    db = Depends(get_db)
):
    """
    测试站点连接
    
    返回统一响应格式：
    {
        "success": true,
        "message": "连接测试成功",
        "data": {
            "site_id": 1,
            "connected": true,
            "message": "连接成功"
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        site = await service.get_site(site_id)
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        result = await service.test_connection(site_id)
        
        if not result.get("success") and "site_id" not in result:
            # 如果返回的success为False且没有site_id，说明是服务层错误
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="TEST_FAILED",
                    error_message=result.get("message", "连接测试失败"),
                    details=result
                ).model_dump()
            )
        
        return success_response(data=result, message="连接测试成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试站点连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"测试站点连接时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{site_id}/checkin", response_model=BaseResponse)
async def checkin_site(
    site_id: int,
    db = Depends(get_db)
):
    """
    站点签到
    
    返回统一响应格式：
    {
        "success": true,
        "message": "签到成功",
        "data": {
            "site_id": 1,
            "message": "签到成功",
            "points": 100
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        site = await service.get_site(site_id)
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        result = await service.checkin(site_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CHECKIN_FAILED",
                    error_message=result.get("message", "签到失败"),
                    details=result
                ).model_dump()
            )
        
        return success_response(data=result, message="签到成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"站点签到失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"站点签到时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/batch-checkin", response_model=BaseResponse)
async def batch_checkin(
    db = Depends(get_db)
):
    """
    批量签到
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量签到完成",
        "data": {
            "total": 10,
            "success_count": 8,
            "failed_count": 2,
            "results": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteService(db)
        result = await service.batch_checkin()
        
        return success_response(data=result, message="批量签到完成")
    except Exception as e:
        logger.error(f"批量签到失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量签到时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{site_id}/icon", response_model=BaseResponse)
async def get_site_icon(
    site_id: int,
    size: int = Query(40, ge=16, le=128, description="图标尺寸"),
    db = Depends(get_db)
):
    """
    获取站点图标
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "type": "cached" | "preset" | "favicon" | "svg",
            "url": str | null,
            "base64": str | null,
            "svg": str | null
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        site_service = SiteService(db)
        site = await site_service.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        icon_service = SiteIconService(db)
        icon_data = await icon_service.get_site_icon(site, size)
        
        return success_response(data=icon_data, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取站点图标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点图标时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{site_id}/icon/refresh", response_model=BaseResponse)
async def refresh_site_icon(
    site_id: int,
    db = Depends(get_db)
):
    """
    刷新站点图标（强制重新抓取）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "刷新成功",
        "data": {
            "type": "cached" | "preset" | "favicon" | "svg",
            "url": str | null,
            "base64": str | null,
            "svg": str | null
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        site_service = SiteService(db)
        site = await site_service.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})"
                ).model_dump()
            )
        
        icon_service = SiteIconService(db)
        icon_data = await icon_service.refresh_icon(site)
        
        return success_response(data=icon_data, message="刷新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新站点图标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"刷新站点图标时发生错误: {str(e)}"
            ).model_dump()
        )

