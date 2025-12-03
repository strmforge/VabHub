"""
站点配置文件管理API
支持站点自动识别和解析
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any
from loguru import logger

from app.core.database import get_db
from app.modules.site.service import SiteService
from app.modules.site_profile.service import SiteProfileService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/sites/{site_id}/profile", tags=["站点配置文件"])


@router.post("/identify", response_model=BaseResponse)
async def identify_site(
    site_id: int,
    db = Depends(get_db)
):
    """
    识别站点类型（根据配置文件）
    """
    try:
        site_service = SiteService(db)
        site = await site_service.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="站点不存在"
                ).model_dump()
            )
        
        profile_service = SiteProfileService()
        profile = await profile_service.identify_site(site)
        
        if profile:
            return success_response(
                data={
                    "matched": True,
                    "profile_id": profile.get("meta", {}).get("id"),
                    "family": profile.get("meta", {}).get("family"),
                    "name": profile.get("meta", {}).get("name")
                },
                message="站点识别成功"
            )
        else:
            return success_response(
                data={"matched": False},
                message="未找到匹配的配置文件"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"识别站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"识别站点失败: {str(e)}"
            ).model_dump()
        )


@router.post("/parse", response_model=BaseResponse)
async def parse_site_content(
    site_id: int,
    parse_type: str = Query("list", description="解析类型：list/detail/user"),
    page_url: Optional[str] = Query(None, description="要解析的页面URL"),
    db = Depends(get_db)
):
    """
    解析站点内容
    """
    try:
        site_service = SiteService(db)
        site = await site_service.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="站点不存在"
                ).model_dump()
            )
        
        profile_service = SiteProfileService()
        result = await profile_service.parse_site_content(site, parse_type, page_url)
        
        return success_response(data=result, message="解析成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析站点内容失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"解析站点内容失败: {str(e)}"
            ).model_dump()
        )


@router.get("/family", response_model=BaseResponse)
async def get_site_family(
    site_id: int,
    db = Depends(get_db)
):
    """
    获取站点类型（family）
    """
    try:
        site_service = SiteService(db)
        site = await site_service.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="站点不存在"
                ).model_dump()
            )
        
        profile_service = SiteProfileService()
        family = profile_service.get_site_family(site)
        
        return success_response(
            data={"family": family},
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取站点类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点类型失败: {str(e)}"
            ).model_dump()
        )


@router.get("/profiles", response_model=BaseResponse)
async def list_profiles():
    """
    列出所有可用的配置文件
    """
    try:
        profile_service = SiteProfileService()
        profiles = profile_service.loader.list_profiles()
        
        profiles_info = []
        for profile_id in profiles:
            profile = profile_service.loader.load_profile(profile_id)
            if profile:
                meta = profile.get("meta", {})
                profiles_info.append({
                    "id": profile_id,
                    "name": meta.get("name"),
                    "family": meta.get("family"),
                    "version": meta.get("version"),
                    "domains": meta.get("domains", [])
                })
        
        return success_response(data=profiles_info, message="获取成功")
    except Exception as e:
        logger.error(f"列出配置文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"列出配置文件失败: {str(e)}"
            ).model_dump()
        )

