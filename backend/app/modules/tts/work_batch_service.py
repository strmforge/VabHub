"""
TTS Work Batch Service

提供批量应用 TTS 声线预设到作品的服务
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import joinedload, aliased
from loguru import logger

from app.models.ebook import EBook
from app.models.tts_work_profile import TTSWorkProfile
from app.models.tts_voice_preset import TTSVoicePreset
from app.schemas.tts import (
    TTSWorkBatchFilter,
    TTSWorkBatchPreviewItem,
    ApplyTTSWorkPresetResult
)


async def preview_ebooks_for_preset_batch(
    db: AsyncSession,
    filter: TTSWorkBatchFilter,
    limit: int = 500,
) -> List[TTSWorkBatchPreviewItem]:
    """
    预览符合条件的 EBook 列表及其 TTS Profile 状态
    
    Args:
        db: 数据库会话
        filter: 筛选条件
        limit: 最大返回数量
    
    Returns:
        List[TTSWorkBatchPreviewItem]: 预览项列表
    """
    # 构建查询条件
    conditions = []
    
    if filter.language:
        conditions.append(EBook.language == filter.language)
    
    if filter.author_substring:
        conditions.append(EBook.author.ilike(f"%{filter.author_substring}%"))
    
    if filter.series_substring:
        conditions.append(EBook.series.ilike(f"%{filter.series_substring}%"))
    
    if filter.tag_keyword:
        conditions.append(EBook.tags.ilike(f"%{filter.tag_keyword}%"))
    
    if filter.created_from:
        conditions.append(EBook.created_at >= filter.created_from)
    
    if filter.created_to:
        conditions.append(EBook.created_at <= filter.created_to)
    
    # 构建查询：Left join TTSWorkProfile 和 TTSVoicePreset
    query = (
        select(
            EBook.id,
            EBook.title,
            EBook.author,
            EBook.series,
            EBook.language,
            EBook.created_at,
            TTSWorkProfile.id.label("profile_id"),
            TTSWorkProfile.enabled.label("profile_enabled"),
            TTSWorkProfile.preset_id,
            TTSVoicePreset.name.label("preset_name")
        )
        .outerjoin(TTSWorkProfile, EBook.id == TTSWorkProfile.ebook_id)
        .outerjoin(TTSVoicePreset, TTSWorkProfile.preset_id == TTSVoicePreset.id)
        .where(and_(*conditions) if conditions else True)
    )
    
    # 如果有 has_profile 条件，需要额外过滤
    if filter.has_profile is not None:
        if filter.has_profile:
            # 只返回有 Profile 的
            query = query.where(TTSWorkProfile.id.isnot(None))
        else:
            # 只返回没有 Profile 的
            query = query.where(TTSWorkProfile.id.is_(None))
    
    query = query.order_by(EBook.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # 转换为 PreviewItem
    items = []
    for row in rows:
        has_profile = row.profile_id is not None
        items.append(TTSWorkBatchPreviewItem(
            ebook_id=row.id,
            title=row.title,
            author=row.author,
            series=row.series,
            language=row.language,
            created_at=row.created_at,
            has_profile=has_profile,
            profile_enabled=row.profile_enabled if has_profile else None,
            profile_preset_id=row.preset_id if has_profile else None,
            profile_preset_name=row.preset_name if has_profile else None
        ))
    
    return items


async def apply_preset_to_ebooks(
    db: AsyncSession,
    preset_id: int,
    filter: TTSWorkBatchFilter,
    override_existing: bool,
    enable_profile: bool,
    dry_run: bool = False,
    max_items: int = 500,
) -> ApplyTTSWorkPresetResult:
    """
    批量应用预设到符合条件的 EBook
    
    Args:
        db: 数据库会话
        preset_id: 要应用的预设 ID
        filter: 筛选条件
        override_existing: 是否覆盖已有 Profile
        enable_profile: 是否启用 Profile
        dry_run: 是否仅统计不写入
        max_items: 最大处理数量
    
    Returns:
        ApplyTTSWorkPresetResult: 处理结果统计
    """
    # 验证预设存在
    preset_result = await db.execute(
        select(TTSVoicePreset)
        .where(TTSVoicePreset.id == preset_id)
    )
    preset = preset_result.scalar_one_or_none()
    if not preset:
        raise ValueError(f"TTSVoicePreset {preset_id} not found")
    
    # 构建查询条件（与 preview 相同）
    conditions = []
    
    if filter.language:
        conditions.append(EBook.language == filter.language)
    
    if filter.author_substring:
        conditions.append(EBook.author.ilike(f"%{filter.author_substring}%"))
    
    if filter.series_substring:
        conditions.append(EBook.series.ilike(f"%{filter.series_substring}%"))
    
    if filter.tag_keyword:
        conditions.append(EBook.tags.ilike(f"%{filter.tag_keyword}%"))
    
    if filter.created_from:
        conditions.append(EBook.created_at >= filter.created_from)
    
    if filter.created_to:
        conditions.append(EBook.created_at <= filter.created_to)
    
    # 查询符合条件的 EBook
    query = (
        select(EBook)
        .outerjoin(TTSWorkProfile, EBook.id == TTSWorkProfile.ebook_id)
        .where(and_(*conditions) if conditions else True)
    )
    
    # 如果有 has_profile 条件，需要额外过滤
    if filter.has_profile is not None:
        if filter.has_profile:
            # 只返回有 Profile 的
            query = query.where(TTSWorkProfile.id.isnot(None))
        else:
            # 只返回没有 Profile 的
            query = query.where(TTSWorkProfile.id.is_(None))
    
    query = query.order_by(EBook.created_at.desc()).limit(max_items)
    
    result = await db.execute(query)
    ebooks = result.scalars().unique().all()
    
    # 统计变量
    matched_ebooks = len(ebooks)
    created_profiles = 0
    updated_profiles = 0
    skipped_existing_profile = 0
    
    # 批量加载所有 Profile
    ebook_ids = [ebook.id for ebook in ebooks]
    profiles_dict = {}
    if ebook_ids:
        profiles_result = await db.execute(
            select(TTSWorkProfile)
            .where(TTSWorkProfile.ebook_id.in_(ebook_ids))
        )
        profiles_dict = {p.ebook_id: p for p in profiles_result.scalars().all()}
    
    # 逐个处理
    for ebook in ebooks:
        profile = profiles_dict.get(ebook.id)
        
        if not profile:
            # 没有 Profile，创建新的
            if not dry_run:
                profile = TTSWorkProfile(
                    ebook_id=ebook.id,
                    preset_id=preset_id,
                    enabled=enable_profile
                )
                db.add(profile)
            created_profiles += 1
            logger.debug(f"为 EBook {ebook.id} 创建 Profile（preset_id={preset_id}）")
        else:
            # 已有 Profile
            if not override_existing:
                skipped_existing_profile += 1
                logger.debug(f"跳过 EBook {ebook.id}（已有 Profile，override_existing=False）")
            else:
                # 更新现有 Profile
                if not dry_run:
                    profile.preset_id = preset_id
                    profile.enabled = enable_profile
                updated_profiles += 1
                logger.debug(f"更新 EBook {ebook.id} 的 Profile（preset_id={preset_id}, enabled={enable_profile}）")
    
    if not dry_run:
        await db.commit()
        logger.info(
            f"批量应用预设 {preset_id} 完成: 匹配 {matched_ebooks} 本，"
            f"创建 {created_profiles} 个 Profile，更新 {updated_profiles} 个，跳过 {skipped_existing_profile} 个"
        )
    else:
        logger.info(
            f"Dry-run 批量应用预设 {preset_id}: 匹配 {matched_ebooks} 本，"
            f"将创建 {created_profiles} 个 Profile，更新 {updated_profiles} 个，跳过 {skipped_existing_profile} 个"
        )
    
    return ApplyTTSWorkPresetResult(
        matched_ebooks=matched_ebooks,
        created_profiles=created_profiles,
        updated_profiles=updated_profiles,
        skipped_existing_profile=skipped_existing_profile
    )

