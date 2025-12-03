"""
实时推荐模块
支持流式推荐计算、实时特征更新、A/B测试
"""

from .stream_processor import StreamProcessor
from .feature_updater import FeatureUpdater
from .ab_testing import ABTestingFramework

__all__ = [
    "StreamProcessor",
    "FeatureUpdater",
    "ABTestingFramework",
]

