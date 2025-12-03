"""
带 PT 检测器的聚合测试
"""

import pytest
from pathlib import Path

from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.service import MediaTypeDetectionService
from app.modules.inbox.media_detection.pt_category_detector import PTCategoryDetector
from app.modules.inbox.media_detection.extension_detector import ExtensionDetector
from app.modules.inbox.media_detection.novel_txt_detector import NovelTxtDetector
from app.core.config import settings


def test_detection_service_with_pt_category_priority(tmp_path):
    """测试 PT 分类检测器优先级高于扩展名检测器"""
    # 创建一个 .mp3 文件，但 PT 分类为"有声书"
    test_file = tmp_path / "test.mp3"
    test_file.write_text("fake audio")
    
    item = InboxItem(
        path=test_file,
        source_category="有声书"
    )
    
    # 构造检测服务，包含三种检测器
    detectors = [
        PTCategoryDetector(score=0.95),  # PT 分类检测器（高优先级）
        ExtensionDetector(),  # 扩展名检测器（对 .mp3 可能判为 audiobook 或 music，score 约 0.6）
        NovelTxtDetector(),  # Novel TXT 检测器（对非 txt 返回 None）
    ]
    
    service = MediaTypeDetectionService(
        detectors=detectors,
        min_score=settings.INBOX_DETECTION_MIN_SCORE
    )
    
    guess = service.detect(item)
    
    # 应该使用 PT 分类检测器的结果
    assert guess.media_type == "audiobook"
    assert guess.score == 0.95  # PT 检测器的分数
    assert "pt_category" in guess.reason or "有声书" in guess.reason


def test_detection_service_pt_category_vs_extension(tmp_path):
    """测试 PT 分类检测器覆盖扩展名检测器"""
    # 创建一个 .mkv 文件，但 PT 分类为"有声书"（异常情况，但测试逻辑）
    test_file = tmp_path / "test.mkv"
    test_file.write_text("fake video")
    
    item = InboxItem(
        path=test_file,
        source_category="有声书"
    )
    
    detectors = [
        PTCategoryDetector(score=0.95),
        ExtensionDetector(),  # 对 .mkv 会判为 movie，score 0.9
        NovelTxtDetector(),
    ]
    
    service = MediaTypeDetectionService(
        detectors=detectors,
        min_score=settings.INBOX_DETECTION_MIN_SCORE
    )
    
    guess = service.detect(item)
    
    # PT 分类检测器的分数更高，应该优先
    assert guess.media_type == "audiobook"
    assert guess.score == 0.95


def test_detection_service_no_pt_hint_falls_back(tmp_path):
    """测试没有 PT hint 时回退到其他检测器"""
    test_file = tmp_path / "test.epub"
    test_file.write_text("fake ebook")
    
    item = InboxItem(
        path=test_file,
        source_category=None,
        source_tags=None
    )
    
    detectors = [
        PTCategoryDetector(),  # 没有 hint，返回 None
        ExtensionDetector(),  # 应该匹配 .epub => ebook
        NovelTxtDetector(),
    ]
    
    service = MediaTypeDetectionService(
        detectors=detectors,
        min_score=settings.INBOX_DETECTION_MIN_SCORE
    )
    
    guess = service.detect(item)
    
    # 应该使用扩展名检测器的结果
    assert guess.media_type == "ebook"
    assert guess.score >= 0.9  # ExtensionDetector 对 .epub 的分数
    assert "extension" in guess.reason.lower()

