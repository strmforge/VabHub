"""
作品详情 API 测试
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ebook import EBook, EBookFile
from app.models.audiobook import AudiobookFile
from app.models.comic import Comic, ComicFile
from app.api.work import get_work_detail


@pytest.mark.asyncio
async def test_work_detail_basic_ebook_only(db_session: AsyncSession):
    """测试只有 ebook 和 ebook_files，没有 audiobook/comic"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        series="测试系列",
        volume_index="1",
        language="zh-CN",
        publish_year=2023
    )
    db_session.add(ebook)
    await db_session.flush()
    
    ebook_file = EBookFile(
        ebook_id=ebook.id,
        file_path="/path/to/test.epub",
        format="epub",
        file_size_bytes=1024 * 1024 * 5,  # 5 MB
        is_deleted=False
    )
    db_session.add(ebook_file)
    await db_session.commit()
    await db_session.refresh(ebook)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict，包含 success 和 data）
    assert response["success"] is True
    data = response["data"]
    assert data["ebook"]["id"] == ebook.id
    assert data["ebook"]["title"] == "测试电子书"
    assert len(data["ebook_files"]) == 1
    assert data["ebook_files"][0]["format"] == "epub"
    assert len(data["audiobooks"]) == 0
    assert len(data["comics"]) == 0
    assert len(data["comic_files"]) == 0


@pytest.mark.asyncio
async def test_work_detail_with_audiobooks(db_session: AsyncSession):
    """测试有 audiobook 关联，验证 audiobooks 数组"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    audiobook_file = AudiobookFile(
        ebook_id=ebook.id,
        file_path="/path/to/test.mp3",
        format="mp3",
        duration_seconds=3600,
        narrator="测试朗读者",
        is_deleted=False
    )
    db_session.add(audiobook_file)
    await db_session.commit()
    await db_session.refresh(ebook)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict）
    assert response["success"] is True
    data = response["data"]
    assert len(data["audiobooks"]) == 1
    assert data["audiobooks"][0]["narrator"] == "测试朗读者"
    assert data["audiobooks"][0]["duration_seconds"] == 3600
    assert data["audiobooks"][0]["title"] == "测试电子书"  # 使用 EBook 的标题


@pytest.mark.asyncio
async def test_work_detail_with_comics_by_series_match(db_session: AsyncSession):
    """测试建一个 series 一致的 Comic，验证被找到"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        series="测试系列",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建匹配的漫画（series 一致）
    comic = Comic(
        title="测试漫画",
        series="测试系列",
        volume_index=1,
        author="测试作者",
        language="zh-CN",
        region="CN"
    )
    db_session.add(comic)
    await db_session.flush()
    
    comic_file = ComicFile(
        comic_id=comic.id,
        file_path="/path/to/comic.cbz",
        format="cbz",
        file_size_bytes=1024 * 1024 * 10,
        is_deleted=False
    )
    db_session.add(comic_file)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(comic)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict）
    assert response["success"] is True
    data = response["data"]
    assert len(data["comics"]) >= 1
    # 找到匹配的漫画
    matched_comic = next((c for c in data["comics"] if c["series"] == "测试系列"), None)
    assert matched_comic is not None
    assert matched_comic["id"] == comic.id
    assert len(data["comic_files"]) >= 1


@pytest.mark.asyncio
async def test_work_detail_with_comics_by_title_match(db_session: AsyncSession):
    """测试通过 title 匹配漫画"""
    # 创建测试数据（没有 series）
    ebook = EBook(
        title="测试标题",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建匹配的漫画（title 一致）
    comic = Comic(
        title="测试标题",
        volume_index=1,
        author="测试作者",
        language="zh-CN",
        region="CN"
    )
    db_session.add(comic)
    await db_session.flush()
    
    comic_file = ComicFile(
        comic_id=comic.id,
        file_path="/path/to/comic.cbz",
        format="cbz",
        is_deleted=False
    )
    db_session.add(comic_file)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(comic)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict）
    assert response["success"] is True
    data = response["data"]
    assert len(data["comics"]) >= 1
    # 找到匹配的漫画
    matched_comic = next((c for c in data["comics"] if c["title"] == "测试标题"), None)
    assert matched_comic is not None


@pytest.mark.asyncio
async def test_work_detail_not_found(db_session: AsyncSession):
    """测试 ebook_id 不存在时返回 404"""
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        await get_work_detail(99999, db_session)
    
    assert exc_info.value.status_code == 404
    assert "不存在" in str(exc_info.value.detail)

