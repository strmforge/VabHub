"""
STRM生命周期追踪服务
记录STRM文件从创建到删除的完整生命周期事件
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.strm import STRMLifeEvent, STRMFile


class LifecycleTracker:
    """STRM生命周期追踪器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_create_event(
        self,
        strm_file_id: int,
        cloud_file_id: str,
        cloud_storage: str,
        file_info: Dict[str, Any]
    ):
        """
        记录STRM文件创建事件
        
        Args:
            strm_file_id: STRM文件ID
            cloud_file_id: 云存储文件ID（pick_code）
            cloud_storage: 云存储类型（115/123）
            file_info: 文件信息
        """
        try:
            event = STRMLifeEvent(
                type=1,  # 创建
                file_id=strm_file_id,
                parent_id=file_info.get("parent_id"),
                file_name=file_info.get("file_name", ""),
                file_category=file_info.get("file_category", 1),  # 1:文件
                file_type=file_info.get("file_type", 4),  # 4:视频
                file_size=file_info.get("file_size"),
                sha1=file_info.get("sha1"),
                pick_code=cloud_file_id,
                update_time=file_info.get("update_time"),
                create_time=int(datetime.now(timezone.utc).timestamp())
            )
            self.db.add(event)
            await self.db.commit()
            logger.info(f"记录STRM文件创建事件: file_id={strm_file_id}, pick_code={cloud_file_id}")
        except Exception as e:
            logger.error(f"记录STRM文件创建事件失败: {e}")
            await self.db.rollback()
            raise
    
    async def record_update_event(
        self,
        strm_file_id: int,
        cloud_file_id: str,
        cloud_storage: str,
        file_info: Dict[str, Any]
    ):
        """
        记录STRM文件更新事件
        
        Args:
            strm_file_id: STRM文件ID
            cloud_file_id: 云存储文件ID（pick_code）
            cloud_storage: 云存储类型（115/123）
            file_info: 文件信息
        """
        try:
            event = STRMLifeEvent(
                type=2,  # 更新
                file_id=strm_file_id,
                parent_id=file_info.get("parent_id"),
                file_name=file_info.get("file_name", ""),
                file_category=file_info.get("file_category", 1),
                file_type=file_info.get("file_type", 4),
                file_size=file_info.get("file_size"),
                sha1=file_info.get("sha1"),
                pick_code=cloud_file_id,
                update_time=file_info.get("update_time"),
                create_time=int(datetime.now(timezone.utc).timestamp())
            )
            self.db.add(event)
            await self.db.commit()
            logger.info(f"记录STRM文件更新事件: file_id={strm_file_id}, pick_code={cloud_file_id}")
        except Exception as e:
            logger.error(f"记录STRM文件更新事件失败: {e}")
            await self.db.rollback()
            raise
    
    async def record_delete_event(
        self,
        strm_file_id: Optional[int],
        cloud_file_id: str,
        cloud_storage: str,
        file_info: Dict[str, Any]
    ):
        """
        记录STRM文件删除事件
        
        Args:
            strm_file_id: STRM文件ID（可选，如果为None则通过cloud_file_id查询）
            cloud_file_id: 云存储文件ID（pick_code）
            cloud_storage: 云存储类型（115/123）
            file_info: 文件信息
        """
        try:
            # 如果strm_file_id为None，尝试通过cloud_file_id查询
            if strm_file_id is None:
                result = await self.db.execute(
                    select(STRMFile).where(
                        STRMFile.cloud_file_id == cloud_file_id,
                        STRMFile.cloud_storage == cloud_storage
                    )
                )
                strm_file = result.scalar_one_or_none()
                if strm_file:
                    strm_file_id = strm_file.id
            
            event = STRMLifeEvent(
                type=3,  # 删除
                file_id=strm_file_id,
                parent_id=file_info.get("parent_id"),
                file_name=file_info.get("file_name", ""),
                file_category=file_info.get("file_category", 1),
                file_type=file_info.get("file_type", 4),
                file_size=file_info.get("file_size"),
                sha1=file_info.get("sha1"),
                pick_code=cloud_file_id,
                update_time=file_info.get("update_time"),
                create_time=int(datetime.now(timezone.utc).timestamp())
            )
            self.db.add(event)
            await self.db.commit()
            logger.info(f"记录STRM文件删除事件: file_id={strm_file_id}, pick_code={cloud_file_id}")
        except Exception as e:
            logger.error(f"记录STRM文件删除事件失败: {e}")
            await self.db.rollback()
            raise
    
    async def get_file_lifecycle(
        self,
        strm_file_id: Optional[int] = None,
        cloud_file_id: Optional[str] = None,
        cloud_storage: Optional[str] = None
    ) -> List[STRMLifeEvent]:
        """
        获取文件的完整生命周期事件
        
        Args:
            strm_file_id: STRM文件ID
            cloud_file_id: 云存储文件ID（pick_code）
            cloud_storage: 云存储类型（115/123）
        
        Returns:
            生命周期事件列表
        """
        try:
            query = select(STRMLifeEvent)
            
            if strm_file_id:
                query = query.where(STRMLifeEvent.file_id == strm_file_id)
            elif cloud_file_id and cloud_storage:
                # 先查询STRM文件ID
                result = await self.db.execute(
                    select(STRMFile).where(
                        STRMFile.cloud_file_id == cloud_file_id,
                        STRMFile.cloud_storage == cloud_storage
                    )
                )
                strm_file = result.scalar_one_or_none()
                if strm_file:
                    query = query.where(STRMLifeEvent.file_id == strm_file.id)
                else:
                    return []
            else:
                return []
            
            query = query.order_by(STRMLifeEvent.create_time)
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            return list(events)
        except Exception as e:
            logger.error(f"获取文件生命周期事件失败: {e}")
            return []
    
    async def get_recent_changes(
        self,
        hours: int = 24,
        event_type: Optional[int] = None
    ) -> List[STRMLifeEvent]:
        """
        获取最近N小时内的变更事件
        
        Args:
            hours: 小时数
            event_type: 事件类型（1-创建，2-更新，3-删除），如果为None则返回所有类型
        
        Returns:
            生命周期事件列表
        """
        try:
            since_time = int((datetime.now(timezone.utc).timestamp() - hours * 3600))
            
            query = select(STRMLifeEvent).where(
                STRMLifeEvent.create_time > since_time
            )
            
            if event_type:
                query = query.where(STRMLifeEvent.type == event_type)
            
            query = query.order_by(STRMLifeEvent.create_time.desc())
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            return list(events)
        except Exception as e:
            logger.error(f"获取最近变更事件失败: {e}")
            return []

