"""
WorkDetail 与手动链接集成测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ebook import EBook
from app.models.media import Media
from app.models.comic import Comic
from app.models.music import Music
from app.models.work_link import WorkLink
from app.api.work import get_work_detail
from app.constants.media_types import MEDIA_TYPE_MOVIE


@pytest.mark.asyncio
async def test_manual_include_video_overrides_heuristic(db_session: AsyncSession):
    """测试手动 include 的视频即使启发式匹配不到也会显示"""
    # 创建测试数据
    ebook = EBook(
        title="完全独立的作品",
        author="独立作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建一个与 ebook 标题/系列名完全不匹配的视频
    media = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="完全不相关的电影",
        year=2023
    )
    db_session.add(media)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(media)
    
    # 手动创建 include 链接
    link = WorkLink(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media.id,
        relation="include"
    )
    db_session.add(link)
    await db_session.commit()
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应
    assert response["success"] is True
    data = response["data"]
    
    # 验证 videos 列表包含手动 include 的视频
    assert "videos" in data
    assert len(data["videos"]) >= 1
    
    # 找到匹配的视频
    matched_video = next((v for v in data["videos"] if v["id"] == media.id), None)
    assert matched_video is not None
    assert matched_video["title"] == media.title


@pytest.mark.asyncio
async def test_manual_exclude_video_filters_out_heuristic_match(db_session: AsyncSession):
    """测试手动 exclude 的视频即使启发式匹配到了也不会显示"""
    # 创建测试数据
    ebook = EBook(
        title="测试作品",
        series="测试系列",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建一个会被启发式匹配到的视频（标题包含 series）
    media = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试系列",
        year=2023
    )
    db_session.add(media)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(media)
    
    # 手动创建 exclude 链接
    link = WorkLink(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media.id,
        relation="exclude"
    )
    db_session.add(link)
    await db_session.commit()
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应
    assert response["success"] is True
    data = response["data"]
    
    # 验证 videos 列表不包含被 exclude 的视频
    assert "videos" in data
    video_ids = [v["id"] for v in data["videos"]]
    assert media.id not in video_ids


@pytest.mark.asyncio
async def test_manual_include_comic_overrides_heuristic(db_session: AsyncSession):
    """测试手动 include 的漫画即使启发式匹配不到也会显示"""
    # 创建测试数据
    ebook = EBook(
        title="完全独立的作品",
        author="独立作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建一个与 ebook 标题/系列名完全不匹配的漫画
    comic = Comic(
        title="完全不相关的漫画",
        series="不相关系列"
    )
    db_session.add(comic)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(comic)
    
    # 手动创建 include 链接
    link = WorkLink(
        ebook_id=ebook.id,
        target_type="comic",
        target_id=comic.id,
        relation="include"
    )
    db_session.add(link)
    await db_session.commit()
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应
    assert response["success"] is True
    data = response["data"]
    
    # 验证 comics 列表包含手动 include 的漫画
    assert "comics" in data
    assert len(data["comics"]) >= 1
    
    # 找到匹配的漫画
    matched_comic = next((c for c in data["comics"] if c["id"] == comic.id), None)
    assert matched_comic is not None
    assert matched_comic["title"] == comic.title


@pytest.mark.asyncio
async def test_manual_exclude_music_filters_out_heuristic_match(db_session: AsyncSession):
    """测试手动 exclude 的音乐即使启发式匹配到了也不会显示"""
    # 创建测试数据
    ebook = EBook(
        title="测试作品",
        series="测试系列",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建一个会被启发式匹配到的音乐（title 包含 series）
    music = Music(
        title="测试系列 OST",
        artist="测试艺术家",
        year=2023
    )
    db_session.add(music)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(music)
    
    # 手动创建 exclude 链接
    link = WorkLink(
        ebook_id=ebook.id,
        target_type="music",
        target_id=music.id,
        relation="exclude"
    )
    db_session.add(link)
    await db_session.commit()
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应
    assert response["success"] is True
    data = response["data"]
    
    # 验证 music 列表不包含被 exclude 的音乐
    assert "music" in data
    music_ids = [m["id"] for m in data["music"]]
    assert music.id not in music_ids


@pytest.mark.asyncio
async def test_manual_include_priority_over_heuristic(db_session: AsyncSession):
    """测试手动 include 的记录优先显示，且不会重复"""
    # 创建测试数据
    ebook = EBook(
        title="测试作品",
        series="测试系列",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建一个会被启发式匹配到的视频
    media = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试系列",
        year=2023
    )
    db_session.add(media)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(media)
    
    # 手动创建 include 链接
    link = WorkLink(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media.id,
        relation="include"
    )
    db_session.add(link)
    await db_session.commit()
    
    # 调用 API
    response = await get_work_detail(ebook.id, db_session)
    
    # 验证响应
    assert response["success"] is True
    data = response["data"]
    
    # 验证 videos 列表包含该视频，且只出现一次
    assert "videos" in data
    video_ids = [v["id"] for v in data["videos"]]
    assert media.id in video_ids
    assert video_ids.count(media.id) == 1  # 不重复

