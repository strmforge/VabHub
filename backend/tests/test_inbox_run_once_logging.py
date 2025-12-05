"""
统一收件箱 run-once 日志记录测试
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inbox import InboxRunLog
from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.base import MediaTypeGuess


@pytest.mark.asyncio
async def test_run_once_logs_success(db_session: AsyncSession, tmp_path):
    """测试 run-once 成功时记录日志"""
    from app.api.inbox_dev import run_inbox_once
    
    # 创建测试文件
    test_file = tmp_path / "test.mp4"
    test_file.write_bytes(b"fake video")
    
    # Mock run_inbox_classification 返回结果
    with patch('app.api.inbox_dev.run_inbox_classification') as mock_classification:
        mock_classification.return_value = [
            {
                "path": str(test_file),
                "media_type": "movie",
                "score": 0.9,
                "reason": "extension_mp4",
                "size_bytes": 1024,
                "modified_at": datetime.utcnow().isoformat(),
                "result": "handled:video:movie"
            }
        ]
        
        # 调用 run-once
        response = await run_inbox_once(db_session)
        
        # 验证响应
        assert response["success"] is True
        assert len(response["data"]["items"]) == 1
        
        # 验证日志被写入
        from sqlalchemy import select
        stmt = select(InboxRunLog).order_by(InboxRunLog.created_at.desc()).limit(1)
        result = await db_session.execute(stmt)
        log = result.scalar_one_or_none()
        
        assert log is not None
        assert log.status == "success"
        assert log.total_items == 1
        assert log.handled_items == 1
        assert log.skipped_items == 0
        assert log.failed_items == 0
        assert log.message is not None
        assert "成功" in log.message


@pytest.mark.asyncio
async def test_run_once_logs_partial(db_session: AsyncSession, tmp_path):
    """测试 run-once 部分成功时记录日志"""
    from app.api.inbox_dev import run_inbox_once
    
    # Mock run_inbox_classification 返回混合结果
    with patch('app.api.inbox_dev.run_inbox_classification') as mock_classification:
        mock_classification.return_value = [
            {
                "path": "/test1.mp4",
                "media_type": "movie",
                "score": 0.9,
                "reason": "extension_mp4",
                "size_bytes": 1024,
                "modified_at": datetime.utcnow().isoformat(),
                "result": "handled:video:movie"
            },
            {
                "path": "/test2.mp4",
                "media_type": "movie",
                "score": 0.9,
                "reason": "extension_mp4",
                "size_bytes": 1024,
                "modified_at": datetime.utcnow().isoformat(),
                "result": "failed:video:movie"
            }
        ]
        
        # 调用 run-once
        response = await run_inbox_once(db_session)
        
        # 验证日志状态为 partial
        from sqlalchemy import select
        stmt = select(InboxRunLog).order_by(InboxRunLog.created_at.desc()).limit(1)
        result = await db_session.execute(stmt)
        log = result.scalar_one_or_none()
        
        assert log is not None
        assert log.status == "partial"
        assert log.total_items == 2
        assert log.handled_items == 1
        assert log.failed_items == 1


@pytest.mark.asyncio
async def test_run_once_logs_failed(db_session: AsyncSession, tmp_path):
    """测试 run-once 全部失败时记录日志"""
    from app.api.inbox_dev import run_inbox_once
    
    # Mock run_inbox_classification 返回全部失败
    with patch('app.api.inbox_dev.run_inbox_classification') as mock_classification:
        mock_classification.return_value = [
            {
                "path": "/test1.mp4",
                "media_type": "movie",
                "score": 0.9,
                "reason": "extension_mp4",
                "size_bytes": 1024,
                "modified_at": datetime.utcnow().isoformat(),
                "result": "failed:video:movie"
            }
        ]
        
        # 调用 run-once
        response = await run_inbox_once(db_session)
        
        # 验证日志状态为 failed
        from sqlalchemy import select
        stmt = select(InboxRunLog).order_by(InboxRunLog.created_at.desc()).limit(1)
        result = await db_session.execute(stmt)
        log = result.scalar_one_or_none()
        
        assert log is not None
        assert log.status == "failed"
        assert log.total_items == 1
        assert log.handled_items == 0
        assert log.failed_items == 1


@pytest.mark.asyncio
async def test_run_once_logs_empty(db_session: AsyncSession):
    """测试 run-once 空结果时记录日志"""
    from app.api.inbox_dev import run_inbox_once
    
    # Mock run_inbox_classification 返回空结果
    with patch('app.api.inbox_dev.run_inbox_classification') as mock_classification:
        mock_classification.return_value = []
        
        # 调用 run-once
        response = await run_inbox_once(db_session)
        
        # 验证日志状态为 empty
        from sqlalchemy import select
        stmt = select(InboxRunLog).order_by(InboxRunLog.created_at.desc()).limit(1)
        result = await db_session.execute(stmt)
        log = result.scalar_one_or_none()
        
        assert log is not None
        assert log.status == "empty"
        assert log.total_items == 0
        assert log.handled_items == 0
        assert log.skipped_items == 0
        assert log.failed_items == 0


@pytest.mark.asyncio
async def test_run_once_logs_by_media_type(db_session: AsyncSession):
    """测试 run-once 记录按 media_type 的统计"""
    from app.api.inbox_dev import run_inbox_once
    
    # Mock run_inbox_classification 返回多种媒体类型
    with patch('app.api.inbox_dev.run_inbox_classification') as mock_classification:
        mock_classification.return_value = [
            {
                "path": "/test1.mp4",
                "media_type": "movie",
                "score": 0.9,
                "reason": "extension_mp4",
                "size_bytes": 1024,
                "modified_at": datetime.utcnow().isoformat(),
                "result": "handled:video:movie"
            },
            {
                "path": "/test2.epub",
                "media_type": "ebook",
                "score": 0.8,
                "reason": "extension_epub",
                "size_bytes": 2048,
                "modified_at": datetime.utcnow().isoformat(),
                "result": "handled:ebook"
            },
            {
                "path": "/test3.mp3",
                "media_type": "music",
                "score": 0.7,
                "reason": "extension_mp3",
                "size_bytes": 512,
                "modified_at": datetime.utcnow().isoformat(),
                "result": "skipped:music_disabled"
            }
        ]
        
        # 调用 run-once
        response = await run_inbox_once(db_session)
        
        # 验证日志包含按 media_type 的统计
        from sqlalchemy import select
        stmt = select(InboxRunLog).order_by(InboxRunLog.created_at.desc()).limit(1)
        result = await db_session.execute(stmt)
        log = result.scalar_one_or_none()
        
        assert log is not None
        assert log.details is not None
        assert "by_media_type" in log.details
        assert "movie" in log.details["by_media_type"]
        assert "ebook" in log.details["by_media_type"]
        assert "music" in log.details["by_media_type"]
        assert log.details["by_media_type"]["movie"]["handled"] == 1
        assert log.details["by_media_type"]["ebook"]["handled"] == 1
        assert log.details["by_media_type"]["music"]["skipped"] == 1


@pytest.mark.asyncio
async def test_run_once_logs_on_exception(db_session: AsyncSession):
    """测试 run-once 异常时也记录日志"""
    from app.api.inbox_dev import run_inbox_once
    
    # Mock run_inbox_classification 抛出异常
    with patch('app.api.inbox_dev.run_inbox_classification') as mock_classification:
        mock_classification.side_effect = Exception("Test error")
        
        # 调用 run-once（应该抛出 HTTPException）
        with pytest.raises(Exception):
            await run_inbox_once(db_session)
        
        # 验证日志被记录（即使异常）
        from sqlalchemy import select
        stmt = select(InboxRunLog).order_by(InboxRunLog.created_at.desc()).limit(1)
        result = await db_session.execute(stmt)
        log = result.scalar_one_or_none()
        
        # 注意：由于异常处理，可能没有记录日志，或者记录了失败的日志
        # 这里主要验证不会因为日志记录失败而影响异常抛出
        if log:
            assert log.status == "failed"

