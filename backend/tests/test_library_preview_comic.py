"""
统一库预览漫画测试
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comic import Comic
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
async def test_library_preview_includes_comic(client: AsyncClient, create_comic_data):
    """测试统一库预览默认包含漫画"""
    response = await client.get("/api/library/preview")
    assert response.status_code == 200
    data = response.json()["data"]
    
    comic_items = [item for item in data["items"] if item["media_type"] == "comic"]
    assert len(comic_items) >= 2  # 可能包含其他媒体类型
    assert any(item["title"] == "测试漫画1" or item["title"] == "测试系列" for item in comic_items)
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_library_preview_comic_only(client: AsyncClient, create_comic_data):
    """测试只查询漫画类型"""
    response = await client.get("/api/library/preview", params={"media_types": "comic"})
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert len(data["items"]) == 2
    assert all(item["media_type"] == "comic" for item in data["items"])
    assert data["items"][0]["title"] in ["测试漫画2", "测试系列"]  # 按 created_at desc 排序
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_library_preview_comic_extra_fields(client: AsyncClient, create_comic_data):
    """测试漫画项的 extra 字段包含 series/volume_index/author/illustrator/region"""
    response = await client.get("/api/library/preview", params={"media_types": "comic"})
    assert response.status_code == 200
    data = response.json()["data"]
    
    comic_item = next((item for item in data["items"] if item.get("extra", {}).get("series") == "测试系列"), None)
    assert comic_item is not None
    assert comic_item["extra"]["series"] == "测试系列"
    assert comic_item["extra"].get("author") == "测试作者"
    assert comic_item["extra"].get("illustrator") == "测试作画"
    assert comic_item["extra"].get("region") in ["CN", "JP"]

