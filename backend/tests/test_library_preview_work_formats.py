"""
统一媒体库预览 work_formats 字段测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.comic import Comic
from app.api.library import get_library_preview
from app.schemas.library import WorkFormats


@pytest.mark.asyncio
async def test_work_formats_for_ebook_only(db_session: AsyncSession):
    """测试只有 EBook，无 Audiobook/Comic"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        series="测试系列",
        language="zh-CN",
        publish_year=2023
    )
    db_session.add(ebook)
    await db_session.commit()
    await db_session.refresh(ebook)
    
    # 调用 API
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="ebook",
        db=db_session
    )
    
    # 验证响应（response 是 LibraryPreviewResponse 对象）
    assert len(response.items) >= 1
    
    # 找到对应的 ebook item
    ebook_item = next((item for item in response.items if item.id == ebook.id), None)
    assert ebook_item is not None
    assert ebook_item.media_type == "ebook"
    
    # 验证 work_formats
    assert ebook_item.work_formats is not None
    work_formats = ebook_item.work_formats
    assert work_formats.has_ebook is True
    assert work_formats.has_audiobook is False
    assert work_formats.has_comic is False
    assert work_formats.has_music is False


@pytest.mark.asyncio
async def test_work_formats_with_audiobook(db_session: AsyncSession):
    """测试为某个 ebook 插入对应的 AudiobookFile"""
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
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="ebook",
        db=db_session
    )
    
    # 验证响应
    assert len(response.items) >= 1
    
    # 找到对应的 ebook item
    ebook_item = next((item for item in response.items if item.id == ebook.id), None)
    assert ebook_item is not None
    
    # 验证 work_formats
    assert ebook_item.work_formats is not None
    work_formats = ebook_item.work_formats
    assert work_formats.has_ebook is True
    assert work_formats.has_audiobook is True
    assert work_formats.has_comic is False


@pytest.mark.asyncio
async def test_work_formats_with_comic_by_series(db_session: AsyncSession):
    """测试 ebook.series = 'xxx'，有 Comic.series = 'xxx'"""
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
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(comic)
    
    # 调用 API
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="ebook",
        db=db_session
    )
    
    # 验证响应
    assert len(response.items) >= 1
    
    # 找到对应的 ebook item
    ebook_item = next((item for item in response.items if item.id == ebook.id), None)
    assert ebook_item is not None
    
    # 验证 work_formats
    assert ebook_item.work_formats is not None
    work_formats = ebook_item.work_formats
    assert work_formats.has_ebook is True
    assert work_formats.has_comic is True


@pytest.mark.asyncio
async def test_work_formats_with_comic_by_title(db_session: AsyncSession):
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
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(comic)
    
    # 调用 API
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="ebook",
        db=db_session
    )
    
    # 验证响应
    assert len(response.items) >= 1
    
    # 找到对应的 ebook item
    ebook_item = next((item for item in response.items if item.id == ebook.id), None)
    assert ebook_item is not None
    
    # 验证 work_formats
    assert ebook_item.work_formats is not None
    work_formats = ebook_item.work_formats
    assert work_formats.has_ebook is True
    assert work_formats.has_comic is True


@pytest.mark.asyncio
async def test_library_preview_non_ebook_has_no_work_formats(db_session: AsyncSession):
    """测试 movie/tv/music 类型 item 的 work_formats 为 None 或不返回"""
    from app.models.media import Media
    from app.models.music import Music
    
    # 创建测试数据
    movie = Media(
        media_type="movie",
        title="测试电影",
        year=2023
    )
    db_session.add(movie)
    
    music = Music(
        title="测试音乐",
        artist="测试艺术家",
        year=2023
    )
    db_session.add(music)
    await db_session.commit()
    await db_session.refresh(movie)
    await db_session.refresh(music)
    
    # 调用 API
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="movie,music",
        db=db_session
    )
    
    # 验证响应
    assert len(response.items) >= 1
    
    # 找到对应的 item
    movie_item = next((item for item in response.items if item.id == movie.id), None)
    music_item = next((item for item in response.items if item.id == music.id), None)
    
    assert movie_item is not None
    assert music_item is not None
    
    # 验证 work_formats 为 None 或不返回
    assert movie_item.work_formats is None
    assert music_item.work_formats is None

