"""
WorkLink 模型和 API 测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.work_link import WorkLink
from app.models.ebook import EBook
from app.models.media import Media
from app.models.comic import Comic
from app.models.music import Music
from app.api.work_links import create_or_update_link, get_links_by_ebook, delete_link
from app.schemas.work_link import WorkLinkCreate
from app.constants.media_types import MEDIA_TYPE_MOVIE


@pytest.mark.asyncio
async def test_create_include_link_and_update_relation(db_session: AsyncSession):
    """测试创建 include 链接，然后用相同组合键更新 relation"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    media = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试电影",
        year=2023
    )
    db_session.add(media)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(media)
    
    # 第一次创建 include 链接
    payload1 = WorkLinkCreate(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media.id,
        relation="include"
    )
    response1 = await create_or_update_link(payload1, db_session)
    
    assert response1["success"] is True
    link_data1 = response1["data"]
    assert link_data1["relation"] == "include"
    link_id = link_data1["id"]
    
    # 第二次用相同组合键更新为 exclude
    payload2 = WorkLinkCreate(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media.id,
        relation="exclude"
    )
    response2 = await create_or_update_link(payload2, db_session)
    
    assert response2["success"] is True
    link_data2 = response2["data"]
    assert link_data2["id"] == link_id  # 应该是同一条记录
    assert link_data2["relation"] == "exclude"  # relation 已更新


@pytest.mark.asyncio
async def test_delete_link(db_session: AsyncSession):
    """测试删除 WorkLink"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    media = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试电影",
        year=2023
    )
    db_session.add(media)
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(media)
    
    # 创建链接
    link = WorkLink(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media.id,
        relation="include"
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)
    
    # 删除链接
    response = await delete_link(link.id, db_session)
    
    assert response["success"] is True
    
    # 验证已删除
    from sqlalchemy import select
    check_stmt = select(WorkLink).where(WorkLink.id == link.id)
    check_result = await db_session.execute(check_stmt)
    deleted_link = check_result.scalar_one_or_none()
    assert deleted_link is None


@pytest.mark.asyncio
async def test_get_links_by_ebook(db_session: AsyncSession):
    """测试获取指定 ebook 的所有 WorkLink"""
    # 创建测试数据
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    media1 = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试电影1",
        year=2023
    )
    db_session.add(media1)
    
    media2 = Media(
        media_type=MEDIA_TYPE_MOVIE,
        title="测试电影2",
        year=2024
    )
    db_session.add(media2)
    
    comic = Comic(
        title="测试漫画",
        series="测试系列"
    )
    db_session.add(comic)
    
    await db_session.commit()
    await db_session.refresh(ebook)
    await db_session.refresh(media1)
    await db_session.refresh(media2)
    await db_session.refresh(comic)
    
    # 创建多个链接
    link1 = WorkLink(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media1.id,
        relation="include"
    )
    db_session.add(link1)
    
    link2 = WorkLink(
        ebook_id=ebook.id,
        target_type="video",
        target_id=media2.id,
        relation="exclude"
    )
    db_session.add(link2)
    
    link3 = WorkLink(
        ebook_id=ebook.id,
        target_type="comic",
        target_id=comic.id,
        relation="include"
    )
    db_session.add(link3)
    
    await db_session.commit()
    
    # 获取链接
    response = await get_links_by_ebook(ebook.id, db_session)
    
    assert response["success"] is True
    links = response["data"]
    assert len(links) == 3
    
    # 验证包含所有链接
    link_ids = [link["id"] for link in links]
    assert link1.id in link_ids
    assert link2.id in link_ids
    assert link3.id in link_ids

