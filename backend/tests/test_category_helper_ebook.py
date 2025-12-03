"""
电子书分类助手测试
"""

import pytest
from unittest.mock import patch, MagicMock
from app.modules.media_renamer.category_helper import CategoryHelper
from pathlib import Path
import tempfile
import shutil
import yaml


@pytest.fixture
def temp_category_yaml(tmp_path):
    """创建临时分类配置文件"""
    yaml_content = """ebook:
  科幻:
    tags: '科幻,硬科幻,软科幻,science-fiction,sci-fi,SF'
  言情:
    tags: '言情,romance,爱情,恋爱'
  推理:
    tags: '推理,mystery,悬疑,侦探'
  其他电子书:
"""
    yaml_file = tmp_path / "category.yaml"
    yaml_file.write_text(yaml_content, encoding='utf-8')
    return yaml_file


def test_get_ebook_category_by_tags_science_fiction(temp_category_yaml, monkeypatch):
    """测试通过标签匹配科幻分类"""
    # Mock ruamel.yaml
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    
    mock_ruamel_module = MagicMock()
    mock_ruamel_module.yaml.YAML.return_value = mock_yaml_instance
    
    monkeypatch.setattr('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
    monkeypatch.setattr('app.modules.media_renamer.category_helper.ruamel', mock_ruamel_module)
    
    helper = CategoryHelper(config_path=temp_category_yaml)
    
    ebook_info = {
        "tags": ["科幻", "硬科幻"],
        "language": "zh-CN"
    }
    
    category = helper.get_ebook_category(ebook_info)
    
    assert category == "科幻"


def test_get_ebook_category_by_tags_romance(temp_category_yaml, monkeypatch):
    """测试通过标签匹配言情分类"""
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    
    mock_ruamel_module = MagicMock()
    mock_ruamel_module.yaml.YAML.return_value = mock_yaml_instance
    
    monkeypatch.setattr('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
    monkeypatch.setattr('app.modules.media_renamer.category_helper.ruamel', mock_ruamel_module)
    
    helper = CategoryHelper(config_path=temp_category_yaml)
    
    ebook_info = {
        "tags": ["romance"],
        "language": "en"
    }
    
    category = helper.get_ebook_category(ebook_info)
    
    assert category is not None
    assert category.category == "电子书"
    assert category.subcategory == "言情"


def test_get_ebook_category_no_tags_returns_default(temp_category_yaml, monkeypatch):
    """测试没有标签时返回默认分类"""
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    
    mock_ruamel_module = MagicMock()
    mock_ruamel_module.yaml.YAML.return_value = mock_yaml_instance
    
    monkeypatch.setattr('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
    monkeypatch.setattr('app.modules.media_renamer.category_helper.ruamel', mock_ruamel_module)
    
    helper = CategoryHelper(config_path=temp_category_yaml)
    
    ebook_info = {
        "tags": [],
        "language": "zh-CN"
    }
    
    category = helper.get_ebook_category(ebook_info)
    
    assert category is not None
    assert category.category == "电子书"
    assert category.subcategory == "其他电子书"


def test_get_ebook_category_no_match_returns_default(temp_category_yaml, monkeypatch):
    """测试无匹配标签时返回默认分类"""
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    
    mock_ruamel_module = MagicMock()
    mock_ruamel_module.yaml.YAML.return_value = mock_yaml_instance
    
    monkeypatch.setattr('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
    monkeypatch.setattr('app.modules.media_renamer.category_helper.ruamel', mock_ruamel_module)
    
    helper = CategoryHelper(config_path=temp_category_yaml)
    
    ebook_info = {
        "tags": ["其他标签"],
        "language": "zh-CN"
    }
    
    category = helper.get_ebook_category(ebook_info)
    
    assert category is not None
    assert category.category == "电子书"
    assert category.subcategory == "其他电子书"


def test_get_ebook_category_tags_from_string(temp_category_yaml, monkeypatch):
    """测试从字符串解析标签"""
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    
    mock_ruamel_module = MagicMock()
    mock_ruamel_module.yaml.YAML.return_value = mock_yaml_instance
    
    monkeypatch.setattr('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
    monkeypatch.setattr('app.modules.media_renamer.category_helper.ruamel', mock_ruamel_module)
    
    helper = CategoryHelper(config_path=temp_category_yaml)
    
    ebook_info = {
        "tags": "科幻,硬科幻",  # 逗号分隔字符串
        "language": "zh-CN"
    }
    
    category = helper.get_ebook_category(ebook_info)
    
    assert category == "科幻"


def test_get_ebook_category_tags_from_extra_metadata(temp_category_yaml, monkeypatch):
    """测试从 extra_metadata 中提取标签"""
    mock_yaml_instance = MagicMock()
    with open(temp_category_yaml, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    
    mock_ruamel_module = MagicMock()
    mock_ruamel_module.yaml.YAML.return_value = mock_yaml_instance
    
    monkeypatch.setattr('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
    monkeypatch.setattr('app.modules.media_renamer.category_helper.ruamel', mock_ruamel_module)
    
    helper = CategoryHelper(config_path=temp_category_yaml)
    
    ebook_info = {
        "tags": None,
        "language": "zh-CN",
        "extra_metadata": {
            "tags": ["推理", "悬疑"]
        }
    }
    
    category = helper.get_ebook_category(ebook_info)
    
    assert category is not None
    assert category.category == "电子书"
    assert category.subcategory == "推理"


def test_get_ebook_category_no_config_returns_none(tmp_path, monkeypatch):
    """测试没有配置时返回 None"""
    # 创建一个不包含 ebook 配置的 YAML
    yaml_content = """movie:
  动画电影:
    genre_ids: '16'
"""
    yaml_file = tmp_path / "category.yaml"
    yaml_file.write_text(yaml_content, encoding='utf-8')
    
    mock_yaml_instance = MagicMock()
    with open(yaml_file, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    mock_yaml_instance.load.return_value = yaml_data
    
    mock_ruamel_module = MagicMock()
    mock_ruamel_module.yaml.YAML.return_value = mock_yaml_instance
    
    monkeypatch.setattr('app.modules.media_renamer.category_helper.RUAMEL_YAML_AVAILABLE', True)
    monkeypatch.setattr('app.modules.media_renamer.category_helper.ruamel', mock_ruamel_module)
    
    helper = CategoryHelper(config_path=yaml_file)
    
    ebook_info = {
        "tags": ["科幻"],
        "language": "zh-CN"
    }
    
    category = helper.get_ebook_category(ebook_info)
    
    assert category is None

