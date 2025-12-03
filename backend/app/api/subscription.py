"""
订阅相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.modules.subscription.service import SubscriptionService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class SubscriptionCreate(BaseModel):
    """创建订阅请求"""
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    media_type: str  # movie, tv, short_drama, music, anime
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    poster: Optional[str] = None  # 海报图片URL
    backdrop: Optional[str] = None  # 背景图片URL
    # 电视剧相关
    season: Optional[int] = None  # 季数（电视剧专用）
    total_episode: Optional[int] = None  # 总集数（电视剧专用）
    start_episode: Optional[int] = None  # 起始集数（电视剧专用）
    episode_group: Optional[str] = None  # 剧集组ID
    # 基础规则
    quality: Optional[str] = None
    resolution: Optional[str] = None
    effect: Optional[str] = None
    sites: Optional[List[int]] = None
    downloader: Optional[str] = None
    save_path: Optional[str] = None
    min_seeders: int = 5
    auto_download: bool = True
    best_version: bool = False
    search_imdbid: bool = False
    # 进阶规则
    include: Optional[str] = None
    exclude: Optional[str] = None
    filter_group_ids: Optional[List[int]] = []  # 过滤规则组ID列表
    extra_metadata: Optional[dict] = None
    short_drama_metadata: Optional[dict] = None
    # 安全策略（VIDEO-AUTOLOOP-1）
    allow_hr: Optional[bool] = False  # 是否允许 HR/H&R
    allow_h3h5: Optional[bool] = False  # 是否允许 H3/H5 等扩展规则
    strict_free_only: Optional[bool] = False  # 只下载 free/促销种


class SubscriptionResponse(BaseModel):
    """订阅响应"""
    id: int
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    media_type: str
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    poster: Optional[str] = None  # 海报图片URL
    backdrop: Optional[str] = None  # 背景图片URL
    status: str
    # 电视剧相关
    season: Optional[int] = None  # 季数（电视剧专用）
    total_episode: Optional[int] = None  # 总集数（电视剧专用）
    start_episode: Optional[int] = None  # 起始集数（电视剧专用）
    episode_group: Optional[str] = None  # 剧集组ID
    # 基础规则
    quality: Optional[str] = None
    resolution: Optional[str] = None
    effect: Optional[str] = None
    sites: Optional[List[int]] = None
    downloader: Optional[str] = None
    save_path: Optional[str] = None
    min_seeders: int
    auto_download: bool
    best_version: bool
    search_imdbid: bool
    # 进阶规则
    include: Optional[str] = None
    exclude: Optional[str] = None
    filter_group_ids: Optional[List[int]] = []  # 过滤规则组ID列表
    # 其他
    search_rules: Optional[dict] = None
    extra_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    last_search: Optional[datetime] = None
    next_search: Optional[datetime] = None
    # 安全策略（VIDEO-AUTOLOOP-1）
    allow_hr: Optional[bool] = False  # 是否允许 HR/H&R
    allow_h3h5: Optional[bool] = False  # 是否允许 H3/H5 等扩展规则
    strict_free_only: Optional[bool] = False  # 只下载 free/促销种
    # 运行状态（VIDEO-AUTOLOOP-1）
    last_check_at: Optional[datetime] = None  # 最后检查时间
    last_success_at: Optional[datetime] = None  # 最后成功时间
    last_error: Optional[str] = None  # 最后错误信息
    
    class Config:
        from_attributes = True


@router.post("/", response_model=BaseResponse, status_code=http_status.HTTP_201_CREATED)
async def create_subscription(
    subscription: SubscriptionCreate,
    db = Depends(get_db)
):
    """
    创建订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": SubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        result = await service.create_subscription(subscription.model_dump())
        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CREATE_FAILED",
                    error_message="创建订阅失败"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = SubscriptionResponse.model_validate(result)
        return success_response(data=subscription_response.model_dump(), message="创建成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/", response_model=BaseResponse)
