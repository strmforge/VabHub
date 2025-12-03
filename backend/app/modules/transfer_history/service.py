"""
转移历史记录服务
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from sqlalchemy.orm import selectinload
from loguru import logger

from app.models.transfer_history import TransferHistory


class TransferHistoryService:
    """转移历史记录服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_history(
        self,
        src: str,
        dest: str,
        src_storage: str = "local",
        dest_storage: str = "local",
        mode: str = "move",
        media_info: Optional[Dict[str, Any]] = None,
        file_size: Optional[int] = None,
        status: bool = True,
        errmsg: Optional[str] = None,
        downloader: Optional[str] = None,
        download_hash: Optional[str] = None,
        files: Optional[List[Dict[str, Any]]] = None
    ) -> TransferHistory:
        """创建转移历史记录"""
        try:
            # 格式化日期字符串
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            history = TransferHistory(
                src=src,
                dest=dest,
                src_storage=src_storage,
                dest_storage=dest_storage,
                mode=mode,
                file_size=file_size,
                status=status,
                errmsg=errmsg,
                downloader=downloader,
                download_hash=download_hash,
                date=date_str,
                files=files or []
            )
            
            # 设置媒体信息
            if media_info:
                history.type = media_info.get("media_type")
                history.category = media_info.get("category")
                history.title = media_info.get("title")
                history.year = str(media_info.get("year")) if media_info.get("year") else None
                history.tmdbid = media_info.get("tmdb_id")
                history.imdbid = media_info.get("imdb_id")
                history.tvdbid = media_info.get("tvdb_id")
                history.doubanid = media_info.get("douban_id")
                history.seasons = media_info.get("season")
                history.episodes = media_info.get("episode")
                history.episode_group = media_info.get("episode_group")
                history.image = media_info.get("poster_url")
            
            self.db.add(history)
            await self.db.commit()
            await self.db.refresh(history)
            
            logger.info(f"转移历史记录已创建: {src} -> {dest}")
            return history
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建转移历史记录失败: {e}")
            raise
    
    async def list_by_page(
        self,
        page: int = 1,
        count: int = 50,
        status: Optional[bool] = None
    ) -> List[TransferHistory]:
        """分页查询转移历史"""
        try:
            query = select(TransferHistory)
            
            if status is not None:
                query = query.where(TransferHistory.status == status)
            
            query = query.order_by(TransferHistory.created_at.desc())
            
            if count >= 0:
                query = query.offset((page - 1) * count).limit(count)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"查询转移历史失败: {e}")
            return []
    
    async def list_by_title(
        self,
        title: str,
        page: int = 1,
        count: int = 50,
        status: Optional[bool] = None
    ) -> List[TransferHistory]:
        """按标题搜索转移历史"""
        try:
            query = select(TransferHistory).where(
                or_(
                    TransferHistory.title.like(f'%{title}%'),
                    TransferHistory.src.like(f'%{title}%'),
                    TransferHistory.dest.like(f'%{title}%')
                )
            )
            
            if status is not None:
                query = query.where(TransferHistory.status == status)
            
            query = query.order_by(TransferHistory.created_at.desc())
            
            if count >= 0:
                query = query.offset((page - 1) * count).limit(count)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"搜索转移历史失败: {e}")
            return []
    
    async def count(
        self,
        status: Optional[bool] = None
    ) -> int:
        """统计转移历史总数"""
        try:
            query = select(func.count(TransferHistory.id))
            
            if status is not None:
                query = query.where(TransferHistory.status == status)
            
            result = await self.db.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"统计转移历史失败: {e}")
            return 0
    
    async def count_by_title(
        self,
        title: str,
        status: Optional[bool] = None
    ) -> int:
        """按标题统计转移历史"""
        try:
            query = select(func.count(TransferHistory.id)).where(
                or_(
                    TransferHistory.title.like(f'%{title}%'),
                    TransferHistory.src.like(f'%{title}%'),
                    TransferHistory.dest.like(f'%{title}%')
                )
            )
            
            if status is not None:
                query = query.where(TransferHistory.status == status)
            
            result = await self.db.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"统计转移历史失败: {e}")
            return 0
    
    async def delete_history(self, history_id: int) -> bool:
        """删除转移历史记录"""
        try:
            result = await self.db.execute(
                delete(TransferHistory).where(TransferHistory.id == history_id)
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除转移历史记录失败: {e}")
            return False
    
    async def get_by_hash(self, download_hash: str) -> Optional[TransferHistory]:
        """根据下载器hash获取转移历史"""
        try:
            result = await self.db.execute(
                select(TransferHistory).where(TransferHistory.download_hash == download_hash)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"查询转移历史失败: {e}")
            return None

