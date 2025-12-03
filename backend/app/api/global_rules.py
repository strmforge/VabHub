"""
全局规则设置API
SETTINGS-RULES-1: 提供全局规则的 REST 接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from app.core.database import get_db
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)
from app.models.global_rules import GlobalRuleSettings
from app.models.enums.global_rules import (
    HRPolicy, HRMode, ResolutionTier, ResolutionPolicy,
    SourceQualityPolicy, HdrPolicy, CodecPolicy,
    SubtitlePolicy, AudioLangPolicy, ExtraFeaturePolicy
)

router = APIRouter()


class GlobalRuleSettingsResponse(BaseModel):
    """全局规则设置响应模型"""
    id: int
    hr_policy: str
    hr_mode: str
    resolution_policy: str
    resolution_tier: str
    source_quality_policy: str
    hdr_policy: str
    codec_policy: str
    subtitle_policy: str
    audio_lang_policy: str
    extra_feature_policy: str
    created_at: datetime
    updated_at: datetime
    created_by: str = None
    updated_by: str = None


class GlobalRuleSettingsUpdateRequest(BaseModel):
    """全局规则设置更新请求模型"""
    hr_policy: str = None
    hr_mode: str = None
    resolution_policy: str = None
    resolution_tier: str = None
    source_quality_policy: str = None
    hdr_policy: str = None
    codec_policy: str = None
    subtitle_policy: str = None
    audio_lang_policy: str = None
    extra_feature_policy: str = None
    updated_by: str = None


class GlobalRuleModeProfileResponse(BaseModel):
    """全局规则模式配置响应模型"""
    mode: str
    mode_name: str
    description: str
    settings: Dict[str, str]
    warnings: list[str] = []


@router.get("/global", response_model=BaseResponse[GlobalRuleSettingsResponse])
async def get_global_rules(
    db: AsyncSession = Depends(get_db)
):
    """
    获取全局规则设置
    
    Returns:
        全局规则设置数据
    """
    try:
        # 查询全局规则设置（固定ID为1）
        result = await db.execute(
            select(GlobalRuleSettings).where(GlobalRuleSettings.id == 1)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 如果不存在，创建默认设置
            logger.info("全局规则设置不存在，创建默认设置")
            default_data = GlobalRuleSettings.get_default_settings()
            settings = GlobalRuleSettings(
                id=1,
                **default_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        
        return success_response(
            data=GlobalRuleSettingsResponse(
                id=settings.id,
                hr_policy=settings.hr_policy,
                hr_mode=settings.hr_mode,
                resolution_policy=settings.resolution_policy,
                resolution_tier=settings.resolution_tier,
                source_quality_policy=settings.source_quality_policy,
                hdr_policy=settings.hdr_policy,
                codec_policy=settings.codec_policy,
                subtitle_policy=settings.subtitle_policy,
                audio_lang_policy=settings.audio_lang_policy,
                extra_feature_policy=settings.extra_feature_policy,
                created_at=settings.created_at,
                updated_at=settings.updated_at,
                created_by=settings.created_by,
                updated_by=settings.updated_by
            ),
            message="获取全局规则设置成功"
        )
        
    except Exception as e:
        logger.error(f"获取全局规则设置失败: {e}")
        return error_response(
            message="获取全局规则设置失败",
            details=str(e)
        )


@router.put("/global", response_model=BaseResponse[GlobalRuleSettingsResponse])
async def update_global_rules(
    request: GlobalRuleSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新全局规则设置
    
    Args:
        request: 更新请求数据
        
    Returns:
        更新后的全局规则设置
    """
    try:
        # 查询现有设置
        result = await db.execute(
            select(GlobalRuleSettings).where(GlobalRuleSettings.id == 1)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 如果不存在，创建新设置
            logger.info("全局规则设置不存在，创建新设置")
            default_data = GlobalRuleSettings.get_default_settings()
            settings = GlobalRuleSettings(
                id=1,
                **default_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(settings)
        
        # 验证枚举值
        if request.hr_policy and request.hr_policy not in [e.value for e in HRPolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的HR策略: {request.hr_policy}"
            )
        
        if request.hr_mode and request.hr_mode not in [e.value for e in HRMode]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的HR模式: {request.hr_mode}"
            )
        
        if request.resolution_policy and request.resolution_policy not in [e.value for e in ResolutionPolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的分辨率策略: {request.resolution_policy}"
            )
        
        if request.resolution_tier and request.resolution_tier not in [e.value for e in ResolutionTier]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的分辨率档位: {request.resolution_tier}"
            )
        
        if request.source_quality_policy and request.source_quality_policy not in [e.value for e in SourceQualityPolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的源质量策略: {request.source_quality_policy}"
            )
        
        if request.hdr_policy and request.hdr_policy not in [e.value for e in HdrPolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的HDR策略: {request.hdr_policy}"
            )
        
        if request.codec_policy and request.codec_policy not in [e.value for e in CodecPolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的编码策略: {request.codec_policy}"
            )
        
        if request.subtitle_policy and request.subtitle_policy not in [e.value for e in SubtitlePolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的字幕策略: {request.subtitle_policy}"
            )
        
        if request.audio_lang_policy and request.audio_lang_policy not in [e.value for e in AudioLangPolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的音轨策略: {request.audio_lang_policy}"
            )
        
        if request.extra_feature_policy and request.extra_feature_policy not in [e.value for e in ExtraFeaturePolicy]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的额外功能策略: {request.extra_feature_policy}"
            )
        
        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(settings)
        
        logger.info(f"全局规则设置更新成功，HR模式: {settings.hr_mode}")
        
        return success_response(
            data=GlobalRuleSettingsResponse(
                id=settings.id,
                hr_policy=settings.hr_policy,
                hr_mode=settings.hr_mode,
                resolution_policy=settings.resolution_policy,
                resolution_tier=settings.resolution_tier,
                source_quality_policy=settings.source_quality_policy,
                hdr_policy=settings.hdr_policy,
                codec_policy=settings.codec_policy,
                subtitle_policy=settings.subtitle_policy,
                audio_lang_policy=settings.audio_lang_policy,
                extra_feature_policy=settings.extra_feature_policy,
                created_at=settings.created_at,
                updated_at=settings.updated_at,
                created_by=settings.created_by,
                updated_by=settings.updated_by
            ),
            message="更新全局规则设置成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新全局规则设置失败: {e}")
        await db.rollback()
        return error_response(
            message="更新全局规则设置失败",
            details=str(e)
        )


