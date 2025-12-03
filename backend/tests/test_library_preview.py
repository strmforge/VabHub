"""
测试统一媒体库预览接口
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.media import Media
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_EBOOK, MEDIA_TYPE_AUDIOBOOK
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(name="db_session")
async def db_session_fixture():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )
    
    async with AsyncSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="test_data")
async def test_data_fixture(db_session: AsyncSession):
    """创建测试数据"""
    now = datetime.utcnow()
    
    # 创建电影数据
    movies = [
        Media(
            title="指环王：护戒使者",
            year=2001,
            media_type=MEDIA_TYPE_MOVIE,
            tmdb_id=120,
            poster_url="https://example.com/poster1.jpg",
            created_at=now - timedelta(hours=2),
            extra_metadata={"rating": 8.8}
        ),
        Media(
            title="黑客帝国",
            year=1999,
            media_type=MEDIA_TYPE_MOVIE,
            tmdb_id=603,
            poster_url="https://example.com/poster2.jpg",
            created_at=now - timedelta(hours=1),
            extra_metadata={"rating": 8.7}
        ),
    ]
    
    # 创建电子书数据
    ebooks = [
        EBook(
            title="三体",
            author="刘慈欣",
            series="地球往事",
            publish_year=2008,
            cover_url="https://example.com/cover1.jpg",
            isbn="9787536692930",
            created_at=now - timedelta(minutes=30),
        ),
        EBook(
            title="1984",
            author="George Orwell",
            publish_year=1949,
            cover_url="https://example.com/cover2.jpg",
            created_at=now - timedelta(minutes=15),
        ),
    ]
    
    for movie in movies:
        db_session.add(movie)
    for ebook in ebooks:
        db_session.add(ebook)
    
    await db_session.commit()
    
    # 刷新以获取 ID
    for movie in movies:
        await db_session.refresh(movie)
    for ebook in ebooks:
        await db_session.refresh(ebook)
    
    return {
        "movies": movies,
        "ebooks": ebooks
    }


@pytest.mark.asyncio
async def test_library_preview_basic(db_session: AsyncSession, test_data):
    """测试基础预览功能"""
    from app.api.library import get_library_preview
    
    # 模拟依赖注入
    async def get_db_override():
        yield db_session
    
    # 由于 FastAPI 的依赖注入在测试中比较复杂，我们直接调用函数
    # 但需要手动传递 db 参数
    response = await get_library_preview(
        page=1,
        page_size=10,
        media_types=None,
        db=db_session
    )
    
    assert response.total >= 4  # 至少包含我们创建的 2 个电影和 2 个电子书
    assert len(response.items) > 0
    assert response.page == 1
    assert response.page_size == 10
    
    # 验证至少包含一种 movie 和一种 ebook
    media_types = [item.media_type for item in response.items]
    assert MEDIA_TYPE_MOVIE in media_types
    assert MEDIA_TYPE_EBOOK in media_types
    
    # 验证 created_at 降序排列
    for i in range(len(response.items) - 1):
        assert response.items[i].created_at >= response.items[i + 1].created_at


@pytest.mark.asyncio
async def test_library_preview_pagination(db_session: AsyncSession, test_data):
    """测试分页功能"""
    from app.api.library import get_library_preview
    
    # 创建更多数据
    now = datetime.utcnow()
    for i in range(10):
        movie = Media(
            title=f"测试电影 {i}",
            year=2000 + i,
            media_type=MEDIA_TYPE_MOVIE,
            created_at=now - timedelta(minutes=i)
        )
        db_session.add(movie)
    
    for i in range(10):
        ebook = EBook(
            title=f"测试电子书 {i}",
            author=f"作者 {i}",
            created_at=now - timedelta(minutes=i + 10)
        )
        db_session.add(ebook)
    
    await db_session.commit()
    
    # 测试第一页
    response1 = await get_library_preview(
        page=1,
        page_size=5,
        media_types=None,
        db=db_session
    )
    
    assert len(response1.items) == 5
    assert response1.page == 1
    assert response1.page_size == 5
    assert response1.total >= 24  # 2 + 2 + 10 + 10
    
    # 测试第二页
    response2 = await get_library_preview(
        page=2,
        page_size=5,
        media_types=None,
        db=db_session
    )
    
    assert len(response2.items) == 5
    assert response2.page == 2
    
    # 验证不同页的记录不重复（通过 ID）
    page1_ids = {item.id for item in response1.items}
    page2_ids = {item.id for item in response2.items}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_library_preview_filter_by_media_type(db_session: AsyncSession, test_data):
    """测试按媒体类型过滤"""
    from app.api.library import get_library_preview
    
    # 只查询电子书
    response = await get_library_preview(
        page=1,
        page_size=10,
        media_types=MEDIA_TYPE_EBOOK,
        db=db_session
    )
    
    # 验证所有项都是电子书
    assert all(item.media_type == MEDIA_TYPE_EBOOK for item in response.items)
    
    # 验证总数只包含电子书
    assert response.total >= 2  # 至少包含我们创建的 2 个电子书


@pytest.mark.asyncio
async def test_library_preview_item_structure(db_session: AsyncSession, test_data):
    """测试预览项结构"""
    from app.api.library import get_library_preview
    
    response = await get_library_preview(
        page=1,
        page_size=10,
        media_types=None,
        db=db_session
    )
    
    assert len(response.items) > 0
    
    for item in response.items:
        # 验证必需字段
        assert item.id is not None
        assert item.media_type is not None
        assert item.title is not None
        assert item.created_at is not None
        
        # 验证 media_type 是有效值
        assert item.media_type in [MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_EBOOK]
        
        # 如果是电子书，验证 extra 中包含 author
        if item.media_type == MEDIA_TYPE_EBOOK:
            if item.extra:
                # 某些电子书可能有 author
                pass
        
        # 如果是电影，验证 extra 中可能包含 tmdb_id
        if item.media_type == MEDIA_TYPE_MOVIE:
            if item.extra:
                # 某些电影可能有 tmdb_id
                pass


@pytest.mark.asyncio
async def test_library_preview_empty_result(db_session: AsyncSession):
    """测试空结果"""
    from app.api.library import get_library_preview
    
    # 查询不存在的媒体类型
    response = await get_library_preview(
        page=1,
        page_size=10,
        media_types="nonexistent_type",
        db=db_session
    )
    
    assert response.items == []
    assert response.total == 0
    assert response.page == 1
    assert response.page_size == 10

