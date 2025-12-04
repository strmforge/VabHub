import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.database import Base
from app.models.cookiecloud import CookieCloudSettings
from app.models.site import Site
from app.modules.cookiecloud.service import CookieCloudSyncService
from app.schemas.cookiecloud import CookieSource


async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        settings = CookieCloudSettings(
            enabled=True,
            host="https://test.cookiecloud.com",
            uuid="12345678-1234-1234-1234-123456789abc",
            password="test_password",
            sync_interval_minutes=60,
            safe_host_whitelist='["tracker.example.com", "pt.example.org"]',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(settings)
        session.add_all(
            [
                Site(
                    id=1,
                    name="CookieCloud Site 1",
                    url="https://tracker.example.com",
                    cookie="original_cookie=value1",
                    cookie_source=CookieSource.COOKIECLOUD,
                    enabled=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ),
                Site(
                    id=2,
                    name="CookieCloud Site 2",
                    url="https://pt.example.org",
                    cookie="original_cookie=value2",
                    cookie_source=CookieSource.COOKIECLOUD,
                    enabled=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ),
            ]
        )
        await session.commit()

        service = CookieCloudSyncService(session)

        mock_client = AsyncMock()
        mock_client.get_cookies.return_value = {
            "tracker.example.com": {
                "cookie_data": [
                    {
                        "name": "session",
                        "value": "test_session_value",
                        "domain": "tracker.example.com",
                    },
                    {
                        "name": "auth",
                        "value": "test_auth_value",
                        "domain": "tracker.example.com",
                    },
                ]
            },
            "pt.example.org": {
                "cookie_data": [
                    {
                        "name": "uid",
                        "value": "test_uid_value",
                        "domain": "pt.example.org",
                    },
                    {
                        "name": "pass",
                        "value": "test_pass_value",
                        "domain": "pt.example.org",
                    },
                ]
            },
        }

        with patch("app.modules.cookiecloud.service.CookieCloudClient", return_value=mock_client):
            result = await service.sync_all_sites()
        print("sync result:", result)

        res = await session.execute(Site.__table__.select().order_by(Site.id))
        for row in res:
            print(row.id, row.cookie)


if __name__ == "__main__":
    asyncio.run(main())
