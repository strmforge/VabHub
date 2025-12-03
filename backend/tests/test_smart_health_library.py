"""
智能健康检查 Library 区块测试
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media import Media
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.comic import Comic
from app.models.music import Music
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME
from app.api.smart_health import get_library_health, compute_multi_format_work_stats


@pytest.mark.asyncio
async def test_library_health_basic_structure(db_session: AsyncSession):
    """测试 library 健康检查基本结构"""
    from app.api.smart_health import smart_health
    from app.core.config import settings
    
    result = await smart_health(db_session)
    # 确认有 features.library
    assert "features" in result
    assert "library" in result["features"]
    
    library = result["features"]["library"]
    
    # 验证字段齐全
    assert "enabled" in library
    assert "roots" in library
    assert "counts" in library
    assert "multi_format_works" in library
    assert "pending_warning" in library
    
    # 验证 roots 结构
    assert isinstance(library["roots"], dict)
    expected_roots = ["movie", "tv", "anime", "short_drama", "ebook", "comic", "music"]
    for root_key in expected_roots:
        assert root_key in library["roots"]
    
    # 验证 counts 结构
    assert isinstance(library["counts"], dict)
    expected_counts = ["movie", "tv", "anime", "ebook", "audiobook", "comic", "music"]
    for count_key in expected_counts:
        assert count_key in library["counts"]
    
    # 验证 multi_format_works 结构
    assert isinstance(library["multi_format_works"], dict)
    expected_multi = ["ebook_only", "ebook_with_audiobook", "ebook_with_comic", "ebook_with_both"]
    for multi_key in expected_multi:
        assert multi_key in library["multi_format_works"]


@pytest.mark.asyncio
async def test_library_health_counts_non_negative(db_session: AsyncSession):
    """测试所有 counts 字段都是 >= 0 的整数"""
    from app.core.config import settings
    library_status = await get_library_health(settings, db_session)
    
    counts = library_status["counts"]
    for key, value in counts.items():
        assert isinstance(value, int), f"{key} 应该是整数"
        assert value >= 0, f"{key} 应该 >= 0"


@pytest.mark.asyncio
async def test_library_health_empty_library_warning(db_session: AsyncSession):
    """测试空库时 pending_warning == 'empty_library'"""
    # 确保数据库为空（或至少相关表为空）
    # 注意：这个测试假设数据库是测试数据库，可以安全清空
    from app.core.config import settings
    library_status = await get_library_health(settings, db_session)
    
    total_count = sum(library_status["counts"].values())
    
    if total_count == 0:
        assert library_status["pending_warning"] == "empty_library"
    else:
        # 如果数据库不为空，pending_warning 应该为 None
        assert library_status["pending_warning"] is None or library_status["pending_warning"] != "empty_library"


@pytest.mark.asyncio
async def test_library_health_multi_format_stats_consistent(db_session: AsyncSession):
    """测试多形态作品统计的一致性"""
    # 创建测试数据
    ebook1 = EBook(
        title="测试电子书1",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook1)
    await db_session.flush()
    
    ebook2 = EBook(
        title="测试电子书2",
        author="测试作者",
        series="测试系列",
        language="zh-CN"
    )
    db_session.add(ebook2)
    await db_session.flush()
    
    # ebook1 只有电子书
    # ebook2 有有声书和漫画
    
    audiobook_file = AudiobookFile(
        ebook_id=ebook2.id,
        file_path="/path/to/test.mp3",
        format="mp3",
        duration_seconds=3600,
        narrator="测试朗读者",
        is_deleted=False
    )
    db_session.add(audiobook_file)
    
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
    await db_session.refresh(ebook1)
    await db_session.refresh(ebook2)
    
    # 计算多形态统计
    stats = await compute_multi_format_work_stats(db_session)
    
    # 验证统计一致性
    total_ebooks = stats["ebook_only"] + stats["ebook_with_audiobook"] + stats["ebook_with_comic"] + stats["ebook_with_both"]
    
    # 获取实际 ebook 总数
    from sqlalchemy import select, func
    ebook_count_stmt = select(func.count(EBook.id))
    ebook_count_result = await db_session.execute(ebook_count_stmt)
    actual_ebook_count = ebook_count_result.scalar() or 0
    
    # 验证：ebook_only + ebook_with_audiobook + ebook_with_comic + ebook_with_both == 总 ebook 数
    # 注意：由于数据库中可能已有其他 ebook，这里只验证公式成立
    assert total_ebooks == actual_ebook_count, f"多形态统计总和 ({total_ebooks}) 应该等于总 ebook 数 ({actual_ebook_count})"
    
    # 验证至少有一个 ebook_only（ebook1）
    assert stats["ebook_only"] >= 1
    
    # 验证至少有一个 ebook_with_both（ebook2，既有 audiobook 又有 comic）
    assert stats["ebook_with_both"] >= 1


@pytest.mark.asyncio
async def test_library_health_counts_accurate(db_session: AsyncSession):
    """测试 counts 统计的准确性"""
    # 创建测试数据
    movie = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试电影",
        year=2023
    )
    db_session.add(movie)
    
    tv = Media(
        media_type=MEDIA_TYPE_TV,
        title="测试剧集",
        year=2023
    )
    db_session.add(tv)
    
    anime = Media(
        media_type=MEDIA_TYPE_ANIME,
        title="测试动漫",
        year=2023
    )
    db_session.add(anime)
    
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
        is_deleted=False
    )
    db_session.add(audiobook_file)
    
    comic = Comic(
        title="测试漫画",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(comic)
    
    music = Music(
        title="测试音乐",
        artist="测试艺术家",
        year=2023
    )
    db_session.add(music)
    await db_session.commit()
    
    # 获取统计
    from app.core.config import settings
    library_status = await get_library_health(settings, db_session)
    counts = library_status["counts"]
    
    # 验证至少包含我们创建的数据
    assert counts["movie"] >= 1
    assert counts["tv"] >= 1
    assert counts["anime"] >= 1
    assert counts["ebook"] >= 1
    assert counts["audiobook"] >= 1
    assert counts["comic"] >= 1
    assert counts["music"] >= 1

