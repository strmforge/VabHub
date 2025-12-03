"""
漫画模型测试
"""

import pytest
from datetime import datetime
from app.models.comic import Comic, ComicFile


def test_comic_model_creation():
    """测试 Comic 模型基本创建"""
    comic = Comic(
        title="测试漫画",
        series="测试系列",
        volume_index=1,
        author="测试作者",
        illustrator="测试作画",
        language="zh-CN",
        region="CN"
    )
    assert comic.title == "测试漫画"
    assert comic.series == "测试系列"
    assert comic.volume_index == 1
    assert comic.author == "测试作者"
    assert comic.illustrator == "测试作画"
    assert comic.language == "zh-CN"
    assert comic.region == "CN"
    # created_at 在数据库操作时才会自动设置，这里只验证字段存在
    assert hasattr(comic, 'created_at')


def test_comic_file_model_creation():
    """测试 ComicFile 模型基本创建"""
    comic = Comic(title="测试漫画", series="测试系列")
    comic.id = 1  # 在真实场景中，comic 会被提交到数据库并获得 ID
    
    comic_file = ComicFile(
        comic_id=comic.id,
        file_path="/path/to/test.cbz",
        file_size_bytes=1024 * 1024 * 10,  # 10 MB
        format="cbz",
        page_count=100
    )
    assert comic_file.comic_id == 1
    assert comic_file.file_path == "/path/to/test.cbz"
    assert comic_file.format == "cbz"
    assert comic_file.page_count == 100
    assert comic_file.file_size_mb == 10.0


def test_comic_file_auto_calculate_size():
    """测试 ComicFile 自动计算 file_size_mb"""
    comic = Comic(title="测试漫画", series="测试系列")
    comic.id = 1
    
    comic_file = ComicFile(
        comic_id=comic.id,
        file_path="/path/to/another.cbr",
        file_size_bytes=1024 * 1024 * 5.5,  # 5.5 MB
        format="cbr"
    )
    assert comic_file.file_size_mb == 5.5


def test_comic_file_without_size():
    """测试 ComicFile 没有文件大小的情况"""
    comic = Comic(title="测试漫画", series="测试系列")
    comic.id = 1
    
    comic_file = ComicFile(
        comic_id=comic.id,
        file_path="/path/to/no_size.zip",
        format="zip"
    )
    assert comic_file.file_size_bytes is None
    assert comic_file.file_size_mb is None

