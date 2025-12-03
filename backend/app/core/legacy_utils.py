"""
过往版本功能工具 - 提供便捷的调用函数
简化过往版本功能的调用
"""

from typing import Dict, List, Optional, Any
from loguru import logger
from app.core.legacy_adapter import get_legacy_adapter, get_recommendation_engine, get_media_parser, get_music_charts_service


async def get_user_recommendations(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    获取用户推荐（便捷函数）
    
    Args:
        user_id: 用户ID
        limit: 返回数量
        
    Returns:
        推荐列表
    """
    try:
        engine = get_recommendation_engine(version="vabhub_1")
        if engine and hasattr(engine, "update_recommendations"):
            recommendations = engine.update_recommendations(user_id)
            return recommendations[:limit]
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
    return []


def parse_media_filename(file_path: str) -> Optional[Dict[str, Any]]:
    """
    解析媒体文件名（便捷函数）
    
    Args:
        file_path: 文件路径
        
    Returns:
        解析结果
    """
    try:
        parser = get_media_parser(version="vabhub_1")
        if parser:
            return parser.parse_filename(file_path)
    except Exception as e:
        logger.error(f"解析文件名失败: {e}")
    return None


async def get_music_charts(platform: str, chart_type: str = "hot", limit: int = 50) -> List[Dict[str, Any]]:
    """
    获取音乐榜单（便捷函数）
    
    Args:
        platform: 平台（qq_music, netease, spotify等）
        chart_type: 榜单类型（hot, new, trending等）
        limit: 返回数量
        
    Returns:
        榜单列表
    """
    try:
        service = get_music_charts_service(version="vabhub_1")
        if service and hasattr(service, "get_charts"):
            charts = await service.get_charts(platform, chart_type, "CN", limit)
            return charts
    except Exception as e:
        logger.error(f"获取榜单失败: {e}")
    return []


def list_available_functions() -> Dict[str, Dict[str, Any]]:
    """
    列出所有可用功能（便捷函数）
    
    Returns:
        功能列表
    """
    adapter = get_legacy_adapter()
    return adapter.get_available_functions()

