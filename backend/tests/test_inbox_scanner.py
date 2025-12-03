"""
统一收件箱扫描器测试
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from app.modules.inbox.scanner import InboxScanner
from app.modules.inbox.models import InboxItem


def test_scan_inbox_empty_dir(tmp_path):
    """测试扫描空目录"""
    scanner = InboxScanner(inbox_root=tmp_path)
    items = scanner.scan_inbox()
    
    assert len(items) == 0


def test_scan_inbox_with_files(tmp_path):
    """测试扫描包含文件的目录"""
    # 创建测试文件
    (tmp_path / "test1.txt").write_text("test content")
    (tmp_path / "test2.epub").write_text("test content")
    (tmp_path / "test3.mp3").write_text("test content")
    
    scanner = InboxScanner(inbox_root=tmp_path)
    items = scanner.scan_inbox()
    
    assert len(items) == 3
    assert all(isinstance(item, InboxItem) for item in items)
    assert all(item.path.exists() for item in items)


def test_scan_inbox_ignores_hidden_files(tmp_path):
    """测试忽略隐藏文件"""
    (tmp_path / ".hidden.txt").write_text("hidden")
    (tmp_path / "visible.txt").write_text("visible")
    
    scanner = InboxScanner(inbox_root=tmp_path)
    items = scanner.scan_inbox()
    
    assert len(items) == 1
    assert items[0].path.name == "visible.txt"


def test_scan_inbox_ignores_imported_files(tmp_path):
    """测试忽略已处理标记的文件"""
    (tmp_path / "test.txt").write_text("test")
    (tmp_path / "test.txt.imported").write_text("imported")
    
    scanner = InboxScanner(inbox_root=tmp_path)
    items = scanner.scan_inbox()
    
    assert len(items) == 1
    assert items[0].path.name == "test.txt"


def test_scan_inbox_max_items(tmp_path):
    """测试最大项目数限制"""
    # 创建超过限制的文件
    for i in range(10):
        (tmp_path / f"test{i}.txt").write_text("test")
    
    scanner = InboxScanner(inbox_root=tmp_path, max_items=5)
    items = scanner.scan_inbox()
    
    assert len(items) <= 5

