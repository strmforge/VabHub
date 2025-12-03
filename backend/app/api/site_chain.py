"""
站点API（Chain模式版本）
使用Chain模式的站点API实现
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.chain import get_site_chain

router = APIRouter()


class SiteCreate(BaseModel):
    """创建站点请求"""
    name: str
    url: str
    cookie: Optional[str] = None
    cookiecloud_uuid: Optional[str] = None
    cookiecloud_password: Optional[str] = None
    cookiecloud_server: Optional[str] = None
    is_active: bool = True


class SiteUpdate(BaseModel):
    """更新站点请求"""
    name: Optional[str] = None
    url: Optional[str] = None
    cookie: Optional[str] = None
    cookiecloud_uuid: Optional[str] = None
    cookiecloud_password: Optional[str] = None
    cookiecloud_server: Optional[str] = None
    is_active: Optional[bool] = None
    user_data: Optional[dict] = None


class SiteResponse(BaseModel):
    """站点响应"""
    id: int
    name: str
    url: str
    is_active: bool
    cookiecloud_uuid: Optional[str] = None
    cookiecloud_server: Optional[str] = None
    user_data: Optional[dict] = None
    last_checkin: Optional[str] = None
    created_at: str
    updated_at: str


@router.get("", response_model=List[SiteResponse])
async def list_sites(active_only: bool = Query(False)):
    """列出站点（Chain模式）"""
    try:
        chain = get_site_chain()
        sites = await chain.list_sites(active_only=active_only)
        # 隐藏敏感信息
        for site in sites:
            site.pop("cookie", None)
        return [SiteResponse(**site) for site in sites]
    except Exception as e:
        logger.error(f"列出站点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出站点失败: {str(e)}"
        )


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: int):
    """获取站点详情（Chain模式）"""
    try:
        chain = get_site_chain()
        site = await chain.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="站点不存在"
            )
        # 隐藏敏感信息
        site.pop("cookie", None)
        return SiteResponse(**site)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取站点详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取站点详情失败: {str(e)}"
        )


@router.post("/{site_id}/checkin", response_model=dict)
async def checkin_site(site_id: int):
    """执行站点签到（Chain模式）"""
    try:
        chain = get_site_chain()
        result = await chain.checkin(site_id)
        return result
    except Exception as e:
        logger.error(f"站点签到失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"站点签到失败: {str(e)}"
        )


@router.post("/batch-checkin", response_model=dict)
async def batch_checkin(site_ids: Optional[List[int]] = None):
    """批量签到（Chain模式）"""
    try:
        chain = get_site_chain()
        result = await chain.batch_checkin(site_ids)
        return result
    except Exception as e:
        logger.error(f"批量签到失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量签到失败: {str(e)}"
        )


@router.post("/{site_id}/test-connection", response_model=dict)
async def test_site_connection(site_id: int):
    """测试站点连接（Chain模式）"""
    try:
        chain = get_site_chain()
        result = await chain.test_connection(site_id)
        return result
    except Exception as e:
        logger.error(f"测试站点连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试站点连接失败: {str(e)}"
        )

