"""
电视墙状态聚合服务

批量预加载 + 内存聚合方案，避免N+1查询问题
"""
from typing import List, Dict, Set, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from dataclasses import dataclass
from datetime import datetime

from app.models.media import Media
from app.models.media_file import MediaFile
from app.models.strm import STRMFile
from app.models.user_video_progress import UserVideoProgress
from app.models.subscription import Subscription
from app.models.download import DownloadTask
from app.core.intel_local.repo.sqlalchemy import SqlAlchemyHRCasesRepository
from app.core.intel_local.repo.hr_cases_repo import HRCasesRepository


@dataclass
class MediaStatusInfo:
    """媒体状态信息"""
    has_subscription: bool = False
    subscription_status: Optional[str] = None
    has_active_downloads: bool = False
    download_count: int = 0
    library_status: str = 'not_in_library'
    hr_risk: bool = False
    hr_level: Optional[str] = None
    has_progress: bool = False
    progress_percent: float = 0.0
    is_finished: bool = False


class PlayerWallAggregationService:
    """电视墙状态聚合服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hr_repo: HRCasesRepository = SqlAlchemyHRCasesRepository(lambda: db)
    
    async def aggregate_media_list_with_status(
        self,
        media_list: List[Media],
        user_id: int
    ) -> List[Tuple[Media, MediaStatusInfo]]:
        """
        聚合媒体列表和状态信息
        
        Args:
            media_list: 媒体列表
            user_id: 用户ID
            
        Returns:
            List[Tuple[Media, MediaStatusInfo]]: 聚合后的列表
        """
        if not media_list:
            return []
        
        # 提取所有媒体ID
        media_ids = [media.id for media in media_list]
        media_tmdb_ids = {media.id: media.tmdb_id for media in media_list}
        
        # 并行批量查询各种状态
        (
            local_files_map,
            strm_files_map,
            subscription_map,
            active_downloads_map,
            progress_map,
            hr_risk_map
        ) = await self._batch_query_status(media_ids, media_tmdb_ids, user_id)
        
        # 聚合结果
        result = []
        for media in media_list:
            status_info = self._build_status_info(
                media.id,
                local_files_map,
                strm_files_map,
                subscription_map,
                active_downloads_map,
                progress_map,
                hr_risk_map
            )
            result.append((media, status_info))
        
        return result
    
    async def _batch_query_status(
        self,
        media_ids: List[int],
        media_tmdb_ids: Dict[int, Optional[int]],
        user_id: int
    ) -> Tuple[
        Dict[int, bool],      # local_files_map
        Dict[int, bool],      # strm_files_map
        Dict[int, Dict],      # subscription_map
        Dict[int, int],       # active_downloads_map
        Dict[int, Dict],      # progress_map
        Dict[int, Dict]       # hr_risk_map
    ]:
        """批量查询各种状态"""
        
        # 1. 查询本地文件状态
        local_files_query = (
            select(MediaFile.media_id)
            .where(MediaFile.media_id.in_(media_ids))
            .distinct()
        )
        local_files_result = await self.db.execute(local_files_query)
        local_files_map = {row[0]: True for row in local_files_result.fetchall()}
        
        # 2. 查询115源状态
        strm_files_query = (
            select(STRMFile.media_file_id, MediaFile.media_id)
            .join(MediaFile, STRMFile.media_file_id == MediaFile.id)
            .where(
                and_(
                    MediaFile.media_id.in_(media_ids),
                    STRMFile.cloud_storage == "115"
                )
            )
            .distinct()
        )
        strm_files_result = await self.db.execute(strm_files_query)
        strm_files_map = {row[1]: True for row in strm_files_result.fetchall()}
        
        # 3. 查询订阅状态（用户相关，通过tmdb_id关联）
        subscription_query = (
            select(Subscription.tmdb_id, Subscription.status)
            .where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.tmdb_id.in_([tmdb_id for tmdb_id in media_tmdb_ids.values() if tmdb_id])
                )
            )
        )
        subscription_result = await self.db.execute(subscription_query)
        subscription_map = {}
        for row in subscription_result.fetchall():
            tmdb_id, status = row
            # 通过tmdb_id找到对应的media_id
            for media_id, media_tmdb_id in media_tmdb_ids.items():
                if media_tmdb_id == tmdb_id:
                    subscription_map[media_id] = {"status": status}
                    break
        
        # 4. 查询活跃下载任务（DownloadTask没有user_id和media_id字段，暂时跳过）
        # TODO: 需要确认下载任务如何关联到用户和作品
        active_downloads_map = {}
        
        # 5. 查询播放进度（用户相关）
        progress_query = (
            select(UserVideoProgress.work_id, UserVideoProgress.progress_percent, UserVideoProgress.is_finished)
            .where(
                and_(
                    UserVideoProgress.user_id == user_id,
                    UserVideoProgress.work_id.in_(media_ids)
                )
            )
        )
        progress_result = await self.db.execute(progress_query)
        progress_map = {
            row[0]: {
                "progress_percent": row[1],
                "is_finished": row[2]
            }
            for row in progress_result.fetchall()
        }
        
        # 6. 查询HR风险状态（批量查询）
        hr_risk_map = await self._batch_query_hr_risk(media_tmdb_ids)
        
        return (
            local_files_map,
            strm_files_map,
            subscription_map,
            active_downloads_map,
            progress_map,
            hr_risk_map
        )
    
    async def _batch_query_hr_risk(self, media_tmdb_ids: Dict[int, Optional[int]]) -> Dict[int, Dict]:
        """批量查询HR风险状态"""
        hr_risk_map = {}
        
        # 只查询有TMDB ID的作品
        valid_tmdb_ids = [(mid, tmdb_id) for mid, tmdb_id in media_tmdb_ids.items() if tmdb_id]
        
        if not valid_tmdb_ids:
            return hr_risk_map
        
        try:
            # 由于HR仓库没有批量查询方法，暂时逐个查询
            # TODO: 后续可以优化为批量查询或添加缓存
            for media_id, tmdb_id in valid_tmdb_ids:
                try:
                    # 检查是否有get_by_tmdb_id方法
                    if hasattr(self.hr_repo, 'get_by_tmdb_id'):
                        hr_cases = await self.hr_repo.get_by_tmdb_id(tmdb_id)
                    else:
                        # 如果没有get_by_tmdb_id方法，暂时返回无风险
                        hr_cases = None
                    
                    if hr_cases:
                        # 计算风险等级
                        risk_level = self._calculate_hr_risk_level(hr_cases)
                        hr_risk_map[media_id] = {
                            "hr_risk": True,
                            "hr_level": risk_level
                        }
                    else:
                        hr_risk_map[media_id] = {
                            "hr_risk": False,
                            "hr_level": None
                        }
                except Exception as e:
                    # 单个查询失败，默认为无风险
                    print(f"查询HR风险失败 (media_id={media_id}, tmdb_id={tmdb_id}): {e}")
                    hr_risk_map[media_id] = {
                        "hr_risk": False,
                        "hr_level": None
                    }
                    
        except Exception as e:
            # 整体查询失败，默认所有作品为无风险
            print(f"批量查询HR风险失败: {e}")
            for media_id, _ in valid_tmdb_ids:
                hr_risk_map[media_id] = {
                    "hr_risk": False,
                    "hr_level": None
                }
        
        return hr_risk_map
    
    def _calculate_hr_risk_level(self, hr_cases) -> Optional[str]:
        """计算HR风险等级"""
        if not hr_cases:
            return None
        
        # 根据HR案例数量和类型计算风险等级
        risk_count = len(hr_cases)
        
        if risk_count == 0:
            return None
        elif risk_count <= 2:
            return "low"
        elif risk_count <= 5:
            return "medium"
        else:
            return "high"
    
    def _build_status_info(
        self,
        media_id: int,
        local_files_map: Dict[int, bool],
        strm_files_map: Dict[int, bool],
        subscription_map: Dict[int, Dict],
        active_downloads_map: Dict[int, int],
        progress_map: Dict[int, Dict],
        hr_risk_map: Dict[int, Dict]
    ) -> MediaStatusInfo:
        """构建状态信息"""
        
        # 订阅状态
        subscription_info = subscription_map.get(media_id, {})
        has_subscription = bool(subscription_info)
        subscription_status = subscription_info.get("status") if has_subscription else None
        
        # 下载状态
        download_count = active_downloads_map.get(media_id, 0)
        has_active_downloads = download_count > 0
        
        # 入库状态
        has_local = local_files_map.get(media_id, False)
        has_115 = strm_files_map.get(media_id, False)
        if has_local:
            library_status = "in_library"
        elif has_115:
            library_status = "partial"
        else:
            library_status = "not_in_library"
        
        # HR风险状态
        hr_info = hr_risk_map.get(media_id, {})
        hr_risk = hr_info.get("hr_risk", False)
        hr_level = hr_info.get("hr_level")
        
        # 播放进度
        progress_info = progress_map.get(media_id, {})
        has_progress = bool(progress_info)
        progress_percent = progress_info.get("progress_percent", 0.0)
        is_finished = progress_info.get("is_finished", False)
        
        return MediaStatusInfo(
            has_subscription=has_subscription,
            subscription_status=subscription_status,
            has_active_downloads=has_active_downloads,
            download_count=download_count,
            library_status=library_status,
            hr_risk=hr_risk,
            hr_level=hr_level,
            has_progress=has_progress,
            progress_percent=progress_percent,
            is_finished=is_finished
        )
