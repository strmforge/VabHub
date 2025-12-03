"""
测试媒体类型常量对 ebook 的支持
"""

import pytest
from app.constants.media_types import (
    MEDIA_TYPE_EBOOK,
    MEDIA_TYPE_CHOICES,
    normalize_media_type,
)


def test_ebook_in_choices():
    """测试 MEDIA_TYPE_EBOOK 在 MEDIA_TYPE_CHOICES 中"""
    assert MEDIA_TYPE_EBOOK in MEDIA_TYPE_CHOICES


def test_normalize_ebook():
    """测试 normalize_media_type 对 ebook 的支持"""
    assert normalize_media_type("ebook") == MEDIA_TYPE_EBOOK
    assert normalize_media_type("EBOOK") == MEDIA_TYPE_EBOOK
    assert normalize_media_type("Book") == MEDIA_TYPE_EBOOK
    assert normalize_media_type("book") == MEDIA_TYPE_EBOOK
    assert normalize_media_type("books") == MEDIA_TYPE_EBOOK
    assert normalize_media_type("电子书") == MEDIA_TYPE_EBOOK


def test_normalize_ebook_variants():
    """测试 normalize_media_type 对 ebook 变体的支持"""
    # 测试常见变体
    variants = ["ebook", "EBOOK", "Book", "book", "books", "电子书"]
    for variant in variants:
        assert normalize_media_type(variant) == MEDIA_TYPE_EBOOK

