"""
站点 AI 适配管理 API

提供站点适配配置的分析、查看等管理功能。
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.config import settings
from app.core.site_ai_adapter.service import (
    analyze_and_save_for_site,
    get_site_adapter_config,
    load_parsed_config,  # Phase AI-2
)
from app.core.schemas import success_response, error_response
from app.models.site import Site
from sqlalchemy import select

router = APIRouter(prefix="/api/admin/site-ai-adapter", tags=["站点 AI 适配管理"])


@router.post("/refresh/{site_id}")
async def refresh_site_adapter(
    site_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    刷新站点适配配置
    
    根据站点 ID 重新分析站点并生成适配配置。
    
    Args:
        site_id: 站点 ID
        db: 数据库会话
        
    Returns:
        分析结果
    """
    if not settings.AI_ADAPTER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="AI_ADAPTER_DISABLED",
                error_message="AI 适配功能已禁用",
            ).model_dump(),
        )
    
    try:
        result = await analyze_and_save_for_site(site_id, db)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="ANALYSIS_FAILED",
                    error_message="站点适配分析失败",
                ).model_dump(),
            )
        
        return success_response(
            data={
                "ok": True,
                "site_id": result.site_id,
                "engine": result.engine,
                "created_at": result.created_at.isoformat(),
                "config": result.config.model_dump(),
            },
            message="站点适配配置分析成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新站点适配配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_ERROR",
                error_message=f"服务器内部错误: {str(e)}",
            ).model_dump(),
        )


@router.get("/config/{site_id}")
async def get_site_adapter_config_api(
    site_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取站点适配配置
    
    从数据库读取已缓存的站点适配配置。
    
    Args:
        site_id: 站点 ID
        db: 数据库会话
        
    Returns:
        配置信息
    """
    try:
        config = await get_site_adapter_config(site_id, db)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="CONFIG_NOT_FOUND",
                    error_message=f"站点 {site_id} 的适配配置不存在",
                ).model_dump(),
            )
        
        return success_response(
            data={
                "site_id": site_id,
                "config": config,
            },
            message="获取站点适配配置成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取站点适配配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_ERROR",
                error_message=f"服务器内部错误: {str(e)}",
            ).model_dump(),
        )


@router.get("/effective-config/{site_id}")
async def get_effective_config(
    site_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取站点生效的配置（包括 AI 配置转换结果）
    
    Phase AI-2: 调试接口，显示 AI 配置如何转换为 Local Intel 和 External Indexer 配置
    
    Args:
        site_id: 站点 ID
        db: 数据库会话
        
    Returns:
        生效配置信息
    """
    try:
        # 1. 加载站点对象
        result = await db.execute(select(Site).where(Site.id == int(site_id)))
        site = result.scalar_one_or_none()
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="SITE_NOT_FOUND",
                    error_message=f"站点不存在 (ID: {site_id})",
                ).model_dump(),
            )
        
        # 2. 加载原始 AI 配置
        ai_cfg = await load_parsed_config(str(site.id), db)
        
        # Phase AI-4: 获取 AI 适配记录以获取禁用/优先策略和可信度
        from app.models.ai_site_adapter import AISiteAdapter
        ai_record_result = await db.execute(
            select(AISiteAdapter).where(AISiteAdapter.site_id == site_id)
        )
        ai_record = ai_record_result.scalar_one_or_none()
        
        ai_disabled = ai_record.disabled if ai_record else False
        ai_manual_profile_preferred = ai_record.manual_profile_preferred if ai_record else False
        ai_confidence_score = ai_record.confidence_score if ai_record else None
        ai_last_error_preview = ai_record.last_error[:200] if ai_record and ai_record.last_error else None
        
        # 3. 检查 Local Intel 配置
        intel_profile = None
        intel_mode = "none"
        try:
            from app.core.intel_local.site_profiles import (
                get_site_profile,
                get_site_profile_with_ai_fallback,
            )
            
            # 先尝试手工配置
            manual_profile = get_site_profile(site.name.lower().strip())
            if manual_profile:
                intel_profile = {
                    "site": manual_profile.site,
                    "hr_enabled": manual_profile.hr.enabled,
                    "hr_page_path": manual_profile.hr.page_path,
                    "inbox_enabled": manual_profile.inbox.enabled,
                }
                intel_mode = "manual_profile"
            else:
                # 尝试 AI 配置回退
                ai_intel_profile = await get_site_profile_with_ai_fallback(
                    site.name.lower().strip(),
                    site_obj=site,
                    db=db,
                )
                if ai_intel_profile:
                    intel_profile = {
                        "site": ai_intel_profile.site,
                        "hr_enabled": ai_intel_profile.hr.enabled,
                        "hr_page_path": ai_intel_profile.hr.page_path,
                        "inbox_enabled": ai_intel_profile.inbox.enabled,
                    }
                    intel_mode = "ai_profile"
        except Exception as e:
            logger.warning(f"获取 Local Intel 配置失败: {e}", exc_info=True)
        
        # 4. 检查 External Indexer 配置
        ext_config = None
        ext_mode = "none"
        try:
            from app.core.ext_indexer.site_importer import (
                get_site_config,
                get_site_config_with_ai_fallback,
            )
            
            # 先尝试手工配置
            manual_ext_config = get_site_config(str(site.id))
            if manual_ext_config:
                ext_config = {
                    "site_id": manual_ext_config.site_id,
                    "name": manual_ext_config.name,
                    "base_url": manual_ext_config.base_url,
                    "framework": manual_ext_config.framework,
                    "capabilities": manual_ext_config.capabilities,
                }
                ext_mode = "manual_config"
            else:
                # 尝试 AI 配置回退
                ai_ext_config = await get_site_config_with_ai_fallback(
                    str(site.id),
                    site_obj=site,
                    db=db,
                )
                if ai_ext_config:
                    ext_config = {
                        "site_id": ai_ext_config.site_id,
                        "name": ai_ext_config.name,
                        "base_url": ai_ext_config.base_url,
                        "framework": ai_ext_config.framework,
                        "capabilities": ai_ext_config.capabilities,
                    }
                    ext_mode = "ai_config"
        except Exception as e:
            logger.warning(f"获取 External Indexer 配置失败: {e}", exc_info=True)
        
        # 5. 构建响应
        response_data = {
            "site_id": str(site.id),
            "site_name": site.name,
            "ai_adapter_enabled_global": settings.AI_ADAPTER_ENABLED,  # Phase AI-4: 全局启用状态
            "ai_disabled": ai_disabled,  # Phase AI-4
            "ai_manual_profile_preferred": ai_manual_profile_preferred,  # Phase AI-4
            "ai_config_exists": ai_cfg is not None,
            "ai_confidence_score": ai_confidence_score,  # Phase AI-4
            "last_error_preview": ai_last_error_preview,  # Phase AI-4
            "ai_config": {
                "engine": ai_cfg.engine if ai_cfg else None,
                "search_url": ai_cfg.search.url if ai_cfg else None,
                "detail_url": ai_cfg.detail.url if ai_cfg else None,
                "hr_enabled": ai_cfg.hr.enabled if ai_cfg and ai_cfg.hr else False,
            } if ai_cfg else None,
            "local_intel": {
                "mode": intel_mode,
                "profile": intel_profile,
            },
            "external_indexer": {
                "mode": ext_mode,
                "config": ext_config,
            },
        }
        
        return success_response(
            data=response_data,
            message="获取生效配置成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取生效配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_ERROR",
                error_message=f"服务器内部错误: {str(e)}",
            ).model_dump(),
        )
