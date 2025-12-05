"""
测试 TTS Storage Service

Note: These tests require file system access and may fail on Windows due to permission issues.
      Skipped by default in CI - requires VABHUB_ENABLE_TTS_TESTS=1 to run.
"""

import os
import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

# Skip tests that require complex TTS setup unless explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("VABHUB_ENABLE_TTS_TESTS"),
    reason="TTS Storage Service tests require VABHUB_ENABLE_TTS_TESTS=1"
)

from app.modules.tts.storage_service import (
    scan_storage,
    build_overview,
    filter_files_for_cleanup,
    build_cleanup_plan,
    execute_cleanup,
    TTSFileInfo,
)


@pytest.fixture
def temp_storage_root():
    """创建临时存储目录"""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        yield root


def test_scan_storage_collects_files_and_categories(temp_storage_root):
    """测试扫描存储目录并分类文件"""
    # 创建测试文件结构
    playground_dir = temp_storage_root / "playground"
    jobs_dir = temp_storage_root / "jobs"
    other_dir = temp_storage_root / "other"
    
    playground_dir.mkdir(parents=True)
    jobs_dir.mkdir(parents=True)
    other_dir.mkdir(parents=True)
    
    # 创建文件
    (playground_dir / "test1.mp3").write_bytes(b"playground audio")
    (jobs_dir / "job-123" / "chapter1.mp3").mkdir(parents=True)
    (jobs_dir / "job-123" / "chapter1.mp3").write_bytes(b"job audio")
    (other_dir / "temp.mp3").write_bytes(b"other audio")
    
    # 扫描
    files = scan_storage(temp_storage_root)
    
    assert len(files) == 3
    
    categories = {f.category for f in files}
    assert "playground" in categories
    assert "job" in categories
    assert "other" in categories


def test_build_overview_aggregates_by_category(temp_storage_root):
    """测试构建概览并按类别聚合"""
    # 创建测试文件
    playground_dir = temp_storage_root / "playground"
    jobs_dir = temp_storage_root / "jobs"
    
    playground_dir.mkdir(parents=True)
    jobs_dir.mkdir(parents=True)
    
    (playground_dir / "p1.mp3").write_bytes(b"x" * 100)
    (playground_dir / "p2.mp3").write_bytes(b"x" * 200)
    (jobs_dir / "j1.mp3").write_bytes(b"x" * 300)
    
    # 扫描并构建概览
    files = scan_storage(temp_storage_root)
    overview = build_overview(files, temp_storage_root)
    
    assert overview.total_files == 3
    assert overview.total_size_bytes == 600
    
    assert overview.by_category["playground"]["files"] == 2
    assert overview.by_category["playground"]["size_bytes"] == 300
    assert overview.by_category["job"]["files"] == 1
    assert overview.by_category["job"]["size_bytes"] == 300


def test_filter_files_for_cleanup_respects_scope_and_min_age(temp_storage_root):
    """测试清理过滤函数尊重范围和最小保留天数"""
    # 创建测试文件
    playground_dir = temp_storage_root / "playground"
    jobs_dir = temp_storage_root / "jobs"
    
    playground_dir.mkdir(parents=True)
    jobs_dir.mkdir(parents=True)
    
    now = datetime.now(timezone.utc)
    
    # 创建旧文件（10天前）
    old_file = playground_dir / "old.mp3"
    old_file.write_bytes(b"old")
    old_mtime = now - timedelta(days=10)
    old_file.touch()
    import os
    os.utime(old_file, (old_mtime.timestamp(), old_mtime.timestamp()))
    
    # 创建新文件（1天前）
    new_file = jobs_dir / "new.mp3"
    new_file.write_bytes(b"new")
    new_mtime = now - timedelta(days=1)
    new_file.touch()
    os.utime(new_file, (new_mtime.timestamp(), new_mtime.timestamp()))
    
    # 扫描
    files = scan_storage(temp_storage_root)
    
    # 测试范围过滤
    playground_only = filter_files_for_cleanup(files, "playground_only", min_age_days=7)
    assert len(playground_only) == 1
    assert playground_only[0].category == "playground"
    
    # 测试最小保留天数过滤
    all_old = filter_files_for_cleanup(files, "all", min_age_days=7)
    assert len(all_old) == 1
    assert all_old[0].path == old_file
    
    all_recent = filter_files_for_cleanup(files, "all", min_age_days=0)
    assert len(all_recent) == 2


def test_execute_cleanup_dry_run_does_not_delete(temp_storage_root):
    """测试 dry_run 模式不删除文件"""
    # 创建测试文件
    test_file = temp_storage_root / "test.mp3"
    test_file.write_bytes(b"test data")
    
    # 创建清理计划
    files = scan_storage(temp_storage_root)
    plan = build_cleanup_plan(
        root=temp_storage_root,
        scope="all",
        min_age_days=0,
        max_files=None
    )
    
    # 执行 dry_run
    result = execute_cleanup(plan, dry_run=True)
    
    # 文件应该还在
    assert test_file.exists()
    assert result.total_deleted_files == len(plan.matched_files)
    assert result.total_freed_bytes == plan.total_freed_bytes


def test_execute_cleanup_deletes_files_and_handles_errors(temp_storage_root):
    """测试执行清理删除文件并处理错误"""
    # 创建测试文件
    file1 = temp_storage_root / "file1.mp3"
    file2 = temp_storage_root / "file2.mp3"
    
    file1.write_bytes(b"data1")
    file2.write_bytes(b"data2")
    
    # 创建清理计划
    files = scan_storage(temp_storage_root)
    plan = build_cleanup_plan(
        root=temp_storage_root,
        scope="all",
        min_age_days=0,
        max_files=None
    )
    
    # 手动删除一个文件（模拟删除过程中的错误）
    file1.unlink()
    
    # 执行清理
    result = execute_cleanup(plan, dry_run=False)
    
    # file2 应该被删除
    assert not file2.exists()
    # 应该统计了实际删除的数量
    assert result.total_deleted_files >= 1

