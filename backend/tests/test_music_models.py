"""
音乐模型测试
"""

import pytest
from datetime import datetime
from app.models.music import Music, MusicFile


def test_music_creation():
    """测试 Music 模型基本创建"""
    music = Music(
        title="测试专辑",
        artist="测试歌手",
        album="测试专辑名",
        year=2023
    )
    
    assert music.title == "测试专辑"
    assert music.artist == "测试歌手"
    assert music.album == "测试专辑名"
    assert music.year == 2023
    # created_at 在保存到数据库时才会自动设置，这里只检查对象创建成功


def test_music_file_creation():
    """测试 MusicFile 模型基本创建"""
    # 先创建一个 Music 对象（模拟）
    music = Music(
        id=1,
        title="测试曲目",
        artist="测试歌手"
    )
    
    music_file = MusicFile(
        music_id=music.id,
        file_path="/path/to/test.mp3",
        file_size_bytes=1024 * 1024 * 5,  # 5MB
        format="mp3",
        track_number=1
    )
    
    assert music_file.music_id == 1
    assert music_file.file_path == "/path/to/test.mp3"
    assert music_file.file_size_bytes == 1024 * 1024 * 5
    assert music_file.format == "mp3"
    assert music_file.track_number == 1
    # 自动计算 file_size_mb
    assert music_file.file_size_mb == pytest.approx(5.0, rel=0.01)


def test_music_file_auto_calculate_size():
    """测试 MusicFile 自动计算 file_size_mb"""
    music_file = MusicFile(
        music_id=1,
        file_path="/path/to/test.flac",
        file_size_bytes=1024 * 1024 * 10,  # 10MB
        format="flac"
    )
    
    # file_size_mb 应该自动计算
    assert music_file.file_size_mb == pytest.approx(10.0, rel=0.01)


def test_music_file_without_size():
    """测试 MusicFile 没有 file_size_bytes 时不计算 file_size_mb"""
    music_file = MusicFile(
        music_id=1,
        file_path="/path/to/test.mp3",
        format="mp3"
    )
    
    # 如果没有 file_size_bytes，file_size_mb 应该为 None
    assert music_file.file_size_mb is None

