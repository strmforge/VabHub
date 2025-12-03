"""
统一库预览音乐支持测试
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.music import Music
from app.constants.media_types import MEDIA_TYPE_MUSIC


@pytest.mark.asyncio
async def test_library_preview_includes_music(db: AsyncSession):
    """测试统一库预览默认包含音乐"""
    from app.api.library import get_library_preview
    
    # 创建测试音乐记录
    music = Music(
        title="测试曲目",
        artist="测试歌手",
        album="测试专辑",
        year=2023
    )
    db.add(music)
    await db.commit()
    
    # 调用预览接口（不指定 media_types，应该包含所有类型）
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types=None,
        db=db
    )
    
    # 检查是否包含音乐
    music_items = [item for item in response.items if item.media_type == MEDIA_TYPE_MUSIC]
    assert len(music_items) > 0
    
    # 检查音乐项的字段
    music_item = music_items[0]
    assert music_item.media_type == MEDIA_TYPE_MUSIC
    assert music_item.title == "测试曲目"
    assert music_item.year == 2023
    assert music_item.extra is not None
    assert music_item.extra.get("artist") == "测试歌手"
    assert music_item.extra.get("album") == "测试专辑"


@pytest.mark.asyncio
async def test_library_preview_music_only(db: AsyncSession):
    """测试只查询音乐类型"""
    from app.api.library import get_library_preview
    
    # 创建测试音乐记录
    music = Music(
        title="测试曲目2",
        artist="测试歌手2",
        genre="流行"
    )
    db.add(music)
    await db.commit()
    
    # 只查询音乐类型
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="music",
        db=db
    )
    
    # 所有项都应该是音乐类型
    assert all(item.media_type == MEDIA_TYPE_MUSIC for item in response.items)
    
    # 检查 extra 中包含 genre
    if response.items:
        music_item = response.items[0]
        if music_item.extra:
            assert "genre" in music_item.extra or "artist" in music_item.extra


@pytest.mark.asyncio
async def test_library_preview_music_extra_fields(db: AsyncSession):
    """测试音乐项的 extra 字段"""
    from app.api.library import get_library_preview
    
    # 创建包含完整信息的音乐记录
    music = Music(
        title="完整信息曲目",
        artist="完整信息歌手",
        album="完整信息专辑",
        album_artist="专辑艺术家",
        genre="摇滚",
        year=2022
    )
    db.add(music)
    await db.commit()
    
    # 查询音乐
    response = await get_library_preview(
        page=1,
        page_size=20,
        media_types="music",
        db=db
    )
    
    # 找到对应的音乐项
    music_item = next((item for item in response.items if item.title == "完整信息曲目"), None)
    assert music_item is not None
    assert music_item.extra is not None
    assert music_item.extra.get("artist") == "完整信息歌手"
    assert music_item.extra.get("album") == "完整信息专辑"
    assert music_item.extra.get("genre") == "摇滚"
    assert music_item.extra.get("album_artist") == "专辑艺术家"

