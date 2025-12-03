"""
过滤规则组API
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.schemas import BaseResponse
from app.core.security import get_current_user
from app.models.user import User
from app.modules.filter_rule_group.service import FilterRuleGroupService
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/filter-rule-groups", tags=["filter-rule-groups"])


# Pydantic模型
class FilterRuleGroupRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    media_types: List[str] = ["movie", "tv"]
    priority: int = 100
    rules: List[Dict] = []
    enabled: bool = True


class FilterRuleGroupResponse(BaseModel):
    id: int
    user_id: Optional[int]
    name: str
    description: str
    media_types: List[str]
    priority: int
    rules: List[Dict]
    enabled: bool
    created_at: str
    updated_at: str
    created_by: Optional[int]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


class FilterRuleGroupListResponse(BaseModel):
    items: List[FilterRuleGroupResponse]
    total: int
    page: int
    size: int


class MediaTypesResponse(BaseModel):
    media_types: List[str]


class ValidateResponse(BaseModel):
    valid: bool
    errors: Optional[List[str]] = None


# 依赖注入
async def get_service(db: AsyncSession = Depends(get_db)) -> FilterRuleGroupService:
    return FilterRuleGroupService(db)


# API端点
@router.get("/", response_model=BaseResponse[FilterRuleGroupListResponse])
async def list_filter_rule_groups(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    media_type: Optional[str] = Query(None, description="媒体类型过滤"),
    enabled: Optional[bool] = Query(None, description="启用状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    service: FilterRuleGroupService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取过滤规则组列表
    """
    try:
        # 获取所有规则组
        groups = await service.list_groups(
            user_id=current_user.id,
            media_type=media_type,
            enabled_only=enabled is not None and enabled
        )
        
        # 搜索过滤
        if search:
            groups = [g for g in groups if search.lower() in g.name.lower() or 
                     (g.description and search.lower() in g.description.lower())]
        
        # 状态过滤
        if enabled is not None:
            groups = [g for g in groups if g.enabled == enabled]
        
        # 分页处理
        total = len(groups)
        start = (page - 1) * size
        end = start + size
        paginated_groups = groups[start:end]
        
        return BaseResponse(
            data=FilterRuleGroupListResponse(
                items=[FilterRuleGroupResponse.model_validate(g) for g in paginated_groups],
                total=total,
                page=page,
                size=size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{group_id}", response_model=BaseResponse[FilterRuleGroupResponse])
async def get_filter_rule_group(
    group_id: int,
    service: FilterRuleGroupService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个过滤规则组
    """
    try:
        group = await service.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="规则组不存在")
        
        # 检查权限
        if group.user_id is not None and group.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此规则组")
        
        return BaseResponse(data=FilterRuleGroupResponse.model_validate(group))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=BaseResponse[FilterRuleGroupResponse])
async def create_filter_rule_group(
    data: FilterRuleGroupRequest,
    service: FilterRuleGroupService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    创建过滤规则组
    """
    try:
        group = await service.create_group(
            user_id=current_user.id,
            data=data.model_dump(),
            created_by=current_user.username
        )
        
        return BaseResponse(data=FilterRuleGroupResponse.model_validate(group))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{group_id}", response_model=BaseResponse[FilterRuleGroupResponse])
async def update_filter_rule_group(
    group_id: int,
    data: FilterRuleGroupRequest,
    service: FilterRuleGroupService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    更新过滤规则组
    """
    try:
        # 检查规则组是否存在
        existing_group = await service.get_group(group_id)
        if not existing_group:
            raise HTTPException(status_code=404, detail="规则组不存在")
        
        # 检查权限
        if existing_group.user_id is not None and existing_group.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此规则组")
        
        group = await service.update_group(
            group_id=group_id,
            data=data.model_dump(),
            updated_by=current_user.username
        )
        
        return BaseResponse(data=FilterRuleGroupResponse.model_validate(group))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{group_id}", response_model=BaseResponse[dict])
async def delete_filter_rule_group(
    group_id: int,
    service: FilterRuleGroupService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    删除过滤规则组
    """
    try:
        # 检查规则组是否存在
        existing_group = await service.get_group(group_id)
        if not existing_group:
            raise HTTPException(status_code=404, detail="规则组不存在")
        
        # 检查权限
        if existing_group.user_id is not None and existing_group.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此规则组")
        
        await service.delete_group(group_id)
        
        return BaseResponse(data={"message": "删除成功"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/", response_model=BaseResponse[dict])
async def delete_filter_rule_groups_batch(
    ids: List[int],
    service: FilterRuleGroupService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    批量删除过滤规则组
    """
    try:
        for group_id in ids:
            # 检查规则组是否存在
            existing_group = await service.get_group(group_id)
            if not existing_group:
                continue
            
            # 检查权限
            if existing_group.user_id is not None and existing_group.user_id != current_user.id:
                continue
            
            await service.delete_group(group_id)
        
        return BaseResponse(data={"message": "批量删除成功"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{group_id}/toggle", response_model=BaseResponse[FilterRuleGroupResponse])
async def toggle_filter_rule_group(
    group_id: int,
    enabled: bool,
    service: FilterRuleGroupService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    启用/禁用过滤规则组
    """
    try:
        # 检查规则组是否存在
        existing_group = await service.get_group(group_id)
        if not existing_group:
            raise HTTPException(status_code=404, detail="规则组不存在")
        
        # 检查权限
        if existing_group.user_id is not None and existing_group.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此规则组")
        
        group = await service.update_group(
            group_id=group_id,
            data={"enabled": enabled},
            updated_by=current_user.username
        )
        
        return BaseResponse(data=FilterRuleGroupResponse.model_validate(group))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media-types", response_model=BaseResponse[MediaTypesResponse])
async def get_media_types():
    """
    获取支持的媒体类型列表
    """
    try:
        media_types = ["movie", "tv", "short_drama", "anime", "music"]
        return BaseResponse(data=MediaTypesResponse(media_types=media_types))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=BaseResponse[ValidateResponse])
async def validate_rule_group(
    data: FilterRuleGroupRequest,
    service: FilterRuleGroupService = Depends(get_service)
):
    """
    验证规则组配置
    """
    try:
        # 这里可以添加验证逻辑
        # 目前简单验证基本字段
        errors = []
        
        if not data.name.strip():
            errors.append("规则组名称不能为空")
        
        if not data.media_types:
            errors.append("请至少选择一个媒体类型")
        
        if data.priority < 0:
            errors.append("优先级不能为负数")
        
        # 验证规则格式
        try:
            if data.rules:
                import json
                json.dumps(data.rules)
        except (TypeError, ValueError):
            errors.append("规则格式不正确")
        
        return BaseResponse(data=ValidateResponse(
            valid=len(errors) == 0,
            errors=errors if errors else None
        ))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
