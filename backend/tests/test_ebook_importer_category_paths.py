"""
电子书导入器分类路径测试
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base

from app.modules.ebook.importer import EBookImporter
from app.models.ebook import EBook
import app.core.config as config_module
from unittest.mock import patch, MagicMock
import yaml
from app.modules.media_renamer.category_helper import RUAMEL_YAML_AVAILABLE

# 如果 ruamel.yaml 未安装，跳过需要分类功能的测试
requires_ruamel = pytest.mark.skipif(
    not RUAMEL_YAML_AVAILABLE,
    reason="ruamel.yaml 未安装，分类功能不可用"
)


@pytest.fixture(name="db_session")
async def db_session_fixture():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def temp_category_yaml(tmp_path):
    """创建临时分类配置文件"""
    yaml_content = """ebook:
  科幻:
    tags: '科幻,硬科幻,软科幻,science-fiction,sci-fi,SF'
  言情:
    tags: '言情,romance,爱情,恋爱'
  其他电子书:
"""
    yaml_file = tmp_path / "category.yaml"
    yaml_file.write_text(yaml_content, encoding='utf-8')
    return yaml_file


@requires_ruamel
@pytest.mark.asyncio
async def test_ebook_importer_path_with_category(tmp_path, db_session, temp_category_yaml, monkeypatch):
    """测试命中分类时，路径包含分类目录"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    importer = EBookImporter(db_session)
    # 替换 category_helper 的配置文件路径
    importer.category_helper = importer.category_helper.__class__(config_path=temp_category_yaml)
    
    # 创建带标签的 EBook
    ebook = EBook(
        title="三体",
        author="刘慈欣",
        tags="科幻,硬科幻",
        language="zh-CN"
    )
    
    target_path = importer.build_target_path(
        title=ebook.title,
        author=ebook.author,
        format="epub",
        ebook=ebook
    )
    
    # 验证路径包含分类目录
    path_str = str(target_path)
    assert "科幻" in path_str
    assert "Books" in path_str
    assert "刘慈欣" in path_str
    assert target_path.name == "三体.epub"


@requires_ruamel
@pytest.mark.asyncio
async def test_ebook_importer_path_without_category(tmp_path, db_session, temp_category_yaml, monkeypatch):
    """测试未命中分类时，路径不包含分类目录（保持原有结构）"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    importer = EBookImporter(db_session)
    importer.category_helper = importer.category_helper.__class__(config_path=temp_category_yaml)
    
    # 创建没有匹配标签的 EBook
    ebook = EBook(
        title="未知书籍",
        author="未知作者",
        tags="其他标签",
        language="zh-CN"
    )
    
    target_path = importer.build_target_path(
        title=ebook.title,
        author=ebook.author,
        format="epub",
        ebook=ebook
    )
    
    # 验证路径包含默认分类"其他电子书"
    path_str = str(target_path)
    assert "Books" in path_str
    assert "未知作者" in path_str
    # 应该包含"其他电子书"（因为匹配到了默认分类）
    assert "其他电子书" in path_str


@pytest.mark.asyncio
async def test_ebook_importer_path_no_ebook_object(tmp_path, db_session, temp_category_yaml, monkeypatch):
    """测试不传入 ebook 对象时，使用原有结构（不包含分类目录）"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    importer = EBookImporter(db_session)
    importer.category_helper = importer.category_helper.__class__(config_path=temp_category_yaml)
    
    target_path = importer.build_target_path(
        title="测试书籍",
        author="测试作者",
        format="epub",
        ebook=None  # 不传入 ebook
    )
    
    # 验证路径不包含分类目录（原有结构）
    path_str = str(target_path)
    assert "Books" in path_str
    assert "测试作者" in path_str
    # 不应该包含任何分类目录（科幻、言情等）
    assert "科幻" not in path_str
    assert "言情" not in path_str
    assert "其他电子书" not in path_str


@requires_ruamel
@pytest.mark.asyncio
async def test_ebook_importer_path_with_series_and_category(tmp_path, db_session, temp_category_yaml, monkeypatch):
    """测试带系列和分类的路径"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    importer = EBookImporter(db_session)
    importer.category_helper = importer.category_helper.__class__(config_path=temp_category_yaml)
    
    ebook = EBook(
        title="三体",
        author="刘慈欣",
        series="地球往事",
        volume_index="1",
        tags="科幻",
        language="zh-CN"
    )
    
    target_path = importer.build_target_path(
        title=ebook.title,
        author=ebook.author,
        series=ebook.series,
        volume_index=ebook.volume_index,
        format="epub",
        ebook=ebook
    )
    
    # 验证完整路径结构：Books/科幻/刘慈欣/地球往事/1 - 三体.epub
    path_str = str(target_path)
    assert "科幻" in path_str
    assert "刘慈欣" in path_str
    assert "地球往事" in path_str
    assert target_path.name == "1 - 三体.epub"

