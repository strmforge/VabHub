"""
榜单相关API - 整合音乐和影视榜单
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.modules.charts.service import ChartsService
from app.modules.charts.video_charts import VideoChartsService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class ChartRequest(BaseModel):
    """榜单请求"""
    platform: str = Field(..., description="榜单平台")
    chart_type: str = Field("hot", description="榜单类型")
    region: str = Field("CN", description="地区代码")
    limit: int = Field(50, ge=1, le=100, description="返回数量")


class VideoChartRequest(BaseModel):
    """影视榜单请求"""
    source: str = Field(..., description="数据源: tmdb, douban, netflix, imdb")
    chart_type: str = Field(..., description="榜单类型")
    region: str = Field("CN", description="地区代码")
    limit: int = Field(20, ge=1, le=100, description="返回数量")
    week: Optional[str] = Field(None, description="周数（仅Netflix使用，格式: 2025W1）")


@router.get("/music/platforms", response_model=BaseResponse)
async def get_music_chart_platforms(db=Depends(get_db)):
    """
    获取支持的音乐榜单平台
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "platforms": [...],
            "total": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = ChartsService(db)
        platforms = await service.get_supported_platforms()
        return success_response(
            data={
                "platforms": platforms,
                "total": len(platforms)
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取音乐榜单平台失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐榜单平台时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/music/jsonl", response_model=BaseResponse)
async def get_music_charts_jsonl(
    platform: str = Query(..., description="平台名称"),
    chart_type: str = Query("hot", description="榜单类型"),
    region: str = Query("CN", description="地区"),
    limit: int = Query(50, description="返回数量"),
    db=Depends(get_db)
):
    """
    获取音乐榜单数据（JSONL格式，参考charts-suite-v2）
    
    返回JSONL格式的榜单数据，便于存储和分析
    """
    try:
        service = ChartsService(db)
        jsonl_data = await service.get_charts_jsonl(
            platform=platform,
            chart_type=chart_type,
            region=region,
            limit=limit
        )
        
        return success_response(
            data={
                "format": "jsonl",
                "platform": platform,
                "chart_type": chart_type,
                "region": region,
                "data": jsonl_data,
                "line_count": len(jsonl_data.split("\n")) if jsonl_data else 0
            },
            message="获取成功（JSONL格式）"
        )
    except Exception as e:
        logger.error(f"获取音乐榜单（JSONL）失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐榜单（JSONL）失败: {str(e)}"
            ).model_dump()
        )


@router.post("/music", response_model=BaseResponse)
async def get_music_charts(
    request: ChartRequest,
    use_chart_row: bool = Query(False, description="是否使用ChartRow格式（参考charts-suite-v2）"),
    db=Depends(get_db)
):
    """
    获取音乐榜单
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "platform": "...",
            "chart_type": "...",
            "region": "...",
            "total": 50,
            "charts": [...],
            "updated_at": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = ChartsService(db)
        charts = await service.get_charts(
            platform=request.platform,
            chart_type=request.chart_type,
            region=request.region,
            limit=request.limit,
            use_chart_row=use_chart_row
        )
        return success_response(
            data={
                "platform": request.platform,
                "chart_type": request.chart_type,
                "region": request.region,
                "total": len(charts),
                "charts": charts,
                "updated_at": datetime.now().isoformat()
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取音乐榜单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐榜单时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/music/compare", response_model=BaseResponse)
async def compare_music_charts(
    platform1: str = Query(..., description="平台1"),
    platform2: str = Query(..., description="平台2"),
    chart_type: str = Query("hot", description="榜单类型"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db=Depends(get_db)
):
    """
    比较不同平台的音乐榜单
    
    返回统一响应格式：
    {
        "success": true,
        "message": "比较完成",
        "data": {comparison_data},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = ChartsService(db)
        comparison = await service.compare_charts(
            platform1=platform1,
            platform2=platform2,
            chart_type=chart_type,
            limit=limit
        )
        return success_response(data=comparison, message="比较完成")
    except Exception as e:
        logger.error(f"比较音乐榜单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"比较音乐榜单时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/video/netflix/weeks", response_model=BaseResponse)
async def get_netflix_weeks(db=Depends(get_db)):
    """获取Netflix Top 10可用的周数列表"""
    try:
        from app.modules.charts.providers.netflix_top10 import NetflixTop10Provider
        provider = NetflixTop10Provider()
        weeks = await provider.get_available_weeks()
        return success_response(
            data={"weeks": weeks, "total": len(weeks)},
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取Netflix周数列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取Netflix周数列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/video/sources", response_model=BaseResponse)
async def get_video_chart_sources(db=Depends(get_db)):
    """
    获取支持的影视榜单数据源
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "sources": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = VideoChartsService(db)
        supported = await service.get_supported_charts()
        return success_response(
            data={
                "sources": [
                    {"id": "tmdb", "name": "TMDB", "charts": supported.get("tmdb", {})},
                    {"id": "douban", "name": "豆瓣", "charts": supported.get("douban", {})},
                    {"id": "netflix", "name": "Netflix", "charts": supported.get("netflix", {})},
                    {"id": "imdb", "name": "IMDb", "charts": supported.get("imdb", {})}
                ]
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取影视榜单数据源失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取影视榜单数据源时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/video", response_model=BaseResponse)
async def get_video_charts(
    request: VideoChartRequest,
    db=Depends(get_db)
):
    """
    获取影视榜单
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "source": "...",
            "chart_type": "...",
            "region": "...",
            "total": 20,
            "charts": [...],
            "updated_at": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = VideoChartsService(db)
        charts = await service.get_charts(
            source=request.source,
            chart_type=request.chart_type,
            region=request.region,
            limit=request.limit,
            week=request.week
        )
        return success_response(
            data={
                "source": request.source,
                "chart_type": request.chart_type,
                "region": request.region,
                "total": len(charts),
                "charts": charts,
                "updated_at": datetime.now().isoformat()
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取影视榜单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取影视榜单时发生错误: {str(e)}"
            ).model_dump()
        )

