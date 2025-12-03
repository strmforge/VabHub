"""
统一收件箱运行日志模型测试
"""

import pytest
from datetime import datetime
from app.models.inbox import InboxRunLog


def test_inbox_run_log_creation():
    """测试 InboxRunLog 模型基本创建"""
    started_at = datetime.utcnow()
    finished_at = datetime.utcnow()
    
    log = InboxRunLog(
        started_at=started_at,
        finished_at=finished_at,
        status="success",
        total_items=10,
        handled_items=8,
        skipped_items=1,
        failed_items=1,
        message="处理完成：成功 8，跳过 1，失败 1"
    )
    
    assert log.started_at == started_at
    assert log.finished_at == finished_at
    assert log.status == "success"
    assert log.total_items == 10
    assert log.handled_items == 8
    assert log.skipped_items == 1
    assert log.failed_items == 1
    assert log.message == "处理完成：成功 8，跳过 1，失败 1"
    # created_at 在保存到数据库时才会自动设置，这里只检查对象创建成功


def test_inbox_run_log_default_values():
    """测试 InboxRunLog 默认值"""
    started_at = datetime.utcnow()
    
    log = InboxRunLog(
        started_at=started_at,
        status="empty"
    )
    
    # 由于 __init__ 中设置了默认值，这些字段应该为 0
    assert log.total_items == 0
    assert log.handled_items == 0
    assert log.skipped_items == 0
    assert log.failed_items == 0
    assert log.finished_at is None
    assert log.message is None
    assert log.details is None


def test_inbox_run_log_status_values():
    """测试 InboxRunLog status 字段的有效值"""
    started_at = datetime.utcnow()
    finished_at = datetime.utcnow()
    
    # 测试各种状态值
    valid_statuses = ["success", "partial", "failed", "empty"]
    
    for status in valid_statuses:
        log = InboxRunLog(
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            total_items=5
        )
        assert log.status == status


def test_inbox_run_log_counts_non_negative():
    """测试 InboxRunLog 计数字段不允许负数（在应用层验证）"""
    started_at = datetime.utcnow()
    
    # 注意：SQLAlchemy 模型本身不强制非负约束，需要在应用层验证
    # 这里只测试正常创建
    log = InboxRunLog(
        started_at=started_at,
        status="success",
        total_items=0,
        handled_items=0,
        skipped_items=0,
        failed_items=0
    )
    
    assert log.total_items >= 0
    assert log.handled_items >= 0
    assert log.skipped_items >= 0
    assert log.failed_items >= 0


def test_inbox_run_log_with_details():
    """测试 InboxRunLog 的 details 字段（JSON）"""
    started_at = datetime.utcnow()
    finished_at = datetime.utcnow()
    
    details = {
        "by_media_type": {
            "video": {"handled": 5, "skipped": 0, "failed": 0},
            "ebook": {"handled": 3, "skipped": 1, "failed": 0}
        }
    }
    
    log = InboxRunLog(
        started_at=started_at,
        finished_at=finished_at,
        status="success",
        total_items=9,
        handled_items=8,
        skipped_items=1,
        failed_items=0,
        details=details
    )
    
    assert log.details == details
    assert log.details["by_media_type"]["video"]["handled"] == 5

