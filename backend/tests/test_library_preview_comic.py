"""
统一库预览漫画测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comic import Comic
from app.constants.media_types import MEDIA_TYPE_COMIC
from datetime import datetime, timedelta


@pytest.fixture
async def create_comic_data(db_session: AsyncSession):
    """创建测试用的漫画数据"""
    comic1 = Comic(
        title="测试漫画1",
        series="测试系列",
        volume_index=1,
        author="测试作者",
        illustrator="测试作画",
        language="zh-CN",
        region="CN",
        publish_year=2023,
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    comic2 = Comic(
        title="测试漫画2",
        series="测试系列",
        volume_index=2,
        author="测试作者",
        illustrator="测试作画",
        language="ja",
        region="JP",
        publish_year=2022,
        created_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add_all([comic1, comic2])
    await db_session.commit()
    await db_session.refresh(comic1)
    await db_session.refresh(comic2)
    return [comic1, comic2]


@pytest.mark.asyncio
async def test_library_preview_includes_comic(db_session: AsyncSession, create_comic_data):
    """测试统一库预览默认包含漫画"""
    from app.api.library import get_library_preview
    
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types=None,
        db=db_session
    )
    
    comic_items = [item for item in response.items if item.media_type == MEDIA_TYPE_COMIC]
    assert len(comic_items) >= 2
    assert any(item.title == "测试漫画1" or item.title == "测试漫画2" for item in comic_items)
    assert response.total >= 2


@pytest.mark.asyncio
async def test_library_preview_comic_only(db_session: AsyncSession, create_comic_data):
    """测试只查询漫画类型"""
    from app.api.library import get_library_preview
    
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="comic",
        db=db_session
    )
    
    assert len(response.items) == 2
    assert all(item.media_type == MEDIA_TYPE_COMIC for item in response.items)
    assert response.items[0].title in ["测试漫画1", "测试漫画2"]
    assert response.total == 2


@pytest.mark.asyncio
async def test_library_preview_comic_extra_fields(db_session: AsyncSession, create_comic_data):
    """测试漫画项的 extra 字段包含 series/volume_index/author/illustrator/region"""
    from app.api.library import get_library_preview
    
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="comic",
        db=db_session
    )
    
    comic_item = next((item for item in response.items if item.extra and item.extra.get("series") == "测试系列"), None)
    assert comic_item is not None
    assert comic_item.extra["series"] == "测试系列"
    assert comic_item.extra.get("author") == "测试作者"
    assert comic_item.extra.get("illustrator") == "测试作画"
    assert comic_item.extra.get("region") in ["CN", "JP"]

