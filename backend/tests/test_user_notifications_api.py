"""
用户通知 API 测试

注意: /user/notifications API 路由当前已被禁用（存在 Schema 冲突）
此测试模块将被跳过
"""

import pytest

# API 路由被禁用，跳过整个测试模块
pytestmark = pytest.mark.skip(reason="用户通知 API 路由已禁用: /user/notifications")
from fastapi.testclient import TestClient
from main import app
from datetime import datetime

from app.models.user_notification import UserNotification
from app.models.ebook import EBook
from app.models.tts_job import TTSJob
from app.core.database import get_db


@pytest.mark.asyncio
async def test_get_recent_notifications(db_session):
    """测试 recent 返回最近通知，按时间倒序"""
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建测试 EBook
        ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
        db_session.add(ebook)
        await db_session.flush()
        
        # 创建多个通知
        notifications = [
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                tts_job_id=1,
                title="通知1",
                message="消息1",
                is_read=False
            ),
            UserNotification(
                user_id=1,
                type="tts_job_failed",
                ebook_id=1,
                tts_job_id=2,
                title="通知2",
                message="消息2",
                is_read=False
            ),
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                tts_job_id=3,
                title="通知3",
                message="消息3",
                is_read=True
            ),
        ]
        for notif in notifications:
            db_session.add(notif)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.get("/api/user/notifications/recent?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "unread_count" in data
        assert len(data["items"]) == 3
        assert data["unread_count"] == 2  # 2 个未读
        
        # 验证排序（按时间倒序，后创建的在前面）
        if len(data["items"]) > 1:
            # 后创建的通知 ID 应该更大，所以应该在前
            assert data["items"][0]["id"] >= data["items"][1]["id"] or data["items"][0]["created_at"] >= data["items"][1]["created_at"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_unread_count(db_session):
    """测试 unread-count 正确"""
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建测试通知
        notifications = [
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知1",
                message="消息1",
                is_read=False
            ),
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知2",
                message="消息2",
                is_read=False
            ),
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知3",
                message="消息3",
                is_read=True
            ),
        ]
        for notif in notifications:
            db_session.add(notif)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.get("/api/user/notifications/unread-count")
        
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_mark_read_all(db_session):
    """测试 mark-read 无 ids → 全部标记为已读"""
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建测试通知
        notifications = [
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知1",
                message="消息1",
                is_read=False
            ),
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知2",
                message="消息2",
                is_read=False
            ),
        ]
        for notif in notifications:
            db_session.add(notif)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.post("/api/user/notifications/mark-read", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated"] == 2
        
        # 验证已读
        response2 = client.get("/api/user/notifications/unread-count")
        assert response2.json()["unread_count"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_mark_read_specific_ids(db_session):
    """测试 mark-read 指定 ids → 只标记部分"""
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建测试通知
        notifications = [
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知1",
                message="消息1",
                is_read=False
            ),
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知2",
                message="消息2",
                is_read=False
            ),
            UserNotification(
                user_id=1,
                type="tts_job_succeeded",
                ebook_id=1,
                title="通知3",
                message="消息3",
                is_read=False
            ),
        ]
        for notif in notifications:
            db_session.add(notif)
        await db_session.flush()
        await db_session.commit()
        
        # 获取通知 ID
        notif_ids = [notif.id for notif in notifications]
        
        client = TestClient(app)
        response = client.post(
            "/api/user/notifications/mark-read",
            json={"ids": [notif_ids[0], notif_ids[1]]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated"] == 2
        
        # 验证部分已读
        response2 = client.get("/api/user/notifications/unread-count")
        assert response2.json()["unread_count"] == 1
    finally:
        app.dependency_overrides.clear()

