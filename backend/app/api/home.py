"""
首页仪表盘 API
HOME-1 实现
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.home_dashboard import HomeDashboardResponse
from app.schemas.response import BaseResponse, success_response
from app.services.home_dashboard_service import get_home_dashboard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/home", tags=["首页"])


@router.get("/dashboard", response_model=BaseResponse, summary="获取首页仪表盘数据")
async def get_home_dashboard_api(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取首页仪表盘数据
    
    包含：
    - 快速统计（小说数、漫画数、音乐数、最近活动数）
    - 继续阅读/收听列表
    - 最近新增项目
    - Runner 状态
    - 任务汇总
    """
    try:
        data = await get_home_dashboard(current_user=current_user, db=db)
        return success_response(
            data=data.model_dump(),
            message="获取首页数据成功"
        )
    except Exception as e:
        logger.error(f"获取首页数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取首页数据失败: {str(e)}"
        )
