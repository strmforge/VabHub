"""
用户通知模型和服务测试
"""

import pytest
from datetime import datetime

from app.models.user_notification import UserNotification
from app.models.ebook import EBook
from app.models.tts_job import TTSJob
from app.modules.tts.notification_service import create_tts_job_notification


@pytest.mark.asyncio
async def test_create_notification_success(db_session):
    """测试创建通知成功，字段正确"""
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建测试 Job
    job = TTSJob(
        ebook_id=1,
        status="success",
        requested_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        processed_chapters=10,
        created_files_count=10,
        error_count=0,
        created_by="test"
    )
    db_session.add(job)
    await db_session.flush()
    
    # 创建通知
    notification = await create_tts_job_notification(
        db=db_session,
        job=job,
        ebook=ebook,
        status="success",
        summary={"generated_chapters": 10, "total_chapters": 10}
    )
    await db_session.commit()
    
    # 验证
    assert notification.id > 0
    assert notification.type == "tts_job_succeeded"
    assert notification.severity == "success"
    assert notification.ebook_id == 1
    assert notification.tts_job_id == job.id
    assert notification.is_read is False
    assert "测试小说" in notification.title
    assert "生成" in notification.message


@pytest.mark.asyncio
async def test_create_notification_for_different_statuses(db_session):
    """测试不同 Job status 生成不同 type / severity"""
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.flush()
    
    # 测试 success
    job1 = TTSJob(
        ebook_id=1,
        status="success",
        requested_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        processed_chapters=10,
        created_files_count=10,
        error_count=0,
        created_by="test"
    )
    db_session.add(job1)
    await db_session.flush()
    
    notif1 = await create_tts_job_notification(
        db=db_session,
        job=job1,
        ebook=ebook,
        status="success"
    )
    assert notif1.type == "tts_job_succeeded"
    assert notif1.severity == "success"
    
    # 测试 partial
    job2 = TTSJob(
        ebook_id=1,
        status="partial",
        requested_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        processed_chapters=5,
        created_files_count=5,
        error_count=0,
        created_by="test"
    )
    db_session.add(job2)
    await db_session.flush()
    
    notif2 = await create_tts_job_notification(
        db=db_session,
        job=job2,
        ebook=ebook,
        status="partial",
        summary={"generated_chapters": 5, "total_chapters": 10}
    )
    assert notif2.type == "tts_job_partial"
    assert notif2.severity == "warning"
    
    # 测试 failed
    job3 = TTSJob(
        ebook_id=1,
        status="failed",
        requested_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=1,
        last_error="测试错误",
        created_by="test"
    )
    db_session.add(job3)
    await db_session.flush()
    
    notif3 = await create_tts_job_notification(
        db=db_session,
        job=job3,
        ebook=ebook,
        status="failed"
    )
    assert notif3.type == "tts_job_failed"
    assert notif3.severity == "error"
    assert "失败" in notif3.message
    
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_notification_without_ebook(db_session):
    """测试 ebook 为空时标题 message 不崩"""
    # 创建测试 EBook（用于 Job，但通知时传 None）
    ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建测试 Job（有 ebook_id，但通知时 ebook 参数为 None）
    job = TTSJob(
        ebook_id=1,
        status="success",
        requested_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        processed_chapters=10,
        created_files_count=10,
        error_count=0,
        created_by="test"
    )
    db_session.add(job)
    await db_session.flush()
    
    # 创建通知（ebook 参数为 None，但 job.ebook_id 存在）
    notification = await create_tts_job_notification(
        db=db_session,
        job=job,
        ebook=None,  # 故意传 None 测试 graceful fallback
        status="success"
    )
    await db_session.commit()
    
    # 验证
    assert notification.id > 0
    assert "某作品" in notification.title or "作品" in notification.title
    assert notification.message  # 消息不为空

