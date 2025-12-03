"""
测试电子书作品模型与去重逻辑
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.ebook import EBook, EBookFile
from app.modules.ebook.work_resolver import EBookWorkResolver
from app.modules.ebook.importer import EBookImporter
from pathlib import Path
import tempfile
import shutil


@pytest.fixture(name="db_session")
async def db_session_fixture():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 使用 async_sessionmaker 而不是 sessionmaker
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
async def test_work_resolver_normalize_isbn():
    """测试 ISBN 规范化"""
    resolver = EBookWorkResolver()
    
    assert resolver.normalize_isbn("978-0-261-10357-3") == "9780261103573"
    assert resolver.normalize_isbn("978 0 261 10357 3") == "9780261103573"
    assert resolver.normalize_isbn("9780261103573") == "9780261103573"
    assert resolver.normalize_isbn(None) is None
    assert resolver.normalize_isbn("") is None


@pytest.mark.asyncio
async def test_work_resolver_normalize_title():
    """测试书名规范化"""
    resolver = EBookWorkResolver()
    
    assert resolver.normalize_title(" 三体 [精校版] ") == "三体"
    assert resolver.normalize_title("三体 (完整版)") == "三体"
    assert resolver.normalize_title("三体 [EPUB]") == "三体"
    assert resolver.normalize_title("三体") == "三体"
    assert resolver.normalize_title("") == ""


@pytest.mark.asyncio
async def test_work_resolver_normalize_author():
    """测试作者名规范化"""
    resolver = EBookWorkResolver()
    
    # 注意：规范化后会转为小写，所以比较时也要用小写
    # 测试中文括号（全角）
    result1 = resolver.normalize_author(" 刘慈欣（作者版） ")
    assert result1 == "刘慈欣" or result1 == "刘慈欣".lower()  # 可能转为小写
    
    # 测试英文括号
    result2 = resolver.normalize_author("刘慈欣(作者版)")
    assert result2 == "刘慈欣" or result2 == "刘慈欣".lower()
    
    # 测试方括号
    result3 = resolver.normalize_author("刘慈欣 [著]")
    assert result3 == "刘慈欣" or result3 == "刘慈欣".lower()
    
    # 测试无后缀
    result4 = resolver.normalize_author("刘慈欣")
    assert result4 == "刘慈欣" or result4 == "刘慈欣".lower()
    
    assert resolver.normalize_author(None) is None
    assert resolver.normalize_author("") is None


@pytest.mark.asyncio
async def test_work_resolver_find_by_isbn(db_session: AsyncSession):
    """测试通过 ISBN 查找作品"""
    resolver = EBookWorkResolver()
    
    # 创建测试数据
    ebook1 = EBook(
        title="三体",
        author="刘慈欣",
        isbn="9787536692930",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook1)
    await db_session.commit()
    await db_session.refresh(ebook1)
    
    # 测试：使用相同 ISBN（不同格式）查找
    found = await resolver.find_existing_work(
        db_session,
        isbn="978-7536-6929-30",  # 带连字符的 ISBN
        title="三体",
        author="刘慈欣"
    )
    
    assert found is not None
    assert found.id == ebook1.id
    assert found.isbn == "9787536692930"


@pytest.mark.asyncio
async def test_work_resolver_find_by_title_author_series_volume(db_session: AsyncSession):
    """测试通过 title+author+series+volume 查找作品"""
    resolver = EBookWorkResolver()
    
    # 创建测试数据
    ebook1 = EBook(
        title="三体",
        author="刘慈欣",
        series="地球往事",
        volume_index="1",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook1)
    await db_session.commit()
    await db_session.refresh(ebook1)
    
    # 测试：使用相同的 title+author+series+volume（但可能有不同的后缀）
    # 注意：规范化会移除后缀并转为小写，所以应该能匹配
    found = await resolver.find_existing_work(
        db_session,
        title="三体 [精校版]",  # 带后缀，规范化后应该匹配
        author="刘慈欣",  # 先测试不带后缀的情况
        series="地球往事",
        volume_index="1"
    )
    
    assert found is not None
    assert found.id == ebook1.id


@pytest.mark.asyncio
async def test_work_resolver_different_author_not_match(db_session: AsyncSession):
    """测试 title 相同但 author 不同时不匹配"""
    resolver = EBookWorkResolver()
    
    # 创建测试数据
    ebook1 = EBook(
        title="三体",
        author="刘慈欣",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook1)
    await db_session.commit()
    await db_session.refresh(ebook1)
    
    # 测试：title 相同但 author 不同
    found = await resolver.find_existing_work(
        db_session,
        title="三体",
        author="其他作者"  # 不同的作者
    )
    
    # 应该不匹配（保守策略）
    assert found is None


@pytest.mark.asyncio
async def test_importer_same_isbn_reuses_ebook(db_session: AsyncSession, temp_dir: Path):
    """测试同 ISBN 的两个文件复用同一 EBook"""
    importer = EBookImporter(db_session)
    
    # 创建第一个文件
    file1 = temp_dir / "test_book_1.epub"
    file1.write_text("test content 1")
    
    # 第一次导入（模拟元数据增强返回 ISBN）
    # 由于元数据增强可能未启用，我们直接测试 WorkResolver 的逻辑
    # 先手动创建一个带 ISBN 的 EBook
    ebook1 = EBook(
        title="测试书籍",
        author="测试作者",
        isbn="9780261103573",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook1)
    await db_session.commit()
    await db_session.refresh(ebook1)
    
    # 创建第二个文件（相同 ISBN，但文件名可能不同）
    file2 = temp_dir / "test_book_2.pdf"
    file2.write_text("test content 2")
    
    # 模拟第二次导入：使用 WorkResolver 查找
    resolver = EBookWorkResolver()
    found = await resolver.find_existing_work(
        db_session,
        isbn="978-0261-10357-3",  # 不同格式的相同 ISBN
        title="测试书籍（完整版）",  # 不同的标题后缀
        author="测试作者"
    )
    
    assert found is not None
    assert found.id == ebook1.id
    
    # 验证：两个文件应该可以关联到同一个 EBook
    # 这里只测试 WorkResolver，实际的 importer 集成测试在下面


@pytest.mark.asyncio
async def test_importer_same_title_author_series_volume_reuses_ebook(db_session: AsyncSession, temp_dir: Path):
    """测试无 ISBN，但 title+author+series+volume 完全相同，复用同一 EBook"""
    importer = EBookImporter(db_session)
    
    # 先手动创建一个 EBook（无 ISBN）
    ebook1 = EBook(
        title="三体",
        author="刘慈欣",
        series="地球往事",
        volume_index="1",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook1)
    await db_session.commit()
    await db_session.refresh(ebook1)
    
    # 使用 WorkResolver 查找（相同的 title+author+series+volume）
    resolver = EBookWorkResolver()
    found = await resolver.find_existing_work(
        db_session,
        isbn=None,
        title="三体 [精校版]",  # 带后缀，但规范化后应该匹配
        author="刘慈欣",  # 先测试不带后缀的情况
        series="地球往事",
        volume_index="1"
    )
    
    assert found is not None
    assert found.id == ebook1.id


@pytest.mark.asyncio
async def test_importer_different_author_creates_new_ebook(db_session: AsyncSession, temp_dir: Path):
    """测试 title 相同但 author 不同，创建新的 EBook"""
    resolver = EBookWorkResolver()
    
    # 创建第一个 EBook
    ebook1 = EBook(
        title="三体",
        author="刘慈欣",
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook1)
    await db_session.commit()
    await db_session.refresh(ebook1)
    
    # 尝试查找（title 相同但 author 不同）
    found = await resolver.find_existing_work(
        db_session,
        title="三体",
        author="其他作者"  # 不同的作者
    )
    
    # 应该不匹配（保守策略）
    assert found is None
    
    # 验证：应该创建新的 EBook
    # 这里只测试 WorkResolver，实际的 importer 会创建新的 EBook


@pytest.mark.asyncio
async def test_work_resolver_isbn_takes_priority(db_session: AsyncSession):
    """测试 ISBN 匹配优先于 title+author 匹配"""
    resolver = EBookWorkResolver()
    
    # 创建两个 EBook：
    # 1. 有 ISBN，title="三体"
    # 2. 无 ISBN，title="三体"，author="刘慈欣"
    ebook1 = EBook(
        title="三体",
        author="刘慈欣",
        isbn="9787536692930",
        created_at=datetime.utcnow(),
    )
    ebook2 = EBook(
        title="三体",
        author="刘慈欣",
        isbn=None,  # 无 ISBN
        created_at=datetime.utcnow(),
    )
    db_session.add(ebook1)
    db_session.add(ebook2)
    await db_session.commit()
    await db_session.refresh(ebook1)
    await db_session.refresh(ebook2)
    
    # 使用 ISBN 查找，应该找到 ebook1（有 ISBN 的那个）
    found = await resolver.find_existing_work(
        db_session,
        isbn="9787536692930",
        title="三体",
        author="刘慈欣"
    )
    
    assert found is not None
    assert found.id == ebook1.id
    assert found.isbn == "9787536692930"


@pytest.mark.asyncio
async def test_importer_integration_with_work_resolver(db_session: AsyncSession, temp_dir: Path):
    """测试 importer 集成 WorkResolver 的完整流程"""
    # 设置临时目录作为库根目录
    import app.core.config as config_module
    original_root = config_module.settings.EBOOK_LIBRARY_ROOT
    config_module.settings.EBOOK_LIBRARY_ROOT = str(temp_dir)
    
    try:
        importer = EBookImporter(db_session)
        
        # 创建第一个文件（使用简单的文件名，避免中文路径问题）
        file1 = temp_dir / "Author - Title.epub"
        file1.write_text("test content 1")
        
        # 第一次导入
        ebook1 = await importer.import_ebook_from_file(str(file1))
        
        assert ebook1 is not None
        assert ebook1.title == "Title"
        assert ebook1.author == "Author"
        
        # 验证 EBookFile 已创建
        from sqlalchemy import select, func
        stmt = select(func.count(EBookFile.id)).where(EBookFile.ebook_id == ebook1.id)
        result = await db_session.execute(stmt)
        file_count = result.scalar()
        assert file_count == 1
        
        # 创建第二个文件（相同作品，不同格式）
        file2 = temp_dir / "Author - Title [Enhanced].pdf"
        file2.write_text("test content 2")
        
        # 第二次导入
        ebook2 = await importer.import_ebook_from_file(str(file2))
        
        assert ebook2 is not None
        # 应该复用同一个 EBook（规范化后 title 应该匹配）
        assert ebook2.id == ebook1.id
        
        # 验证现在有两个 EBookFile 关联到同一个 EBook
        stmt = select(func.count(EBookFile.id)).where(EBookFile.ebook_id == ebook1.id)
        result = await db_session.execute(stmt)
        file_count = result.scalar()
        assert file_count == 2
        
    finally:
        # 恢复原始配置
        config_module.settings.EBOOK_LIBRARY_ROOT = original_root

