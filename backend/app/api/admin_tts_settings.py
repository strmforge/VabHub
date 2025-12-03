"""
TTS 设置管理 API（只读）

提供 TTS 子系统配置、健康状态、限流信息和使用统计的只读总览。
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from pathlib import Path
from app.schemas.tts import (
    TTSSettingsResponse, 
    TTSRateLimitInfo, 
    TTSUsageStats,
    TTSVoicePresetUsage,
    TTSWorkProfileSummary,
    TTSStorageOverviewSummary
)
from app.api.smart_health import get_tts_health
from app.models.audiobook import AudiobookFile
from app.models.ebook import EBook
from app.models.tts_work_profile import TTSWorkProfile
from app.models.tts_voice_preset import TTSVoicePreset

router = APIRouter()


def classify_preset_heat(
    bound_works_count: int,
    tts_generated_works_count: int,
    last_used_at: Optional[datetime],
    usage_ratio: float
) -> Tuple[str, bool, bool, bool]:
    """
    根据预设使用情况分类热度
    
    Args:
        bound_works_count: 绑定作品数
        tts_generated_works_count: 已生成 TTS 作品数
        last_used_at: 最近使用时间
        usage_ratio: 使用比例（生成/绑定）
    
    Returns:
        Tuple[heat_level, is_hot, is_sleeping, is_cold]
    """
    now = datetime.utcnow()
    days_since_last_used = None
    if last_used_at:
        days_since_last_used = (now - last_used_at).days
    
    # 热门：绑定 >= 10 且 usage_ratio >= 0.6 且 最近 30 天有使用
    is_hot = (
        bound_works_count >= 10
        and usage_ratio >= 0.6
        and days_since_last_used is not None
        and days_since_last_used <= 30
    )
    
    # 沉睡：绑定 > 0 且 最近 30 天无使用
    is_sleeping = (
        bound_works_count > 0
        and (last_used_at is None or days_since_last_used is None or days_since_last_used > 30)
    )
    
    # 冷门：绑定 <= 2 且 tts_generated_works_count <= 1
    is_cold = (
        bound_works_count <= 2
        and tts_generated_works_count <= 1
    )
    
    # 确定主状态（优先级：hot > sleeping > cold > normal）
    if is_hot:
        heat_level = "hot"
    elif is_sleeping:
        heat_level = "sleeping"
    elif is_cold:
        heat_level = "cold"
    else:
        heat_level = "normal"
    
    return heat_level, is_hot, is_sleeping, is_cold


async def _compute_work_profile_summary(db: AsyncSession) -> TTSWorkProfileSummary:
    """
    计算作品 Profile 总览统计
    
    Args:
        db: 数据库会话
    
    Returns:
        TTSWorkProfileSummary: 作品 Profile 总览
    """
    try:
        # 总作品数
        works_total_result = await db.execute(select(func.count(EBook.id)))
        works_total = works_total_result.scalar() or 0
        
        # 有 Profile 的作品数
        works_with_profile_result = await db.execute(
            select(func.count(func.distinct(TTSWorkProfile.ebook_id)))
        )
        works_with_profile = works_with_profile_result.scalar() or 0
        
        # 有 preset_id 的作品数
        works_with_preset_result = await db.execute(
            select(func.count(func.distinct(TTSWorkProfile.ebook_id)))
            .where(TTSWorkProfile.preset_id.isnot(None))
        )
        works_with_preset = works_with_preset_result.scalar() or 0
        
        # 计算派生值
        works_without_profile = works_total - works_with_profile
        works_without_preset = works_with_profile - works_with_preset
        
        return TTSWorkProfileSummary(
            works_total=works_total,
            works_with_profile=works_with_profile,
            works_without_profile=works_without_profile,
            works_with_preset=works_with_preset,
            works_without_preset=works_without_preset
        )
    except Exception as e:
        logger.error(f"计算作品 Profile 总览失败: {e}", exc_info=True)
        return TTSWorkProfileSummary()


async def _compute_preset_usage(db: AsyncSession) -> List[TTSVoicePresetUsage]:
    """
    计算声线预设使用情况
    
    Args:
        db: 数据库会话
    
    Returns:
        List[TTSVoicePresetUsage]: 预设使用情况列表
    """
    try:
        # 1. 查出所有 preset
        presets_result = await db.execute(select(TTSVoicePreset))
        presets = presets_result.scalars().all()
        
        if not presets:
            return []
        
        # 2. 按 preset_id 聚合作品数量
        bound_counts_result = await db.execute(
            select(
                TTSWorkProfile.preset_id,
                func.count(func.distinct(TTSWorkProfile.ebook_id)).label("cnt")
            )
            .where(TTSWorkProfile.preset_id.isnot(None))
            .group_by(TTSWorkProfile.preset_id)
        )
        bound_counts = {row.preset_id: row.cnt for row in bound_counts_result.all()}
        
        # 3. 按 preset_id 聚合"已生成 TTS 的作品数" & last_used_at
        tts_stats_result = await db.execute(
            select(
                TTSWorkProfile.preset_id,
                func.count(func.distinct(AudiobookFile.ebook_id)).label("cnt"),
                func.max(AudiobookFile.created_at).label("last_used_at")
            )
            .join(
                AudiobookFile,
                AudiobookFile.ebook_id == TTSWorkProfile.ebook_id
            )
            .where(
                TTSWorkProfile.preset_id.isnot(None),
                AudiobookFile.is_tts_generated == True
            )
            .group_by(TTSWorkProfile.preset_id)
        )
        
        tts_counts = {}
        last_used_map = {}
        for row in tts_stats_result.all():
            preset_id = row.preset_id
            tts_counts[preset_id] = row.cnt or 0
            last_used_map[preset_id] = row.last_used_at
        
        # 4. 组装 TTSVoicePresetUsage 列表并计算热度
        usages: List[TTSVoicePresetUsage] = []
        for preset in presets:
            pid = preset.id
            bound_count = bound_counts.get(pid, 0)
            tts_count = tts_counts.get(pid, 0)
            last_used = last_used_map.get(pid)
            
            # 计算使用比例
            usage_ratio = 0.0
            if bound_count > 0:
                usage_ratio = tts_count / bound_count
                # 确保不超过 1.0（理论上不应该，但防御性编程）
                usage_ratio = min(usage_ratio, 1.0)
            
            # 计算热度
            heat_level, is_hot, is_sleeping, is_cold = classify_preset_heat(
                bound_works_count=bound_count,
                tts_generated_works_count=tts_count,
                last_used_at=last_used,
                usage_ratio=usage_ratio
            )
            
            usages.append(
                TTSVoicePresetUsage(
                    id=pid,
                    name=preset.name,
                    provider=preset.provider,
                    language=preset.language,
                    voice=preset.voice,
                    is_default=bool(getattr(preset, "is_default", False)),
                    bound_works_count=bound_count,
                    tts_generated_works_count=tts_count,
                    last_used_at=last_used,
                    usage_ratio=usage_ratio,
                    heat_level=heat_level,
                    is_hot=is_hot,
                    is_sleeping=is_sleeping,
                    is_cold=is_cold
                )
            )
        
        return usages
    except Exception as e:
        logger.error(f"计算预设使用情况失败: {e}", exc_info=True)
        return []


async def get_tts_usage_stats(db: AsyncSession) -> TTSUsageStats:
    """
    从数据库统计 TTS 生成的有声书文件
    
    Args:
        db: 数据库会话
    
    Returns:
        TTSUsageStats: 包含总数和按 provider 分布的统计
    """
    try:
        # 查询 is_tts_generated=True 的总数
        total_query = select(func.count(AudiobookFile.id)).where(
            AudiobookFile.is_tts_generated == True
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar() or 0
        
        # 按 provider 分组统计
        provider_query = select(
            AudiobookFile.tts_provider,
            func.count(AudiobookFile.id).label("count")
        ).where(
            AudiobookFile.is_tts_generated == True
        ).group_by(AudiobookFile.tts_provider)
        
        provider_result = await db.execute(provider_query)
        provider_rows = provider_result.all()
        
        # 构建 by_provider 字典
        by_provider: Dict[str, int] = {}
        for row in provider_rows:
            provider = row.tts_provider or "unknown"
            count = row.count or 0
            by_provider[provider] = count
        
        return TTSUsageStats(
            total_tts_audiobooks=total_count,
            by_provider=by_provider
        )
    except Exception as e:
        logger.error(f"获取 TTS 使用统计失败: {e}", exc_info=True)
        # 出错时返回空统计
        return TTSUsageStats(
            total_tts_audiobooks=0,
            by_provider={}
        )


@router.get("/", response_model=TTSSettingsResponse, summary="获取 TTS 设置总览（只读）")
async def get_tts_settings(
    db: AsyncSession = Depends(get_db)
) -> TTSSettingsResponse:
    """
    获取 TTS 子系统的只读总览
    
    返回当前配置、健康状态、限流信息和数据库中的使用统计。
    此接口为只读，不提供修改功能。
    
    Returns:
        TTSSettingsResponse: 包含 TTS 配置、健康状态、限流信息和使用统计
    """
    try:
        # 1. 获取健康状态（复用 smart_health 的逻辑）
        tts_health = await get_tts_health(settings, db)
        
        # 2. 获取限流信息
        rate_limit_enabled = bool(getattr(settings, 'SMART_TTS_RATE_LIMIT_ENABLED', False))
        rate_limit_info: Optional[TTSRateLimitInfo] = None
        
        if rate_limit_enabled:
            try:
                from app.modules.tts.rate_limiter import get_state as get_rate_limit_state
                rate_state = get_rate_limit_state()
                
                rate_limit_info = TTSRateLimitInfo(
                    max_daily_requests=getattr(settings, 'SMART_TTS_MAX_DAILY_REQUESTS', 0),
                    max_daily_characters=getattr(settings, 'SMART_TTS_MAX_DAILY_CHARACTERS', 0),
                    max_requests_per_run=getattr(settings, 'SMART_TTS_MAX_REQUESTS_PER_RUN', 0),
                    last_limited_at=rate_state.last_limited_at,
                    last_limited_reason=rate_state.last_limited_reason
                )
            except Exception as e:
                logger.warning(f"获取 TTS 限流状态失败: {e}")
                # 即使获取状态失败，也返回配置信息
                rate_limit_info = TTSRateLimitInfo(
                    max_daily_requests=getattr(settings, 'SMART_TTS_MAX_DAILY_REQUESTS', 0),
                    max_daily_characters=getattr(settings, 'SMART_TTS_MAX_DAILY_CHARACTERS', 0),
                    max_requests_per_run=getattr(settings, 'SMART_TTS_MAX_REQUESTS_PER_RUN', 0),
                    last_limited_at=None,
                    last_limited_reason=None
                )
        
        # 3. 获取使用统计
        usage_stats = await get_tts_usage_stats(db)
        
        # 4. 获取预设使用统计和作品 Profile 总览
        preset_usage = await _compute_preset_usage(db)
        work_profile_summary = await _compute_work_profile_summary(db)
        
        # 5. 获取存储概览
        storage_overview: Optional[TTSStorageOverviewSummary] = None
        try:
            from app.modules.tts.storage_service import scan_storage, build_overview
            
            root = Path(settings.SMART_TTS_OUTPUT_ROOT)
            if not root.exists():
                storage_overview = TTSStorageOverviewSummary(
                    root=str(root),
                    total_files=0,
                    total_size_bytes=0,
                    warning="no_root",
                )
            else:
                # 扫描并构建概览
                files = scan_storage(root, max_files=None)
                overview = build_overview(files, root)
                
                total_size_bytes = overview.total_size_bytes or 0
                total_files = overview.total_files
                
                # 基于阈值计算 warning
                size_gb = total_size_bytes / (1024**3) if total_size_bytes else 0
                warn_threshold = getattr(settings, 'SMART_TTS_STORAGE_WARN_SIZE_GB', 10.0)
                critical_threshold = getattr(settings, 'SMART_TTS_STORAGE_CRITICAL_SIZE_GB', 30.0)
                
                if size_gb >= critical_threshold:
                    warning = "critical"
                elif size_gb >= warn_threshold:
                    warning = "high_usage"
                else:
                    warning = "ok"
                
                storage_overview = TTSStorageOverviewSummary(
                    root=str(root),
                    total_files=total_files,
                    total_size_bytes=total_size_bytes,
                    warning=warning,
                )
        except Exception as exc:
            logger.warning(f"获取 TTS 存储概览失败: {exc}")
            storage_overview = TTSStorageOverviewSummary(
                root=str(settings.SMART_TTS_OUTPUT_ROOT),
                total_files=0,
                total_size_bytes=0,
                warning="scan_error",
            )
        
        # 6. 构建响应
        # 处理 last_used_at（从 ISO 字符串转换为 datetime）
        last_used_at = None
        if tts_health.get("last_used_at"):
            try:
                from datetime import datetime
                last_used_at = datetime.fromisoformat(tts_health["last_used_at"].replace('Z', '+00:00'))
            except Exception:
                pass
        
        return TTSSettingsResponse(
            enabled=tts_health["enabled"],
            provider=tts_health["provider"],
            status=tts_health["status"],
            output_root=tts_health.get("output_root"),
            max_chapters=tts_health.get("max_chapters"),
            strategy=tts_health.get("strategy"),
            last_used_at=last_used_at,
            last_error=tts_health.get("last_error"),
            rate_limit_enabled=rate_limit_enabled,
            rate_limit_info=rate_limit_info,
            usage_stats=usage_stats,
            preset_usage=preset_usage,
            work_profile_summary=work_profile_summary,
            storage_overview=storage_overview
        )
        
    except Exception as e:
        logger.error(f"获取 TTS 设置失败: {e}", exc_info=True)
        # 即使出错，也返回基本结构（使用默认值）
        return TTSSettingsResponse(
            enabled=False,
            provider="dummy",
            status="disabled",
            output_root=None,
            max_chapters=None,
            strategy=None,
            last_used_at=None,
            last_error=None,
            rate_limit_enabled=False,
            rate_limit_info=None,
            usage_stats=TTSUsageStats(
                total_tts_audiobooks=0,
                by_provider={}
            ),
            preset_usage=[],
            work_profile_summary=None,
            storage_overview=None
        )

