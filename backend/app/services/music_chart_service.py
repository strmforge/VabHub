"""
音乐榜单服务

提供榜单抓取、同步和管理功能。
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger

from app.models.music_chart_source import MusicChartSource
from app.models.music_chart import MusicChart
from app.models.music_chart_item import MusicChartItem
from app.modules.music_charts.factory import get_chart_fetcher
from app.modules.music_charts.base import MusicChartItemPayload


async def fetch_chart_items_for_chart(
    session: AsyncSession,
    chart_id: int,
) -> Dict[str, Any]:
    """
    拉取单个榜单的最新条目并同步到数据库
    
    Args:
        session: 数据库会话
        chart_id: 榜单 ID
        
    Returns:
        同步结果，包含新增/更新数量
    """
    # 查询榜单和源
    result = await session.execute(
        select(MusicChart, MusicChartSource).join(
            MusicChartSource, MusicChart.source_id == MusicChartSource.id
        ).where(MusicChart.id == chart_id)
    )
    row = result.first()
    
    if not row:
        raise ValueError(f"榜单不存在: {chart_id}")
    
    chart, source = row
    
    # 获取抓取器
    fetcher = get_chart_fetcher(source)
    
    # 抓取数据
    logger.info(f"开始抓取榜单: {chart.display_name} (source={source.platform})")
    fetch_result = await fetcher.fetch_chart_items(chart)
    
    if not fetch_result.success:
        logger.error(f"榜单抓取失败: {fetch_result.error_message}")
        return {
            "success": False,
            "error": fetch_result.error_message,
            "new_count": 0,
            "updated_count": 0,
        }
    
    # 生成批次 ID
    batch_id = str(uuid.uuid4())
    
    # 同步到数据库
    new_count = 0
    updated_count = 0
    
    for item_payload in fetch_result.items:
        # 生成去重哈希
        hash_key = MusicChartItem.generate_hash_key(
            item_payload.title,
            item_payload.artist_name
        )
        
        # 查找是否已存在
        existing_result = await session.execute(
            select(MusicChartItem).where(
                and_(
                    MusicChartItem.chart_id == chart_id,
                    MusicChartItem.hash_key == hash_key
                )
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # 更新已存在的条目
            existing.rank = item_payload.rank
            existing.last_seen_at = datetime.utcnow()
            existing.batch_id = batch_id
            if item_payload.cover_url:
                existing.cover_url = item_payload.cover_url
            if item_payload.external_url:
                existing.external_url = item_payload.external_url
            if item_payload.duration_seconds:
                existing.duration_seconds = item_payload.duration_seconds
            if item_payload.external_ids:
                existing.external_ids = item_payload.external_ids
            updated_count += 1
        else:
            # 创建新条目
            new_item = MusicChartItem(
                chart_id=chart_id,
                rank=item_payload.rank,
                title=item_payload.title,
                artist_name=item_payload.artist_name,
                album_name=item_payload.album_name,
                external_ids=item_payload.external_ids,
                duration_seconds=item_payload.duration_seconds,
                cover_url=item_payload.cover_url,
                external_url=item_payload.external_url,
                hash_key=hash_key,
                batch_id=batch_id,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
            )
            session.add(new_item)
            new_count += 1
    
    # 更新榜单的最后抓取时间
    chart.last_fetched_at = datetime.utcnow()
    
    await session.commit()
    
    logger.info(f"榜单同步完成: {chart.display_name}, 新增={new_count}, 更新={updated_count}")
    
    return {
        "success": True,
        "chart_id": chart_id,
        "chart_name": chart.display_name,
        "new_count": new_count,
        "updated_count": updated_count,
        "total_fetched": len(fetch_result.items),
        "batch_id": batch_id,
    }


async def sync_all_enabled_charts(
    session: AsyncSession,
    *,
    source_id: Optional[int] = None,
    limit_per_run: Optional[int] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    批量同步启用的榜单
    
    Args:
        session: 数据库会话
        source_id: 只同步指定源的榜单（可选）
        limit_per_run: 单次最多同步的榜单数（可选）
        force: 是否强制同步（忽略抓取间隔）
        
    Returns:
        同步结果统计
    """
    # 构建查询
    query = select(MusicChart).where(MusicChart.is_enabled == True)
    
    if source_id:
        query = query.where(MusicChart.source_id == source_id)
    
    if not force:
        # 只同步需要更新的榜单（超过抓取间隔）
        now = datetime.utcnow()
        query = query.where(
            (MusicChart.last_fetched_at == None) |
            (MusicChart.last_fetched_at < now - timedelta(minutes=1))  # 临时使用 1 分钟，实际应该用 fetch_interval_minutes
        )
    
    # 按最后抓取时间排序（优先同步最久未更新的）
    query = query.order_by(MusicChart.last_fetched_at.asc().nullsfirst())
    
    if limit_per_run:
        query = query.limit(limit_per_run)
    
    result = await session.execute(query)
    charts = result.scalars().all()
    
    stats = {
        "total_charts": len(charts),
        "success_count": 0,
        "failed_count": 0,
        "total_new_items": 0,
        "total_updated_items": 0,
        "errors": [],
    }
    
    for chart in charts:
        try:
            sync_result = await fetch_chart_items_for_chart(session, chart.id)
            
            if sync_result.get("success"):
                stats["success_count"] += 1
                stats["total_new_items"] += sync_result.get("new_count", 0)
                stats["total_updated_items"] += sync_result.get("updated_count", 0)
            else:
                stats["failed_count"] += 1
                stats["errors"].append({
                    "chart_id": chart.id,
                    "chart_name": chart.display_name,
                    "error": sync_result.get("error"),
                })
        except Exception as e:
            logger.error(f"同步榜单失败 {chart.id}: {e}")
            stats["failed_count"] += 1
            stats["errors"].append({
                "chart_id": chart.id,
                "chart_name": chart.display_name,
                "error": str(e),
            })
    
    return stats


async def get_recent_chart_items(
    session: AsyncSession,
    chart_id: int,
    *,
    hours: int = 24,
    limit: int = 50,
) -> List[MusicChartItem]:
    """
    获取榜单中最近新增的条目
    
    Args:
        session: 数据库会话
        chart_id: 榜单 ID
        hours: 时间范围（小时）
        limit: 最大返回数量
        
    Returns:
        最近新增的条目列表
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    result = await session.execute(
        select(MusicChartItem).where(
            and_(
                MusicChartItem.chart_id == chart_id,
                MusicChartItem.first_seen_at >= since
            )
        ).order_by(MusicChartItem.first_seen_at.desc()).limit(limit)
    )
    
    return list(result.scalars().all())


async def get_unprocessed_chart_items(
    session: AsyncSession,
    chart_id: int,
    *,
    processed_item_ids: Optional[List[int]] = None,
    limit: int = 50,
) -> List[MusicChartItem]:
    """
    获取榜单中未处理的条目
    
    Args:
        session: 数据库会话
        chart_id: 榜单 ID
        processed_item_ids: 已处理的条目 ID 列表
        limit: 最大返回数量
        
    Returns:
        未处理的条目列表
    """
    query = select(MusicChartItem).where(MusicChartItem.chart_id == chart_id)
    
    if processed_item_ids:
        query = query.where(~MusicChartItem.id.in_(processed_item_ids))
    
    query = query.order_by(MusicChartItem.rank.asc().nullslast()).limit(limit)
    
    result = await session.execute(query)
    return list(result.scalars().all())