@router.get("/global/mode-profiles", response_model=BaseResponse[list[GlobalRuleModeProfileResponse]])
async def get_mode_profiles():
    """
    获取三档模式的预设配置
    
    Returns:
        三档模式的预设配置列表
    """
    try:
        # A档（保种安全）预设
        a_safe_profile = {
            "hr_policy": HRPolicy.STRICT_SKIP.value,
            "resolution_policy": ResolutionPolicy.MAX_TIER.value,
            "resolution_tier": ResolutionTier.MID_1080P.value,
            "source_quality_policy": SourceQualityPolicy.NO_TRASH.value,
            "hdr_policy": HdrPolicy.SDR_ONLY.value,
            "codec_policy": CodecPolicy.ANY.value,
            "subtitle_policy": SubtitlePolicy.ANY.value,
            "audio_lang_policy": AudioLangPolicy.ANY.value,
            "extra_feature_policy": ExtraFeaturePolicy.FORBID_3D.value
        }
        
        # B档（平衡）预设
        b_balanced_profile = {
            "hr_policy": HRPolicy.SAFE_SKIP.value,
            "resolution_policy": ResolutionPolicy.AUTO.value,
            "resolution_tier": ResolutionTier.HIGH_4K.value,
            "source_quality_policy": SourceQualityPolicy.NO_TRASH.value,
            "hdr_policy": HdrPolicy.ANY.value,
            "codec_policy": CodecPolicy.ANY.value,
            "subtitle_policy": SubtitlePolicy.ANY.value,
            "audio_lang_policy": AudioLangPolicy.ANY.value,
            "extra_feature_policy": ExtraFeaturePolicy.FORBID_3D.value
        }
        
        # C档（老司机）预设
        c_pro_profile = {
            "hr_policy": HRPolicy.IGNORE.value,
            "resolution_policy": ResolutionPolicy.AUTO.value,
            "resolution_tier": ResolutionTier.HIGH_4K.value,
            "source_quality_policy": SourceQualityPolicy.ANY.value,
            "hdr_policy": HdrPolicy.HDR_PREFERRED.value,
            "codec_policy": CodecPolicy.ANY.value,
            "subtitle_policy": SubtitlePolicy.ANY.value,
            "audio_lang_policy": AudioLangPolicy.ORIGINAL_PREFERRED.value,
            "extra_feature_policy": ExtraFeaturePolicy.FORBID_3D.value
        }
        
        profiles = [
            GlobalRuleModeProfileResponse(
                mode=HRMode.A_SAFE.value,
                mode_name="A档 - 保种安全",
                description="限制HR、分辨率最高1080p，禁止3D，默认只复制/硬链接",
                settings=a_safe_profile,
                warnings=["STRM允许", "本地只允许复制/硬链接", "网盘禁止移动上传"]
            ),
            GlobalRuleModeProfileResponse(
                mode=HRMode.B_BALANCED.value,
                mode_name="B档 - 平衡模式",
                description="默认平衡设置，允许4K，保留移动整理功能",
                settings=b_balanced_profile,
                warnings=["STRM允许", "本地移动允许", "网盘移动允许"]
            ),
            GlobalRuleModeProfileResponse(
                mode=HRMode.C_PRO.value,
                mode_name="C档 - 老司机模式",
                description="解锁高阶行为，但强制禁用移动整理避免保种炸雷",
                settings=c_pro_profile,
                warnings=[
                    "如使用，系统将禁用『网盘移动上传』或『本地移动保存』，避免导致保种炸雷，请谨慎使用。",
                    "STRM允许", "本地移动强制降级为复制/硬链接", "网盘移动强制降级为复制"
                ]
            )
        ]
        
        return success_response(
            data=profiles,
            message="获取三档模式预设配置成功"
        )
        
    except Exception as e:
        logger.error(f"获取三档模式预设配置失败: {e}")
        return error_response(
            message="获取三档模式预设配置失败",
            details=str(e)
        )


