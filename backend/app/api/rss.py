"""
RSS订阅相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.modules.rss.service import RSSSubscriptionService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class RSSSubscriptionCreate(BaseModel):
    """创建RSS订阅请求"""
    name: str
    url: str
    user_id: int  # 用户ID
    site_id: Optional[int] = None
    enabled: bool = True
    interval: int = 30  # 刷新间隔（分钟）
    filter_rules: Optional[dict] = None  # 过滤规则
    download_rules: Optional[dict] = None  # 下载规则
    filter_group_ids: Optional[List[int]] = []  # 过滤规则组ID列表
    description: Optional[str] = None


class RSSSubscriptionResponse(BaseModel):
    """RSS订阅响应"""
    id: int
    user_id: int  # 用户ID
    name: str
    url: str
    site_id: Optional[int] = None
    enabled: bool
    interval: int
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None
    last_item_hash: Optional[str] = None
    filter_rules: Optional[dict] = None
    download_rules: Optional[dict] = None
    filter_group_ids: Optional[List[int]] = []  # 过滤规则组ID列表
    total_items: int
    downloaded_items: int
    skipped_items: int
    error_count: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=BaseResponse, status_code=http_status.HTTP_201_CREATED)
async def create_rss_subscription(
    subscription: RSSSubscriptionCreate,
    db = Depends(get_db)
):
    """
    创建RSS订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": RSSSubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        result = await service.create_rss_subscription(subscription.model_dump())
        
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = RSSSubscriptionResponse.model_validate(result)
        return success_response(data=subscription_response.model_dump(), message="创建成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建RSS订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建RSS订阅时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/", response_model=BaseResponse)
async def list_rss_subscriptions(
    enabled: Optional[bool] = Query(None, description="是否启用过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取RSS订阅列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [RSSSubscriptionResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        subscriptions = await service.list_rss_subscriptions(enabled=enabled)
        
        # 计算分页
        total = len(subscriptions)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = subscriptions[start:end]
        
        # 将SQLAlchemy对象列表转换为Pydantic模型列表
        subscription_responses = [
            RSSSubscriptionResponse.model_validate(item) for item in paginated_items
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
        logger.error(f"获取RSS订阅列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSS订阅列表时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/{subscription_id}", response_model=BaseResponse)
async def get_rss_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    获取RSS订阅详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": RSSSubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        subscription = await service.get_rss_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"RSS订阅不存在 (ID: {subscription_id})"
                ).model_dump(mode='json')
            )
        
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = RSSSubscriptionResponse.model_validate(subscription)
        return success_response(data=subscription_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取RSS订阅详情失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSS订阅详情时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.put("/{subscription_id}", response_model=BaseResponse)
async def update_rss_subscription(
    subscription_id: int,
    subscription: RSSSubscriptionCreate,
    db = Depends(get_db)
):
    """
    更新RSS订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": RSSSubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        result = await service.update_rss_subscription(subscription_id, subscription.model_dump())
        if not result:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"RSS订阅不存在 (ID: {subscription_id})"
                ).model_dump(mode='json')
            )
        
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = RSSSubscriptionResponse.model_validate(result)
        return success_response(data=subscription_response.model_dump(), message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新RSS订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新RSS订阅时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.delete("/{subscription_id}", response_model=BaseResponse)
async def delete_rss_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    删除RSS订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        success = await service.delete_rss_subscription(subscription_id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"RSS订阅不存在 (ID: {subscription_id})"
                ).model_dump(mode='json')
            )
        
        return success_response(data=None, message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除RSS订阅失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除RSS订阅时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.post("/{subscription_id}/check", response_model=BaseResponse)
async def check_rss_updates(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    手动检查RSS订阅更新
    
    返回统一响应格式：
    {
        "success": true,
        "message": "检查完成",
        "data": {
            "new_items": 10,
            "processed_items": 8,
            "downloaded_items": 5,
            "skipped_items": 3,
            "errors": []
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        result = await service.check_rss_updates(subscription_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CHECK_FAILED",
                    error_message=result.get("error", "检查RSS更新失败")
                ).model_dump(mode='json')
            )
        
        return success_response(data=result, message="检查完成")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查RSS订阅更新失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检查RSS订阅更新时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


class RSSItemResponse(BaseModel):
    """RSS项响应"""
    id: int
    subscription_id: int
    item_hash: str
    title: str
    link: str
    description: Optional[str] = None
    pub_date: Optional[datetime] = None
    processed: bool
    downloaded: bool
    download_task_id: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


@router.get("/items", response_model=BaseResponse)
async def list_rss_items(
    subscription_id: Optional[int] = Query(None, description="RSS订阅ID"),
    processed: Optional[bool] = Query(None, description="是否已处理"),
    downloaded: Optional[bool] = Query(None, description="是否已下载"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取RSS项列表（支持分页和过滤）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [RSSItemResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        items, total = await service.list_rss_items(
            subscription_id=subscription_id,
            processed=processed,
            downloaded=downloaded,
            page=page,
            page_size=page_size
        )
        
        # 将SQLAlchemy对象列表转换为Pydantic模型列表
        item_responses = [
            RSSItemResponse.model_validate(item) for item in items
        ]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=[item.model_dump() for item in item_responses],
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取RSS项列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSS项列表时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/items/{item_id}", response_model=BaseResponse)
async def get_rss_item(
    item_id: int,
    db = Depends(get_db)
):
    """
    获取RSS项详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": RSSItemResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        item = await service.get_rss_item(item_id)
        if not item:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"RSS项不存在 (ID: {item_id})"
                ).model_dump(mode='json')
            )
        
        # 将SQLAlchemy对象转换为Pydantic模型
        item_response = RSSItemResponse.model_validate(item)
        return success_response(data=item_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取RSS项详情失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSS项详情时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/{subscription_id}/items", response_model=BaseResponse)
async def list_subscription_rss_items(
    subscription_id: int,
    processed: Optional[bool] = Query(None, description="是否已处理"),
    downloaded: Optional[bool] = Query(None, description="是否已下载"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取指定RSS订阅的项列表（支持分页和过滤）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [RSSItemResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        # 验证订阅是否存在
        subscription = await service.get_rss_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"RSS订阅不存在 (ID: {subscription_id})"
                ).model_dump(mode='json')
            )
        
        items, total = await service.list_rss_items(
            subscription_id=subscription_id,
            processed=processed,
            downloaded=downloaded,
            page=page,
            page_size=page_size
        )
        
        # 将SQLAlchemy对象列表转换为Pydantic模型列表
        item_responses = [
            RSSItemResponse.model_validate(item) for item in items
        ]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=[item.model_dump() for item in item_responses],
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取RSS订阅项列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSS订阅项列表时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/{subscription_id}/items/stats", response_model=BaseResponse)
async def get_subscription_items_stats(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    获取RSS订阅的项统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total": 100,
            "processed": 80,
            "unprocessed": 20,
            "downloaded": 60,
            "skipped": 20
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RSSSubscriptionService(db)
        # 验证订阅是否存在
        subscription = await service.get_rss_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"RSS订阅不存在 (ID: {subscription_id})"
                ).model_dump(mode='json')
            )
        
        stats = await service.count_rss_items(subscription_id=subscription_id)
        return success_response(data=stats, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取RSS订阅项统计失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取RSS订阅项统计时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )

