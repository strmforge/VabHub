"""
统一收件箱媒体类型检测测试
"""

import pytest
from pathlib import Path
import tempfile

from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.extension_detector import ExtensionDetector
from app.modules.inbox.media_detection.novel_txt_detector import NovelTxtDetector
from app.modules.inbox.media_detection.service import MediaTypeDetectionService, get_default_detection_service


def test_extension_detector_ebook(tmp_path):
    """测试扩展名检测器识别电子书"""
    test_file = tmp_path / "test.epub"
    test_file.write_text("fake epub")
    
    item = InboxItem(path=test_file)
    detector = ExtensionDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "ebook"
    assert guess.score >= 0.9


def test_extension_detector_video(tmp_path):
    """测试扩展名检测器识别视频"""
    test_file = tmp_path / "test.mkv"
    test_file.write_text("fake video")
    
    item = InboxItem(path=test_file)
    detector = ExtensionDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "movie"
    assert guess.score >= 0.9


def test_extension_detector_audio(tmp_path):
    """测试扩展名检测器识别音频"""
    test_file = tmp_path / "test.mp3"
    test_file.write_text("fake audio")
    
    item = InboxItem(path=test_file)
    detector = ExtensionDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "audiobook"
    assert guess.score >= 0.6


def test_extension_detector_txt(tmp_path):
    """测试扩展名检测器识别 TXT"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("fake txt")
    
    item = InboxItem(path=test_file)
    detector = ExtensionDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "novel_txt"
    assert guess.score >= 0.5


def test_novel_txt_detector_with_chapters(tmp_path):
    """测试小说 TXT 检测器识别带章节的文件"""
    # 确保文件足够大（超过 50KB）
    content = """第1章 开始
这是第一章的内容。
有很多中文字符。

第2章 继续
这是第二章的内容。
继续写。
""" * 2000  # 重复内容使文件足够大
    test_file = tmp_path / "novel.txt"
    test_file.write_text(content, encoding='utf-8')
    
    item = InboxItem(path=test_file)
    detector = NovelTxtDetector()
    guess = detector.guess(item)
    
    assert guess is not None
    assert guess.media_type == "novel_txt"
    assert guess.score >= 0.7


def test_novel_txt_detector_small_file(tmp_path):
    """测试小说 TXT 检测器跳过太小的文件"""
    test_file = tmp_path / "small.txt"
    test_file.write_text("too small")  # 小于 50KB
    
    item = InboxItem(path=test_file)
    detector = NovelTxtDetector()
    guess = detector.guess(item)
    
    # 太小的文件应该返回 None
    assert guess is None


def test_detection_service_aggregation(tmp_path):
    """测试检测服务聚合多个检测器"""
    # 创建一个带章节的 TXT 文件，确保文件足够大
    content = """第1章 开始
这是第一章的内容。
有很多中文字符。
""" * 2000  # 重复内容使文件足够大
    test_file = tmp_path / "novel.txt"
    test_file.write_text(content, encoding='utf-8')
    
    item = InboxItem(path=test_file)
    
    # 使用默认检测服务
    service = get_default_detection_service()
    guess = service.detect(item)
    
    assert guess.media_type == "novel_txt"
    # novel_txt_detector 应该提升分数（从 0.5 提升到至少 0.7）
    assert guess.score >= 0.7


def test_detection_service_unknown(tmp_path):
    """测试检测服务返回 unknown"""
    # 创建一个无法识别的文件
    test_file = tmp_path / "unknown.bin"
    test_file.write_bytes(b"binary content")
    
    item = InboxItem(path=test_file)
    service = get_default_detection_service()
    guess = service.detect(item)
    
    assert guess.media_type == "unknown"
    assert guess.score < 0.4  # 低于阈值

