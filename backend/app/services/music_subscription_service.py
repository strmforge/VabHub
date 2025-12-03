"""
音乐订阅服务

处理用户订阅的自动搜索和下载逻辑。
Phase 3 升级：集成 External Indexer 进行真实 PT 搜索。
MUSIC-SUBS-1 扩展：支持关键字订阅。
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger

from app.models.user_music_subscription import UserMusicSubscription, MusicSubscriptionType
from app.services.download_search_service import SafeDownloadCandidate
from app.models.music_chart_item import MusicChartItem
from app.models.music_download_job import MusicDownloadJob, MusicDownloadJobSource
from app.models.user import User
from app.schemas.music import SubscriptionRunResult, UserMusicSubscriptionCreate, MusicAutoLoopResult
from app.services.music_indexer_service import get_music_indexer_service, MusicTorrentCandidate


async def run_subscription_once(
    session: AsyncSession,
    subscription: UserMusicSubscription,
    *,
    auto_download: bool = True,
) -> MusicAutoLoopResult:
    """
    运行一次订阅任务（MUSIC-AUTOLOOP-2 扩展版本）
    
    支持两种订阅类型：
    1. CHART类型：检测榜单新增曲目并搜索下载
    2. KEYWORD类型：根据关键字搜索新资源
    
    Args:
        session: 数据库会话
        subscription: 用户订阅
        auto_download: 是否实际创建下载任务（False=仅统计）
        
    Returns:
        MusicAutoLoopResult: 详细运行结果统计
    """
    # 根据订阅类型分支处理
    if subscription.subscription_type == MusicSubscriptionType.KEYWORD:
        return await check_keyword_subscription(session, subscription, auto_download=auto_download)
    elif subscription.subscription_type == MusicSubscriptionType.CHART:
        return await _run_chart_subscription_once(session, subscription, auto_download=auto_download)
    else:
        result = MusicAutoLoopResult(
            subscription_id=subscription.id,
            errors=[f"不支持的订阅类型: {subscription.subscription_type}"],
        )
        return result


async def _run_chart_subscription_once(
    session: AsyncSession,
    subscription: UserMusicSubscription,
    *,
    auto_download: bool = True,
) -> MusicAutoLoopResult:
    """
    运行一次榜单订阅任务（MUSIC-AUTOLOOP-2 扩展版本）
    
    流程：
    1. 找到该订阅对应的 MusicChart
    2. 找出近期新增的 MusicChartItem（未处理过的）
    3. 最多取 max_new_tracks_per_run 首
    4. 为每首曲目调用 PT 搜索
    5. 应用安全策略过滤
    6. 检查去重并创建 MusicDownloadJob 记录
    
    Args:
        session: 数据库会话
        subscription: 用户订阅
        auto_download: 是否实际创建下载任务（False=仅统计）
        
    Returns:
        MusicAutoLoopResult: 详细运行结果统计
    """
    result = MusicAutoLoopResult(
        subscription_id=subscription.id,
        filtered_out={
            "hr": 0,
            "h3h5": 0,
            "non_free": 0,
            "duplicate": 0,
        }
    )
    
    # 获取榜单
    chart_result = await session.execute(
        select(MusicChart).where(MusicChart.id == subscription.chart_id)
    )
    chart = chart_result.scalar_one_or_none()
    
    if not chart:
        result.errors.append("榜单不存在")
        return result
    
    # 获取已处理的条目 ID（排除已有 Job 的条目）
    processed_result = await session.execute(
        select(MusicDownloadJob.chart_item_id).where(
            and_(
                MusicDownloadJob.subscription_id == subscription.id,
                MusicDownloadJob.chart_item_id != None
            )
        )
    )
    processed_item_ids = [row[0] for row in processed_result.all()]
    
    # 获取未处理的新条目
    items_query = select(MusicChartItem).where(
        and_(
            MusicChartItem.chart_id == chart.id,
            ~MusicChartItem.id.in_(processed_item_ids) if processed_item_ids else True
        )
    ).order_by(MusicChartItem.rank.asc().nullslast()).limit(subscription.max_new_tracks_per_run)
    
    items_result = await session.execute(items_query)
    new_items = list(items_result.scalars().all())
    
    result.new_items_count = len(new_items)
    
    if not new_items:
        logger.info(f"订阅 {subscription.id} 没有新曲目需要处理")
        subscription.last_run_at = datetime.utcnow()
        subscription.last_run_new_count = 0
        subscription.last_run_search_count = 0
        subscription.last_run_download_count = 0
        await session.commit()
        return result
    
    # 解析优先站点
    preferred_sites = None
    if subscription.preferred_sites:
        preferred_sites = [s.strip() for s in subscription.preferred_sites.split(",") if s.strip()]
    
    # 获取搜索服务
    indexer_service = get_music_indexer_service()
    
    # 处理每个新条目
    for item in new_items:
        try:
            # 生成搜索关键词
            search_query = f"{item.artist_name} - {item.title}"
            
            # 创建下载任务记录
            job = MusicDownloadJob(
                subscription_id=subscription.id,
                chart_item_id=item.id,
                user_id=subscription.user_id,
                search_query=search_query,
                status="pending",
            )
            session.add(job)
            await session.flush()  # 获取 job.id
            
            if subscription.auto_search:
                # 执行 PT 搜索
                job.status = "searching"
                job.started_at = datetime.utcnow()
                
                candidates = await indexer_service.search_for_chart_item(
                    session,
                    item,
                    sites=preferred_sites,
                    limit=10,
                )
                
                result.found_total += len(candidates)
                job.search_candidates_count = len(candidates)
                
                if candidates:
                    # 应用安全策略过滤
                    filtered_candidates = await _apply_security_filter(
                        candidates,
                        subscription,
                        result.filtered_out
                    )
                    
                    if filtered_candidates:
                        # 检查去重
                        final_candidates = await _deduplicate_candidates(
                            session,
                            filtered_candidates,
                            subscription.user_id
                        )
                        
                        result.skipped_existing += len(filtered_candidates) - len(final_candidates)
                        
                        if final_candidates:
                            # 选择最佳候选
                            best = final_candidates[0]
                            
                            # 根据质量偏好过滤
                            if subscription.quality_preference:
                                quality_filtered = _filter_by_quality_preference(
                                    final_candidates,
                                    subscription.quality_preference,
                                )
                                if quality_filtered:
                                    best = quality_filtered[0]
                            
                            # 更新 Job 信息
                            job.status = "found"
                            job.matched_site = best.site
                            job.matched_torrent_id = best.id
                            job.matched_torrent_name = best.title
                            job.matched_torrent_size_bytes = best.size_bytes
                            job.matched_seeders = best.seeders
                            job.matched_leechers = best.leechers
                            job.matched_free_percent = 100 if best.is_free else 50 if best.is_half_free else 0
                            job.quality_score = 0.8  # 默认质量分数
                            
                            result.created_tasks += 1
                            
                            logger.info(f"为订阅 {subscription.id} 找到匹配: {best.title}")
                        else:
                            job.status = "skipped_duplicate"
                            logger.info(f"订阅 {subscription.id} 所有候选都重复，跳过")
                    else:
                        job.status = "filtered_out"
                        logger.info(f"订阅 {subscription.id} 所有候选都被安全策略过滤")
                else:
                    job.status = "not_found"
                    logger.info(f"订阅 {subscription.id} 未找到搜索结果")
            
            # 更新订阅统计
            result.search_count += 1
            
        except Exception as e:
            logger.error(f"处理榜单条目 {item.id} 失败: {e}")
            result.errors.append(f"处理条目 {item.id}: {str(e)}")
            continue
    
    # 更新订阅状态
    subscription.last_run_at = datetime.utcnow()
    subscription.last_run_new_count = len(new_items)
    subscription.last_run_search_count = result.search_count
    subscription.last_run_download_count = result.created_tasks
    
    await session.commit()
    
    logger.info(f"榜单订阅 {subscription.id} 完成: 搜索={result.found_total}, "
                f"过滤={sum(result.filtered_out.values())}, "
                f"去重={result.skipped_existing}, "
                f"创建={result.created_tasks}")
    
    return result


def _filter_by_quality_preference(
    candidates: List[MusicTorrentCandidate],
    preference: str,
) -> List[MusicTorrentCandidate]:
    """
    根据质量偏好过滤候选
    
    Args:
        candidates: 候选种子列表
        preference: 质量偏好 (flac/mp3_320/any)
        
    Returns:
        过滤后的候选列表
    """
    if preference == "any":
        return candidates
    
    filtered = []
    for candidate in candidates:
        format_hint = candidate.format_hint or ""
        
        if preference == "flac" and "flac" in format_hint.lower():
            filtered.append(candidate)
        elif preference == "mp3_320" and (
            "mp3" in format_hint.lower() and 
            (candidate.bitrate_hint or 0) >= 320
        ):
            filtered.append(candidate)
        elif preference == "mp3" and "mp3" in format_hint.lower():
            filtered.append(candidate)
    
    return filtered if filtered else candidates  # 如果没有匹配的，返回原列表


async def _apply_security_filter(
    candidates: List[SafeDownloadCandidate],
    subscription: UserMusicSubscription,
    filtered_out: Dict[str, int],
) -> List[SafeDownloadCandidate]:
    """
    应用安全策略过滤（参考download_search_service.py模式）
    
    Args:
        candidates: 候选种子列表
        subscription: 订阅配置
        filtered_out: 过滤统计字典
        
    Returns:
        过滤后的候选列表
    """
    filtered_candidates = []
    
    for candidate in candidates:
        # 检查HR状态
        if not subscription.allow_hr and candidate.is_hr:
            filtered_out["hr"] += 1
            continue
        
        # 检查H3/H5状态（从标题检测）
        is_h3h5 = _detect_h3h5(candidate.title)
        if not subscription.allow_h3h5 and is_h3h5:
            filtered_out["h3h5"] += 1
            continue
        
        # 检查Free状态
        if subscription.strict_free_only and not (candidate.is_free or candidate.is_half_free):
            filtered_out["non_free"] += 1
            continue
        
        # 通过所有过滤条件
        filtered_candidates.append(candidate)
    
    return filtered_candidates


def _detect_h3h5(title: str) -> bool:
    """
    检测标题是否包含H3/H5标记
    
    Args:
        title: 种子标题
        
    Returns:
        是否为H3/H5
    """
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in ["h3", "h5", "hit and run"])


async def _deduplicate_candidates(
    session: AsyncSession,
    candidates: List[SafeDownloadCandidate],
    user_id: int,
) -> List[SafeDownloadCandidate]:
    """
    去重候选种子（基于已有任务）
    
    Args:
        session: 数据库会话
        candidates: 候选种子列表
        user_id: 用户ID
        
    Returns:
        去重后的候选列表
    """
    if not candidates:
        return []
    
    # 查询已存在的任务
    existing_tasks_result = await session.execute(
        select(MusicDownloadJob.matched_site, MusicDownloadJob.matched_torrent_id).where(
            and_(
                MusicDownloadJob.user_id == user_id,
                MusicDownloadJob.matched_site.in_([c.site for c in candidates]),
                MusicDownloadJob.matched_torrent_id.in_([c.id for c in candidates]),
                MusicDownloadJob.status.not_in_(['failed', 'cancelled'])  # 排除失败的任务
            )
        )
    )
    existing_tasks = set(existing_tasks_result.all())
    
    # 过滤已存在的任务
    deduplicated = []
    for candidate in candidates:
        task_key = (candidate.site, candidate.id)
        if task_key not in existing_tasks:
            deduplicated.append(candidate)
    
    return deduplicated


async def check_keyword_subscription(
    session: AsyncSession,
    subscription: UserMusicSubscription,
    *,
    auto_download: bool = True,
) -> MusicAutoLoopResult:
    """
    检查关键字订阅（MUSIC-AUTOLOOP-2 扩展版本）
    
    Args:
        session: 数据库会话
        subscription: 关键字订阅对象
        auto_download: 是否实际创建下载任务（False=仅统计）
        
    Returns:
        MusicAutoLoopResult: 详细运行结果统计
    """
    result = MusicAutoLoopResult(
        subscription_id=subscription.id,
        filtered_out={
            "hr": 0,
            "h3h5": 0,
            "non_free": 0,
            "duplicate": 0,
        }
    )
    
    if not subscription.music_query:
        result.errors.append("关键字订阅缺少搜索关键字")
        return result
    
    # 检查最近是否已搜索过相同关键字（避免重复搜索）
    recent_job_result = await session.execute(
        select(MusicDownloadJob).where(
            and_(
                MusicDownloadJob.subscription_id == subscription.id,
                MusicDownloadJob.search_query == subscription.music_query,
                MusicDownloadJob.created_at >= datetime.utcnow() - timedelta(hours=1)
            )
        ).order_by(MusicDownloadJob.created_at.desc()).limit(1)
    )
    recent_job = recent_job_result.scalar_one_or_none()
    
    if recent_job and recent_job.status not in ['failed', 'cancelled']:
        result.errors.append(f"关键字 '{subscription.music_query}' 在1小时内已搜索过")
        return result
    
    # 解析优先站点
    preferred_sites = None
    if subscription.preferred_sites:
        preferred_sites = [s.strip() for s in subscription.preferred_sites.split(",") if s.strip()]
    
    # 获取搜索服务
    indexer_service = get_music_indexer_service()
    
    try:
        # 执行关键字搜索
        candidates = await indexer_service.search_by_keyword(
            session,
            subscription.music_query,
            sites=preferred_sites or [subscription.music_site] if subscription.music_site else None,
            limit=20,
        )
        
        result.found_total = len(candidates)
        
        if candidates:
            # 应用安全策略过滤
            filtered_candidates = await _apply_security_filter(
                candidates,
                subscription,
                result.filtered_out
            )
            
            if filtered_candidates:
                # 检查去重
                final_candidates = await _deduplicate_candidates(
                    session,
                    filtered_candidates,
                    subscription.user_id
                )
                
                result.skipped_existing += len(filtered_candidates) - len(final_candidates)
                
                if final_candidates and auto_download:
                    # 限制每次运行创建的任务数量
                    MAX_TASKS_PER_RUN = 2
                    final_candidates = final_candidates[:MAX_TASKS_PER_RUN]
                    
                    # 为每个候选创建下载任务
                    for candidate in final_candidates:
                        job = MusicDownloadJob(
                            source_type=MusicDownloadJobSource.KEYWORD,
                            subscription_id=subscription.id,
                            user_id=subscription.user_id,
                            search_query=subscription.music_query,
                            status="found",
                            matched_site=candidate.source,
                            matched_torrent_id=candidate.torrent_id,
                            matched_torrent_name=candidate.title,
                            matched_torrent_size_bytes=candidate.size_bytes,
                            matched_seeders=candidate.seeders,
                            matched_leechers=candidate.leechers,
                            matched_free_percent=candidate.free_percent,
                            quality_score=candidate.quality_score,
                            search_candidates_count=len(candidates),
                            started_at=datetime.utcnow(),
                        )
                        session.add(job)
                        result.created_tasks += 1
                        
                        logger.info(f"关键字订阅 {subscription.id} 创建任务: {candidate.title}")
        
        # 更新订阅状态
        subscription.last_run_at = datetime.utcnow()
        subscription.last_run_new_count = result.created_tasks
        subscription.last_run_search_count = result.search_count
        subscription.last_run_download_count = result.created_tasks
        
        await session.commit()
        
        logger.info(f"关键字订阅 {subscription.id} 完成: 搜索={result.found_total}, "
                    f"过滤={sum(result.filtered_out.values())}, "
                    f"去重={result.skipped_existing}, "
                    f"创建={result.created_tasks}")
        
        return result
        
    except Exception as e:
        logger.error(f"关键字订阅 {subscription.id} 搜索失败: {e}")
        result.errors.append(f"搜索失败: {str(e)}")
        
        # 更新错误状态
        subscription.last_run_at = datetime.utcnow()
        subscription.last_run_new_count = 0
        subscription.last_run_search_count = 0
        subscription.last_run_download_count = 0
        
        await session.commit()
        return result


async def sync_all_active_subscriptions(
    session: AsyncSession,
    *,
    include_paused: bool = False,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    同步所有活跃订阅
    
    Args:
        session: 数据库会话
        include_paused: 是否包含暂停的订阅
        limit: 最大处理数量
        
    Returns:
        同步结果统计
    """
    query = select(UserMusicSubscription)
    
    if not include_paused:
        query = query.where(UserMusicSubscription.status == "active")
    
    # 按最后运行时间排序
    query = query.order_by(UserMusicSubscription.last_run_at.asc().nullsfirst())
    
    if limit:
        query = query.limit(limit)
    
    result = await session.execute(query)
    subscriptions = list(result.scalars().all())
    
    stats = {
        "total_subscriptions": len(subscriptions),
        "success_count": 0,
        "failed_count": 0,
        "total_new_items": 0,
        "total_searches": 0,
        "total_downloads": 0,
        "errors": [],
    }
    
    for subscription in subscriptions:
        try:
            run_result = await run_subscription_once(session, subscription)
            
            stats["success_count"] += 1
            stats["total_new_items"] += run_result.new_items_count
            stats["total_searches"] += run_result.search_count
            stats["total_downloads"] += run_result.download_count
            
            if run_result.errors:
                stats["errors"].extend(run_result.errors)
                
        except Exception as e:
            logger.error(f"处理订阅 {subscription.id} 失败: {e}")
            stats["failed_count"] += 1
            stats["errors"].append(f"订阅 {subscription.id}: {str(e)}")
    
    return stats


