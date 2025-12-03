"""
站点 AI 适配状态查询

Phase AI-3: 提供站点 AI 适配状态的查询接口
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from pydantic import BaseModel

from app.core.config import settings
from app.models.ai_site_adapter import AISiteAdapter


class AISiteAdapterStatus(BaseModel):
    """站点 AI 适配状态"""
    ai_adapter_enabled: bool  # 全局是否启用 AI 适配
    ai_config_present: bool  # 此站点是否有 AI 配置记录
    ai_config_last_analyzed_at: Optional[datetime] = None  # 上次分析时间
    ai_effective_mode: str  # "manual_profile" | "ai_profile" | "none"
    # Phase AI-4: 站点级别的控制字段
    disabled: bool = False  # 是否禁用本站点的 AI 适配
    manual_profile_preferred: bool = False  # 是否优先使用人工配置
    confidence_score: Optional[int] = None  # AI 配置可信度分数（0-100）
    last_error_preview: Optional[str] = None  # 最近一次错误摘要（截断）
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


async def get_ai_adapter_status_for_site(
    site_id: str,
    db: AsyncSession,
) -> AISiteAdapterStatus:
    """
    获取站点的 AI 适配状态
    
    Phase AI-3: 用于在站点列表/详情中显示 AI 适配状态
    
    Args:
        site_id: 站点 ID（字符串格式）
        db: 数据库会话
        
    Returns:
        AISiteAdapterStatus 对象
    """
    # 1. 全局是否启用
    ai_adapter_enabled = settings.AI_ADAPTER_ENABLED
    
    # 2. 查询是否有 AI 配置记录
    ai_config_present = False
    ai_config_last_analyzed_at = None
    disabled = False
    manual_profile_preferred = False
    confidence_score = None
    last_error_preview = None
    
    try:
        result = await db.execute(
            select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        record = result.scalar_one_or_none()
        
        if record:
            ai_config_present = True
            ai_config_last_analyzed_at = record.updated_at or record.created_at
            # Phase AI-4: 读取站点级别的控制字段
            disabled = record.disabled if record.disabled is not None else False
            manual_profile_preferred = record.manual_profile_preferred if record.manual_profile_preferred is not None else False
            confidence_score = record.confidence_score
            # 截断错误信息（最多 200 字符）
            if record.last_error:
                last_error_preview = record.last_error[:200] + ("..." if len(record.last_error) > 200 else "")
    except Exception as e:
        logger.debug(f"查询站点 {site_id} 的 AI 配置记录失败: {e}")
    
    # 3. 判断生效模式 (更新以考虑 manual_profile_preferred)
    ai_effective_mode = "none"
    
    if ai_config_present and not disabled:  # 只有在未禁用时才考虑 AI
        try:
            # 检查 Local Intel 是否使用 AI 配置
            from app.core.intel_local.site_profiles import get_site_profile
            from app.models.site import Site
            
            # 获取站点对象
            from sqlalchemy import select as sql_select
            site_result = await db.execute(
                sql_select(Site).where(Site.id == int(site_id))
            )
            site = site_result.scalar_one_or_none()
            
            if site:
                # 检查是否有手工配置
                manual_profile = get_site_profile(site.name.lower().strip())
                if manual_profile:
                    if manual_profile_preferred:  # Phase AI-4: 优先人工
                        ai_effective_mode = "manual_profile"
                    else:  # 如果不优先人工，但有人工，也算人工
                        ai_effective_mode = "manual_profile"
                else:
                    # 尝试加载 AI 配置
                    from app.core.site_ai_adapter import load_parsed_config
                    from app.core.site_ai_adapter.intel_bridge import ai_config_to_intel_profile
                    
                    ai_cfg = await load_parsed_config(site_id, db)
                    if ai_cfg:
                        ai_profile = ai_config_to_intel_profile(site, ai_cfg)
                        if ai_profile:
                            ai_effective_mode = "ai_profile"
        except Exception as e:
            logger.debug(f"判断站点 {site_id} 的 AI 生效模式失败: {e}")
    
    return AISiteAdapterStatus(
        ai_adapter_enabled=ai_adapter_enabled,
        ai_config_present=ai_config_present,
        ai_config_last_analyzed_at=ai_config_last_analyzed_at,
        ai_effective_mode=ai_effective_mode,
        disabled=disabled,
        manual_profile_preferred=manual_profile_preferred,
        confidence_score=confidence_score,
        last_error_preview=last_error_preview,
    )