@router.post("/global/reset", response_model=BaseResponse[GlobalRuleSettingsResponse])
async def reset_global_rules(
    mode: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    重置全局规则设置到默认值或指定模式
    
    Args:
        mode: 可选，指定重置到哪个模式（A_SAFE/B_BALANCED/C_PRO）
        
    Returns:
        重置后的全局规则设置
    """
    try:
        # 查询现有设置
        result = await db.execute(
            select(GlobalRuleSettings).where(GlobalRuleSettings.id == 1)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 如果不存在，创建新设置
            settings = GlobalRuleSettings(id=1)
            db.add(settings)
        
        # 获取重置配置
        if mode:
            if mode not in [e.value for e in HRMode]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的HR模式: {mode}"
                )
            
            # 获取指定模式的预设配置
            profiles_result = await get_mode_profiles()
            profiles = profiles_result.data["data"]
            target_profile = next((p for p in profiles if p["mode"] == mode), None)
            
            if not target_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"未找到模式配置: {mode}"
                )
            
            reset_data = target_profile["settings"]
            logger.info(f"重置全局规则设置到 {mode} 模式")
        else:
            # 重置到默认值
            reset_data = GlobalRuleSettings.get_default_settings()
            logger.info("重置全局规则设置到默认值")
        
        # 应用重置配置
        for field, value in reset_data.items():
            setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(settings)
        
        return success_response(
            data=GlobalRuleSettingsResponse(
                id=settings.id,
                hr_policy=settings.hr_policy,
                hr_mode=settings.hr_mode,
                resolution_policy=settings.resolution_policy,
                resolution_tier=settings.resolution_tier,
                source_quality_policy=settings.source_quality_policy,
                hdr_policy=settings.hdr_policy,
                codec_policy=settings.codec_policy,
                subtitle_policy=settings.subtitle_policy,
                audio_lang_policy=settings.audio_lang_policy,
                extra_feature_policy=settings.extra_feature_policy,
                created_at=settings.created_at,
                updated_at=settings.updated_at,
                created_by=settings.created_by,
                updated_by=settings.updated_by
            ),
            message=f"重置全局规则设置成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置全局规则设置失败: {e}")
        await db.rollback()
        return error_response(
            message="重置全局规则设置失败",
            details=str(e)
        )
