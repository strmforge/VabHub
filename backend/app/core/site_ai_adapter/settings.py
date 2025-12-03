"""
站点 AI 适配设置管理

Phase AI-4: 提供站点级别的 AI 适配设置更新功能
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.ai_site_adapter import AISiteAdapter


async def update_site_ai_settings(
    site_id: str,
    db: AsyncSession,
    *,
    disabled: Optional[bool] = None,
    manual_profile_preferred: Optional[bool] = None,
) -> bool:
    """
    更新站点的 AI 适配设置
    
    Phase AI-4: 允许单独设置站点的 AI 适配禁用和优先策略
    
    Args:
        site_id: 站点 ID（字符串格式）
        db: 数据库会话
        disabled: 是否禁用本站点的 AI 适配（None 表示不更新）
        manual_profile_preferred: 是否优先使用人工配置（None 表示不更新）
        
    Returns:
        是否成功更新
    """
    try:
        result = await db.execute(
            select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            # 如果记录不存在，创建一个新记录（只有设置，没有配置）
            record = AISiteAdapter(
                site_id=site_id,
                engine="unknown",
                config_json={},  # 空配置占位
                version=1,
                disabled=disabled if disabled is not None else False,
                manual_profile_preferred=manual_profile_preferred if manual_profile_preferred is not None else False,
            )
            db.add(record)
            logger.info(f"创建站点 AI 适配设置记录 (site_id: {site_id})")
        else:
            # 更新现有记录
            if disabled is not None:
                record.disabled = disabled
            if manual_profile_preferred is not None:
                record.manual_profile_preferred = manual_profile_preferred
            logger.info(f"更新站点 AI 适配设置 (site_id: {site_id})")
        
        await db.commit()
        return True
        
    except Exception as e:
        logger.error(f"更新站点 AI 适配设置失败 (site_id: {site_id}): {e}", exc_info=True)
        await db.rollback()
        return False

