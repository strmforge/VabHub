"""
推荐相关API - 整合过往版本的推荐功能
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.modules.recommendation.service import RecommendationService
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class RecommendationResponse(BaseModel):
    """推荐响应"""
    media_id: str
    score: float
    reason: str
    confidence: float
    recommendation_type: str
    media_type: Optional[str] = None
    title: Optional[str] = None


class RecommendationSettings(BaseModel):
    """推荐设置"""
    algorithm: str = Field(default="hybrid", description="推荐算法")
    limit: int = Field(default=20, ge=10, le=100, description="推荐数量")
    preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "includeMovies": True,
        "includeTVShows": True,
        "includeAnime": True
    }, description="推荐偏好")
    weights: Dict[str, int] = Field(default_factory=lambda: {
        "collaborative": 30,
        "content": 30,
        "popularity": 20,
        "deep_learning": 20
    }, description="算法权重")


class RecommendationSettingsResponse(BaseModel):
    """推荐设置响应"""
    algorithm: str
    limit: int
    preferences: Dict[str, Any]
    weights: Dict[str, int]


@router.get("/", response_model=BaseResponse)
async def get_recommendations(
    user_id: int = Query(1, description="用户ID"),
    limit: int = Query(20, ge=10, le=100, description="推荐数量"),
    algorithm: str = Query("hybrid", description="推荐算法: hybrid, collaborative, content_based, popularity, deep_learning"),
    db = Depends(get_db)
):
    """
    获取推荐列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [RecommendationResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RecommendationService(db)
        recommendations = await service.get_recommendations(
            user_id=user_id,
            limit=limit,
            algorithm=algorithm
        )
        
        # 转换为响应格式
        recommendation_responses = [
            RecommendationResponse(
                media_id=rec["media_id"],
                score=rec["score"],
                reason=rec["reason"],
                confidence=rec["confidence"],
                recommendation_type=rec["recommendation_type"],
                media_type=rec.get("media_type"),
                title=rec.get("title")
            )
            for rec in recommendations
        ]
        
        return success_response(
            data=[rec.model_dump() for rec in recommendation_responses],
            message="获取推荐成功"
        )
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取推荐时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/similar/{media_id}", response_model=BaseResponse)
async def get_similar_content(
    media_id: str,
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    db = Depends(get_db)
):
    """
    获取相似内容推荐
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [RecommendationResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RecommendationService(db)
        recommendations = await service.get_similar_content(media_id, limit)
        
        # 转换为响应格式
        recommendation_responses = [
            RecommendationResponse(
                media_id=rec["media_id"],
                score=rec.get("similarity", rec.get("score", 0.0)),
                reason=rec.get("reason", "内容相似"),
                confidence=rec.get("similarity", rec.get("confidence", 0.0)),
                recommendation_type="similar",
                media_type=rec.get("media_type"),
                title=rec.get("title")
            )
            for rec in recommendations
        ]
        
        return success_response(
            data=[rec.model_dump() for rec in recommendation_responses],
            message="获取相似内容成功"
        )
    except Exception as e:
        logger.error(f"获取相似内容失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取相似内容时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/popular", response_model=BaseResponse)
async def get_popular_recommendations(
    limit: int = Query(20, ge=10, le=100, description="推荐数量"),
    db = Depends(get_db)
):
    """
    获取热门推荐
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [RecommendationResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RecommendationService(db)
        recommendations = await service.get_popular_recommendations(limit)
        
        # 转换为响应格式
        recommendation_responses = [
            RecommendationResponse(
                media_id=rec["media_id"],
                score=rec["score"],
                reason=rec["reason"],
                confidence=rec["confidence"],
                recommendation_type=rec["recommendation_type"],
                media_type=rec.get("media_type"),
                title=rec.get("title")
            )
            for rec in recommendations
        ]
        
        return success_response(
            data=[rec.model_dump() for rec in recommendation_responses],
            message="获取热门推荐成功"
        )
    except Exception as e:
        logger.error(f"获取热门推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取热门推荐时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/bangumi", response_model=BaseResponse)
async def get_bangumi_recommendations(
    limit: int = Query(20, ge=10, le=100, description="推荐数量"),
    source: str = Query("calendar", description="推荐来源: calendar(每日放送), popular(热门动漫)"),
    db = Depends(get_db)
):
    """
    获取Bangumi动漫推荐
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [RecommendationResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RecommendationService(db)
        recommendations = await service.get_bangumi_recommendations(limit=limit, source=source)
        
        # 转换为响应格式
        recommendation_responses = []
        for rec in recommendations:
            response = RecommendationResponse(
                media_id=rec["media_id"],
                score=rec["score"],
                reason=rec["reason"],
                confidence=rec["confidence"],
                recommendation_type=rec["recommendation_type"],
                media_type=rec.get("media_type"),
                title=rec.get("title")
            )
            # 添加额外字段（如果需要）
            response_dict = response.model_dump()
            if "summary" in rec:
                response_dict["summary"] = rec["summary"]
            if "images" in rec:
                response_dict["images"] = rec["images"]
            if "rating" in rec:
                response_dict["rating"] = rec["rating"]
            if "url" in rec:
                response_dict["url"] = rec["url"]
            recommendation_responses.append(response_dict)
        
        return success_response(
            data=recommendation_responses,
            message="获取Bangumi推荐成功"
        )
    except Exception as e:
        logger.error(f"获取Bangumi推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取Bangumi推荐时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/preferences", response_model=BaseResponse)
async def get_user_preferences(
    user_id: int = Query(1, description="用户ID"),
    db = Depends(get_db)
):
    """
    获取用户推荐偏好设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "includeMovies": true,
            "includeTVShows": true,
            "includeAnime": true,
            "preferredGenres": [],
            "minRating": 0.0,
            "algorithm": "hybrid",
            "weights": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RecommendationService(db)
        preferences = await service.get_user_preferences(user_id)
        
        return success_response(
            data=preferences,
            message="获取用户偏好设置成功"
        )
    except Exception as e:
        logger.error(f"获取用户偏好设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取用户偏好设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/preferences", response_model=BaseResponse)
async def update_user_preferences(
    user_id: int = Query(1, description="用户ID"),
    preferences: Dict[str, Any] = Body(..., description="偏好设置"),
    db = Depends(get_db)
):
    """
    更新用户推荐偏好设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = RecommendationService(db)
        success = await service.update_user_preferences(user_id, preferences)
        
        if success:
            return success_response(message="用户偏好设置更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="UPDATE_FAILED",
                    error_message="更新用户偏好设置失败"
                ).model_dump()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户偏好设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新用户偏好设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/settings", response_model=BaseResponse)
async def get_recommendation_settings(
    db = Depends(get_db)
):
    """
    获取推荐设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": RecommendationSettingsResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 从设置中获取推荐配置
        algorithm = await settings_service.get_setting("recommendation_algorithm") or "hybrid"
        limit = int(await settings_service.get_setting("recommendation_limit") or 20)
        
        # 获取偏好设置
        preferences = {
            "includeMovies": await settings_service.get_setting("recommendation_include_movies") != "false",
            "includeTVShows": await settings_service.get_setting("recommendation_include_tv_shows") != "false",
            "includeAnime": await settings_service.get_setting("recommendation_include_anime") != "false"
        }
        
        # 获取权重设置
        weights = {
            "collaborative": int(await settings_service.get_setting("recommendation_weight_collaborative") or 30),
            "content": int(await settings_service.get_setting("recommendation_weight_content") or 30),
            "popularity": int(await settings_service.get_setting("recommendation_weight_popularity") or 20),
            "deep_learning": int(await settings_service.get_setting("recommendation_weight_deep_learning") or 20)
        }
        
        settings_response = RecommendationSettingsResponse(
            algorithm=algorithm,
            limit=limit,
            preferences=preferences,
            weights=weights
        )
        
        return success_response(
            data=settings_response.model_dump(),
            message="获取推荐设置成功"
        )
    except Exception as e:
        logger.error(f"获取推荐设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取推荐设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/settings", response_model=BaseResponse)
async def update_recommendation_settings(
    settings: RecommendationSettings,
    db = Depends(get_db)
):
    """
    更新推荐设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 保存设置
        await settings_service.set_setting("recommendation_algorithm", settings.algorithm)
        await settings_service.set_setting("recommendation_limit", str(settings.limit))
        await settings_service.set_setting("recommendation_include_movies", str(settings.preferences.get("includeMovies", True)))
        await settings_service.set_setting("recommendation_include_tv_shows", str(settings.preferences.get("includeTVShows", True)))
        await settings_service.set_setting("recommendation_include_anime", str(settings.preferences.get("includeAnime", True)))
        await settings_service.set_setting("recommendation_weight_collaborative", str(settings.weights.get("collaborative", 30)))
        await settings_service.set_setting("recommendation_weight_content", str(settings.weights.get("content", 30)))
        await settings_service.set_setting("recommendation_weight_popularity", str(settings.weights.get("popularity", 20)))
        await settings_service.set_setting("recommendation_weight_deep_learning", str(settings.weights.get("deep_learning", 20)))
        
        return success_response(message="推荐设置更新成功")
    except Exception as e:
        logger.error(f"更新推荐设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新推荐设置时发生错误: {str(e)}"
            ).model_dump()
        )


# 深度学习推荐相关API
@router.get("/deep-learning/info", response_model=BaseResponse)
async def get_deep_learning_info(
    db = Depends(get_db)
):
    """
    获取深度学习模型信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "enabled": true,
            "model_type": "ncf",
            "is_trained": true,
            "device": "cuda",
            "gpu_enabled": true,
            "gpu_available": true,
            ...
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.deep_learning_recommender import DeepLearningRecommender
        
        dl_recommender = DeepLearningRecommender(db)
        info = await dl_recommender.get_model_info()
        
        return success_response(data=info, message="获取深度学习模型信息成功")
    except Exception as e:
        logger.error(f"获取深度学习模型信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取深度学习模型信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/deep-learning/train", response_model=BaseResponse)
async def train_deep_learning_model(
    db = Depends(get_db)
):
    """
    训练深度学习模型
    
    返回统一响应格式：
    {
        "success": true,
        "message": "训练成功",
        "data": {
            "model_info": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.deep_learning_recommender import DeepLearningRecommender
        
        dl_recommender = DeepLearningRecommender(db)
        await dl_recommender.train_model()
        
        info = await dl_recommender.get_model_info()
        
        return success_response(
            data={"model_info": info},
            message="深度学习模型训练成功"
        )
    except Exception as e:
        logger.error(f"训练深度学习模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"训练深度学习模型时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/deep-learning/device-info", response_model=BaseResponse)
async def get_device_info():
    """
    获取GPU设备信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "torch_available": true,
            "gpu_available": true,
            "device_count": 1,
            "current_device": "cuda:0",
            "device_name": "NVIDIA GeForce RTX 3090"
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.deep_learning.gpu_utils import get_device_info
        
        info = get_device_info()
        
        return success_response(data=info, message="获取设备信息成功")
    except Exception as e:
        logger.error(f"获取设备信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取设备信息时发生错误: {str(e)}"
            ).model_dump()
        )


# 实时推荐相关API
@router.post("/realtime/interaction", response_model=BaseResponse)
async def record_realtime_interaction(
    user_id: int = Body(..., description="用户ID"),
    item_id: str = Body(..., description="物品ID（media_id）"),
    interaction_type: str = Body(..., description="交互类型（view, click, like, dislike, share, bookmark, subscribe, skip等）"),
    value: Optional[float] = Body(None, description="交互值（如评分）"),
    context: Optional[Dict[str, Any]] = Body(None, description="上下文信息"),
    db = Depends(get_db)
):
    """
    记录实时用户交互
    
    返回统一响应格式：
    {
        "success": true,
        "message": "记录成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        await realtime_service.record_interaction(
            user_id=user_id,
            item_id=item_id,
            interaction_type=interaction_type,
            value=value,
            context=context
        )
        
        return success_response(message="交互记录成功")
    except Exception as e:
        logger.error(f"记录实时交互失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"记录实时交互时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/realtime/{user_id}", response_model=BaseResponse)
async def get_realtime_recommendations(
    user_id: int,
    limit: int = Query(20, ge=10, le=100, description="推荐数量"),
    algorithm: str = Query("hybrid", description="推荐算法"),
    experiment_id: Optional[str] = Query(None, description="A/B测试实验ID"),
    db = Depends(get_db)
):
    """
    获取实时推荐
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [RecommendationResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        recommendations = await realtime_service.get_realtime_recommendations(
            user_id=user_id,
            limit=limit,
            algorithm=algorithm,
            experiment_id=experiment_id
        )
        
        # 转换为响应格式
        recommendation_responses = [
            RecommendationResponse(
                media_id=rec["media_id"],
                score=rec["score"],
                reason=rec["reason"],
                confidence=rec["confidence"],
                recommendation_type=rec["recommendation_type"],
                media_type=rec.get("media_type"),
                title=rec.get("title")
            )
            for rec in recommendations
        ]
        
        return success_response(
            data=[rec.model_dump() for rec in recommendation_responses],
            message="获取实时推荐成功"
        )
    except Exception as e:
        logger.error(f"获取实时推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取实时推荐时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/realtime/{user_id}/features", response_model=BaseResponse)
async def get_user_features(
    user_id: int,
    db = Depends(get_db)
):
    """
    获取用户实时特征
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "interaction_frequency": 10,
            "activity_level": 0.8,
            "category_preferences": {...},
            ...
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        features = await realtime_service.get_user_features(user_id)
        
        return success_response(data=features, message="获取用户特征成功")
    except Exception as e:
        logger.error(f"获取用户特征失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取用户特征时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/realtime/status", response_model=BaseResponse)
async def get_realtime_status(
    db = Depends(get_db)
):
    """
    获取实时推荐系统状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "enabled": true,
            "stream_processor": {...},
            "feature_updater": {...},
            "ab_testing": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        status_info = realtime_service.get_status()
        
        return success_response(data=status_info, message="获取实时推荐系统状态成功")
    except Exception as e:
        logger.error(f"获取实时推荐系统状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取实时推荐系统状态时发生错误: {str(e)}"
            ).model_dump()
        )


# A/B测试相关API
@router.post("/ab-testing/experiments", response_model=BaseResponse)
async def create_ab_experiment(
    experiment_id: str = Body(..., description="实验ID"),
    name: str = Body(..., description="实验名称"),
    variants: List[Dict[str, Any]] = Body(..., description="实验变体列表"),
    description: Optional[str] = Body(None, description="实验描述"),
    db = Depends(get_db)
):
    """
    创建A/B测试实验
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": {
            "experiment_id": "...",
            "name": "...",
            "status": "draft",
            "variants": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        experiment = await realtime_service.create_experiment(
            experiment_id=experiment_id,
            name=name,
            variants=variants,
            description=description
        )
        
        return success_response(data=experiment, message="A/B测试实验创建成功")
    except Exception as e:
        logger.error(f"创建A/B测试实验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建A/B测试实验时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/ab-testing/experiments/{experiment_id}/start", response_model=BaseResponse)
async def start_ab_experiment(
    experiment_id: str,
    db = Depends(get_db)
):
    """
    启动A/B测试实验
    
    返回统一响应格式：
    {
        "success": true,
        "message": "启动成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        await realtime_service.start_experiment(experiment_id)
        
        return success_response(message="A/B测试实验启动成功")
    except Exception as e:
        logger.error(f"启动A/B测试实验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"启动A/B测试实验时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/ab-testing/experiments/{experiment_id}/evaluate", response_model=BaseResponse)
async def evaluate_ab_experiment(
    experiment_id: str,
    db = Depends(get_db)
):
    """
    评估A/B测试实验
    
    返回统一响应格式：
    {
        "success": true,
        "message": "评估成功",
        "data": {
            "status": "completed",
            "metrics": {...},
            "significance": {...},
            "best_variant": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        evaluation = await realtime_service.evaluate_experiment(experiment_id)
        
        return success_response(data=evaluation, message="A/B测试实验评估成功")
    except Exception as e:
        logger.error(f"评估A/B测试实验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"评估A/B测试实验时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/ab-testing/experiments/{experiment_id}/stop", response_model=BaseResponse)
async def stop_ab_experiment(
    experiment_id: str,
    db = Depends(get_db)
):
    """
    停止A/B测试实验
    
    返回统一响应格式：
    {
        "success": true,
        "message": "停止成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.recommendation.realtime_service import RealtimeRecommendationService
        
        realtime_service = RealtimeRecommendationService(db)
        await realtime_service.stop_experiment(experiment_id)
        
        return success_response(message="A/B测试实验停止成功")
    except Exception as e:
        logger.error(f"停止A/B测试实验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"停止A/B测试实验时发生错误: {str(e)}"
            ).model_dump()
        )
