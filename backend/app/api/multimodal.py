"""
多模态分析API
提供视频、音频、文本分析API端点
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger
import os
import tempfile

from app.core.database import get_db
from app.modules.multimodal.video_analyzer import VideoAnalyzer
from app.modules.multimodal.audio_analyzer import AudioAnalyzer
from app.modules.multimodal.text_analyzer import TextAnalyzer
from app.modules.multimodal.fusion import MultimodalFeatureFusion
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class TextAnalysisRequest(BaseModel):
    """文本分析请求"""
    text: str = Field(..., description="要分析的文本内容")




class MultimodalFusionRequest(BaseModel):
    """多模态特征融合请求"""
    video_features: Optional[Dict[str, Any]] = None
    audio_features: Optional[Dict[str, Any]] = None
    text_features: Optional[Dict[str, Any]] = None
    feature_weights: Optional[Dict[str, float]] = None


class SimilarityRequest(BaseModel):
    """相似度计算请求"""
    features1: Dict[str, Any] = Field(..., description="第一个特征字典")
    features2: Dict[str, Any] = Field(..., description="第二个特征字典")
    method: str = Field(default="cosine", description="相似度计算方法（cosine或euclidean）")


@router.post("/analyze/text", response_model=BaseResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    db = Depends(get_db)
):
    """分析文本内容"""
    try:
        analyzer = TextAnalyzer(enable_cache=True, cache_ttl=3600)
        result = await analyzer.analyze_text(request.text)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="ANALYSIS_FAILED",
                    error_message=result.get("error", "文本分析失败")
                ).model_dump()
            )
        
        return success_response(data=result, message="文本分析成功")
    except Exception as e:
        logger.error(f"文本分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"文本分析时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/analyze/video", response_model=BaseResponse)
async def analyze_video(
    file: UploadFile = File(..., description="视频文件"),
    detect_scenes: bool = Query(True, description="是否检测场景"),
    db = Depends(get_db)
):
    """分析视频内容"""
    try:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            analyzer = VideoAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
            result = await analyzer.analyze_video(tmp_path, detect_scenes=detect_scenes)
            
            if "error" in result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(
                        error_code="ANALYSIS_FAILED",
                        error_message=result.get("error", "视频分析失败")
                    ).model_dump()
                )
            
            return success_response(data=result, message="视频分析成功")
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")
                
    except Exception as e:
        logger.error(f"视频分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"视频分析时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/analyze/video/path", response_model=BaseResponse)
async def analyze_video_by_path(
    video_path: str = Query(..., description="视频文件路径"),
    detect_scenes: bool = Query(True, description="是否检测场景"),
    db = Depends(get_db)
):
    """通过路径分析视频内容"""
    try:
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"视频文件不存在: {video_path}"
                ).model_dump()
            )
        
        analyzer = VideoAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
        result = await analyzer.analyze_video(video_path, detect_scenes=detect_scenes)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="ANALYSIS_FAILED",
                    error_message=result.get("error", "视频分析失败")
                ).model_dump()
            )
        
        return success_response(data=result, message="视频分析成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"视频分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"视频分析时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/analyze/audio", response_model=BaseResponse)
async def analyze_audio(
    file: UploadFile = File(..., description="音频文件"),
    extract_features: bool = Query(True, description="是否提取音频特征"),
    db = Depends(get_db)
):
    """分析音频内容"""
    try:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            analyzer = AudioAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
            result = await analyzer.analyze_audio(tmp_path, extract_features=extract_features)
            
            if "error" in result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(
                        error_code="ANALYSIS_FAILED",
                        error_message=result.get("error", "音频分析失败")
                    ).model_dump()
                )
            
            return success_response(data=result, message="音频分析成功")
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")
                
    except Exception as e:
        logger.error(f"音频分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"音频分析时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/analyze/audio/path", response_model=BaseResponse)
async def analyze_audio_by_path(
    audio_path: str = Query(..., description="音频文件路径"),
    extract_features: bool = Query(True, description="是否提取音频特征"),
    db = Depends(get_db)
):
    """通过路径分析音频内容"""
    try:
        if not os.path.exists(audio_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"音频文件不存在: {audio_path}"
                ).model_dump()
            )
        
        analyzer = AudioAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
        result = await analyzer.analyze_audio(audio_path, extract_features=extract_features)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="ANALYSIS_FAILED",
                    error_message=result.get("error", "音频分析失败")
                ).model_dump()
            )
        
        return success_response(data=result, message="音频分析成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音频分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"音频分析时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/fuse", response_model=BaseResponse)
async def fuse_features(
    request: MultimodalFusionRequest,
    db = Depends(get_db)
):
    """融合多模态特征"""
    try:
        fusion = MultimodalFeatureFusion(enable_cache=True, cache_ttl=3600)
        
        # 更新特征权重（如果提供）
        if request.feature_weights:
            fusion.update_feature_weights(request.feature_weights)
        
        # 融合特征
        result = await fusion.fuse_features(
            video_features=request.video_features,
            audio_features=request.audio_features,
            text_features=request.text_features
        )
        
        return success_response(data=result, message="特征融合成功")
    except Exception as e:
        logger.error(f"特征融合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"特征融合时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/similarity", response_model=BaseResponse)
async def calculate_similarity(
    request: SimilarityRequest,
    db = Depends(get_db)
):
    """计算多模态特征相似度"""
    try:
        fusion = MultimodalFeatureFusion(enable_cache=True, cache_ttl=3600)
        
        similarity = await fusion.calculate_similarity(
            features1=request.features1,
            features2=request.features2,
            method=request.method
        )
        
        result = {
            "similarity": similarity,
            "method": request.method,
            "features1_modalities": request.features1.get("modalities", []),
            "features2_modalities": request.features2.get("modalities", [])
        }
        
        return success_response(data=result, message="相似度计算成功")
    except Exception as e:
        logger.error(f"相似度计算失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"相似度计算时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/video/scenes", response_model=BaseResponse)
async def detect_video_scenes(
    video_path: str = Query(..., description="视频文件路径"),
    min_scene_length: float = Query(2.0, ge=0.1, le=10.0, description="最小场景长度（秒）"),
    threshold: float = Query(30.0, ge=0.0, le=100.0, description="场景检测阈值（0-100）"),
    db = Depends(get_db)
):
    """检测视频场景"""
    try:
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"视频文件不存在: {video_path}"
                ).model_dump()
            )
        
        analyzer = VideoAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
        scenes = await analyzer.detect_scenes(
            video_path=video_path,
            min_scene_length=min_scene_length,
            threshold=threshold
        )
        
        return success_response(data={"scenes": scenes, "count": len(scenes)}, message="场景检测成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"场景检测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"场景检测时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/audio/features", response_model=BaseResponse)
async def extract_audio_features(
    audio_path: str = Query(..., description="音频文件路径"),
    db = Depends(get_db)
):
    """提取音频特征"""
    try:
        if not os.path.exists(audio_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"音频文件不存在: {audio_path}"
                ).model_dump()
            )
        
        analyzer = AudioAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
        features = await analyzer.extract_features(audio_path)
        
        return success_response(data=features, message="音频特征提取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音频特征提取失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"音频特征提取时发生错误: {str(e)}"
            ).model_dump()
        )

