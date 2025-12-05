"""
pytest 共享配置和 fixtures
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
from typing import AsyncGenerator

from app.core.database import Base
from app.models.site import Site
from app.models.ai_site_adapter import AISiteAdapter
from app.models.cookiecloud import CookieCloudSettings
from app.models.user import User
from app.models.filter_rule_group import FilterRuleGroup


# 测试数据库 URL（使用内存 SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    为每个测试函数创建独立的数据库会话和表
    """
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # 清理表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    创建一个测试用户
    """
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_test_password",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        role="user"
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_site(db_session: AsyncSession) -> Site:
    """
    创建一个测试站点
    """
    site = Site(
        id=1,
        name="Test Site",
        url="https://test.example.com",
        cookie="test_cookie=value",
        is_active=True,
    )
    db_session.add(site)
    await db_session.flush()
    await db_session.refresh(site)
    return site


@pytest.fixture
async def test_ai_adapter_record(db_session: AsyncSession, test_site: Site) -> AISiteAdapter:
    """
    创建一个测试 AI 适配记录
    """
    from app.core.site_ai_adapter.models import AISiteAdapterConfig, AISearchConfig, AIDetailConfig, AIHRConfig, AIAuthConfig
    
    # 创建测试配置
    test_config = AISiteAdapterConfig(
        search=AISearchConfig(url="/torrents.php", query_params={"search": "{keyword}"}),
        detail=AIDetailConfig(url="/details.php?id={id}"),
        hr=AIHRConfig(enabled=True),
        auth=AIAuthConfig(),
    )
    
    record = AISiteAdapter(
        site_id=str(test_site.id),
        engine="nexusphp",
        config_json=test_config.model_dump(),
        raw_model_output="test output",
        version=1,
        disabled=False,
        manual_profile_preferred=False,
        confidence_score=80,
        last_error=None,
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)
    return record


@pytest.fixture
async def test_cookiecloud_settings(db_session: AsyncSession) -> CookieCloudSettings:
    """
    创建测试CookieCloud设置
    """
    settings = CookieCloudSettings(
        enabled=True,
        host="https://test.cookiecloud.com",
        uuid="12345678-1234-1234-1234-123456789abc",
        password="test_password",
        sync_interval_minutes=60,
        safe_host_whitelist='["tracker.example.com", "pt.example.org"]',
        last_status="NEVER",
        last_error=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings


@pytest.fixture
async def test_cookiecloud_sites(db_session: AsyncSession) -> list[Site]:
    """
    创建多个测试站点（包含CookieCloud站点）
    """
    from app.schemas.cookiecloud import CookieSource
    
    sites = [
        Site(
            id=1,
            name="CookieCloud Site 1",
            url="https://tracker.example.com",
            cookie="original_cookie=value1",
            cookie_source=CookieSource.COOKIECLOUD,
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        Site(
            id=2,
            name="CookieCloud Site 2", 
            url="https://pt.example.org",
            cookie="original_cookie=value2",
            cookie_source=CookieSource.COOKIECLOUD,
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        Site(
            id=3,
            name="Manual Site",
            url="https://manual.example.com",
            cookie="manual_cookie=value3",
            cookie_source=CookieSource.MANUAL,
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        Site(
            id=4,
            name="Disabled Site",
            url="https://disabled.example.com",
            cookie="disabled_cookie=value4",
            cookie_source=CookieSource.COOKIECLOUD,
            enabled=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    for site in sites:
        db_session.add(site)
    
    await db_session.commit()
    return sites


@pytest.fixture
def mock_cookiecloud_client():
    """
    Mock CookieCloud客户端
    """
    from unittest.mock import AsyncMock, MagicMock
    
    mock_client = AsyncMock()
    # 模拟成功获取Cookie数据
    mock_client.get_cookies.return_value = {
        "tracker.example.com": {
            "cookie_data": [
                {"name": "session", "value": "test_session_value", "domain": "tracker.example.com"},
                {"name": "auth", "value": "test_auth_value", "domain": "tracker.example.com"}
            ]
        },
        "pt.example.org": {
            "cookie_data": [
                {"name": "uid", "value": "test_uid_value", "domain": "pt.example.org"},
                {"name": "pass", "value": "test_pass_value", "domain": "pt.example.org"}
            ]
        }
    }
    return mock_client


# 注意：pytest-asyncio 会自动处理事件循环，不需要手动创建


@pytest.fixture(autouse=True)
def reset_tts_state():
    """
    自动重置 TTS 相关全局状态，避免测试间污染
    """
    # 在测试开始前重置
    try:
        from app.modules.tts.usage_tracker import reset as reset_usage_tracker
        reset_usage_tracker()
    except ImportError:
        pass
    
    try:
        from app.modules.tts.rate_limiter import reset as reset_rate_limiter
        reset_rate_limiter()
    except ImportError:
        pass
    
    yield
    
    # 测试结束后再次重置
    try:
        from app.modules.tts.usage_tracker import reset as reset_usage_tracker
        reset_usage_tracker()
    except ImportError:
        pass
    
    try:
        from app.modules.tts.rate_limiter import reset as reset_rate_limiter
        reset_rate_limiter()
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def reset_app_dependency_overrides():
    """
    自动清理 FastAPI app 的依赖覆盖，避免测试间污染
    注意：只在测试结束后清理，以免影响测试内设置的覆盖
    """
    from main import app
    
    # 记录测试开始前的覆盖状态
    initial_overrides = dict(app.dependency_overrides)
    
    yield
    
    # 测试结束后：恢复到初始状态（通常是空）
    app.dependency_overrides.clear()
    app.dependency_overrides.update(initial_overrides)


@pytest.fixture
def override_get_db(db_session):
    """
    提供统一的 get_db 覆盖函数，可在测试中使用
    用法：
        def test_xxx(override_get_db):
            from main import app
            from app.core.database import get_db
            app.dependency_overrides[get_db] = override_get_db
            # ... test code ...
    """
    async def _override():
        yield db_session
    return _override


@pytest.fixture
def apply_db_override(db_session):
    """
    自动应用 get_db 覆盖的 fixture
    用法：直接使用即可，无需手动设置 dependency_overrides
    """
    from main import app
    from app.core.database import get_db
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield
    # 清理由 reset_app_dependency_overrides 处理


@pytest.fixture(autouse=True)
def reset_settings_state(monkeypatch):
    """
    确保 settings.DEBUG 等配置在测试间不会污染
    """
    # 这个 fixture 不主动修改 settings，但确保测试结束后恢复
    yield
    # monkeypatch 会自动在测试结束后恢复所有修改


@pytest.fixture(autouse=True)
def reset_notification_state():
    """
    重置通知服务相关的全局状态
    """
    yield
    # 通知服务通常没有全局状态需要重置，但保留此 fixture 以备扩展


@pytest.fixture
def mock_settings_debug(monkeypatch):
    """
    设置 DEBUG=True 的便捷 fixture
    同时 patch 核心配置和常见 API 模块
    """
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    # 常见的 API 模块也需要 patch
    modules_to_patch = [
        "app.api.tts_jobs.settings.DEBUG",
        "app.api.tts_playground.settings.DEBUG",
        "app.api.tts_voice_presets.settings.DEBUG",
        "app.api.tts_work_profile.settings.DEBUG",
        "app.api.tts_work_batch.settings.DEBUG",
        "app.api.tts_user_flow.settings.DEBUG",
        "app.api.tts_user_batch.settings.DEBUG",
    ]
    for module_path in modules_to_patch:
        try:
            monkeypatch.setattr(module_path, True)
        except AttributeError:
            pass  # 模块可能不存在
    yield

