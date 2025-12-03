"""
测试电子书模型
"""

import pytest
from datetime import datetime
from app.models.ebook import EBook, EBookFile


@pytest.mark.asyncio
async def test_ebook_model_creation(db_session):
    """测试创建电子书模型"""
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
        series="测试系列",
        volume_index="1",
        language="zh-CN",
        publish_year=2024,
    )
    db_session.add(ebook)
    await db_session.flush()
    
    assert ebook.id is not None
    assert ebook.title == "测试电子书"
    assert ebook.author == "测试作者"
    assert ebook.series == "测试系列"
    assert ebook.volume_index == "1"
    assert ebook.language == "zh-CN"
    assert ebook.publish_year == 2024
    assert ebook.created_at is not None
    assert ebook.updated_at is not None


@pytest.mark.asyncio
async def test_ebook_file_model_creation(db_session):
    """测试创建电子书文件模型"""
    # 先创建电子书
    ebook = EBook(
        title="测试电子书",
        author="测试作者",
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建电子书文件
    ebook_file = EBookFile(
        ebook_id=ebook.id,
        file_path="/path/to/book.epub",
        file_size_bytes=1024 * 1024,  # 1MB
        format="epub",
    )
    db_session.add(ebook_file)
    await db_session.flush()
    
    assert ebook_file.id is not None
    assert ebook_file.ebook_id == ebook.id
    assert ebook_file.file_path == "/path/to/book.epub"
    assert ebook_file.file_size_bytes == 1024 * 1024
    assert ebook_file.file_size_mb == 1.0  # 自动计算
    assert ebook_file.format == "epub"
    assert ebook_file.is_deleted is False

