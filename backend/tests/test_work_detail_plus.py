"""
Work Hub Plus 测试：相关视频改编和相关音乐
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ebook import EBook
from app.models.media import Media
from app.models.music import Music
from app.api.work import get_work_detail
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME
from app.core.schemas import success_response


@pytest.mark.asyncio
async def test_work_detail_videos_by_series_match(db_session: AsyncSession):
    """测试通过 series 匹配相关视频"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        series="三体",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建匹配的 Media 记录
    movie = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="三体",
        year=2023,
        poster_url="https://example.com/poster.jpg"
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(movie)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict，包含 success 和 data）
    assert response["success"] is True
    data = response["data"]
    
    # 验证 videos 列表包含匹配的视频
    assert "videos" in data
    assert len(data["videos"]) >= 1
    
    # 找到匹配的视频
    matched_video = next((v for v in data["videos"] if v["id"] == movie.id), None)
    assert matched_video is not None
    assert matched_video["media_type"] == MEDIA_TYPE_MOVIE
    assert matched_video["title"] == movie.title


@pytest.mark.asyncio
async def test_work_detail_videos_by_title_match(db_session: AsyncSession):
    """测试通过 title 匹配相关视频（没有 series）"""
    # 创建测试数据（没有 series）
    ebook = EBook(
        title="流浪地球",
        author="刘慈欣",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建匹配的 Media 记录
    movie = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="流浪地球",
        original_title="The Wandering Earth",
        year=2019,
        poster_url="https://example.com/poster.jpg"
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(movie)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict，包含 success 和 data）
    assert response["success"] is True
    data = response["data"]
    
    # 验证 videos 列表包含匹配的视频
    assert "videos" in data
    assert len(data["videos"]) >= 1
    
    # 找到匹配的视频
    matched_video = next((v for v in data["videos"] if v["id"] == movie.id), None)
    assert matched_video is not None
    assert matched_video["title"] == movie.title


@pytest.mark.asyncio
async def test_work_detail_music_by_title_or_series(db_session: AsyncSession):
    """测试通过 title/series 匹配相关音乐"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        series="测试系列",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建匹配的 Music 记录（title 包含 series）
    music1 = Music(
        title="测试系列 OST",
        artist="测试艺术家",
        album="测试系列原声带",
        year=2023,
        genre="Soundtrack"
    )
    db_session.add(music1)
    
    # 创建匹配的 Music 记录（album 包含 title）
    music2 = Music(
        title="主题曲",
        artist="测试艺术家",
        album="测试电子书原声带",
        year=2023,
        genre="Soundtrack"
    )
    db_session.add(music2)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(music1)
    await db_session.refresh(music2)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict，包含 success 和 data）
    assert response["success"] is True
    data = response["data"]
    
    # 验证 music 列表包含匹配的音乐
    assert "music" in data
    assert len(data["music"]) >= 1
    
    # 找到匹配的音乐
    matched_music_ids = [m["id"] for m in data["music"]]
    assert music1.id in matched_music_ids or music2.id in matched_music_ids


@pytest.mark.asyncio
async def test_work_detail_videos_and_music_empty_when_no_match(db_session: AsyncSession):
    """测试无任何匹配数据时，videos / music 均为空列表"""
    # 创建测试数据（没有匹配的视频/音乐）
    ebook = EBook(
        title="完全独立的作品",
        author="独立作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.commit()
    await db_session.refresh(ebook)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict，包含 success 和 data）
    assert response["success"] is True
    data = response["data"]
    
    # 验证 videos 和 music 都是空列表
    assert "videos" in data
    assert isinstance(data["videos"], list)
    assert len(data["videos"]) == 0
    
    assert "music" in data
    assert isinstance(data["music"], list)
    assert len(data["music"]) == 0


@pytest.mark.asyncio
async def test_work_detail_videos_media_type_filter(db_session: AsyncSession):
    """测试只匹配指定类型的视频（movie/tv/anime/short_drama）"""
    # 创建测试数据
    ebook = EBook(
        title="测试作品",
        series="测试系列",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建匹配的 Media 记录（movie 类型）
    movie = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试系列",
        year=2023
    )
    db_session.add(movie)
    
    # 创建不匹配的 Media 记录（其他类型，如果有的话）
    # 注意：这里假设只有 movie/tv/anime/short_drama 会被匹配
    
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(movie)
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应（response 是 dict，包含 success 和 data）
    assert response["success"] is True
    data = response["data"]
    
    # 验证 videos 列表中的 media_type 都是允许的类型
    assert "videos" in data
    allowed_types = [MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, "short_drama"]
    for video in data["videos"]:
        assert video["media_type"] in allowed_types

