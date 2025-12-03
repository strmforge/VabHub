"""
GPU工具模块
提供GPU检测、设备选择等功能，支持Docker环境
"""

import os
from typing import Optional
from loguru import logger

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, GPU features will be disabled")


def check_gpu_available(enable_gpu: bool = True) -> bool:
    """
    检查GPU是否可用
    
    Args:
        enable_gpu: 是否启用GPU（配置开关）
    
    Returns:
        bool: GPU是否可用
    """
    if not TORCH_AVAILABLE:
        return False
    
    if not enable_gpu:
        logger.info("GPU disabled by configuration")
        return False
    
    # 检查CUDA是否可用
    if not torch.cuda.is_available():
        logger.info("CUDA not available, using CPU")
        return False
    
    # 检查CUDA设备数量
    device_count = torch.cuda.device_count()
    if device_count == 0:
        logger.info("No CUDA devices found, using CPU")
        return False
    
    # 检查Docker环境（通过环境变量）
    # 在Docker环境中，即使有GPU，也可能无法访问
    if os.getenv("DOCKER_CONTAINER") == "true":
        # 检查NVIDIA环境变量（Docker GPU支持）
        nvidia_visible = os.getenv("NVIDIA_VISIBLE_DEVICES")
        if nvidia_visible == "" or nvidia_visible == "void":
            logger.warning("Docker container detected but NVIDIA_VISIBLE_DEVICES is not set, using CPU")
            return False
    
    logger.info(f"GPU available: {device_count} device(s)")
    return True


def get_device(enable_gpu: bool = True, device_id: Optional[int] = None) -> str:
    """
    获取计算设备（CPU或GPU）
    
    Args:
        enable_gpu: 是否启用GPU（配置开关）
        device_id: GPU设备ID（None表示使用默认设备）
    
    Returns:
        str: 设备名称（'cuda' 或 'cpu'）
    """
    if not TORCH_AVAILABLE:
        return "cpu"
    
    if not enable_gpu:
        return "cpu"
    
    if check_gpu_available(enable_gpu):
        if device_id is not None:
            return f"cuda:{device_id}"
        return "cuda"
    
    return "cpu"


def get_device_info() -> dict:
    """
    获取设备信息
    
    Returns:
        dict: 设备信息
    """
    info = {
        "torch_available": TORCH_AVAILABLE,
        "gpu_available": False,
        "device_count": 0,
        "current_device": "cpu",
        "device_name": "CPU"
    }
    
    if not TORCH_AVAILABLE:
        return info
    
    if torch.cuda.is_available():
        info["gpu_available"] = True
        info["device_count"] = torch.cuda.device_count()
        info["current_device"] = f"cuda:0"
        info["device_name"] = torch.cuda.get_device_name(0)
    
    return info

