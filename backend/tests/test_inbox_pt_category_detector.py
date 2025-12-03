"""
PT 分类检测器测试
"""

import pytest
from pathlib import Path

from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.pt_category_detector import (
    PTCategoryDetector,
    DEFAULT_PT_CATEGORY_MEDIA_TYPE_MAPPING
)


def test_pt_category_detector_by_category_exact_match(tmp_path):
    """测试通过分类精确匹配"""
    test_file = tmp_path / "test.mkv"
    test_file.write_text("fake video")
    
    item = InboxItem(
        path=test_file,
        source_category="电影"
    )
    
    detector = PTCategoryDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "movie"
    assert guess.score >= 0.9
    assert "电影" in guess.reason or "pt_category" in guess.reason


def test_pt_category_detector_by_category_substring(tmp_path):
    """测试通过分类子串匹配"""
    test_file = tmp_path / "test.mkv"
    test_file.write_text("fake video")
    
    item = InboxItem(
        path=test_file,
        source_category="Movie / 电影"
    )
    
    detector = PTCategoryDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "movie"
    assert guess.score >= 0.9


def test_pt_category_detector_by_tags(tmp_path):
    """测试通过标签匹配"""
    test_file = tmp_path / "test.mp3"
    test_file.write_text("fake audio")
    
    item = InboxItem(
        path=test_file,
        source_category=None,
        source_tags=["有声书", "xx"]
    )
    
    detector = PTCategoryDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "audiobook"
    assert guess.score >= 0.9
    assert "有声书" in guess.reason or "pt_tag" in guess.reason


def test_pt_category_detector_no_match_returns_none(tmp_path):
    """测试无匹配时返回 None"""
    test_file = tmp_path / "test.bin"
    test_file.write_text("unknown")
    
    item = InboxItem(
        path=test_file,
        source_category="杂项"
    )
    
    detector = PTCategoryDetector()
    guess = detector.guess(item)
    
    assert guess is None


def test_pt_category_detector_no_hint_returns_none(tmp_path):
    """测试无 hint 时返回 None"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    
    item = InboxItem(
        path=test_file,
        source_category=None,
        source_tags=None
    )
    
    detector = PTCategoryDetector()
    guess = detector.guess(item)
    
    assert guess is None


def test_pt_category_detector_english_category(tmp_path):
    """测试英文分类匹配"""
    test_file = tmp_path / "test.epub"
    test_file.write_text("fake ebook")
    
    item = InboxItem(
        path=test_file,
        source_category="E-Book"
    )
    
    detector = PTCategoryDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "ebook"
    assert guess.score >= 0.9


def test_pt_category_detector_custom_mapping(tmp_path):
    """测试自定义映射"""
    test_file = tmp_path / "test.mkv"
    test_file.write_text("fake video")
    
    custom_mapping = {
        "custom_movie": "movie"
    }
    
    item = InboxItem(
        path=test_file,
        source_category="custom_movie"
    )
    
    detector = PTCategoryDetector(mapping=custom_mapping)
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "movie"


def test_pt_category_detector_tag_score_slightly_lower(tmp_path):
    """测试标签匹配的分数略低于分类匹配"""
    test_file = tmp_path / "test.mp3"
    test_file.write_text("fake audio")
    
    item = InboxItem(
        path=test_file,
        source_category=None,
        source_tags=["audiobook"]
    )
    
    detector = PTCategoryDetector(score=0.95)
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "audiobook"
    # 标签匹配的分数应该略低（0.9 而不是 0.95）
    assert 0.9 <= guess.score < 0.95

