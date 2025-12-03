"""
用户音乐订阅 API

提供用户订阅榜单的 CRUD 操作和手动触发功能。
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from loguru import logger

from app.core.database import get_async_session
from app.core.response import success_response
from app.models.user_music_subscription import UserMusicSubscription
from app.models.music_chart import MusicChart
from app.models.music_chart_source import MusicChartSource
from app.models.music_download_job import MusicDownloadJob
from app.schemas.music import (
    UserMusicSubscriptionCreate,
    UserMusicSubscriptionUpdate,
    UserMusicSubscriptionRead,
    UserMusicSubscriptionListResponse,
    SubscriptionRunResult,
    MusicSubscriptionRunResponse,
    MusicSubscriptionBatchRunResponse,
    MusicDownloadJobRead,
    MusicDownloadJobListResponse,
)

router = APIRouter(prefix="/api/music/subscriptions", tags=["音乐订阅"])

# 临时用户 ID（实际应从认证中获取）
TEMP_USER_ID = 1


def get_current_user_id() -> int:
    """获取当前用户 ID（临时实现）"""
    return TEMP_USER_ID


# ========== 用户订阅 CRUD ==========

@router.get("", summary="获取我的订阅列表")
async def list_my_subscriptions(
    status: Optional[str] = Query(None, description="状态过滤: active/paused"),
    subscription_type: Optional[str] = Query(None, description="订阅类型过滤: chart/keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """获取当前用户的音乐订阅列表（支持榜单和关键字订阅）"""
    user_id = get_current_user_id()
    
    # 使用LEFT JOIN支持关键字订阅（chart_id为NULL）
    query = select(
        UserMusicSubscription,
        MusicChart,
        MusicChartSource
    ).outerjoin(
        MusicChart, UserMusicSubscription.chart_id == MusicChart.id
    ).outerjoin(
        MusicChartSource, MusicChart.source_id == MusicChartSource.id
    ).where(UserMusicSubscription.user_id == user_id)
    
    count_query = select(func.count(UserMusicSubscription.id)).where(
        UserMusicSubscription.user_id == user_id
    )
    
    if status:
        query = query.where(UserMusicSubscription.status == status)
        count_query = count_query.where(UserMusicSubscription.status == status)
    
    if subscription_type:
        query = query.where(UserMusicSubscription.subscription_type == subscription_type)
        count_query = count_query.where(UserMusicSubscription.subscription_type == subscription_type)
    
    # 统计总数
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(UserMusicSubscription.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    rows = result.all()
    
    items = []
    for sub, chart, source in rows:
        item = UserMusicSubscriptionRead.model_validate(sub)
        
        # 根据订阅类型设置关联信息
        if sub.subscription_type == "chart" and chart:
            item.chart_display_name = chart.display_name
            item.source_platform = source.platform if source else None
        elif sub.subscription_type == "keyword":
            # 关键字订阅显示查询信息
            item.chart_display_name = f"关键字: {sub.music_query}"
            item.source_platform = sub.music_site
        
        items.append(item)
    
    total_pages = (total + page_size - 1) // page_size
    
    return success_response(
        data=UserMusicSubscriptionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("", summary="创建订阅")
async def create_subscription(
    data: UserMusicSubscriptionCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """创建新的音乐订阅（支持榜单和关键字订阅）"""
    user_id = get_current_user_id()
    
    # 根据订阅类型进行验证
    if data.subscription_type == "chart":
        # 榜单订阅验证
        if not data.chart_id:
            raise HTTPException(status_code=400, detail="榜单订阅必须指定chart_id")
        
        # 检查榜单是否存在
        chart_result = await session.execute(
            select(MusicChart).where(MusicChart.id == data.chart_id)
        )
        chart = chart_result.scalar_one_or_none()
        if not chart:
            raise HTTPException(status_code=400, detail="榜单不存在")
        
        # 检查是否已订阅该榜单
        existing = await session.execute(
            select(UserMusicSubscription).where(
                and_(
                    UserMusicSubscription.user_id == user_id,
                    UserMusicSubscription.subscription_type == "chart",
                    UserMusicSubscription.chart_id == data.chart_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="已订阅该榜单")
        
        # 创建榜单订阅
        subscription = UserMusicSubscription(
            user_id=user_id,
            subscription_type="chart",
            chart_id=data.chart_id,
            music_query=None,
            music_site=None,
            music_quality=None,
            auto_search=data.auto_search,
            auto_download=data.auto_download,
            max_new_tracks_per_run=data.max_new_tracks_per_run,
            quality_preference=data.quality_preference,
            preferred_sites=data.preferred_sites,
            allow_hr=data.allow_hr,
            allow_h3h5=data.allow_h3h5,
            strict_free_only=data.strict_free_only,
        )
        
    elif data.subscription_type == "keyword":
        # 关键字订阅验证
        if not data.music_query or not data.music_query.strip():
            raise HTTPException(status_code=400, detail="关键字订阅必须指定music_query")
        
        # 检查是否已存在相同关键字订阅
        existing = await session.execute(
            select(UserMusicSubscription).where(
                and_(
                    UserMusicSubscription.user_id == user_id,
                    UserMusicSubscription.subscription_type == "keyword",
                    UserMusicSubscription.music_query == data.music_query.strip()
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="已存在相同关键字的订阅")
        
        # 创建关键字订阅
        subscription = UserMusicSubscription(
            user_id=user_id,
            subscription_type="keyword",
            chart_id=None,
            music_query=data.music_query.strip(),
            music_site=data.music_site,
            music_quality=data.music_quality,
            auto_search=data.auto_search,
            auto_download=data.auto_download,
            max_new_tracks_per_run=data.max_new_tracks_per_run,
            quality_preference=data.quality_preference,
            preferred_sites=data.preferred_sites,
            allow_hr=data.allow_hr,
            allow_h3h5=data.allow_h3h5,
            strict_free_only=data.strict_free_only,
        )
        
    else:
        raise HTTPException(status_code=400, detail="不支持的订阅类型，请选择chart或keyword")
    
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    
    # 构建返回结果
    result = UserMusicSubscriptionRead.model_validate(subscription)
    
    # 设置关联信息
    if subscription.subscription_type == "chart":
        chart_result = await session.execute(
            select(MusicChart, MusicChartSource).join(
                MusicChartSource, MusicChart.source_id == MusicChartSource.id
            ).where(MusicChart.id == subscription.chart_id)
        )
        row = chart_result.first()
        if row:
            chart, source = row
            result.chart_display_name = chart.display_name
            result.source_platform = source.platform
    elif subscription.subscription_type == "keyword":
        result.chart_display_name = f"关键字: {subscription.music_query}"
        result.source_platform = subscription.music_site
    
    return success_response(data=result, message="订阅创建成功")


@router.get("/{subscription_id}", summary="获取订阅详情")
async def get_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """获取订阅详情（支持榜单和关键字订阅）"""
    user_id = get_current_user_id()
    
    # 使用LEFT JOIN支持关键字订阅
    result = await session.execute(
        select(UserMusicSubscription, MusicChart, MusicChartSource).outerjoin(
            MusicChart, UserMusicSubscription.chart_id == MusicChart.id
        ).outerjoin(
            MusicChartSource, MusicChart.source_id == MusicChartSource.id
        ).where(
            and_(
                UserMusicSubscription.id == subscription_id,
                UserMusicSubscription.user_id == user_id
            )
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    sub, chart, source = row
    item = UserMusicSubscriptionRead.model_validate(sub)
    
    # 根据订阅类型设置关联信息
    if sub.subscription_type == "chart" and chart:
        item.chart_display_name = chart.display_name
        item.source_platform = source.platform if source else None
    elif sub.subscription_type == "keyword":
        # 关键字订阅显示查询信息
        item.chart_display_name = f"关键字: {sub.music_query}"
        item.source_platform = sub.music_site
    
    return success_response(data=item)


@router.put("/{subscription_id}", summary="更新订阅")
async def update_subscription(
    subscription_id: int,
    data: UserMusicSubscriptionUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """更新订阅设置"""
    user_id = get_current_user_id()
    
    result = await session.execute(
        select(UserMusicSubscription).where(
            and_(
                UserMusicSubscription.id == subscription_id,
                UserMusicSubscription.user_id == user_id
            )
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 防止订阅类型转换（从chart到keyword或反之）
    if "subscription_type" in update_data:
        new_type = update_data["subscription_type"]
        if new_type != subscription.subscription_type:
            raise HTTPException(
                status_code=400, 
                detail="不允许修改订阅类型，请删除后重新创建"
            )
    
    # 根据当前订阅类型验证字段
    if subscription.subscription_type == "chart":
        # 榜单订阅：不允许清空chart_id
        if "chart_id" in update_data and update_data["chart_id"] is None:
            raise HTTPException(status_code=400, detail="榜单订阅不能移除chart_id")
        
        # 检查新的chart_id是否存在（如果修改了）
        if "chart_id" in update_data and update_data["chart_id"] != subscription.chart_id:
            chart_result = await session.execute(
                select(MusicChart).where(MusicChart.id == update_data["chart_id"])
            )
            if not chart_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="指定的榜单不存在")
    
    elif subscription.subscription_type == "keyword":
        # 关键字订阅：不允许清空music_query
        if "music_query" in update_data:
            new_query = update_data["music_query"]
            if not new_query or not new_query.strip():
                raise HTTPException(status_code=400, detail="关键字订阅必须指定music_query")
            
            # 检查是否与其他订阅重复
            if new_query.strip() != subscription.music_query:
                existing = await session.execute(
                    select(UserMusicSubscription).where(
                        and_(
                            UserMusicSubscription.user_id == user_id,
                            UserMusicSubscription.subscription_type == "keyword",
                            UserMusicSubscription.music_query == new_query.strip(),
                            UserMusicSubscription.id != subscription_id
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="已存在相同关键字的订阅")
    
    # 应用更新
    for key, value in update_data.items():
        if key == "music_query" and value:
            setattr(subscription, key, value.strip())
        else:
            setattr(subscription, key, value)
    
    await session.commit()
    await session.refresh(subscription)
    
    # 构建返回结果
    result = UserMusicSubscriptionRead.model_validate(subscription)
    
    # 设置关联信息
    if subscription.subscription_type == "chart":
        chart_result = await session.execute(
            select(MusicChart, MusicChartSource).join(
                MusicChartSource, MusicChart.source_id == MusicChartSource.id
            ).where(MusicChart.id == subscription.chart_id)
        )
        row = chart_result.first()
        if row:
            chart, source = row
            result.chart_display_name = chart.display_name
            result.source_platform = source.platform
    elif subscription.subscription_type == "keyword":
        result.chart_display_name = f"关键字: {subscription.music_query}"
        result.source_platform = subscription.music_site
    
    return success_response(
        data=result,
        message="订阅更新成功"
    )


@router.delete("/{subscription_id}", summary="删除订阅")
async def delete_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """删除订阅"""
    user_id = get_current_user_id()
    
    result = await session.execute(
        select(UserMusicSubscription).where(
            and_(
                UserMusicSubscription.id == subscription_id,
                UserMusicSubscription.user_id == user_id
            )
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    await session.delete(subscription)
    await session.commit()
    
    return success_response(message="订阅删除成功")


@router.post("/{subscription_id}/run_once", summary="手动运行一次", response_model=None)
async def run_subscription_once(
    subscription_id: int,
    dry_run: bool = Query(False, description="试运行模式（仅统计，不创建任务）"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    手动触发一次订阅运行（MUSIC-AUTOLOOP-2 升级版本）
    
    支持试运行模式，可以只进行搜索和过滤统计，不实际创建下载任务
    """
    user_id = get_current_user_id()
    
    result = await session.execute(
        select(UserMusicSubscription).where(
            and_(
                UserMusicSubscription.id == subscription_id,
                UserMusicSubscription.user_id == user_id
            )
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    # 调用升级后的订阅服务
    try:
        from app.services.music_subscription_service import run_subscription_once
        run_result = await run_subscription_once(
            session, 
            subscription, 
            auto_download=not dry_run
        )
        
        # 构建API响应
        response_data = MusicSubscriptionRunResponse(
            subscription_id=run_result.subscription_id,
            found_total=run_result.found_total,
            filtered_out=run_result.filtered_out,
            skipped_existing=run_result.skipped_existing,
            created_tasks=run_result.created_tasks,
            errors=run_result.errors,
        )
        
        mode_text = "试运行" if dry_run else "运行"
        message = f"{mode_text}完成：找到 {run_result.found_total} 条候选"
        
        if run_result.filtered_out:
            filtered_total = sum(run_result.filtered_out.values())
            message += f"，过滤 {filtered_total} 条"
        
        if run_result.skipped_existing > 0:
            message += f"，跳过重复 {run_result.skipped_existing} 条"
        
        if not dry_run:
            message += f"，创建任务 {run_result.created_tasks} 个"
        
        return success_response(
            data=response_data.model_dump(),
            message=message
        )
        
    except Exception as e:
        logger.error(f"音乐订阅 {subscription_id} 运行失败: {e}")
        raise HTTPException(status_code=500, detail=f"运行失败: {str(e)}")


@router.post("/{subscription_id}/pause", summary="暂停订阅")
async def pause_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """暂停订阅"""
    user_id = get_current_user_id()
    
    result = await session.execute(
        select(UserMusicSubscription).where(
            and_(
                UserMusicSubscription.id == subscription_id,
                UserMusicSubscription.user_id == user_id
            )
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    subscription.status = "paused"
    await session.commit()
    
    return success_response(message="订阅已暂停")


@router.post("/{subscription_id}/resume", summary="恢复订阅")
async def resume_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """恢复订阅"""
    user_id = get_current_user_id()
    
    result = await session.execute(
        select(UserMusicSubscription).where(
            and_(
                UserMusicSubscription.id == subscription_id,
                UserMusicSubscription.user_id == user_id
            )
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    subscription.status = "active"
    await session.commit()
    
    return success_response(message="订阅已恢复")


# ========== 下载任务查询 ==========

@router.get("/jobs", summary="获取我的下载任务")
async def list_my_download_jobs(
    status: Optional[str] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """获取当前用户的音乐下载任务列表"""
    user_id = get_current_user_id()
    
    from app.models.music_chart_item import MusicChartItem
    
    query = select(MusicDownloadJob, MusicChartItem).outerjoin(
        MusicChartItem, MusicDownloadJob.chart_item_id == MusicChartItem.id
    ).where(MusicDownloadJob.user_id == user_id)
    
    count_query = select(func.count(MusicDownloadJob.id)).where(
        MusicDownloadJob.user_id == user_id
    )
    
    if status:
        query = query.where(MusicDownloadJob.status == status)
        count_query = count_query.where(MusicDownloadJob.status == status)
    
    # 统计总数
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(MusicDownloadJob.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    rows = result.all()
    
    items = []
    for job, chart_item in rows:
        item = MusicDownloadJobRead.model_validate(job)
        if chart_item:
            item.chart_item_title = chart_item.title
            item.chart_item_artist = chart_item.artist_name
        items.append(item)
    
    total_pages = (total + page_size - 1) // page_size
    
    return success_response(
        data=MusicDownloadJobListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


# ========== Phase 3: 任务操作 ==========

@router.post("/jobs/{job_id}/retry", summary="重试失败的任务")
async def retry_download_job(
    job_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """重试失败的下载任务"""
    user_id = get_current_user_id()
    
    result = await session.execute(
        select(MusicDownloadJob).where(
            and_(
                MusicDownloadJob.id == job_id,
                MusicDownloadJob.user_id == user_id
            )
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if job.status not in ["failed", "not_found"]:
        raise HTTPException(status_code=400, detail="只能重试失败的任务")
    
    if job.retry_count >= job.max_retries:
        raise HTTPException(status_code=400, detail="已达到最大重试次数")
    
    # 重置状态为 pending，等待下次调度
    job.status = "pending"
    job.last_error = None
    job.retry_count += 1
    await session.commit()
    
    return success_response(message="任务已重新排队")


@router.post("/jobs/{job_id}/skip", summary="跳过任务")
async def skip_download_job(
    job_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """跳过下载任务"""
    user_id = get_current_user_id()
    
    result = await session.execute(
        select(MusicDownloadJob).where(
            and_(
                MusicDownloadJob.id == job_id,
                MusicDownloadJob.user_id == user_id
            )
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    job.status = "skipped_duplicate"
    job.last_error = "用户手动跳过"
    await session.commit()
    
    return success_response(message="任务已跳过")


@router.get("/{subscription_id}/coverage", summary="获取订阅覆盖统计")
async def get_subscription_coverage(
    subscription_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """获取订阅的榜单覆盖统计"""
    user_id = get_current_user_id()
    
    from app.models.music_chart_item import MusicChartItem
    from app.schemas.music import SubscriptionCoverageStats
    
    # 验证订阅存在
    sub_result = await session.execute(
        select(UserMusicSubscription).where(
            and_(
                UserMusicSubscription.id == subscription_id,
                UserMusicSubscription.user_id == user_id
            )
        )
    )
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")
    
    # 统计榜单条目总数
    total_result = await session.execute(
        select(func.count(MusicChartItem.id)).where(
            MusicChartItem.chart_id == subscription.chart_id
        )
    )
    total_items = total_result.scalar() or 0
    
    # 统计各状态的任务数
    jobs_result = await session.execute(
        select(MusicDownloadJob.status, func.count(MusicDownloadJob.id)).where(
            MusicDownloadJob.subscription_id == subscription_id
        ).group_by(MusicDownloadJob.status)
    )
    status_counts = {row[0]: row[1] for row in jobs_result.all()}
    
    ready_count = status_counts.get("completed", 0)
    downloading_count = status_counts.get("downloading", 0) + status_counts.get("importing", 0)
    queued_count = status_counts.get("found", 0) + status_counts.get("submitted", 0) + status_counts.get("pending", 0)
    failed_count = status_counts.get("failed", 0) + status_counts.get("not_found", 0)
    
    # 未处理的 = 总数 - 已有任务的
    processed_items = sum(status_counts.values())
    not_queued_count = max(0, total_items - processed_items)
    
    return success_response(
        data=SubscriptionCoverageStats(
            subscription_id=subscription_id,
            chart_id=subscription.chart_id,
            total_items=total_items,
            ready_count=ready_count,
            downloading_count=downloading_count,
            queued_count=queued_count,
            not_queued_count=not_queued_count,
            failed_count=failed_count,
        )
    )


@router.post("/run_all", summary="批量运行所有激活订阅", response_model=None)
async def run_all_subscriptions(
    only_active: bool = Query(True, description="仅运行激活状态的订阅"),
    limit: int = Query(20, ge=1, le=100, description="单次最多运行的订阅数量"),
    dry_run: bool = Query(False, description="试运行模式（仅统计，不创建任务）"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    批量运行音乐订阅（MUSIC-AUTOLOOP-2 新增功能）
    
    支持批量检查多个激活的订阅，返回汇总统计信息
    """
    user_id = get_current_user_id()
    
    try:
        # 查询符合条件的订阅
        query = select(UserMusicSubscription).where(
            UserMusicSubscription.user_id == user_id
        )
        
        if only_active:
            query = query.where(UserMusicSubscription.status == "active")
        
        query = query.order_by(
            UserMusicSubscription.last_run_at.asc().nullslast()
        ).limit(limit)
        
        subscriptions_result = await session.execute(query)
        subscriptions = list(subscriptions_result.scalars().all())
        
        if not subscriptions:
            return success_response(
                data={
                    "total_subscriptions": 0,
                    "runs": [],
                    "summary": {
                        "found_total": 0,
                        "filtered_total": {},
                        "created_tasks_total": 0,
                        "succeeded_checks": 0,
                        "failed_checks": 0,
                    }
                },
                message="没有找到需要运行的订阅"
            )
        
        # 批量处理订阅
        from app.services.music_subscription_service import run_subscription_once
        
        runs = []
        total_found = 0
        total_filtered = {}
        total_created_tasks = 0
        succeeded_checks = 0
        failed_checks = 0
        
        for subscription in subscriptions:
            try:
                run_result = await run_subscription_once(
                    session,
                    subscription,
                    auto_download=not dry_run
                )
                
                # 构建单个订阅的响应
                run_response = MusicSubscriptionRunResponse(
                    subscription_id=run_result.subscription_id,
                    found_total=run_result.found_total,
                    filtered_out=run_result.filtered_out,
                    skipped_existing=run_result.skipped_existing,
                    created_tasks=run_result.created_tasks,
                    errors=run_result.errors,
                )
                
                runs.append(run_response.model_dump())
                
                # 累计统计
                total_found += run_result.found_total
                total_created_tasks += run_result.created_tasks
                
                if run_result.errors:
                    failed_checks += 1
                else:
                    succeeded_checks += 1
                
                # 累计过滤统计
                for filter_type, count in run_result.filtered_out.items():
                    total_filtered[filter_type] = total_filtered.get(filter_type, 0) + count
                
            except Exception as e:
                logger.error(f"批量运行订阅 {subscription.id} 失败: {e}")
                failed_checks += 1
                
                # 添加失败记录
                error_response = MusicSubscriptionRunResponse(
                    subscription_id=subscription.id,
                    found_total=0,
                    filtered_out={},
                    skipped_existing=0,
                    created_tasks=0,
                    errors=[str(e)],
                )
                runs.append(error_response.model_dump())
        
        # 构建汇总响应
        response_data = MusicSubscriptionBatchRunResponse(
            total_subscriptions=len(subscriptions),
            runs=runs,
            summary={
                "found_total": total_found,
                "filtered_total": total_filtered,
                "created_tasks_total": total_created_tasks,
                "succeeded_checks": succeeded_checks,
                "failed_checks": failed_checks,
            }
        )
        
        # 构建消息
        mode_text = "试运行" if dry_run else "批量运行"
        message = f"{mode_text}完成：共检查 {len(subscriptions)} 个订阅"
        
        if total_found > 0:
            message += f"，找到 {total_found} 条候选"
        
        if total_filtered:
            filtered_total = sum(total_filtered.values())
            message += f"，过滤 {filtered_total} 条"
        
        if not dry_run and total_created_tasks > 0:
            message += f"，创建任务 {total_created_tasks} 个"
        
        message += f"，成功 {succeeded_checks} 个，失败 {failed_checks} 个"
        
        return success_response(
            data=response_data.model_dump(),
            message=message
        )
        
    except Exception as e:
        logger.error(f"批量运行音乐订阅失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量运行失败: {str(e)}")
