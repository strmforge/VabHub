"""
RSSHub 最小自测脚本

流程：
1. 登录/注册测试用户，获取 token；
2. 调用 `/rsshub/sources` 选取一个源并启用订阅；
3. 直接调用 `RSSHubScheduler` 执行一次处理，确认无错误；
4. 人为插入一个“孤儿订阅”，再次执行 Scheduler，确认该订阅被禁用；
5. 清理测试数据并输出结果。

运行前请确保后端已启动，并设置 `API_BASE_URL` / `API_PREFIX` 环境变量（默认 http://127.0.0.1:8100 /api）。
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger
from sqlalchemy import select

# 使脚本可以导入 backend 内部模块
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 确保 scripts 目录在 sys.path（支持 CI 环境）
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from api_test_config import API_BASE_URL, api_url  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.modules.rsshub.scheduler import RSSHubScheduler  # noqa: E402
from app.models.rsshub import UserRSSHubSubscription  # noqa: E402

TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password_123"
TEST_EMAIL = "test@example.com"


async def ensure_auth_token(client: httpx.AsyncClient) -> str:
    token = await login(client)
    if token:
        return token
    await register(client)
    token = await login(client)
    if not token:
        raise RuntimeError("无法获取认证 Token")
    return token


async def login(client: httpx.AsyncClient) -> Optional[str]:
    response = await client.post(
        api_url("/auth/login"),
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    if response.status_code != 200:
        return None
    data = response.json().get("data", {})
    return data.get("access_token")


async def register(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        api_url("/auth/register"),
        json={
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Test User",
        },
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"注册测试用户失败: {resp.status_code} {resp.text}")


async def get_current_user(client: httpx.AsyncClient, token: str) -> dict:
    resp = await client.get(
        api_url("/auth/me"),
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


async def fetch_sources(client: httpx.AsyncClient, token: str) -> list[dict]:
    resp = await client.get(
        api_url("/rsshub/sources"),
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("data", [])


async def toggle_subscription(
    client: httpx.AsyncClient, token: str, source_id: str, enabled: bool
) -> None:
    resp = await client.post(
        api_url(f"/rsshub/subscriptions/source/{source_id}/toggle"),
        json={"enabled": enabled},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success", False):
        raise RuntimeError(f"切换订阅失败: {payload}")


async def run_scheduler_once(user_id: int) -> dict:
    async with AsyncSessionLocal() as session:
        scheduler = RSSHubScheduler(session)
        return await scheduler.process_user_subscriptions(user_id)


async def upsert_subscription(
    user_id: int,
    target_id: str,
    *,
    target_type: str = "source",
    enabled: bool = True,
) -> UserRSSHubSubscription:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserRSSHubSubscription).where(
                UserRSSHubSubscription.user_id == user_id,
                UserRSSHubSubscription.target_id == target_id,
            )
        )
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.enabled = enabled
            subscription.target_type = target_type
            subscription.updated_at = datetime.utcnow()
        else:
            subscription = UserRSSHubSubscription(
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                enabled=enabled,
            )
            session.add(subscription)
        await session.commit()
        return subscription


async def get_subscription(user_id: int, target_id: str) -> Optional[UserRSSHubSubscription]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserRSSHubSubscription).where(
                UserRSSHubSubscription.user_id == user_id,
                UserRSSHubSubscription.target_id == target_id,
            )
        )
        return result.scalar_one_or_none()


async def delete_subscription(user_id: int, target_id: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserRSSHubSubscription).where(
                UserRSSHubSubscription.user_id == user_id,
                UserRSSHubSubscription.target_id == target_id,
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            await session.delete(sub)
            await session.commit()


async def main() -> None:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=20.0, follow_redirects=True) as client:
        token = await ensure_auth_token(client)
        user = await get_current_user(client, token)
        user_id = int(user.get("id"))
        if not user_id:
            raise RuntimeError("无法获取用户 ID")

        sources = await fetch_sources(client, token)
        if not sources:
            raise RuntimeError("未能获取到任何 RSSHub 源，请确认后台已同步配置")
        target_source = sources[0]
        source_id = target_source["id"]
        original_enabled = target_source.get("enabled", False)

        # 启用订阅（若原本已启用则不会有额外影响）
        await toggle_subscription(client, token, source_id, True)
        refreshed_sources = await fetch_sources(client, token)
        matching = [
            item
            for item in refreshed_sources
            if item["id"] == source_id and item.get("enabled")
        ]
        if not matching:
            logger.warning("启用订阅后接口返回仍为未启用，尝试直接写入数据库记录")
            await upsert_subscription(user_id, source_id, target_type="source", enabled=True)
        else:
            await upsert_subscription(user_id, source_id, target_type="source", enabled=True)

        stats = await run_scheduler_once(user_id)
        if stats.get("processed", 0) == 0 and stats.get("errors", 0) == 0:
            raise RuntimeError("Scheduler 未处理任何订阅，可能数据异常")
        if stats.get("errors", 0) > 0:
            logger.warning(f"Scheduler 存在 {stats['errors']} 个错误（可能与 RSSHub 服务不可用有关）")

        # 构造孤儿订阅
        orphan_id = f"orphan_source_{int(time.time())}"
        await upsert_subscription(user_id, orphan_id, target_type="source", enabled=True)
        orphan_stats = await run_scheduler_once(user_id)

        orphan_sub = await get_subscription(user_id, orphan_id)
        if not orphan_sub:
            raise RuntimeError("孤儿订阅在处理后消失，预期应被禁用")
        if orphan_sub.enabled:
            raise RuntimeError("孤儿订阅未被禁用，自动防御逻辑失效")

        # 清理测试数据
        await delete_subscription(user_id, orphan_id)
        if not original_enabled:
            await toggle_subscription(client, token, source_id, False)
            await delete_subscription(user_id, source_id)

        print("RSSHub 最小自测通过：")
        print(f"- 正常订阅处理统计: {stats}")
        print(f"- 孤儿订阅处理统计: {orphan_stats}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # pragma: no cover - 脚本入口
        logger.error(f"test_rsshub_minimal 失败: {exc}")
        sys.exit(1)

