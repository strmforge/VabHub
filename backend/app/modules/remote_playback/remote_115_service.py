"""
115 远程播放服务

提供 115 视频播放相关的统一封装
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.strm import STRMFile
from app.models.media import Media, MediaFile
from app.modules.cloud_storage.service import CloudStorageService
from app.core.cloud_storage.providers.cloud_115_api import Cloud115API


class Remote115PlaybackService:
    """115 远程播放服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cloud_storage_service = CloudStorageService()
    
    async def _get_115_api_client(self) -> Optional[Cloud115API]:
        """获取 115 API 客户端"""
        try:
            # 获取 115 云存储配置
            storage = await self.cloud_storage_service.get_storage_by_provider("115")
            if not storage:
                logger.warning("未找到 115 云存储配置")
                return None
            
            # 初始化 provider
            await self.cloud_storage_service.initialize_provider(storage.id)
            provider = self.cloud_storage_service.get_provider(storage.id)
            
            if not provider or not hasattr(provider, '_get_api_client'):
                logger.warning("115 provider 未正确初始化")
                return None
            
            # 获取 API 客户端
            api_client = await provider._get_api_client()
            return api_client
            
        except Exception as e:
            logger.error(f"获取 115 API 客户端失败: {e}", exc_info=True)
            return None
    
    async def get_115_video_play_options(self, work_id: int) -> Dict[str, Any]:
        """
        获取 115 视频播放选项
        
        Args:
            work_id: 作品 ID（Media.id）
        
        Returns:
            播放选项，包含：
            - success: bool
            - work_id: int
            - pick_code: str
            - file_name: str
            - duration: int
            - qualities: list
            - subtitles: list
            - progress: dict (可选)
        """
        try:
            # 1. 查找作品关联的 115 文件
            # 通过 Media -> MediaFile -> STRMFile 查找
            stmt = (
                select(STRMFile)
                .join(MediaFile, STRMFile.media_file_id == MediaFile.id)
                .join(Media, MediaFile.media_id == Media.id)
                .where(
                    Media.id == work_id,
                    STRMFile.cloud_storage == "115"
                )
                .limit(1)
            )
            result = await self.db.execute(stmt)
            strm_file = result.scalar_one_or_none()
            
            if not strm_file:
                return {
                    "success": False,
                    "message": "未找到该作品的 115 绑定"
                }
            
            pick_code = strm_file.cloud_file_id
            if not pick_code:
                return {
                    "success": False,
                    "message": "115 文件缺少 pick_code"
                }
            
            # 2. 获取 115 API 客户端
            api_client = await self._get_115_api_client()
            if not api_client:
                return {
                    "success": False,
                    "message": "115 API 客户端初始化失败"
                }
            
            # 3. 获取播放信息
            play_info = await api_client.get_video_play_info(pick_code)
            if not play_info.get("success"):
                return {
                    "success": False,
                    "message": play_info.get("message", "获取播放信息失败")
                }
            
            # 4. 获取字幕列表
            subtitle_info = await api_client.get_video_subtitles(pick_code)
            subtitles = subtitle_info.get("subtitles", []) if subtitle_info.get("success") else []
            
            # 5. 获取观看历史
            history_info = await api_client.get_video_history(pick_code)
            progress = None
            if history_info.get("success"):
                position = history_info.get("position", 0)
                if position > 0:
                    progress = {
                        "position": position
                    }
            
            # 6. 组装返回结果
            file_info = play_info.get("file", {})
            qualities = play_info.get("qualities", [])
            
            return {
                "success": True,
                "work_id": work_id,
                "pick_code": pick_code,
                "file_name": file_info.get("name", ""),
                "duration": file_info.get("duration", 0),
                "qualities": qualities,
                "subtitles": subtitles,
                "progress": progress
            }
            
        except Exception as e:
            logger.error(f"获取 115 视频播放选项失败 (work_id={work_id}): {e}", exc_info=True)
            return {
                "success": False,
                "message": f"获取播放选项失败: {str(e)}"
            }
    
    async def update_115_video_progress(self, work_id: int, position_sec: int, finished: bool = False) -> Dict[str, Any]:
        """
        更新 115 视频观看进度
        
        Args:
            work_id: 作品 ID（Media.id）
            position_sec: 已播放秒数
            finished: 是否播放完成
        
        Returns:
            更新结果
        """
        try:
            # 1. 查找作品关联的 115 文件
            stmt = (
                select(STRMFile)
                .join(MediaFile, STRMFile.media_file_id == MediaFile.id)
                .join(Media, MediaFile.media_id == Media.id)
                .where(
                    Media.id == work_id,
                    STRMFile.cloud_storage == "115"
                )
                .limit(1)
            )
            result = await self.db.execute(stmt)
            strm_file = result.scalar_one_or_none()
            
            if not strm_file:
                return {
                    "success": False,
                    "message": "未找到该作品的 115 绑定"
                }
            
            pick_code = strm_file.cloud_file_id
            if not pick_code:
                return {
                    "success": False,
                    "message": "115 文件缺少 pick_code"
                }
            
            # 2. 获取 115 API 客户端
            api_client = await self._get_115_api_client()
            if not api_client:
                return {
                    "success": False,
                    "message": "115 API 客户端初始化失败"
                }
            
            # 3. 更新观看历史
            result = await api_client.set_video_history(pick_code, position_sec, finished)
            
            return result
            
        except Exception as e:
            logger.error(f"更新 115 视频观看进度失败 (work_id={work_id}): {e}", exc_info=True)
            return {
                "success": False,
                "message": f"更新观看进度失败: {str(e)}"
            }

