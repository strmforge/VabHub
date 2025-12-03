"""
测试有声书导入器
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.core.database import Base
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.modules.audiobook.importer import AudiobookImporter
from pathlib import Path
import tempfile
import shutil


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


@pytest.fixture(name="temp_dir")
def temp_dir_fixture():
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.mark.asyncio
async def test_audiobook_importer_existing_ebook(db_session: AsyncSession, temp_dir: Path):
    """测试已有 EBook 时，导入有声书文件复用作品"""
    # 设置临时目录作为库根目录
    import app.core.config as config_module
    original_root = config_module.settings.EBOOK_LIBRARY_ROOT
    config_module.settings.EBOOK_LIBRARY_ROOT = str(temp_dir)
    
    try:
        # 先创建一个 EBook（作品）
        ebook = EBook(
            title="测试书籍",
            author="测试作者",
            created_at=datetime.utcnow(),
        )
        db_session.add(ebook)
        await db_session.commit()
        await db_session.refresh(ebook)
        
        # 创建有声书文件
        file1 = temp_dir / "测试作者 - 测试书籍 - 朗读者.mp3"
        file1.write_text("test audio content")
        
        # 导入有声书
        importer = AudiobookImporter(db_session)
        audiobook_file = await importer.import_audiobook_from_file(str(file1))
        
        assert audiobook_file is not None
        assert audiobook_file.ebook_id == ebook.id  # 应该复用已有的 EBook
        assert audiobook_file.narrator == "朗读者"
        
        # 验证没有创建新的 EBook
        stmt = select(func.count(EBook.id))
        result = await db_session.execute(stmt)
        ebook_count = result.scalar()
        assert ebook_count == 1  # 只有一个 EBook
        
    finally:
        config_module.settings.EBOOK_LIBRARY_ROOT = original_root


@pytest.mark.asyncio
async def test_audiobook_importer_new_ebook(db_session: AsyncSession, temp_dir: Path):
    """测试无现有 EBook 时，导入有声书文件创建新作品"""
    # 设置临时目录作为库根目录
    import app.core.config as config_module
    original_root = config_module.settings.EBOOK_LIBRARY_ROOT
    config_module.settings.EBOOK_LIBRARY_ROOT = str(temp_dir)
    
    try:
        # 创建有声书文件
        file1 = temp_dir / "新作者 - 新书籍 - 新朗读者.m4b"
        file1.write_text("test audio content")
        
        # 导入有声书
        importer = AudiobookImporter(db_session)
        audiobook_file = await importer.import_audiobook_from_file(str(file1))
        
        assert audiobook_file is not None
        assert audiobook_file.ebook_id is not None
        
        # 验证创建了新的 EBook
        stmt = select(EBook).where(EBook.id == audiobook_file.ebook_id)
        result = await db_session.execute(stmt)
        ebook = result.scalar_one()
        
        assert ebook.title == "新书籍"
        assert ebook.author == "新作者"
        assert audiobook_file.narrator == "新朗读者"
        
    finally:
        config_module.settings.EBOOK_LIBRARY_ROOT = original_root


@pytest.mark.asyncio
async def test_audiobook_importer_is_audiobook_file(db_session: AsyncSession):
    """测试 is_audiobook_file 方法"""
    importer = AudiobookImporter(db_session)
    
    assert importer.is_audiobook_file("/path/to/test.mp3") is True
    assert importer.is_audiobook_file("/path/to/test.m4b") is True
    assert importer.is_audiobook_file("/path/to/test.flac") is True
    assert importer.is_audiobook_file("/path/to/test.ogg") is True
    assert importer.is_audiobook_file("/path/to/test.epub") is False
    assert importer.is_audiobook_file("/path/to/test.pdf") is False

