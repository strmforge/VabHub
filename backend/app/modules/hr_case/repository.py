"""
HR案件统一仓库实现
支持双写（DB + 内存缓存），确保数据一致性
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional
from dataclasses import dataclass
import logging

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.database import AsyncSessionLocal
from app.core.intel_local.models import HRTorrentState, HRStatus, TorrentLife
from app.core.intel_local.hr_cache import get_from_cache, set_to_cache
from .models import HrCase, HrCaseStatus, HrCaseLifeStatus


# 转换函数定义在这里以避免循环导入
def _map_hr_status_to_case_status(hr_status: HRStatus) -> HrCaseStatus:
    """将旧的HRStatus映射到新的HrCaseStatus"""
    mapping = {
        HRStatus.NONE: HrCaseStatus.NONE,
        HRStatus.UNKNOWN: HrCaseStatus.NONE,
        HRStatus.ACTIVE: HrCaseStatus.ACTIVE,
        HRStatus.FINISHED: HrCaseStatus.SAFE,
        HRStatus.FAILED: HrCaseStatus.VIOLATED,
    }
    return mapping.get(hr_status, HrCaseStatus.NONE)


def _map_case_status_to_hr_status(case_status: HrCaseStatus) -> HRStatus:
    """将新的HrCaseStatus映射到旧的HRStatus"""
    mapping = {
        HrCaseStatus.NONE: HRStatus.NONE,
        HrCaseStatus.ACTIVE: HRStatus.ACTIVE,
        HrCaseStatus.SAFE: HRStatus.FINISHED,
        HrCaseStatus.VIOLATED: HRStatus.FAILED,
        HrCaseStatus.UNKNOWN: HRStatus.UNKNOWN,  # 未知状态保持不变
    }
    return mapping.get(case_status, HRStatus.NONE)


def from_hr_torrent_state(hr_state: HRTorrentState, site_id: int, site_key: str) -> HrCase:
    """从HRTorrentState转换为HrCase"""
    return HrCase(
        site_id=site_id,
        site_key=site_key,
        torrent_id=hr_state.torrent_id,
        status=_map_hr_status_to_case_status(hr_state.hr_status),
        life_status=HrCaseLifeStatus(hr_state.life_status.value),
        requirement_hours=hr_state.required_seed_hours,
        seeded_hours=hr_state.seeded_hours,
        deadline=hr_state.deadline,
        first_seen_at=hr_state.first_seen_at,
        last_seen_at=hr_state.last_seen_at,
        entered_at=hr_state.first_seen_at if hr_state.hr_status == HRStatus.ACTIVE else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def to_hr_torrent_state(hr_case: HrCase) -> HRTorrentState:
    """从HrCase转换为HRTorrentState（向后兼容）"""
    return HRTorrentState(
        site=hr_case.site_key,
        torrent_id=hr_case.torrent_id,
        hr_status=_map_case_status_to_hr_status(hr_case.status),
        life_status=TorrentLife(hr_case.life_status.value),
        required_seed_hours=hr_case.requirement_hours,
        seeded_hours=hr_case.seeded_hours,
        deadline=hr_case.deadline,
        first_seen_at=hr_case.first_seen_at,
        last_seen_at=hr_case.last_seen_at,
    )


@dataclass
class ConsistencyCheckResult:
    """一致性检查结果"""
    total_checked: int = 0
    mismatches: int = 0
    mismatched_keys: List[tuple[str, str]] = None
    
    def __post_init__(self):
        if self.mismatched_keys is None:
            self.mismatched_keys = []


class SqlAlchemyHrCasesRepository:
    """HR案件SQLAlchemy仓库实现
    
    支持双写策略：
    1. 优先写入数据库（事务性）
    2. DB成功后再更新内存缓存
    3. 失败时记录错误，不写入缓存（避免不一致）
    """
    
    def __init__(self, session_factory=None):
        self._session_factory = session_factory or AsyncSessionLocal
        self._logger = logger.bind(component="HrCasesRepository")
    
    async def _get_site_id(self, site_key: str) -> int:
        """从sites表获取site_id，如果不存在则创建临时ID"""
        try:
            async with self._session_factory() as session:
                from app.models.site import Site
                result = await session.execute(
                    select(Site.id).where(Site.key == site_key)
                )
                site_id = result.scalar_one_or_none()
                
                if site_id is not None:
                    return site_id
                
                # 如果找不到对应的site记录，使用负数临时ID
                # 这将在后续与Site模型集成时被修正
                temp_id = -(hash(site_key) % 1000000)
                self._logger.warning(
                    f"未找到站点 {site_key} 在sites表中，使用临时ID: {temp_id}"
                )
                return temp_id
                
        except Exception as e:
            self._logger.error(f"获取site_id失败: {e}")
            # 降级到临时ID方案
            return -(hash(site_key) % 1000000)
    
    async def get(self, site_key: str, torrent_id: str) -> Optional[HrCase]:
        """获取指定站点的HR案件"""
        async with self._session_factory() as session:
            stmt = select(HrCase).where(
                and_(HrCase.site_key == site_key, HrCase.torrent_id == torrent_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_by_site_and_torrent(self, site_key: str, torrent_id: str) -> Optional[HrCase]:
        """获取指定站点的HR案件（别名方法）"""
        return await self.get(site_key, torrent_id)
    
    async def upsert(self, hr_state: HRTorrentState, site_id: int = None, site_key: str = None) -> HrCase:
        """从HRTorrentState更新HR案件（双写）"""
        
        site_key = site_key or hr_state.site
        if site_id is None:
            # 尝试从sites表获取真实的site_id
            site_id = await self._get_site_id(site_key)
        
        try:
            # 1. 先写数据库
            async with self._session_factory() as session:
                # 查找现有记录
                existing = await session.execute(
                    select(HrCase).where(
                        and_(HrCase.site_key == site_key, HrCase.torrent_id == hr_state.torrent_id)
                    )
                )
                existing_case = existing.scalar_one_or_none()
                
                if existing_case:
                    # 更新现有记录
                    hr_case = from_hr_torrent_state(hr_state, site_id, site_key)
                    hr_case.id = existing_case.id
                    hr_case.created_at = existing_case.created_at
                    hr_case.updated_at = datetime.utcnow()
                    
                    # 保留重要的时间戳
                    if existing_case.entered_at and hr_case.status == HrCaseStatus.ACTIVE:
                        hr_case.entered_at = existing_case.entered_at
                    elif hr_case.status == HrCaseStatus.ACTIVE and not existing_case.entered_at:
                        hr_case.entered_at = datetime.utcnow()
                    
                    # 更新字段
                    for field in ['status', 'life_status', 'requirement_hours', 'seeded_hours', 
                                 'deadline', 'last_seen_at', 'penalized_at', 'deleted_at']:
                        setattr(existing_case, field, getattr(hr_case, field))
                    
                    existing_case.updated_at = datetime.utcnow()
                    await session.commit()
                    hr_case = existing_case
                    
                else:
                    # 创建新记录
                    hr_case = from_hr_torrent_state(hr_state, site_id, site_key)
                    if hr_case.status == HrCaseStatus.ACTIVE:
                        hr_case.entered_at = datetime.utcnow()
                    session.add(hr_case)
                    await session.commit()
                    await session.refresh(hr_case)
            
            # 2. DB成功后再更新内存缓存
            cache_key = (site_key, str(hr_state.torrent_id))
            set_to_cache(site_key, str(hr_state.torrent_id), hr_state)
            
            self._logger.info(f"成功更新HR案件: {site_key}/{hr_state.torrent_id}, 状态: {hr_state.hr_status.value}")
            return hr_case
            
        except Exception as e:
            self._logger.error(f"更新HR案件失败: {site_key}/{hr_state.torrent_id}, 错误: {e}")
            # DB写入失败，不更新内存缓存，避免不一致
            raise
    
    async def upsert_from_hr_page(self, site_key: str, torrent_id: str, 
                                 site_id: int, required_hours: float, 
                                 seeded_hours: float, deadline: Optional[datetime] = None) -> HrCase:
        """从HR页面数据更新案件"""
        
        # 创建或获取HRTorrentState
        hr_state = get_from_cache(site_key, torrent_id)
        if hr_state is None:
            # 如果缓存中没有，创建新的HRTorrentState
            hr_state = HRTorrentState(site=site_key, torrent_id=torrent_id)
        hr_state.hr_status = HRStatus.ACTIVE
        hr_state.required_seed_hours = required_hours
        hr_state.seeded_hours = seeded_hours
        hr_state.deadline = deadline
        hr_state.last_seen_at = datetime.utcnow()
        
        if hr_state.first_seen_at is None:
            hr_state.first_seen_at = datetime.utcnow()
        
        return await self.upsert(hr_state, site_id, site_key)
    
    async def mark_safe(self, site_key: str, torrent_id: str, 
                       reason: str = "hr_finished") -> HrCase:
        """标记为安全状态"""
        
        async with self._session_factory() as session:
            # 获取现有案件
            existing = await session.execute(
                select(HrCase).where(
                    and_(HrCase.site_key == site_key, HrCase.torrent_id == torrent_id)
                )
            )
            hr_case = existing.scalar_one_or_none()
            
            if not hr_case:
                raise ValueError(f"HR案件不存在: {site_key}/{torrent_id}")
            
            # 更新状态
            hr_case.status = HrCaseStatus.SAFE
            hr_case.resolved_at = datetime.utcnow()
            hr_case.updated_at = datetime.utcnow()
            hr_case.notes = hr_case.notes or f"标记为安全: {reason}"
            
            await session.commit()
            
            # 同步更新内存缓存
            cache_key = (site_key, torrent_id)
            cache_state = get_from_cache(site_key, torrent_id)
            if cache_state:
                cache_state.hr_status = HRStatus.FINISHED
                cache_state.last_seen_at = datetime.utcnow()
            
            self._logger.info(f"标记HR案件为安全: {site_key}/{torrent_id}, 原因: {reason}")
            return hr_case
    
    async def mark_penalized(self, site_key: str, torrent_id: str) -> HrCase:
        """标记为HR违规"""
        
        async with self._session_factory() as session:
            # 获取现有案件
            existing = await session.execute(
                select(HrCase).where(
                    and_(HrCase.site_key == site_key, HrCase.torrent_id == torrent_id)
                )
            )
            hr_case = existing.scalar_one_or_none()
            
            if not hr_case:
                # 创建新案件记录
                hr_state = get_from_cache(site_key, torrent_id)
                if hr_state is None:
                    # 如果缓存中没有，创建新的HRTorrentState
                    hr_state = HRTorrentState(site=site_key, torrent_id=torrent_id)
                hr_state.hr_status = HRStatus.FAILED
                hr_state.last_seen_at = datetime.utcnow()
                site_id = hash(site_key) % 1000000  # TODO: 从sites表获取
                hr_case = from_hr_torrent_state(hr_state, site_id, site_key)
                hr_case.penalized_at = datetime.utcnow()
                session.add(hr_case)
            else:
                # 更新现有案件
                hr_case.status = HrCaseStatus.VIOLATED
                hr_case.penalized_at = datetime.utcnow()
                hr_case.updated_at = datetime.utcnow()
            
            await session.commit()
            
            # 同步更新内存缓存
            cache_state = get_from_cache(site_key, torrent_id)
            if cache_state:
                cache_state.hr_status = HRStatus.FAILED
                cache_state.last_seen_at = datetime.utcnow()
                set_to_cache(site_key, torrent_id, cache_state)
            
            self._logger.warning(f"标记HR案件为违规: {site_key}/{torrent_id}")
            return hr_case
    
    async def mark_deleted(self, site_key: str, torrent_id: str) -> HrCase:
        """标记为种子被删除"""
        
        async with self._session_factory() as session:
            # 获取现有案件
            existing = await session.execute(
                select(HrCase).where(
                    and_(HrCase.site_key == site_key, HrCase.torrent_id == torrent_id)
                )
            )
            hr_case = existing.scalar_one_or_none()
            
            if not hr_case:
                # 创建新案件记录
                hr_state = get_from_cache(site_key, torrent_id)
                if hr_state is None:
                    # 如果缓存中没有，创建新的HRTorrentState
                    hr_state = HRTorrentState(site=site_key, torrent_id=torrent_id)
                hr_state.life_status = TorrentLife.DELETED
                hr_state.last_seen_at = datetime.utcnow()
                site_id = hash(site_key) % 1000000  # TODO: 从sites表获取
                hr_case = from_hr_torrent_state(hr_state, site_id, site_key)
                hr_case.deleted_at = datetime.utcnow()
                session.add(hr_case)
            else:
                # 更新现有案件
                hr_case.life_status = HrCaseLifeStatus.DELETED
                hr_case.deleted_at = datetime.utcnow()
                hr_case.updated_at = datetime.utcnow()
            
            await session.commit()
            
            # 同步更新内存缓存
            cache_state = get_from_cache(site_key, torrent_id)
            if cache_state:
                cache_state.life_status = TorrentLife.DELETED
                cache_state.last_seen_at = datetime.utcnow()
                set_to_cache(site_key, torrent_id, cache_state)
            
            self._logger.info(f"标记HR案件为已删除: {site_key}/{torrent_id}")
            return hr_case
    
    async def list_active_for_site(self, site_key: str) -> List[HrCase]:
        """列出站点的活跃HR案件"""
        async with self._session_factory() as session:
            stmt = select(HrCase).where(
                and_(
                    HrCase.site_key == site_key,
                    HrCase.status == HrCaseStatus.ACTIVE,
                    HrCase.life_status == HrCaseLifeStatus.ALIVE
                )
            ).order_by(HrCase.deadline.asc().nullslast())
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def list_by_status(self, status: str, limit: int = 100) -> List[HrCase]:
        """按状态列出案件"""
        async with self._session_factory() as session:
            stmt = select(HrCase).where(
                HrCase.status == status
            ).order_by(HrCase.updated_at.desc()).limit(limit)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def list_by_site(self, site_key: str, limit: int = 100) -> List[HrCase]:
        """列出站点的所有案件"""
        async with self._session_factory() as session:
            stmt = select(HrCase).where(
                HrCase.site_key == site_key
            ).order_by(HrCase.updated_at.desc()).limit(limit)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_statistics(self) -> Dict[str, int]:
        """获取HR案件统计信息"""
        async with self._session_factory() as session:
            # 按状态统计
            status_stats = {}
            for status in HrCaseStatus:
                stmt = select(HrCase).where(HrCase.status == status.value)
                result = await session.execute(stmt)
                count = len(result.scalars().all())
                status_stats[status.value] = count
            
            # 按站点统计
            site_stats = {}
            stmt = select(HrCase.site_key, HrCase.status)
            result = await session.execute(stmt)
            for site_key, status in result.all():
                if site_key not in site_stats:
                    site_stats[site_key] = {}
                if status not in site_stats[site_key]:
                    site_stats[site_key][status] = 0
                site_stats[site_key][status] += 1
            
            return {
                "by_status": status_stats,
                "by_site": site_stats,
                "total": sum(status_stats.values())
            }
    
    async def check_consistency(self) -> ConsistencyCheckResult:
        """检查内存缓存与数据库的一致性"""
        result = ConsistencyCheckResult()
        
        try:
            async with self._session_factory() as session:
                # 遍历内存缓存中的所有条目
                from app.core.intel_local.hr_cache import get_all_cache_items
                for (site_key, torrent_id), cache_state in get_all_cache_items():
                    result.total_checked += 1
                    
                    # 查询数据库中的对应记录
                    db_case = await self.get(site_key, torrent_id)
                    
                    if not db_case:
                        # DB中没有记录但缓存中有
                        result.mismatches += 1
                        result.mismatched_keys.append((site_key, torrent_id))
                        self._logger.warning(f"一致性检查: 缓存中有但DB中无: {site_key}/{torrent_id}")
                        continue
                    
                    # 检查关键字段是否一致
                    cache_status = cache_state.hr_status.value
                    db_status = db_case.status.value
                    
                    if cache_status != db_status:
                        result.mismatches += 1
                        result.mismatched_keys.append((site_key, torrent_id))
                        self._logger.warning(
                            f"一致性检查: 状态不一致 {site_key}/{torrent_id}: "
                            f"缓存={cache_status}, DB={db_status}"
                        )
                
                # 检查DB中有但缓存中没有的记录
                all_db_cases = await session.execute(select(HrCase))
                for db_case in all_db_cases.scalars():
                    cache_key = (db_case.site_key, db_case.torrent_id)
                    cache_state = get_from_cache(db_case.site_key, db_case.torrent_id)
                    if cache_state is None:
                        result.mismatches += 1
                        result.mismatched_keys.append(cache_key)
                        self._logger.warning(f"一致性检查: DB中有但缓存中无: {cache_key}")
                
                self._logger.info(
                    f"一致性检查完成: 检查了{result.total_checked}项, "
                    f"发现{result.mismatches}项不一致"
                )
                
                return result
                
        except Exception as e:
            self._logger.error(f"一致性检查失败: {e}")
            result.mismatches = -1  # 表示检查失败
            return result
    
    async def cleanup_old_cases(self, days: int = 30) -> int:
        """清理旧的已解决案件"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self._session_factory() as session:
            stmt = delete(HrCase).where(
                and_(
                    HrCase.status.in_([HrCaseStatus.SAFE, HrCaseStatus.NONE]),
                    HrCase.resolved_at < cutoff_date,
                    HrCase.resolved_at.isnot(None)
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            self._logger.info(f"清理了{deleted_count}个旧的HR案件")
            return deleted_count


# 向后兼容的适配器
class HrCasesRepositoryAdapter:
    """HrCasesRepository适配器，保持与现有代码的兼容性"""
    
    def __init__(self, repo: SqlAlchemyHrCasesRepository):
        self._repo = repo
    
    async def get(self, site: str, torrent_id: str) -> Optional[HRTorrentState]:
        """获取HRTorrentState（向后兼容）"""
        hr_case = await self._repo.get(site, torrent_id)
        if hr_case:
            return to_hr_torrent_state(hr_case)
        return None
    
    async def upsert(self, state: HRTorrentState) -> HRTorrentState:
        """更新HRTorrentState（向后兼容）"""
        hr_case = await self._repo.upsert(state)
        return to_hr_torrent_state(hr_case)
    
    async def list_active_for_site(self, site: str) -> Iterable[HRTorrentState]:
        """列出站点的活跃HR状态（向后兼容）"""
        hr_cases = await self._repo.list_active_for_site(site)
        return [to_hr_torrent_state(case) for case in hr_cases]


# 全局仓库实例
_hr_repository: Optional[SqlAlchemyHrCasesRepository] = None


def get_hr_repository() -> SqlAlchemyHrCasesRepository:
    """获取HR仓库单例"""
    global _hr_repository
    if _hr_repository is None:
        _hr_repository = SqlAlchemyHrCasesRepository()
    return _hr_repository


def get_hr_repository_adapter() -> HrCasesRepositoryAdapter:
    """获取HR仓库适配器（向后兼容）"""
    return HrCasesRepositoryAdapter(get_hr_repository())
