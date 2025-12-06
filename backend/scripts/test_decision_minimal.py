"""
下载决策层最小自测脚本（BACKEND-REGRESSION-DECISION-2 修复版）

覆盖场景：
1. 规则命中 + 质量满足 -> should_download = True
2. 规则命中但质量降级 -> should_download = False
3. 规则未命中 -> should_download = False
4. HNR 风险 -> should_download = False

注意：API 前缀已从 /api/v1 改为 /api（见 api_test_config.py）
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from httpx import HTTPStatusError

# 确保 scripts 目录在 sys.path（支持 CI 环境）
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from api_test_config import API_BASE_URL, api_url

# CI 环境标识
IS_CI = os.getenv("VABHUB_CI") == "1"


def unwrap_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "data" in payload and payload["data"] is not None:
        return payload["data"]
    return payload


def print_http_error(context: str, exc: HTTPStatusError) -> None:
    """输出 HTTP 错误详情"""
    print(f"[ERROR] {context}:")
    print(f"  URL    : {exc.request.url}")
    print(f"  Method : {exc.request.method}")
    print(f"  Status : {exc.response.status_code}")
    try:
        body = exc.response.json()
        print(f"  Body   : {body}")
    except Exception:
        print(f"  Body   : {exc.response.text[:500]}")


async def create_subscription(client: httpx.AsyncClient) -> int:
    """创建测试订阅（用于决策测试）"""
    payload = {
        "title": "决策层测试订阅",
        "media_type": "movie",
        "quality": "2160p",
        "resolution": "2160p",
        "effect": "HDR",
        "include": "HDR",
        "exclude": "CAM",
        "auto_download": False,
        "min_seeders": 5,
        # sites 字段期望 List[int]，CI 环境下不传（可选字段）
    }
    
    try:
        resp = await client.post(api_url("/subscriptions"), json=payload)
        resp.raise_for_status()
    except HTTPStatusError as exc:
        print_http_error("创建订阅失败", exc)
        raise SystemExit(1)
    
    data = unwrap_response(resp.json())
    subscription_id = data.get("id")
    if not subscription_id:
        print(f"[ERROR] 创建订阅响应缺少 ID: {data}")
        raise SystemExit("创建订阅失败：未返回订阅ID")
    print(f"[setup] 订阅创建成功 id={subscription_id}")
    return subscription_id


async def delete_subscription(client: httpx.AsyncClient, subscription_id: int) -> None:
    """删除测试订阅"""
    try:
        resp = await client.delete(api_url(f"/subscriptions/{subscription_id}"))
        if resp.status_code in (404, 410):
            print(f"[cleanup] 订阅 {subscription_id} 已不存在")
            return
        resp.raise_for_status()
        print(f"[cleanup] 订阅 {subscription_id} 已删除")
    except HTTPStatusError as exc:
        print_http_error(f"删除订阅 {subscription_id} 失败", exc)
        # 删除失败不阻塞测试


async def dry_run(
    client: httpx.AsyncClient,
    subscription_id: int,
    candidate: Dict[str, Any],
    *,
    debug: bool = True,
) -> Dict[str, Any]:
    """执行决策 Dry-Run"""
    payload = {
        "subscription_id": subscription_id,
        "candidate": candidate,
        "debug": debug,
    }
    
    try:
        resp = await client.post(api_url("/decision/dry-run"), json=payload)
        resp.raise_for_status()
    except HTTPStatusError as exc:
        print_http_error("决策 Dry-Run 失败", exc)
        raise SystemExit(1)
    
    data = unwrap_response(resp.json()) or {}
    if not data.get("result"):
        print(f"[ERROR] 决策层未返回结果: {data}")
        raise SystemExit("决策层未返回结果")
    return data["result"]


def assert_decision(
    name: str,
    result: Dict[str, Any],
    *,
    expected_should_download: bool,
    expected_reason: Optional[str] = None,
    allowed_reasons: Optional[List[str]] = None,
) -> None:
    should_download = result.get("should_download")
    reason = result.get("reason")
    if should_download is None:
        raise SystemExit(f"[{name}] 决策结果缺少 should_download: {result}")
    if should_download != expected_should_download:
        raise SystemExit(
            f"[{name}] should_download={should_download}, 期望 {expected_should_download}. 全量: {result}"
        )
    if expected_reason and reason != expected_reason:
        raise SystemExit(f"[{name}] reason={reason}, 期望 {expected_reason}")
    if allowed_reasons and reason not in allowed_reasons:
        raise SystemExit(f"[{name}] reason={reason} 不在允许集合 {allowed_reasons}")
    print(f"[{name}] ✅ should_download={should_download} reason={reason}")


def build_candidates() -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    base = {
        "media_type": "movie",
        "site": "test_site",
    }
    return [
        (
            "quality_upgrade",
            {
                **base,
                "title": "Decision.Test.Movie.2025.2160p.HDR.TrueHD",
                "quality": "2160p",
                "resolution": "2160p",
                "effect": "HDR",
                "seeders": 60,
                "size_gb": 18.5,
            },
            {
                "expected_should": True,
                "allowed_reasons": ["ok_new", "ok_upgrade"],
            },
        ),
        (
            "quality_inferior",
            {
                **base,
                "title": "Decision.Test.Movie.2025.720p.HDR",
                "quality": "720p",
                "resolution": "720p",
                "effect": "HDR",
                "seeders": 30,
                "size_gb": 4.0,
            },
            {
                "expected_should": False,
                "expected_reason": "quality_inferior",
            },
        ),
        (
            "rule_mismatch",
            {
                **base,
                "title": "Decision.Test.Movie.2025.2160p.BLURAY",
                "quality": "2160p",
                "resolution": "2160p",
                "seeders": 40,
                "size_gb": 15.0,
            },
            {
                "expected_should": False,
                "expected_reason": "rule_mismatch",
            },
        ),
        (
            "hnr_blocked",
            {
                **base,
                "title": "Decision.Test.Movie.HNR.Hit.and.Run.2160p.HDR",
                "quality": "2160p",
                "resolution": "2160p",
                "effect": "HDR",
                "seeders": 80,
                "size_gb": 16.0,
            },
            {
                "expected_should": False,
                "allowed_reasons": ["hnr_blocked", "hnr_suspected"],
            },
        ),
    ]


async def run_tests() -> None:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=20.0) as client:
        subscription_id = await create_subscription(client)
        try:
            for name, candidate, expectations in build_candidates():
                result = await dry_run(client, subscription_id, candidate, debug=True)
                assert_decision(
                    name,
                    result,
                    expected_should_download=expectations["expected_should"],
                    expected_reason=expectations.get("expected_reason"),
                    allowed_reasons=expectations.get("allowed_reasons"),
                )
        finally:
            await delete_subscription(client, subscription_id)

    print("下载决策层最小自测通过 ✅")


if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        sys.exit(1)


