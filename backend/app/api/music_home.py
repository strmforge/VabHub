"""
音乐首页 API

提供音乐中心首页榜单/推荐数据

Created: 0.0.3 DISCOVER-MUSIC-HOME P4
"""

from fastapi import APIRouter
from loguru import logger

from app.core.schemas import success_response
from app.services.music_discover_service import get_music_discover_service

router = APIRouter()


@router.get("/home", summary="获取音乐首页内容")
async def get_music_home():
    """
    获取音乐首页聚合内容
    
    聚合 RSSHub 榜单和本地配置的榜单源：
    - 网易云热歌榜
    - QQ 音乐热歌榜
    - 本地配置的榜单
    
    返回：
    - sections: 各榜单区块
    - has_rsshub: RSSHub 是否可用
    - has_local_charts: 是否有本地榜单
    - message: 状态提示
    """
    try:
        service = get_music_discover_service()
        result = await service.get_home()
        
        return {
            "sections": [s.model_dump() for s in result.sections],
            "has_rsshub": result.has_rsshub,
            "has_local_charts": result.has_local_charts,
            "message": result.message,
        }
        
    except Exception as e:
        logger.error(f"获取音乐首页内容失败: {e}")
        return {
            "sections": [],
            "has_rsshub": False,
            "has_local_charts": False,
            "message": f"获取内容失败: {str(e)}",
        }