async def create_music_keyword_subscription(
    session: AsyncSession,
    user: User,
    music_query: str,
    *,
    music_site: Optional[str] = None,
    music_quality: Optional[str] = None,
    auto_search: bool = True,
    auto_download: bool = False,
    max_new_tracks_per_run: int = 10,
    quality_preference: Optional[str] = "flac",
    preferred_sites: Optional[str] = None,
) -> UserMusicSubscription:
    """
    创建音乐关键字订阅
    
    Args:
        session: 数据库会话
        user: 用户对象
        music_query: 搜索关键字
        music_site: 指定站点（可选）
        music_quality: 质量偏好（FLAC/MP3/320等）
        auto_search: 是否自动搜索
        auto_download: 是否自动下载
        max_new_tracks_per_run: 每次运行最大处理数
        quality_preference: 质量偏好
        preferred_sites: 优先站点
        
    Returns:
        创建的音乐订阅对象
        
    Raises:
        ValueError: 当关键字为空或已存在相同订阅时
    """
    # 验证关键字
    if not music_query or not music_query.strip():
        raise ValueError("搜索关键字不能为空")
    
    # 检查是否已存在相同的关键字订阅
    existing_result = await session.execute(
        select(UserMusicSubscription).where(
            and_(
                UserMusicSubscription.user_id == user.id,
                UserMusicSubscription.subscription_type == MusicSubscriptionType.KEYWORD,
                UserMusicSubscription.music_query == music_query.strip(),
                UserMusicSubscription.status == "active"
            )
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise ValueError(f"已存在相同关键字的订阅: {music_query}")
    
    # 创建订阅
    subscription = UserMusicSubscription(
        user_id=user.id,
        subscription_type=MusicSubscriptionType.KEYWORD,
        chart_id=None,  # 关键字订阅不需要榜单
        music_query=music_query.strip(),
        music_site=music_site,
        music_quality=music_quality,
        status="active",
        auto_search=auto_search,
        auto_download=auto_download,
        max_new_tracks_per_run=max_new_tracks_per_run,
        quality_preference=quality_preference,
        preferred_sites=preferred_sites,
    )
    
    session.add(subscription)
    await session.flush()
    
    logger.info(f"创建音乐关键字订阅成功: ID={subscription.id}, query={music_query}, user={user.id}")
    return subscription


async def check_keyword_subscription(
    session: AsyncSession,
    subscription: UserMusicSubscription,
    *,
    auto_download: bool = True,
) -> SubscriptionRunResult:
    """
    检查关键字订阅
    
    Args:
        session: 数据库会话
        subscription: 关键字订阅对象
        auto_download: 是否自动下载
        
    Returns:
        运行结果统计
    """
    result = SubscriptionRunResult(
        subscription_id=subscription.id,
        new_items_count=0,
        search_count=0,
        download_count=0,
        failed_count=0,
        errors=[],
    )
    
    if not subscription.music_query:
        result.errors.append("关键字订阅缺少搜索关键字")
        return result
    
    # 检查最近是否已搜索过相同关键字（避免重复搜索）
    recent_job_result = await session.execute(
        select(MusicDownloadJob).where(
            and_(
                MusicDownloadJob.subscription_id == subscription.id,
                MusicDownloadJob.source_type == MusicDownloadJobSource.KEYWORD,
                MusicDownloadJob.search_query == subscription.music_query,
                MusicDownloadJob.created_at >= datetime.utcnow() - timedelta(hours=6)  # 6小时内不重复搜索
            )
        ).order_by(MusicDownloadJob.created_at.desc())
    )
    recent_job = recent_job_result.scalar_one_or_none()
    
    if recent_job:
        logger.info(f"关键字订阅 {subscription.id} 6小时内已搜索过，跳过本次检查")
        return result
    
    # 解析优先站点
    preferred_sites = None
    if subscription.preferred_sites:
        preferred_sites = [s.strip() for s in subscription.preferred_sites.split(",") if s.strip()]
    
    # 如果指定了站点，优先使用指定站点
    search_sites = preferred_sites
    if subscription.music_site:
        search_sites = [subscription.music_site]
    
    # 获取搜索服务
    indexer_service = get_music_indexer_service()
    
    try:
        # 执行关键字搜索
        candidates = await indexer_service.search(
            query=subscription.music_query,
            sites=search_sites,
            limit=10,
        )
        
        result.search_count = len(candidates)
        
        if not candidates:
            logger.info(f"关键字订阅 {subscription.id} 未找到匹配资源")
            await _update_subscription_run_stats(session, subscription, 0, 0, 0)
            return result
        
        # 应用质量偏好过滤
        filtered_candidates = candidates
        if subscription.music_quality or subscription.quality_preference:
            quality_pref = subscription.music_quality or subscription.quality_preference
            filtered_candidates = _filter_by_quality_preference(candidates, quality_pref)
        
        # 应用安全策略过滤（HR/H3H5/Free）
        safe_candidates = _filter_by_safety_policy(candidates, subscription)
        
        if not safe_candidates:
            logger.info(f"关键字订阅 {subscription.id} 所有候选资源都被安全策略过滤")
            await _update_subscription_run_stats(session, subscription, len(candidates), 0, 0)
            return result
        
        # 选择最佳候选
        best_candidate = safe_candidates[0]
        
        # 创建下载任务记录
        job = MusicDownloadJob(
            source_type=MusicDownloadJobSource.KEYWORD,
            subscription_id=subscription.id,
            chart_item_id=None,  # 关键字订阅没有榜单条目
            user_id=subscription.user_id,
            search_query=subscription.music_query,
            status="found",
            matched_site=best_candidate.source,
            matched_torrent_id=best_candidate.torrent_id,
            matched_torrent_name=best_candidate.title,
            matched_torrent_size_bytes=best_candidate.size_bytes,
            matched_seeders=best_candidate.seeders,
            matched_leechers=best_candidate.leechers,
            matched_free_percent=best_candidate.free_percent,
            quality_score=best_candidate.quality_score,
            search_candidates_count=len(candidates),
        )
        
        session.add(job)
        await session.flush()
        
        result.download_count = 1
        
        # 如果启用自动下载，提交下载任务
        if auto_download and subscription.auto_download:
            job.status = "submitted"
            job.started_at = datetime.utcnow()
            # TODO: 调用下载服务提交任务
            logger.info(f"关键字订阅 {subscription.id} 已提交下载任务: {best_candidate.title}")
        
        await _update_subscription_run_stats(session, subscription, len(candidates), 1, 1)
        
        logger.info(f"关键字订阅 {subscription.id} 检查完成: 找到{len(candidates)}个候选，创建1个下载任务")
        
    except Exception as e:
        logger.error(f"关键字订阅 {subscription.id} 搜索失败: {e}")
        result.errors.append(f"搜索失败: {str(e)}")
        result.failed_count = 1
    
    return result


async def _update_subscription_run_stats(
    session: AsyncSession,
    subscription: UserMusicSubscription,
    new_items: int,
    search_count: int,
    download_count: int,
):
    """更新订阅运行统计"""
    subscription.last_run_at = datetime.utcnow()
    subscription.last_run_new_count = new_items
    subscription.last_run_search_count = search_count
    subscription.last_run_download_count = download_count
    await session.commit()


def _filter_by_quality_preference(
    candidates: List[MusicTorrentCandidate],
    quality_preference: str,
) -> List[MusicTorrentCandidate]:
    """根据质量偏好过滤候选资源"""
    if not quality_preference or quality_preference.lower() == "any":
        return candidates
    
    quality_lower = quality_preference.lower()
    filtered = []
    
    for candidate in candidates:
        # 检查格式提示
        if candidate.format_hint:
            if quality_lower in candidate.format_hint.lower():
                filtered.append(candidate)
                continue
        
        # 检查标题中的质量信息
        title_lower = candidate.title.lower()
        if quality_lower in title_lower:
            filtered.append(candidate)
            continue
        
        # 特殊处理一些常见质量标识
        if quality_lower == "flac" and "flac" in title_lower:
            filtered.append(candidate)
        elif quality_lower == "mp3" and ("mp3" in title_lower or "320" in title_lower):
            filtered.append(candidate)
        elif quality_lower == "320" and "320" in title_lower:
            filtered.append(candidate)
    
    return filtered if filtered else candidates  # 如果过滤后为空，返回原列表


def _filter_by_safety_policy(
    candidates: List[MusicTorrentCandidate],
    subscription: UserMusicSubscription,
) -> List[MusicTorrentCandidate]:
    """根据安全策略过滤候选资源"""
    filtered = []
    
    for candidate in candidates:
        # 检查HR策略
        if not subscription.allow_hr and candidate.is_hr:
            continue
        
        # 检查Free策略
        if subscription.strict_free_only and (not candidate.free_percent or candidate.free_percent < 100):
            continue
        
        # TODO: 添加H3H5策略检查（需要候选资源提供更多信息）
        
        filtered.append(candidate)
    
    return filtered
