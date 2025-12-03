"""
音乐榜单管理 API

提供榜单源和榜单的 CRUD 操作（管理员/开发者接口）
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_async_session
from app.core.response import success_response
from app.models.music_chart_source import MusicChartSource
from app.models.music_chart import MusicChart
from app.models.music_chart_item import MusicChartItem
from app.schemas.music import (
    MusicChartSourceCreate,
    MusicChartSourceUpdate,
    MusicChartSourceRead,
    MusicChartSourceListResponse,
    MusicChartCreate,
    MusicChartUpdate,
    MusicChartRead,
    MusicChartListResponse,
    MusicChartItemRead,
    MusicChartItemListResponse,
    MusicChartDetailRead,
)

router = APIRouter(prefix="/api/dev/music/charts", tags=["音乐榜单管理 (Dev)"])


# ========== 榜单源 CRUD ==========

@router.get("/sources", summary="获取榜单源列表")
async def list_chart_sources(
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """获取所有榜单源"""
    query = select(MusicChartSource)
    count_query = select(func.count(MusicChartSource.id))
    
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (MusicChartSource.platform.ilike(keyword_filter)) |
            (MusicChartSource.display_name.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (MusicChartSource.platform.ilike(keyword_filter)) |
            (MusicChartSource.display_name.ilike(keyword_filter))
        )
    
    if is_enabled is not None:
        query = query.where(MusicChartSource.is_enabled == is_enabled)
        count_query = count_query.where(MusicChartSource.is_enabled == is_enabled)
    
    # 统计总数
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(MusicChartSource.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    sources = result.scalars().all()
    
    items = [MusicChartSourceRead.model_validate(s) for s in sources]
    total_pages = (total + page_size - 1) // page_size
    
    return success_response(
        data=MusicChartSourceListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("/sources", summary="创建榜单源")
async def create_chart_source(
    data: MusicChartSourceCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """创建新的榜单源"""
    # 检查 platform 是否已存在
    existing = await session.execute(
        select(MusicChartSource).where(MusicChartSource.platform == data.platform)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"平台 '{data.platform}' 已存在")
    
    source = MusicChartSource(
        platform=data.platform,
        display_name=data.display_name,
        description=data.description,
        config=data.config,
        is_enabled=data.is_enabled,
        icon_url=data.icon_url,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    
    return success_response(
        data=MusicChartSourceRead.model_validate(source),
        message="榜单源创建成功"
    )


@router.get("/sources/{source_id}", summary="获取榜单源详情")
async def get_chart_source(
    source_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """获取榜单源详情"""
    result = await session.execute(
        select(MusicChartSource).where(MusicChartSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="榜单源不存在")
    
    return success_response(data=MusicChartSourceRead.model_validate(source))


@router.put("/sources/{source_id}", summary="更新榜单源")
async def update_chart_source(
    source_id: int,
    data: MusicChartSourceUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """更新榜单源"""
    result = await session.execute(
        select(MusicChartSource).where(MusicChartSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="榜单源不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)
    
    await session.commit()
    await session.refresh(source)
    
    return success_response(
        data=MusicChartSourceRead.model_validate(source),
        message="榜单源更新成功"
    )


@router.delete("/sources/{source_id}", summary="删除榜单源")
async def delete_chart_source(
    source_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """删除榜单源（会级联删除关联的榜单）"""
    result = await session.execute(
        select(MusicChartSource).where(MusicChartSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="榜单源不存在")
    
    await session.delete(source)
    await session.commit()
    
    return success_response(message="榜单源删除成功")


# ========== 榜单 CRUD ==========

@router.get("/list", summary="获取榜单列表")
async def list_charts(
    source_id: Optional[int] = Query(None, description="按源过滤"),
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """获取所有榜单"""
    query = select(MusicChart, MusicChartSource).join(
        MusicChartSource, MusicChart.source_id == MusicChartSource.id
    )
    count_query = select(func.count(MusicChart.id))
    
    if source_id:
        query = query.where(MusicChart.source_id == source_id)
        count_query = count_query.where(MusicChart.source_id == source_id)
    
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (MusicChart.display_name.ilike(keyword_filter)) |
            (MusicChart.chart_key.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (MusicChart.display_name.ilike(keyword_filter)) |
            (MusicChart.chart_key.ilike(keyword_filter))
        )
    
    if is_enabled is not None:
        query = query.where(MusicChart.is_enabled == is_enabled)
        count_query = count_query.where(MusicChart.is_enabled == is_enabled)
    
    # 统计总数
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(MusicChart.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    rows = result.all()
    
    items = []
    for chart, source in rows:
        item = MusicChartRead.model_validate(chart)
        item.source_platform = source.platform
        item.source_display_name = source.display_name
        items.append(item)
    
    total_pages = (total + page_size - 1) // page_size
    
    return success_response(
        data=MusicChartListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("/", summary="创建榜单")
async def create_chart(
    data: MusicChartCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """创建新的榜单"""
    # 检查源是否存在
    source_result = await session.execute(
        select(MusicChartSource).where(MusicChartSource.id == data.source_id)
    )
    source = source_result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=400, detail="榜单源不存在")
    
    # 检查 chart_key 是否已存在
    existing = await session.execute(
        select(MusicChart).where(
            (MusicChart.source_id == data.source_id) &
            (MusicChart.chart_key == data.chart_key)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"榜单 '{data.chart_key}' 在该源下已存在")
    
    chart = MusicChart(
        source_id=data.source_id,
        chart_key=data.chart_key,
        display_name=data.display_name,
        description=data.description,
        region=data.region,
        chart_type=data.chart_type,
        is_enabled=data.is_enabled,
        fetch_interval_minutes=data.fetch_interval_minutes,
        max_items=data.max_items,
    )
    session.add(chart)
    await session.commit()
    await session.refresh(chart)
    
    result = MusicChartRead.model_validate(chart)
    result.source_platform = source.platform
    result.source_display_name = source.display_name
    
    return success_response(data=result, message="榜单创建成功")


@router.get("/{chart_id}", summary="获取榜单详情")
async def get_chart(
    chart_id: int,
    include_items: bool = Query(False, description="是否包含条目"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    """获取榜单详情"""
    result = await session.execute(
        select(MusicChart, MusicChartSource).join(
            MusicChartSource, MusicChart.source_id == MusicChartSource.id
        ).where(MusicChart.id == chart_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="榜单不存在")
    
    chart, source = row
    
    if include_items:
        # 查询条目
        items_query = select(MusicChartItem).where(
            MusicChartItem.chart_id == chart_id
        ).order_by(MusicChartItem.rank.asc().nullslast())
        items_query = items_query.offset((page - 1) * page_size).limit(page_size)
        
        items_result = await session.execute(items_query)
        items = [MusicChartItemRead.model_validate(i) for i in items_result.scalars().all()]
        
        detail = MusicChartDetailRead(
            id=chart.id,
            source_id=chart.source_id,
            chart_key=chart.chart_key,
            display_name=chart.display_name,
            description=chart.description,
            region=chart.region,
            chart_type=chart.chart_type,
            is_enabled=chart.is_enabled,
            last_fetched_at=chart.last_fetched_at,
            source_platform=source.platform,
            source_display_name=source.display_name,
            items=items,
        )
        return success_response(data=detail)
    else:
        result_data = MusicChartRead.model_validate(chart)
        result_data.source_platform = source.platform
        result_data.source_display_name = source.display_name
        return success_response(data=result_data)


@router.put("/{chart_id}", summary="更新榜单")
async def update_chart(
    chart_id: int,
    data: MusicChartUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """更新榜单"""
    result = await session.execute(
        select(MusicChart).where(MusicChart.id == chart_id)
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="榜单不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(chart, key, value)
    
    await session.commit()
    await session.refresh(chart)
    
    return success_response(
        data=MusicChartRead.model_validate(chart),
        message="榜单更新成功"
    )


@router.delete("/{chart_id}", summary="删除榜单")
async def delete_chart(
    chart_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """删除榜单（会级联删除关联的条目）"""
    result = await session.execute(
        select(MusicChart).where(MusicChart.id == chart_id)
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="榜单不存在")
    
    await session.delete(chart)
    await session.commit()
    
    return success_response(message="榜单删除成功")


# ========== 榜单条目查询 ==========

@router.get("/{chart_id}/items", summary="获取榜单条目")
async def list_chart_items(
    chart_id: int,
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    """获取榜单条目列表"""
    # 检查榜单是否存在
    chart_result = await session.execute(
        select(MusicChart).where(MusicChart.id == chart_id)
    )
    if not chart_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="榜单不存在")
    
    query = select(MusicChartItem).where(MusicChartItem.chart_id == chart_id)
    count_query = select(func.count(MusicChartItem.id)).where(MusicChartItem.chart_id == chart_id)
    
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (MusicChartItem.title.ilike(keyword_filter)) |
            (MusicChartItem.artist_name.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (MusicChartItem.title.ilike(keyword_filter)) |
            (MusicChartItem.artist_name.ilike(keyword_filter))
        )
    
    # 统计总数
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(MusicChartItem.rank.asc().nullslast())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    items = [MusicChartItemRead.model_validate(i) for i in result.scalars().all()]
    
    total_pages = (total + page_size - 1) // page_size
    
    return success_response(
        data=MusicChartItemListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("/{chart_id}/sync", summary="手动同步榜单")
async def sync_chart(
    chart_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """手动触发榜单同步"""
    # 检查榜单是否存在
    result = await session.execute(
        select(MusicChart).where(MusicChart.id == chart_id)
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="榜单不存在")
    
    # 调用同步服务（延迟导入避免循环依赖）
    try:
        from app.services.music_chart_service import fetch_chart_items_for_chart
        diff_result = await fetch_chart_items_for_chart(session, chart_id)
        return success_response(
            data=diff_result,
            message=f"榜单同步完成，新增 {diff_result.get('new_count', 0)} 条"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
