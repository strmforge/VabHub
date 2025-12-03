"""
SQLAlchemy-based repositories for Local Intel.

These implementations bridge the Protocol interfaces with the ORM
models defined in ``app.models.intel_local``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable, Optional, List

from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.intel_local.models import (
    HRTorrentState,
    SiteGuardProfile as SiteGuardProfileState,
    HRStatus,
    TorrentLife,
)
from app.models.intel_local import (
    HRCase as HRCaseModel,
    SiteGuardProfile as SiteGuardProfileModel,
    SiteGuardEvent as SiteGuardEventModel,
    InboxCursor as InboxCursorModel,
    TorrentIndex as TorrentIndexModel,
)
from .hr_cases_repo import HRCasesRepository
from .site_guard_repo import SiteGuardRepository, SiteGuardEventRecord
from .inbox_cursor_repo import InboxCursorRepository, InboxCursorRecord
from .torrent_index_repo import (
    TorrentIndexRepository,
    TorrentIndexRecord,
    TorrentIndexCreate,
    TorrentSearchParams,
)


SessionFactory = Callable[[], AsyncSession]


def _state_from_hr_model(model: HRCaseModel) -> HRTorrentState:
    state = HRTorrentState(site=model.site, torrent_id=model.torrent_id)
    state.hr_status = HRStatus(model.hr_status)
    state.life_status = TorrentLife(model.life_status)
    state.required_seed_hours = model.required_seed_hours
    state.seeded_hours = model.seeded_hours or 0.0
    state.deadline = model.deadline
    state.first_seen_at = model.first_seen_at
    state.last_seen_at = model.last_seen_at
    return state


class SqlAlchemyHRCasesRepository(HRCasesRepository):
    """Persist HR states using SQLAlchemy models."""

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    async def get(self, site: str, torrent_id: str) -> Optional[HRTorrentState]:
        async with self._session_factory() as session:
            stmt = select(HRCaseModel).where(
                HRCaseModel.site == site,
                HRCaseModel.torrent_id == torrent_id,
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record is None:
                return None
            return _state_from_hr_model(record)

    async def upsert(self, state: HRTorrentState) -> HRTorrentState:
        async with self._session_factory() as session:
            stmt = select(HRCaseModel).where(
                HRCaseModel.site == state.site,
                HRCaseModel.torrent_id == state.torrent_id,
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()

            now = datetime.utcnow()
            if record is None:
                record = HRCaseModel(
                    site=state.site,
                    torrent_id=state.torrent_id,
                    hr_status=state.hr_status.value,
                    life_status=state.life_status.value,
                    required_seed_hours=state.required_seed_hours,
                    seeded_hours=state.seeded_hours,
                    deadline=state.deadline,
                    first_seen_at=state.first_seen_at or now,
                    last_seen_at=state.last_seen_at or now,
                )
                session.add(record)
            else:
                record.hr_status = state.hr_status.value
                record.life_status = state.life_status.value
                record.required_seed_hours = state.required_seed_hours
                record.seeded_hours = state.seeded_hours
                record.deadline = state.deadline
                record.last_seen_at = state.last_seen_at or now
                if state.first_seen_at:
                    record.first_seen_at = state.first_seen_at

            await session.commit()
            return state

    async def list_active_for_site(self, site: str) -> Iterable[HRTorrentState]:
        async with self._session_factory() as session:
            stmt = select(HRCaseModel).where(HRCaseModel.site == site)
            result = await session.execute(stmt)
            return [_state_from_hr_model(row) for row in result.scalars().all()]


class SqlAlchemySiteGuardRepository(SiteGuardRepository):
    """Persist Site Guard profiles and block events."""

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    async def get_profile(self, site: str) -> SiteGuardProfileState:
        async with self._session_factory() as session:
            stmt = select(SiteGuardProfileModel).where(
                SiteGuardProfileModel.site == site
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record is None:
                return SiteGuardProfileState(site=site)

            profile = SiteGuardProfileState(site=site)
            profile.last_block_start = record.last_block_start
            profile.last_block_end = record.last_block_end
            profile.last_block_cause = record.last_block_cause
            profile.last_full_scan_minutes = record.last_full_scan_minutes
            profile.last_full_scan_pages = record.last_full_scan_pages
            profile.safe_scan_minutes = record.safe_scan_minutes
            profile.safe_pages_per_hour = record.safe_pages_per_hour
            profile.updated_at = record.updated_at
            return profile

    async def save_profile(self, profile: SiteGuardProfileState) -> None:
        async with self._session_factory() as session:
            stmt = select(SiteGuardProfileModel).where(
                SiteGuardProfileModel.site == profile.site
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            now = datetime.utcnow()

            if record is None:
                record = SiteGuardProfileModel(
                    site=profile.site,
                    last_block_start=profile.last_block_start,
                    last_block_end=profile.last_block_end,
                    last_block_cause=profile.last_block_cause,
                    last_full_scan_minutes=profile.last_full_scan_minutes,
                    last_full_scan_pages=profile.last_full_scan_pages,
                    safe_scan_minutes=profile.safe_scan_minutes,
                    safe_pages_per_hour=profile.safe_pages_per_hour,
                    updated_at=now,
                )
                session.add(record)
            else:
                record.last_block_start = profile.last_block_start
                record.last_block_end = profile.last_block_end
                record.last_block_cause = profile.last_block_cause
                record.last_full_scan_minutes = profile.last_full_scan_minutes
                record.last_full_scan_pages = profile.last_full_scan_pages
                record.safe_scan_minutes = profile.safe_scan_minutes
                record.safe_pages_per_hour = profile.safe_pages_per_hour
                record.updated_at = now

            await session.commit()

    async def record_block_event(
        self,
        site: str,
        block_until: datetime,
        cause: str,
        scan_minutes_before_block: Optional[int],
        scan_pages_before_block: Optional[int],
        now: Optional[datetime] = None,
    ) -> SiteGuardEventRecord:
        async with self._session_factory() as session:
            event = SiteGuardEventModel(
                site=site,
                event_type="block",
                created_at=now or datetime.utcnow(),
                block_until=block_until,
                scan_minutes_before_block=scan_minutes_before_block,
                scan_pages_before_block=scan_pages_before_block,
                cause=cause,
            )
            session.add(event)
            await session.commit()
            return SiteGuardEventRecord(
                id=event.id,
                site=event.site,
                event_type=event.event_type,
                created_at=event.created_at,
                block_until=event.block_until,
                scan_minutes_before_block=event.scan_minutes_before_block,
                scan_pages_before_block=event.scan_pages_before_block,
                cause=event.cause,
            )

    async def get_latest_block(self, site: str) -> Optional[SiteGuardEventRecord]:
        async with self._session_factory() as session:
            stmt = (
                select(SiteGuardEventModel)
                .where(SiteGuardEventModel.site == site)
                .order_by(SiteGuardEventModel.created_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record is None:
                return None
            return SiteGuardEventRecord(
                id=record.id,
                site=record.site,
                event_type=record.event_type,
                created_at=record.created_at,
                block_until=record.block_until,
                scan_minutes_before_block=record.scan_minutes_before_block,
                scan_pages_before_block=record.scan_pages_before_block,
                cause=record.cause,
            )


class SqlAlchemyInboxCursorRepository(InboxCursorRepository):
    """Persist inbox cursors, ensuring we process each message once."""

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    async def get(self, site: str) -> InboxCursorRecord:
        async with self._session_factory() as session:
            stmt = select(InboxCursorModel).where(InboxCursorModel.site == site)
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record is None:
                return InboxCursorRecord(site=site, last_message_id=None, last_checked_at=None)
            return InboxCursorRecord(
                site=record.site,
                last_message_id=record.last_message_id,
                last_checked_at=record.last_checked_at,
            )

    async def save(self, cursor: InboxCursorRecord) -> None:
        async with self._session_factory() as session:
            stmt = select(InboxCursorModel).where(InboxCursorModel.site == cursor.site)
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()

            if record is None:
                record = InboxCursorModel(
                    site=cursor.site,
                    last_message_id=cursor.last_message_id,
                    last_checked_at=cursor.last_checked_at,
                )
                session.add(record)
            else:
                record.last_message_id = cursor.last_message_id
                record.last_checked_at = cursor.last_checked_at or datetime.utcnow()

            await session.commit()


class SqlAlchemyTorrentIndexRepository(TorrentIndexRepository):
    """Persist Torrent Index using SQLAlchemy models."""

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    def _model_to_record(self, model: TorrentIndexModel) -> TorrentIndexRecord:
        """将 ORM 模型转换为记录对象"""
        return TorrentIndexRecord(
            id=model.id,
            site_id=model.site_id,
            torrent_id=model.torrent_id,
            title_raw=model.title_raw,
            title_clean=model.title_clean,
            category=model.category,
            is_hr=bool(model.is_hr),
            is_free=bool(model.is_free),
            is_half_free=bool(model.is_half_free),
            size_bytes=model.size_bytes,
            seeders=model.seeders,
            leechers=model.leechers,
            completed=model.completed,
            published_at=model.published_at,
            last_seen_at=model.last_seen_at,
            is_deleted=bool(model.is_deleted),
            deleted_at=model.deleted_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def upsert_many(self, rows: List[TorrentIndexCreate]) -> int:
        """批量插入或更新 Torrent Index 记录"""
        if not rows:
            return 0

        async with self._session_factory() as session:
            count = 0
            now = datetime.utcnow()

            for row in rows:
                # 检查是否已存在
                stmt = select(TorrentIndexModel).where(
                    TorrentIndexModel.site_id == row.site_id,
                    TorrentIndexModel.torrent_id == row.torrent_id,
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing is None:
                    # 插入新记录
                    new_record = TorrentIndexModel(
                        site_id=row.site_id,
                        torrent_id=row.torrent_id,
                        title_raw=row.title_raw,
                        title_clean=row.title_clean,
                        category=row.category,
                        is_hr=1 if row.is_hr else 0,
                        is_free=1 if row.is_free else 0,
                        is_half_free=1 if row.is_half_free else 0,
                        size_bytes=row.size_bytes,
                        seeders=row.seeders,
                        leechers=row.leechers,
                        completed=row.completed,
                        published_at=row.published_at,
                        last_seen_at=row.last_seen_at or now,
                        is_deleted=0,
                        deleted_at=None,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(new_record)
                    count += 1
                else:
                    # 更新现有记录
                    existing.title_raw = row.title_raw
                    if row.title_clean:
                        existing.title_clean = row.title_clean
                    if row.category:
                        existing.category = row.category
                    existing.is_hr = 1 if row.is_hr else 0
                    existing.is_free = 1 if row.is_free else 0
                    existing.is_half_free = 1 if row.is_half_free else 0
                    if row.size_bytes is not None:
                        existing.size_bytes = row.size_bytes
                    existing.seeders = row.seeders
                    existing.leechers = row.leechers
                    if row.completed is not None:
                        existing.completed = row.completed
                    if row.published_at:
                        existing.published_at = row.published_at
                    existing.last_seen_at = row.last_seen_at or now
                    # 如果之前被标记为删除，但现在又出现了，恢复它
                    if existing.is_deleted == 1:
                        existing.is_deleted = 0
                        existing.deleted_at = None
                    existing.updated_at = now
                    count += 1

            await session.commit()
            return count

    async def mark_deleted(
        self,
        site_id: str,
        torrent_id: str,
        deleted_at: datetime | None = None,
    ) -> bool:
        """标记种子为已删除"""
        async with self._session_factory() as session:
            stmt = select(TorrentIndexModel).where(
                TorrentIndexModel.site_id == site_id,
                TorrentIndexModel.torrent_id == torrent_id,
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()

            if record is None:
                return False

            record.is_deleted = 1
            record.deleted_at = deleted_at or datetime.utcnow()
            record.updated_at = datetime.utcnow()
            await session.commit()
            return True

    async def query_for_search(
        self,
        params: TorrentSearchParams,
    ) -> List[TorrentIndexRecord]:
        """根据搜索参数查询 Torrent Index"""
        async with self._session_factory() as session:
            # 构建基础查询
            stmt = select(TorrentIndexModel)

            # 构建 WHERE 条件
            conditions = []

            # 排除已删除的记录（默认）
            if params.exclude_deleted:
                conditions.append(TorrentIndexModel.is_deleted == 0)

            # 关键词搜索（在 title_raw 中搜索）
            if params.keyword:
                keyword_pattern = f"%{params.keyword}%"
                conditions.append(
                    TorrentIndexModel.title_raw.ilike(keyword_pattern)
                )

            # 分类过滤
            if params.category:
                conditions.append(TorrentIndexModel.category == params.category)

            # 站点过滤
            if params.site_ids:
                conditions.append(TorrentIndexModel.site_id.in_(params.site_ids))

            # HR 过滤
            if params.hr_filter == "exclude_hr":
                conditions.append(TorrentIndexModel.is_hr == 0)
            elif params.hr_filter == "hr_only":
                conditions.append(TorrentIndexModel.is_hr == 1)
            # "any" 不添加条件

            # 做种者数量过滤
            if params.min_seeders is not None:
                conditions.append(TorrentIndexModel.seeders >= params.min_seeders)
            if params.max_seeders is not None:
                conditions.append(TorrentIndexModel.seeders <= params.max_seeders)

            # 大小过滤
            if params.min_size_bytes is not None:
                conditions.append(
                    TorrentIndexModel.size_bytes >= params.min_size_bytes
                )
            if params.max_size_bytes is not None:
                conditions.append(
                    TorrentIndexModel.size_bytes <= params.max_size_bytes
                )

            # 应用所有条件
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # 排序
            if params.sort == "seeders":
                stmt = stmt.order_by(TorrentIndexModel.seeders.desc())
            elif params.sort == "published_at":
                stmt = stmt.order_by(
                    TorrentIndexModel.published_at.desc().nulls_last()
                )
            elif params.sort == "size":
                stmt = stmt.order_by(
                    TorrentIndexModel.size_bytes.desc().nulls_last()
                )
            else:
                # 默认排序：按发布时间降序，然后按做种者数量降序
                stmt = stmt.order_by(
                    TorrentIndexModel.published_at.desc().nulls_last(),
                    TorrentIndexModel.seeders.desc(),
                )

            # 分页
            stmt = stmt.offset(params.offset).limit(params.limit)

            # 执行查询
            result = await session.execute(stmt)
            models = result.scalars().all()

            # 转换为记录对象
            return [self._model_to_record(model) for model in models]

    async def get_by_site_and_tid(
        self,
        site_id: str,
        torrent_id: str,
    ) -> Optional[TorrentIndexRecord]:
        """根据站点ID和种子ID获取记录"""
        async with self._session_factory() as session:
            stmt = select(TorrentIndexModel).where(
                TorrentIndexModel.site_id == site_id,
                TorrentIndexModel.torrent_id == torrent_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._model_to_record(model)

