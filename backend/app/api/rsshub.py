"""
RSSHub相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.rsshub.service import RSSHubService, RSSHubDisabledError
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


@router.get("/sources", response_model=BaseResponse)
async def list_rsshub_sources(
    group: Optional[str] = Query(None, description="分组过滤: rank/update"),
    type: Optional[str] = Query(None, description="类型过滤: video/tv/variety/anime/music/mixed"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    获取RSSHub源列表，附带当前用户的订阅状态
    """
    try:
        service = RSSHubService(db)
        sources = await service.list_sources(
            user_id=current_user.id,
            group=group,
            type=type
        )
        return success_response(data=sources, message="获取成功")
    except Exception as e:
        if isinstance(e, RSSHubDisabledError):
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_response(
                    error_code="RSSHUB_DISABLED",
                    error_message=str(e),
                ).model_dump(mode="json"),
            )
        logger.error(f"获取RSSHub源列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSSHub源列表失败: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/composites", response_model=BaseResponse)
async def list_rsshub_composites(
    type: Optional[str] = Query(None, description="类型过滤: video/tv/variety/anime/music/mixed"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    获取RSSHub组合订阅列表，附带当前用户的订阅状态
    """
    try:
        service = RSSHubService(db)
        composites = await service.list_composites(
            user_id=current_user.id,
            type=type
        )
        return success_response(data=composites, message="获取成功")
    except Exception as e:
        if isinstance(e, RSSHubDisabledError):
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_response(
                    error_code="RSSHUB_DISABLED",
                    error_message=str(e),
                ).model_dump(mode="json"),
            )
        logger.error(f"获取RSSHub组合订阅列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSSHub组合订阅列表失败: {str(e)}"
            ).model_dump(mode='json')
        )


class ToggleSubscriptionRequest(BaseModel):
    """切换订阅状态请求"""
    enabled: bool


@router.post("/subscriptions/{target_type}/{target_id}/toggle", response_model=BaseResponse)
async def toggle_rsshub_subscription(
    target_type: str,
    target_id: str,
    request: ToggleSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    切换RSSHub订阅状态
    
    Args:
        target_type: 目标类型（source/composite）
        target_id: 目标ID
        request: 请求体（enabled: bool）
    """
    if target_type not in ['source', 'composite']:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="INVALID_TARGET_TYPE",
                error_message="target_type必须是'source'或'composite'"
            ).model_dump(mode='json')
        )
    
    try:
        service = RSSHubService(db)
        success = await service.toggle_subscription(
            user_id=current_user.id,
            target_type=target_type,
            target_id=target_id,
            enabled=request.enabled
        )
        
        if success:
            return success_response(
                data={"enabled": request.enabled},
                message=f"{'启用' if request.enabled else '禁用'}成功"
            )
        else:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="TOGGLE_FAILED",
                    error_message="切换订阅状态失败"
                ).model_dump(mode='json')
            )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="INVALID_REQUEST",
                error_message=str(e)
            ).model_dump(mode='json')
        )
    except Exception as e:
        if isinstance(e, RSSHubDisabledError):
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_response(
                    error_code="RSSHUB_DISABLED",
                    error_message=str(e),
                ).model_dump(mode="json"),
            )
        logger.error(f"切换RSSHub订阅状态失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"切换订阅状态失败: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/subscriptions/health", response_model=BaseResponse)
async def list_rsshub_subscription_health(
    user_id: Optional[int] = Query(None, description="按用户ID过滤"),
    target_type: Optional[str] = Query(None, regex="^(source|composite)$", description="目标类型过滤"),
    only_legacy: bool = Query(False, description="是否仅返回绑定到 legacy 占位的订阅"),
    limit: int = Query(100, ge=1, le=500, description="返回条目数限制"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    获取 RSSHub 订阅健康检查列表
    """
    try:
        service = RSSHubService(db)
        items = await service.list_subscription_health(
            user_id=user_id,
            target_type=target_type,
            only_legacy=only_legacy,
            limit=limit,
        )
        return success_response(
            data={
                "items": items,
                "total": len(items),
            },
            message="获取成功",
        )
    except Exception as e:
        if isinstance(e, RSSHubDisabledError):
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_response(
                    error_code="RSSHUB_DISABLED",
                    error_message=str(e),
                ).model_dump(mode="json"),
            )
        logger.error(f"获取RSSHub订阅健康列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取订阅健康列表失败: {str(e)}",
            ).model_dump(mode="json"),
        )


@router.get("/sources/{id}/preview", response_model=BaseResponse)
async def preview_rsshub_source(
    id: str,
    limit: int = Query(5, ge=1, le=20, description="预览项数量"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    预览RSSHub源内容（兼容性端点）
    
    支持 {id} 和 {source_id} 两种参数名
    """
    return await preview_rsshub_source_by_id(id, limit, current_user, db)


@router.get("/sources/{source_id}/preview", response_model=BaseResponse)
async def preview_rsshub_source_by_id(
    source_id: str,
    limit: int = Query(5, ge=1, le=20, description="预览项数量"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    预览RSSHub源内容
    
    Args:
        source_id: 源ID
        limit: 预览项数量（1-20）
    """
    try:
        service = RSSHubService(db)
        # 使用 id（与 source_id 相同）
        items = await service.preview_source(id, limit=limit)
        return success_response(data=items, message="预览成功")
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=error_response(
                error_code="SOURCE_NOT_FOUND",
                error_message=str(e)
            ).model_dump(mode='json')
        )
    except Exception as e:
        if isinstance(e, RSSHubDisabledError):
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_response(
                    error_code="RSSHUB_DISABLED",
                    error_message=str(e),
                ).model_dump(mode="json"),
            )
        logger.error(f"预览RSSHub源失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"预览失败: {str(e)}"
            ).model_dump(mode='json')
        )

