"""
TTS 存储策略定义

定义统一的 TTS 存储清理策略，支持按类别（playground/job/other）配置不同的保留规则。
"""
from dataclasses import dataclass
from typing import Optional
from app.core.config import Settings


@dataclass(frozen=True)
class TTSStorageCategoryPolicy:
    """单个类别的存储策略"""
    # 至少保留多少天内的文件不删（0 表示不按天限制）
    min_keep_days: int = 0
    
    # 至少保留多少个最新文件（保护最近生成的）
    min_keep_files: int = 0
    
    # 最多允许保留多少个文件（超过部分按时间从旧到新删）
    max_keep_files: Optional[int] = None


@dataclass(frozen=True)
class TTSStoragePolicy:
    """TTS 存储策略"""
    playground: TTSStorageCategoryPolicy
    job: TTSStorageCategoryPolicy
    other: TTSStorageCategoryPolicy
    
    # 策略名称
    name: str = "default"
    
    # 预留：整体上限等
    # global_max_files: Optional[int] = None


def get_default_storage_policy(settings: Settings) -> TTSStoragePolicy:
    """
    获取默认的 TTS 存储策略
    
    当前实现为硬编码的默认策略，后续可以扩展为从配置文件加载。
    
    Args:
        settings: 配置对象（预留，当前未使用）
    
    Returns:
        TTSStoragePolicy: 默认策略
    """
    # 默认策略：
    # - playground: 保留最近 7 天，至少 10 个，最多 1000 个
    # - job: 保留最近 14 天，至少 20 个，最多 5000 个
    # - other: 保留最近 3 天，至少 5 个，最多 500 个
    
    return TTSStoragePolicy(
        name="default",
        playground=TTSStorageCategoryPolicy(
            min_keep_days=7,
            min_keep_files=10,
            max_keep_files=1000
        ),
        job=TTSStorageCategoryPolicy(
            min_keep_days=14,
            min_keep_files=20,
            max_keep_files=5000
        ),
        other=TTSStorageCategoryPolicy(
            min_keep_days=3,
            min_keep_files=5,
            max_keep_files=500
        )
    )