async def list_subscriptions(
    media_type: Optional[str] = Query(None, description="媒体类型过滤: movie, tv, short_drama, music, anime"),
    subscription_status: Optional[str] = Query(None, alias="status", description="状态过滤: active, inactive"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取订阅列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [SubscriptionResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        subscriptions = await service.list_subscriptions(
            media_type=media_type,
            status=subscription_status
        )
        
        # 计算分页
        total = len(subscriptions)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = subscriptions[start:end]
        
        # 将SQLAlchemy对象列表转换为Pydantic模型列表
        subscription_responses = [
            SubscriptionResponse.model_validate(item) for item in paginated_items
        ]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=[item.model_dump() for item in subscription_responses],
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取订阅列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取订阅列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{subscription_id}", response_model=BaseResponse)
async def get_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    获取订阅详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        subscription = await service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"订阅不存在 (ID: {subscription_id})"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = SubscriptionResponse.model_validate(subscription)
        return success_response(data=subscription_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订阅详情失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取订阅详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{subscription_id}", response_model=BaseResponse)
async def update_subscription(
    subscription_id: int,
    subscription: SubscriptionCreate,
    db = Depends(get_db)
):
    """
    更新订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": SubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        result = await service.update_subscription(subscription_id, subscription.model_dump())
        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"订阅不存在 (ID: {subscription_id})"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = SubscriptionResponse.model_validate(result)
        return success_response(data=subscription_response.model_dump(), message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{subscription_id}", response_model=BaseResponse)
async def delete_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    删除订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        success = await service.delete_subscription(subscription_id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"订阅不存在 (ID: {subscription_id})"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{subscription_id}/enable", response_model=BaseResponse)
async def enable_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    启用订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "启用成功",
        "data": SubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        result = await service.enable_subscription(subscription_id)
        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"订阅不存在 (ID: {subscription_id})"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = SubscriptionResponse.model_validate(result)
        return success_response(data=subscription_response.model_dump(), message="启用成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启用订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"启用订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{subscription_id}/disable", response_model=BaseResponse)
async def disable_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    禁用订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "禁用成功",
        "data": SubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        result = await service.disable_subscription(subscription_id)
        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"订阅不存在 (ID: {subscription_id})"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = SubscriptionResponse.model_validate(result)
        return success_response(data=subscription_response.model_dump(), message="禁用成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"禁用订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/test", response_model=BaseResponse)
async def test_subscription(
    subscription: SubscriptionCreate,
    db = Depends(get_db)
):
    """
    测试订阅配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "测试成功",
        "data": {
            "valid": true,
            "search_result": {...},
            "message": "订阅配置有效"
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.subscription.refresh_engine import SubscriptionRefreshEngine
        
        refresh_engine = SubscriptionRefreshEngine(db)
        
        # 创建临时订阅进行测试
        service = SubscriptionService(db)
        temp_subscription = await service.create_subscription(subscription.model_dump())
        
        if not temp_subscription:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="TEST_FAILED",
                    error_message="无法创建测试订阅"
                ).model_dump()
            )
        
        try:
            # 执行测试搜索
            result = await refresh_engine.refresh_subscription(temp_subscription.id, force=True)
            
            # 删除临时订阅
            await service.delete_subscription(temp_subscription.id)
            
            if result.get("success"):
                return success_response(
                    data={
                        "valid": True,
                        "search_result": result.get("search_result"),
                        "message": "订阅配置有效，测试搜索成功"
                    },
                    message="测试成功"
                )
            else:
                return success_response(
                    data={
                        "valid": False,
                        "error": result.get("error", "测试失败"),
                        "message": "订阅配置可能存在问题"
                    },
                    message="测试完成（有警告）"
                )
        except Exception as e:
            # 确保删除临时订阅
            try:
                await service.delete_subscription(temp_subscription.id)
            except:
                pass
            raise e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"测试订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{subscription_id}/search", response_model=BaseResponse)
async def search_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    执行订阅搜索
    
    返回统一响应格式：
    {
        "success": true,
        "message": "搜索成功",
        "data": {
            "success": true,
            "message": "搜索完成",
            "results": [...],
            "count": 10
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        subscription_service = SubscriptionService(db)
        
        result = await subscription_service.execute_search(subscription_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="SEARCH_FAILED",
                    error_message=result.get("message", "搜索失败"),
                    details=result
                ).model_dump()
            )
        
        return success_response(data=result, message="搜索成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行订阅搜索失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"执行订阅搜索时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{subscription_id}/refresh", response_model=BaseResponse)
async def refresh_subscription(
    subscription_id: int,
    force: bool = Query(False, description="是否强制刷新"),
    db = Depends(get_db)
):
    """
    刷新订阅（使用增量刷新引擎）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "刷新成功",
        "data": {
            "success": true,
            "subscription_id": 1,
            "subscription_title": "Movie Name",
            "search_result": {...},
            "last_search": "2025-01-XX...",
            "next_search": "2025-01-XX..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.subscription.refresh_engine import SubscriptionRefreshEngine
        
        refresh_engine = SubscriptionRefreshEngine(db)
        result = await refresh_engine.refresh_subscription(subscription_id, force=force)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="REFRESH_FAILED",
                    error_message=result.get("error", "刷新失败"),
                    details=result
                ).model_dump()
            )
        
        return success_response(data=result, message="刷新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"刷新订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/refresh/batch", response_model=BaseResponse)
async def refresh_subscriptions_batch(
    max_count: Optional[int] = Query(None, description="最大刷新数量"),
    force: bool = Query(False, description="是否强制刷新"),
    db = Depends(get_db)
):
    """
    批量刷新订阅（使用增量刷新引擎）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量刷新成功",
        "data": {
            "success": true,
            "refreshed_count": 10,
            "error_count": 0,
            "total_count": 10,
            "results": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.subscription.refresh_engine import SubscriptionRefreshEngine
        
        refresh_engine = SubscriptionRefreshEngine(db)
        result = await refresh_engine.refresh_subscriptions_batch(max_count=max_count, force=force)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="BATCH_REFRESH_FAILED",
                    error_message=result.get("error", "批量刷新失败"),
                    details=result
                ).model_dump()
            )
        
        return success_response(data=result, message="批量刷新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量刷新订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量刷新订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{subscription_id}/history", response_model=BaseResponse)
async def get_subscription_history(
    subscription_id: int,
    action_type: Optional[str] = Query(None, description="操作类型过滤: operation, search, download"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db = Depends(get_db)
):
    """
    获取订阅历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {
                "id": 1,
                "subscription_id": 1,
                "action": "create",
                "action_type": "operation",
                "description": "创建订阅: Movie Name",
                "created_at": "2025-01-XX...",
                ...
            },
            ...
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        history = await service.get_subscription_history(
            subscription_id=subscription_id,
            action_type=action_type,
            limit=limit,
            offset=offset
        )
        
        # 转换为字典格式
        history_list = []
        for h in history:
            history_dict = {
                "id": h.id,
                "subscription_id": h.subscription_id,
                "action": h.action,
                "action_type": h.action_type,
                "description": h.description,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "search_query": h.search_query,
                "search_results_count": h.search_results_count,
                "search_params": h.search_params,
                "download_task_id": h.download_task_id,
                "download_title": h.download_title,
                "download_size_gb": h.download_size_gb,
                "status": h.status,
                "error_message": h.error_message,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "user_id": h.user_id
            }
            history_list.append(history_dict)
        
        return success_response(data=history_list, message="获取成功")
    except Exception as e:
        logger.error(f"获取订阅历史失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取订阅历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/history", response_model=BaseResponse)
async def get_all_subscription_history(
    action_type: Optional[str] = Query(None, description="操作类型过滤: operation, search, download"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db = Depends(get_db)
):
    """
    获取所有订阅历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {
                "id": 1,
                "subscription_id": 1,
                "action": "create",
                ...
            },
            ...
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        history = await service.get_all_subscription_history(
            action_type=action_type,
            limit=limit,
            offset=offset
        )
        
        # 转换为字典格式
        history_list = []
        for h in history:
            history_dict = {
                "id": h.id,
                "subscription_id": h.subscription_id,
                "action": h.action,
                "action_type": h.action_type,
                "description": h.description,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "search_query": h.search_query,
                "search_results_count": h.search_results_count,
                "search_params": h.search_params,
                "download_task_id": h.download_task_id,
                "download_title": h.download_title,
                "download_size_gb": h.download_size_gb,
                "status": h.status,
                "error_message": h.error_message,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "user_id": h.user_id
            }
            history_list.append(history_dict)
        
        return success_response(data=history_list, message="获取成功")
    except Exception as e:
        logger.error(f"获取所有订阅历史失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取所有订阅历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{subscription_id}/check", response_model=BaseResponse)
async def check_subscription(
    subscription_id: int,
    auto_download: Optional[bool] = Query(None, description="是否自动下载，不指定则使用订阅设置"),
    db = Depends(get_db)
):
    """
    手动检查订阅（VIDEO-AUTOLOOP-1）
    
    触发订阅的搜索和下载流程，支持安全策略过滤
    
    返回统一响应格式：
    {
        "success": true,
        "message": "检查完成",
        "data": {
            "success": true,
            "message": "找到 X 个候选，创建了 Y 个下载任务",
            "downloaded_count": 1,
            "candidates_found": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubscriptionService(db)
        
        # 检查订阅是否存在
        subscription = await service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="SUBSCRIPTION_NOT_FOUND",
                    error_message=f"订阅 {subscription_id} 不存在"
                ).model_dump()
            )
        
        # 检查订阅状态
        if subscription.status != "active":
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="SUBSCRIPTION_NOT_ACTIVE",
                    error_message=f"订阅状态为 {subscription.status}，无法执行检查"
                ).model_dump()
            )
        
        logger.info(f"手动检查订阅 {subscription_id}: {subscription.title}")
        
        # 执行订阅检查
        result = await service.execute_search(
            subscription_id=subscription_id,
            auto_download_override=auto_download
        )
        
        # 构建响应数据
        response_data = {
            "success": result.get("success", False),
            "message": result.get("message", "检查完成"),
            "downloaded_count": result.get("downloaded_count", 0),
            "candidates_found": result.get("candidates_count", 0),
            "subscription_id": subscription_id,
            "subscription_title": subscription.title,
            "security_settings": {
                "allow_hr": getattr(subscription, 'allow_hr', False),
                "allow_h3h5": getattr(subscription, 'allow_h3h5', False),
                "strict_free_only": getattr(subscription, 'strict_free_only', False)
            }
        }
        
        if result.get("success", False):
            logger.info(f"订阅 {subscription_id} 手动检查成功: {result.get('message', '')}")
            return success_response(data=response_data, message="检查完成")
        else:
            logger.warning(f"订阅 {subscription_id} 手动检查失败: {result.get('message', '未知错误')}")
            return success_response(data=response_data, message="检查完成但未创建下载任务")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动检查订阅 {subscription_id} 失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检查订阅时发生错误: {str(e)}"
            ).model_dump()
        )

