"""
漫画源管理 API（仅管理员）
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response, error_response, PaginatedResponse
from app.core.dependencies import get_current_user, get_current_admin_user
from app.models.manga_source import MangaSource
from app.models.user import User
from app.schemas.manga_source import (
    MangaSourceCreate,
    MangaSourceUpdate,
    MangaSourceRead,
)
from app.services.manga_source_service import test_connection

router = APIRouter(prefix="/api/dev/manga/sources", tags=["漫画源管理"])





@router.get("", response_model=BaseResponse, summary="获取漫画源列表")
async def list_manga_sources(
    keyword: Optional[str] = Query(None, description="关键字（按名称模糊匹配）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取漫画源列表（仅管理员）
    
    支持分页和关键字搜索
    """
    try:
        # 构建查询条件
        conditions = []
        
        if keyword:
            conditions.append(MangaSource.name.ilike(f"%{keyword}%"))
        
        # 总数查询
        count_query = select(func.count()).select_from(MangaSource)
        if conditions:
            count_query = count_query.where(or_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页查询
        query = select(MangaSource)
        if conditions:
            query = query.where(or_(*conditions))
        
        offset = (page - 1) * page_size
        query = query.order_by(MangaSource.id.desc()).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        sources = result.scalars().all()
        
        # 转换为响应格式
        items = [MangaSourceRead.model_validate(source) for source in sources]
        
        paginated_response = PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(
            data=paginated_response.model_dump(),
            message="获取漫画源列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取漫画源列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取列表失败: {str(e)}"
        )


@router.post("", response_model=BaseResponse, status_code=status.HTTP_201_CREATED, summary="创建漫画源")
async def create_manga_source(
    payload: MangaSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    创建漫画源（仅管理员）
    """
    try:
        # 创建新记录
        new_source = MangaSource(
            name=payload.name,
            type=payload.type,
            base_url=str(payload.base_url),
            api_key=payload.api_key,
            username=payload.username,
            password=payload.password,
            is_enabled=payload.is_enabled,
            extra_config=payload.extra_config
        )
        
        db.add(new_source)
        await db.commit()
        await db.refresh(new_source)
        
        return success_response(
            data=MangaSourceRead.model_validate(new_source).model_dump(),
            message="创建漫画源成功"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"创建漫画源失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.put("/{source_id}", response_model=BaseResponse, summary="更新漫画源")
async def update_manga_source(
    source_id: int = Path(..., description="漫画源 ID"),
    payload: MangaSourceUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    更新漫画源（仅管理员）
    """
    try:
        # 查询记录
        stmt = select(MangaSource).where(MangaSource.id == source_id)
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"漫画源不存在 (ID: {source_id})"
            )
        
        # 更新字段
        if payload.name is not None:
            source.name = payload.name
        if payload.type is not None:
            source.type = payload.type
        if payload.base_url is not None:
            source.base_url = str(payload.base_url)
        if payload.api_key is not None:
            source.api_key = payload.api_key
        if payload.username is not None:
            source.username = payload.username
        if payload.password is not None:
            source.password = payload.password
        if payload.is_enabled is not None:
            source.is_enabled = payload.is_enabled
        if payload.extra_config is not None:
            source.extra_config = payload.extra_config
        
        await db.commit()
        await db.refresh(source)
        
        return success_response(
            data=MangaSourceRead.model_validate(source).model_dump(),
            message="更新漫画源成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新漫画源失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.delete("/{source_id}", response_model=BaseResponse, summary="删除漫画源")
async def delete_manga_source(
    source_id: int = Path(..., description="漫画源 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    删除漫画源（仅管理员）
    """
    try:
        # 查询记录
        stmt = select(MangaSource).where(MangaSource.id == source_id)
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"漫画源不存在 (ID: {source_id})"
            )
        
        await db.delete(source)
        await db.commit()
        
        return success_response(message="删除漫画源成功")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除漫画源失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.post("/{source_id}/ping", response_model=BaseResponse, summary="测试漫画源连接")
async def ping_manga_source(
    source_id: int = Path(..., description="漫画源 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """测试漫画源连接（仅管理员）。返回 ok/message 以及库列表。"""
    try:
        ok, message, libraries = await test_connection(db, source_id)

        return success_response(
            data={
                "ok": ok,
                "message": message,
                "libraries": [
                    {"id": lib.id, "name": lib.name} for lib in libraries
                ],
            },
            message="测试连接成功" if ok else "测试连接失败",
        )

    except Exception as e:
        logger.error(f"测试漫画源连接失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败: {str(e)}",
        )

