from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from .database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(128), unique=True, index=True, nullable=False)
    capabilities = Column(String(1024), nullable=True)  # JSON 字符串
    last_heartbeat = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)


class SiteCursor(Base):
    __tablename__ = "site_cursors"
    __table_args__ = (UniqueConstraint("site_id", name="uq_site_cursor_site_id"),)

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(64), nullable=False, index=True)
    cursor_value = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(64), nullable=False, index=True)
    payload = Column(String(2048), nullable=True)  # JSON 字符串
    status = Column(String(32), default="pending", index=True)  # pending/leased/done/failed
    leased_by = Column(String(128), nullable=True)
    leased_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def is_lease_expired(self, lease_seconds: int) -> bool:
        if self.status != "leased" or not self.leased_at:
            return False
        return self.leased_at + timedelta(seconds=lease_seconds) < datetime.utcnow()

