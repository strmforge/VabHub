"""
全局规则服务
SETTINGS-RULES-1: 统一管理全局规则逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
from loguru import logger

from app.models.global_rules import GlobalRuleSettings
from app.models.enums.global_rules import (
    HRPolicy, HRMode, ResolutionTier, ResolutionPolicy,
    SourceQualityPolicy, HdrPolicy, CodecPolicy,
    SubtitlePolicy, AudioLangPolicy, ExtraFeaturePolicy
)
from .filter import filter_by_hr_policy, apply_global_quality_rules, resolve_file_move_behavior


class GlobalRulesService:
    """全局规则服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cached_settings: Optional[GlobalRuleSettings] = None
    
    async def get_settings(self, force_refresh: bool = False) -> GlobalRuleSettings:
        """
        获取全局规则设置
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            全局规则设置对象
        """
        # 检查缓存是否需要刷新（基于更新时间）
        if (self._cached_settings is not None and 
            not force_refresh and 
            hasattr(self._cached_settings, 'updated_at')):
            
            # 查询数据库中的更新时间
            result = await self.db.execute(
                select(GlobalRuleSettings.updated_at).where(GlobalRuleSettings.id == 1)
            )
            db_updated_at = result.scalar_one_or_none()
            
            if db_updated_at and db_updated_at > self._cached_settings.updated_at:
                logger.info("检测到设置更新，刷新缓存")
                force_refresh = True
        
        if self._cached_settings is None or force_refresh:
            result = await self.db.execute(
                select(GlobalRuleSettings).where(GlobalRuleSettings.id == 1)
            )
            settings = result.scalar_one_or_none()
            
            if not settings:
                logger.warning("全局规则设置不存在，创建默认设置")
                default_data = GlobalRuleSettings.get_default_settings()
                settings = GlobalRuleSettings(id=1, **default_data)
                self.db.add(settings)
                await self.db.commit()
                await self.db.refresh(settings)
            
            self._cached_settings = settings
        
        return self._cached_settings
    
    async def update_settings(self, update_data: Dict[str, Any]) -> GlobalRuleSettings:
        """
        更新全局规则设置
        
        Args:
            update_data: 更新数据
            
        Returns:
            更新后的设置对象
        """
        settings = await self.get_settings()
        
        # 验证枚举值
        for field, value in update_data.items():
            if hasattr(settings, field):
                setattr(settings, field, value)
        
        await self.db.commit()
        await self.db.refresh(settings)
        
        # 刷新缓存
        self._cached_settings = settings
        
        logger.info(f"全局规则设置更新成功，HR模式: {settings.hr_mode}")
        return settings
    
    async def reset_to_mode(self, mode: str) -> GlobalRuleSettings:
        """
        重置到指定模式的预设配置
        
        Args:
            mode: HR模式 (A_SAFE/B_BALANCED/C_PRO)
            
        Returns:
            重置后的设置对象
        """
        if mode not in [e.value for e in HRMode]:
            raise ValueError(f"无效的HR模式: {mode}")
        
        # 获取模式预设配置
        mode_profile = self._get_mode_profile(mode)
        
        # 应用预设配置
        settings = await self.get_settings()
        for field, value in mode_profile.items():
            setattr(settings, field, value)
        
        settings.hr_mode = mode
        await self.db.commit()
        await self.db.refresh(settings)
        
        # 刷新缓存
        self._cached_settings = settings
        
        logger.info(f"全局规则设置重置到 {mode} 模式")
        return settings
    
    async def filter_torrents(self, torrents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根据全局规则过滤种子列表
        
        Args:
            torrents: 种子列表
            
        Returns:
            过滤后的种子列表
        """
        settings = await self.get_settings()
        
        # 1. HR策略过滤
        filtered_torrents = filter_by_hr_policy(torrents, settings.hr_policy)
        
        # 2. 质量规则过滤
        filtered_torrents = apply_global_quality_rules(filtered_torrents, settings)
        
        logger.info(f"全局规则过滤完成: 输入={len(torrents)}, 输出={len(filtered_torrents)}")
        return filtered_torrents
    
    async def resolve_move_behavior(
        self, 
        requested_behavior: str, 
        is_strm_generation: bool = False
    ) -> str:
        """
        解析文件移动行为
        
        Args:
            requested_behavior: 请求的移动行为
            is_strm_generation: 是否为STRM生成场景
            
        Returns:
            调整后的移动行为
        """
        settings = await self.get_settings()
        return resolve_file_move_behavior(
            requested_behavior, 
            settings.hr_mode, 
            is_strm_generation
        )
    
    def is_c_pro_mode(self, settings: Optional[GlobalRuleSettings] = None) -> bool:
        """
        检查是否为C档老司机模式
        
        Args:
            settings: 设置对象（可选，如果不提供则使用缓存）
            
        Returns:
            是否为C档模式
        """
        if settings is None:
            if self._cached_settings is None:
                raise ValueError("设置未加载，请先调用 get_settings()")
            settings = self._cached_settings
        
        return settings.is_c_pro_mode()
    
    def is_a_safe_mode(self, settings: Optional[GlobalRuleSettings] = None) -> bool:
        """检查是否为A档安全模式"""
        if settings is None:
            if self._cached_settings is None:
                raise ValueError("设置未加载，请先调用 get_settings()")
            settings = self._cached_settings
        
        return settings.is_a_safe_mode()
    
    def is_b_balanced_mode(self, settings: Optional[GlobalRuleSettings] = None) -> bool:
        """检查是否为B档平衡模式"""
        if settings is None:
            if self._cached_settings is None:
                raise ValueError("设置未加载，请先调用 get_settings()")
            settings = self._cached_settings
        
        return settings.is_b_balanced_mode()
    
    def get_mode_warnings(self, mode: str) -> List[str]:
        """
        获取指定模式的警告信息
        
        Args:
            mode: HR模式
            
        Returns:
            警告信息列表
        """
        warnings = []
        
        if mode == HRMode.A_SAFE.value:
            warnings.extend([
                "STRM允许",
                "本地只允许复制/硬链接", 
                "网盘禁止移动上传"
            ])
        elif mode == HRMode.B_BALANCED.value:
            warnings.extend([
                "STRM允许",
                "本地移动允许",
                "网盘移动允许"
            ])
        elif mode == HRMode.C_PRO.value:
            warnings.extend([
                "如使用，系统将禁用『网盘移动上传』或『本地移动保存』，避免导致保种炸雷，请谨慎使用。",
                "STRM允许",
                "本地移动强制降级为复制/硬链接",
                "网盘移动强制降级为复制"
            ])
        
        return warnings
    
    def _get_mode_profile(self, mode: str) -> Dict[str, str]:
        """
        获取指定模式的预设配置
        
        Args:
            mode: HR模式
            
        Returns:
            模式配置字典
        """
        profiles = {
            HRMode.A_SAFE.value: {
                "hr_policy": HRPolicy.STRICT_SKIP.value,
                "resolution_policy": ResolutionPolicy.MAX_TIER.value,
                "resolution_tier": ResolutionTier.MID_1080P.value,
                "source_quality_policy": SourceQualityPolicy.NO_TRASH.value,
                "hdr_policy": HdrPolicy.SDR_ONLY.value,
                "codec_policy": CodecPolicy.ANY.value,
                "subtitle_policy": SubtitlePolicy.ANY.value,
                "audio_lang_policy": AudioLangPolicy.ANY.value,
                "extra_feature_policy": ExtraFeaturePolicy.FORBID_3D.value
            },
            HRMode.B_BALANCED.value: {
                "hr_policy": HRPolicy.SAFE_SKIP.value,
                "resolution_policy": ResolutionPolicy.AUTO.value,
                "resolution_tier": ResolutionTier.HIGH_4K.value,
                "source_quality_policy": SourceQualityPolicy.NO_TRASH.value,
                "hdr_policy": HdrPolicy.ANY.value,
                "codec_policy": CodecPolicy.ANY.value,
                "subtitle_policy": SubtitlePolicy.ANY.value,
                "audio_lang_policy": AudioLangPolicy.ANY.value,
                "extra_feature_policy": ExtraFeaturePolicy.FORBID_3D.value
            },
            HRMode.C_PRO.value: {
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
        }
        
        return profiles.get(mode, profiles[HRMode.B_BALANCED.value])
    
    async def get_mode_profiles(self) -> List[Dict[str, Any]]:
        """
        获取所有模式配置信息
        
        Returns:
            模式配置列表
        """
        profiles = []
        mode_names = {
            HRMode.A_SAFE.value: "A档 - 保种安全",
            HRMode.B_BALANCED.value: "B档 - 平衡模式", 
            HRMode.C_PRO.value: "C档 - 老司机模式"
        }
        mode_descriptions = {
            HRMode.A_SAFE.value: "限制HR、分辨率最高1080p，禁止3D，默认只复制/硬链接",
            HRMode.B_BALANCED.value: "默认平衡设置，允许4K，保留移动整理功能",
            HRMode.C_PRO.value: "解锁高阶行为，但强制禁用移动整理避免保种炸雷"
        }
        
        for mode in [HRMode.A_SAFE.value, HRMode.B_BALANCED.value, HRMode.C_PRO.value]:
            profiles.append({
                "mode": mode,
                "mode_name": mode_names[mode],
                "description": mode_descriptions[mode],
                "settings": self._get_mode_profile(mode),
                "warnings": self.get_mode_warnings(mode)
            })
        
        return profiles
