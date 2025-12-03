"""
全局规则枚举定义
SETTINGS-RULES-1: 全局 HR 策略、分辨率档位、三档模式相关枚举
"""

from enum import Enum


class HRPolicy(str, Enum):
    """HR 策略枚举"""
    IGNORE = "IGNORE"          # 完全不管 HR
    SAFE_SKIP = "SAFE_SKIP"    # 默认跳过 HR/H&R 等高风险
    STRICT_SKIP = "STRICT_SKIP"# 更严（包括未知规则）


class HRMode(str, Enum):
    """HR 模式枚举（三档模式）"""
    A_SAFE = "A_SAFE"          # 档位 A：保种安全
    B_BALANCED = "B_BALANCED"  # 档位 B：平衡（默认）
    C_PRO = "C_PRO"            # 档位 C：老司机


class ResolutionTier(str, Enum):
    """分辨率档位枚举"""
    LOW_720P = "LOW_720P"
    MID_1080P = "MID_1080P"
    HIGH_4K = "HIGH_4K"


class ResolutionPolicy(str, Enum):
    """分辨率策略枚举"""
    AUTO = "AUTO"          # 根据档位+内容自动
    MAX_TIER = "MAX_TIER"  # 只限制最高分辨率
    FIXED_TIER = "FIXED_TIER"  # 死选某档，少数高级用户用


class SourceQualityPolicy(str, Enum):
    """源质量策略枚举"""
    ANY = "ANY"
    NO_TRASH = "NO_TRASH"       # 禁用 CAM/TS 等明显低质
    HIGH_ONLY = "HIGH_ONLY"     # 只要 REMUX/BLURAY/UHD/高码 WEB-DL


class HdrPolicy(str, Enum):
    """HDR 策略枚举"""
    ANY = "ANY"
    HDR_PREFERRED = "HDR_PREFERRED"
    SDR_ONLY = "SDR_ONLY"


class CodecPolicy(str, Enum):
    """编码策略枚举"""
    ANY = "ANY"
    PREFER_H265 = "PREFER_H265"
    PREFER_H264 = "PREFER_H264"


class SubtitlePolicy(str, Enum):
    """字幕策略枚举"""
    ANY = "ANY"
    REQUIRE_ZH = "REQUIRE_ZH"   # 必须有简/繁中字


class AudioLangPolicy(str, Enum):
    """音轨语言策略枚举"""
    ANY = "ANY"
    ORIGINAL_PREFERRED = "ORIGINAL_PREFERRED"   # 原语+多轨优先
    AVOID_MANDARIN_ONLY = "AVOID_MANDARIN_ONLY" # 尽量避开"只有国语配音"


class ExtraFeaturePolicy(str, Enum):
    """额外功能策略枚举（3D等）"""
    ALLOW_3D = "ALLOW_3D"
    FORBID_3D = "FORBID_3D"


class FileMoveBehavior(str, Enum):
    """文件移动行为枚举"""
    MOVE = "MOVE"          # 移动并删除源文件
    COPY = "COPY"          # 复制保留源文件
    HARDLINK = "HARDLINK"  # 硬链接
    STRM_ONLY = "STRM_ONLY"  # 仅生成STRM文件
