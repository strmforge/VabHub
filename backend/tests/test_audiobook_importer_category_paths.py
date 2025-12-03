"""
有声书导入器分类路径测试
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base

from app.modules.audiobook.importer import AudiobookImporter
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
import app.core.config as config_module
from unittest.mock import patch, MagicMock
import yaml


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
    yaml_content = """audiobook:
  科幻有声:
    tags: '科幻,硬科幻,软科幻,science-fiction,sci-fi,SF'
  言情有声:
    tags: '言情,romance,爱情,恋爱'
  其他有声书:
"""
    yaml_file = tmp_path / "category.yaml"
    yaml_file.write_text(yaml_content, encoding='utf-8')
    return yaml_file


@patch('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
@patch('app.modules.media_renamer.category_helper.ruamel')
def test_audiobook_importer_path_with_category(tmp_path, db_session, temp_category_yaml, monkeypatch, mock_ruamel):
    """测试命中分类时，路径包含分类目录"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    mock_ruamel.yaml.YAML.return_value = mock_yaml_instance
    
    importer = AudiobookImporter(db_session)
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
        narrator="配音组",
        format="mp3",
        ebook=ebook
    )
    
    # 验证路径包含分类目录
    path_str = str(target_path)
    assert "科幻有声" in path_str
    assert "Audiobooks" in path_str
    assert "刘慈欣" in path_str
    assert "配音组" in target_path.name


@patch('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
@patch('app.modules.media_renamer.category_helper.ruamel')
def test_audiobook_importer_path_without_category(tmp_path, db_session, temp_category_yaml, monkeypatch, mock_ruamel):
    """测试未命中分类时，使用原有结构"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    mock_ruamel.yaml.YAML.return_value = mock_yaml_instance
    
    importer = AudiobookImporter(db_session)
    importer.category_helper = importer.category_helper.__class__(config_path=temp_category_yaml)
    
    ebook = EBook(
        title="未知有声书",
        author="未知作者",
        tags="其他标签",
        language="zh-CN"
    )
    
    target_path = importer.build_target_path(
        title=ebook.title,
        author=ebook.author,
        narrator="朗读者",
        format="mp3",
        ebook=ebook
    )
    
    # 验证路径包含默认分类"其他有声书"
    path_str = str(target_path)
    assert "Audiobooks" in path_str
    assert "未知作者" in path_str
    # 应该包含"其他有声书"（因为匹配到了默认分类）
    assert "其他有声书" in path_str


@patch('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
@patch('app.modules.media_renamer.category_helper.ruamel')
def test_audiobook_importer_path_no_ebook_object(tmp_path, db_session, temp_category_yaml, monkeypatch, mock_ruamel):
    """测试不传入 ebook 对象时，使用原有结构"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    mock_ruamel.yaml.YAML.return_value = mock_yaml_instance
    
    importer = AudiobookImporter(db_session)
    importer.category_helper = importer.category_helper.__class__(config_path=temp_category_yaml)
    
    target_path = importer.build_target_path(
        title="测试有声书",
        author="测试作者",
        narrator="测试朗读者",
        format="mp3",
        ebook=None
    )
    
    # 验证路径不包含分类目录（原有结构）
    path_str = str(target_path)
    assert "Audiobooks" in path_str
    assert "测试作者" in path_str
    # 不应该包含任何分类目录
    assert "科幻有声" not in path_str
    assert "言情有声" not in path_str
    assert "其他有声书" not in path_str


@patch('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
@patch('app.modules.media_renamer.category_helper.ruamel')
def test_audiobook_importer_path_with_series_and_category(tmp_path, db_session, temp_category_yaml, monkeypatch, mock_ruamel):
    """测试带系列和分类的路径"""
    library_root = tmp_path / "ebooks"
    monkeypatch.setattr(config_module.settings, "EBOOK_LIBRARY_ROOT", str(library_root))
    
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    mock_ruamel.yaml.YAML.return_value = mock_yaml_instance
    
    importer = AudiobookImporter(db_session)
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
        narrator="配音组",
        format="mp3",
        ebook=ebook
    )
    
    # 验证完整路径结构：Audiobooks/科幻有声/刘慈欣/地球往事/1 - 三体 - 配音组.mp3
    path_str = str(target_path)
    assert "科幻有声" in path_str
    assert "刘慈欣" in path_str
    assert "地球往事" in path_str
    assert "配音组" in target_path.name
    assert target_path.name == "1 - 三体 - 配音组.mp3"

