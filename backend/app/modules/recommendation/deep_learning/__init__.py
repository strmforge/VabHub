"""
深度学习推荐模块
支持神经协同过滤（NCF）、深度因子分解机（DeepFM）、自编码器等模型
"""

from .gpu_utils import check_gpu_available, get_device
from .trainer import DeepLearningTrainer
from .predictor import DeepLearningPredictor

__all__ = [
    "check_gpu_available",
    "get_device",
    "DeepLearningTrainer",
    "DeepLearningPredictor",
]

