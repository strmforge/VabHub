"""
测试有声书模型
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.audiobook import AudiobookFile
from app.models.ebook import EBook


@pytest.fixture(name="db_session")
async def db_session_fixture():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from sqlalchemy.ext.asyncio import async_sessionmaker
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_audiobook_file_model(db_session: AsyncSession):
    """测试 AudiobookFile 模型创建和 file_size_mb 自动计算"""
    # 创建关联的 EBook
    ebook = EBook(
        title="测试有声书",
        author="测试作者",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建 AudiobookFile
    audiobook_file = AudiobookFile(
        ebook_id=ebook.id,
        file_path="/path/to/test.mp3",
        file_size_bytes=100 * 1024 * 1024,  # 100 MB
        format="mp3",
        narrator="测试朗读者",
        duration_seconds=3600,  # 1 小时
        bitrate_kbps=128,
        channels=2,
        sample_rate_hz=44100,
    )
    db_session.add(audiobook_file)
    await db_session.commit()
    
    # 验证 file_size_mb 自动计算
    assert audiobook_file.file_size_mb == 100.0
    
    # 验证关联
    assert audiobook_file.ebook_id == ebook.id
    
    # 验证其他字段
    assert audiobook_file.format == "mp3"
    assert audiobook_file.narrator == "测试朗读者"
    assert audiobook_file.duration_seconds == 3600
    assert audiobook_file.bitrate_kbps == 128
    assert audiobook_file.channels == 2
    assert audiobook_file.sample_rate_hz == 44100


@pytest.mark.asyncio
async def test_audiobook_file_without_size(db_session: AsyncSession):
    """测试 AudiobookFile 在没有 file_size_bytes 时 file_size_mb 为 None"""
    # 创建关联的 EBook
    ebook = EBook(
        title="测试有声书2",
        author="测试作者2",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建 AudiobookFile（不设置 file_size_bytes）
    audiobook_file = AudiobookFile(
        ebook_id=ebook.id,
        file_path="/path/to/test2.m4b",
        format="m4b",
    )
    db_session.add(audiobook_file)
    await db_session.commit()
    
    # 验证 file_size_mb 为 None
    assert audiobook_file.file_size_mb is None

