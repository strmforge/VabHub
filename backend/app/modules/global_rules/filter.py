"""
全局规则过滤函数
SETTINGS-RULES-1: HR策略过滤、质量过滤、移动行为决策
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.enums.global_rules import (
    HRPolicy, HRMode, ResolutionTier, ResolutionPolicy,
    SourceQualityPolicy, HdrPolicy, CodecPolicy,
    SubtitlePolicy, AudioLangPolicy, ExtraFeaturePolicy,
    FileMoveBehavior
)
from app.models.global_rules import GlobalRuleSettings


def filter_by_hr_policy(
    torrents: List[Dict[str, Any]], 
    hr_policy: str
) -> List[Dict[str, Any]]:
    """
    根据HR策略过滤种子列表
    
    Args:
        torrents: 种子列表，每个种子应包含hr_level字段
        hr_policy: HR策略 (IGNORE/SAFE_SKIP/STRICT_SKIP)
        
    Returns:
        过滤后的种子列表
    """
    if hr_policy == HRPolicy.IGNORE.value:
        # 完全不管HR，返回所有种子
        return torrents
    
    filtered_torrents = []
    skipped_count = 0
    
    for torrent in torrents:
        hr_level = torrent.get('hr_level', 'NONE')
        
        if hr_policy == HRPolicy.SAFE_SKIP.value:
            # 默认跳过HR/H&R等高风险
            if hr_level in ['H&R', 'HR']:
                skipped_count += 1
                continue
        elif hr_policy == HRPolicy.STRICT_SKIP.value:
            # 更严（包括未知规则）
            if hr_level in ['H&R', 'HR', 'H3', 'H5', 'UNKNOWN']:
                skipped_count += 1
                continue
        
        filtered_torrents.append(torrent)
    
    logger.info(f"HR策略过滤完成: 策略={hr_policy}, 跳过={skipped_count}, 保留={len(filtered_torrents)}")
    return filtered_torrents


def apply_global_quality_rules(
    torrents: List[Dict[str, Any]], 
    settings: GlobalRuleSettings
) -> List[Dict[str, Any]]:
    """
    应用全局质量规则过滤
    
    Args:
        torrents: 种子列表，每个种子应包含质量相关字段
        settings: 全局规则设置
        
    Returns:
        过滤后的种子列表
    """
    filtered_torrents = []
    skipped_count = 0
    
    for torrent in torrents:
        # 源质量过滤
        if not _check_source_quality(torrent, settings.source_quality_policy):
            skipped_count += 1
            continue
        
        # 分辨率过滤
        if not _check_resolution(torrent, settings):
            skipped_count += 1
            continue
        
        # HDR过滤
        if not _check_hdr(torrent, settings.hdr_policy):
            skipped_count += 1
            continue
        
        # 编码过滤
        if not _check_codec(torrent, settings.codec_policy):
            skipped_count += 1
            continue
        
        # 字幕过滤
        if not _check_subtitle(torrent, settings.subtitle_policy):
            skipped_count += 1
            continue
        
        # 音轨过滤
        if not _check_audio_lang(torrent, settings.audio_lang_policy):
            skipped_count += 1
            continue
        
        # 3D过滤
        if not _check_3d(torrent, settings.extra_feature_policy):
            skipped_count += 1
            continue
        
        filtered_torrents.append(torrent)
    
    logger.info(f"全局质量规则过滤完成: 跳过={skipped_count}, 保留={len(filtered_torrents)}")
    return filtered_torrents


def resolve_file_move_behavior(
    requested_behavior: str,
    hr_mode: str,
    is_strm_generation: bool = False
) -> str:
    """
    解析文件移动行为，根据HR模式调整
    
    Args:
        requested_behavior: 请求的移动行为
        hr_mode: HR模式 (A_SAFE/B_BALANCED/C_PRO)
        is_strm_generation: 是否为STRM生成场景
        
    Returns:
        调整后的移动行为
    """
    if hr_mode == HRMode.C_PRO.value:
        # C档老司机模式：强制关闭移动整理避免保种炸雷
        if requested_behavior == FileMoveBehavior.MOVE.value:
            if is_strm_generation:
                # STRM生成时允许，但降级为STRM_ONLY
                logger.warning("C档模式：本地移动降级为STRM生成")
                return FileMoveBehavior.STRM_ONLY.value
            else:
                # 网盘移动时降级为复制
                logger.warning("C档模式：网盘移动降级为复制")
                return FileMoveBehavior.COPY.value
        
        elif requested_behavior == FileMoveBehavior.HARDLINK.value:
            # 硬链接在C档模式下允许
            return requested_behavior
    
    elif hr_mode == HRMode.A_SAFE.value:
        # A档保种安全模式：限制移动行为
        if requested_behavior == FileMoveBehavior.MOVE.value:
            if is_strm_generation:
                # STRM生成允许
                return requested_behavior
            else:
                # 本地移动降级为硬链接或复制
                logger.warning("A档模式：本地移动降级为硬链接")
                return FileMoveBehavior.HARDLINK.value
    
    # B档平衡模式：保持原有行为
    return requested_behavior


def _check_source_quality(torrent: Dict[str, Any], policy: str) -> bool:
    """检查源质量"""
    if policy == SourceQualityPolicy.ANY.value:
        return True
    
    quality = torrent.get('source_quality', '').lower()
    
    if policy == SourceQualityPolicy.NO_TRASH.value:
        # 禁用CAM/TS等明显低质
        trash_qualities = ['cam', 'ts', 'tc', 'workprint', 'wp']
        return not any(trash in quality for trash in trash_qualities)
    
    elif policy == SourceQualityPolicy.HIGH_ONLY.value:
        # 只要REMUX/BLURAY/UHD/高码WEB-DL
        high_qualities = ['remux', 'bluray', 'bd', 'uhd', 'web-dl', 'webrip']
        return any(high in quality for high in high_qualities)
    
    return True


def _check_resolution(torrent: Dict[str, Any], settings: GlobalRuleSettings) -> bool:
    """检查分辨率"""
    resolution = torrent.get('resolution', '').lower()
    
    if settings.resolution_policy == ResolutionPolicy.AUTO.value:
        # 根据档位+内容自动
        if settings.resolution_tier == ResolutionTier.LOW_720P.value:
            return '720p' in resolution or '480p' in resolution
        elif settings.resolution_tier == ResolutionTier.MID_1080P.value:
            return '1080p' in resolution or '720p' in resolution
        elif settings.resolution_tier == ResolutionTier.HIGH_4K.value:
            return '4k' in resolution or '2160p' in resolution or '1080p' in resolution
    
    elif settings.resolution_policy == ResolutionPolicy.MAX_TIER.value:
        # 只限制最高分辨率
        if settings.resolution_tier == ResolutionTier.LOW_720P.value:
            return not ('1080p' in resolution or '4k' in resolution or '2160p' in resolution)
        elif settings.resolution_tier == ResolutionTier.MID_1080P.value:
            return not ('4k' in resolution or '2160p' in resolution)
        elif settings.resolution_tier == ResolutionTier.HIGH_4K.value:
            return True  # 4K档位不限制
    
    elif settings.resolution_policy == ResolutionPolicy.FIXED_TIER.value:
        # 死选某档
        if settings.resolution_tier == ResolutionTier.LOW_720P.value:
            return '720p' in resolution or '480p' in resolution
        elif settings.resolution_tier == ResolutionTier.MID_1080P.value:
            return '1080p' in resolution
        elif settings.resolution_tier == ResolutionTier.HIGH_4K.value:
            return '4k' in resolution or '2160p' in resolution
    
    return True


def _check_hdr(torrent: Dict[str, Any], policy: str) -> bool:
    """检查HDR"""
    if policy == HdrPolicy.ANY.value:
        return True
    
    hdr_info = torrent.get('hdr', '').lower()
    has_hdr = any(hdr_type in hdr_info for hdr_type in ['hdr', 'dolby vision', 'dv'])
    
    if policy == HdrPolicy.HDR_PREFERRED.value:
        return True  # HDR优先，但不强制
    
    elif policy == HdrPolicy.SDR_ONLY.value:
        return not has_hdr
    
    return True


def _check_codec(torrent: Dict[str, Any], policy: str) -> bool:
    """检查编码"""
    if policy == CodecPolicy.ANY.value:
        return True
    
    codec = torrent.get('codec', '').lower()
    
    if policy == CodecPolicy.PREFER_H265.value:
        return True  # H265优先，但不强制
    
    elif policy == CodecPolicy.PREFER_H264.value:
        return True  # H264优先，但不强制
    
    return True


def _check_subtitle(torrent: Dict[str, Any], policy: str) -> bool:
    """检查字幕"""
    if policy == SubtitlePolicy.ANY.value:
        return True
    
    subtitles = torrent.get('subtitles', [])
    
    if policy == SubtitlePolicy.REQUIRE_ZH.value:
        # 必须有简/繁中字
        has_chinese = any(
            'zh' in sub.get('language', '').lower() or 
            'chinese' in sub.get('language', '').lower() or
            '中' in sub.get('language', '')
            for sub in subtitles
        )
        return has_chinese
    
    return True


def _check_audio_lang(torrent: Dict[str, Any], policy: str) -> bool:
    """检查音轨语言"""
    if policy == AudioLangPolicy.ANY.value:
        return True
    
    audio_tracks = torrent.get('audio_tracks', [])
    
    if policy == AudioLangPolicy.ORIGINAL_PREFERRED.value:
        return True  # 原语+多轨优先，但不强制
    
    elif policy == AudioLangPolicy.AVOID_MANDARIN_ONLY.value:
        # 尽量避开"只有国语配音"
        if len(audio_tracks) == 1:
            lang = audio_tracks[0].get('language', '').lower()
            return not ('mandarin' in lang or '国语' in lang or '中文' in lang)
    
    return True


def _check_3d(torrent: Dict[str, Any], policy: str) -> bool:
    """检查3D"""
    title = torrent.get('title', '').lower()
    is_3d = '3d' in title or 'sbs' in title or 'ou' in title
    
    if policy == ExtraFeaturePolicy.ALLOW_3D.value:
        return True
    
    elif policy == ExtraFeaturePolicy.FORBID_3D.value:
        return not is_3d
    
    return True
