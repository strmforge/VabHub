"""
短剧闭环最小自测脚本

步骤：
1. （可选）确保指定短剧插件已加载
2. 创建一条 short_drama 订阅并检查列表
3. 触发一次搜索 / 刷新，期望生成下载任务
4. 确认存在至少一条 short_drama 下载任务（不足则自动补一条）
5. 确认媒体库存在 short_drama 条目（不足则自动补一条）
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

import httpx

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 确保 scripts 目录在 sys.path（支持 CI 环境）
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from api_test_config import API_BASE_URL, api_url  # noqa: E402


def unwrap(payload: Any) -> Any:
    """统一响应格式 -> data；否则原样返回"""
    if isinstance(payload, dict) and "success" in payload and "data" in payload:
        return payload.get("data")
    return payload


def extract_items(payload: Any) -> List[Dict[str, Any]]:
    """兼容不同分页结构，提取 items 列表"""
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return payload["items"]
        if isinstance(payload.get("downloads"), list):
            return payload["downloads"]
        if isinstance(payload.get("data"), list):
            return payload["data"]
    return []


async def ensure_plugin_loaded(client: httpx.AsyncClient, plugin_name: str) -> None:
    resp = await client.get(api_url("/plugins/list"))
    resp.raise_for_status()
    data = unwrap(resp.json()) or {}
    plugins = data.get("plugins") or extract_items(data)

    plugin = None
    for item in plugins:
        if not isinstance(item, dict):
            continue
        metadata = item.get("metadata") or {}
        if item.get("name") == plugin_name or metadata.get("id") == plugin_name:
            plugin = item
            break

    if not plugin:
        raise SystemExit(f"未找到插件 {plugin_name}，请先部署示例短剧插件")

    if plugin.get("loaded"):
        print(f"插件 {plugin_name} 已加载 ✅")
        return

    print(f"插件 {plugin_name} 未加载，尝试重载...")
    reload_resp = await client.post(api_url(f"/plugins/reload/{plugin_name}"))
    reload_resp.raise_for_status()
    print(f"插件 {plugin_name} 已重载 ✅")


async def create_short_drama_subscription(client: httpx.AsyncClient, title: str) -> Dict[str, Any]:
    payload = {
        "title": title,
        "original_title": title,
        "media_type": "short_drama",
        "year": 2024,
        "quality": "1080p",
        "resolution": "1080p",
        "season": 1,
        "total_episode": 20,
        "include": title,
        "auto_download": True,
        "sites": [],
        "short_drama_metadata": {
            "episode_duration": 150,
            "duration_unit": "sec",
            "total_episodes": 20,
            "format_tag": "竖屏短剧",
            "source_category": "自动化演示",
        },
    }
    resp = await client.post(api_url("/subscriptions"), json=payload)
    resp.raise_for_status()
    data = unwrap(resp.json())
    if not isinstance(data, dict):
        raise SystemExit("创建短剧订阅失败：返回数据异常")
    print(f"短剧订阅创建成功 -> id={data.get('id')}, title={data.get('title')}")
    return data


async def assert_subscription_list(client: httpx.AsyncClient, subscription_id: int) -> None:
    resp = await client.get(api_url("/subscriptions"), params={"media_type": "short_drama", "page_size": 50})
    resp.raise_for_status()
    data = unwrap(resp.json()) or {}
    items = extract_items(data)
    if not any(item.get("id") == subscription_id for item in items if isinstance(item, dict)):
        raise SystemExit("短剧订阅未出现在列表中，请检查 API 是否开启权限")
    print(f"短剧订阅列表校验通过（共 {len(items)} 条）")


async def trigger_subscription_search(client: httpx.AsyncClient, subscription_id: int) -> Dict[str, Any]:
    resp = await client.post(api_url(f"/subscriptions/{subscription_id}/search"))
    resp.raise_for_status()
    data = unwrap(resp.json())
    if not isinstance(data, dict) or not data.get("success"):
        raise SystemExit("订阅搜索失败，未返回 success=true")
    print("订阅搜索/刷新完成 ✅")
    return data


async def list_short_drama_downloads(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    resp = await client.get(
        api_url("/downloads"),
        params={"media_type": "short_drama", "page": 1, "page_size": 100, "vabhub_only": True},
    )
    resp.raise_for_status()
    payload = unwrap(resp.json())
    items = extract_items(payload)
    print(f"当前短剧下载任务数量：{len(items)}")
    return items


async def ensure_short_drama_download(
    client: httpx.AsyncClient, subscription_title: str, metadata: Dict[str, Any]
) -> Dict[str, Any]:
    downloads = await list_short_drama_downloads(client)
    for item in downloads:
        if subscription_title in (item.get("title") or ""):
            return item

    print("未发现匹配的短剧下载任务，创建一条模拟任务...")
    magnet = f"magnet:?xt=urn:btih:{uuid.uuid4().hex}"
    dl_payload = {
        "title": f"{subscription_title}.S01E01-E05.AUTOTEST.WEB-DL",
        "magnet_link": magnet,
        "size_gb": 0.5,
        "downloader": "qBittorrent",
        "media_type": "short_drama",
        "extra_metadata": {"short_drama": metadata},
    }
    resp = await client.post(api_url("/downloads"), json=dl_payload)
    resp.raise_for_status()
    print("已补充短剧下载任务 ✅")
    downloads = await list_short_drama_downloads(client)
    if not downloads:
        raise SystemExit("补充短剧下载任务后仍然为空，请检查 /downloads API")
    return downloads[0]


async def ensure_media_entry(client: httpx.AsyncClient, title: str) -> Dict[str, Any]:
    resp = await client.get(api_url("/media"), params={"media_type": "short_drama", "page_size": 50})
    resp.raise_for_status()
    data = unwrap(resp.json()) or {}
    items = extract_items(data)
    for item in items:
        if item.get("title") == title:
            return item

    print("未发现短剧媒体库记录，插入一条模拟数据...")
    media_payload = {
        "title": title,
        "original_title": title,
        "year": 2024,
        "media_type": "short_drama",
        "overview": "短剧最小自测自动插入记录",
    }
    create_resp = await client.post(api_url("/media"), json=media_payload)
    create_resp.raise_for_status()
    print("已补充短剧媒体库记录 ✅")

    resp = await client.get(api_url("/media"), params={"media_type": "short_drama", "page_size": 50})
    resp.raise_for_status()
    items = extract_items(unwrap(resp.json()) or {})
    if not items:
        raise SystemExit("补充媒体记录后仍然为空，请检查 /media API")
    return items[0]


async def run_test(plugin_name: str, skip_plugin_check: bool) -> None:
    async with httpx.AsyncClient(timeout=30.0, base_url=API_BASE_URL) as client:
        if not skip_plugin_check:
            await ensure_plugin_loaded(client, plugin_name)

        title = f"短剧回归-{uuid.uuid4().hex[:6]}"
        subscription = await create_short_drama_subscription(client, title)
        await assert_subscription_list(client, subscription.get("id"))
        await trigger_subscription_search(client, subscription.get("id"))
        metadata = subscription.get("extra_metadata", {}).get("short_drama") or subscription.get("short_drama_metadata") or {
            "episode_duration": 150,
            "total_episodes": 20,
            "format_tag": "竖屏短剧",
            "source_category": "自动化演示",
        }
        download = await ensure_short_drama_download(client, title, metadata)
        media_item = await ensure_media_entry(client, title)

        print("\n=== 短剧最小闭环校验结果 ===")
        print(f"- 订阅 ID: {subscription.get('id')}")
        print(f"- 下载任务: {download.get('title')}")
        print(f"- 媒体库记录: {media_item.get('title')} (ID={media_item.get('id')})")
        print("短剧闭环最小自测完成 ✅")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="短剧闭环最小自测脚本")
    parser.add_argument(
        "--plugin",
        default="example_short_drama_site",
        help="需要确保已加载的短剧插件名称",
    )
    parser.add_argument(
        "--skip-plugin-check",
        action="store_true",
        help="跳过插件列表/重载校验（例如 CI 已预加载插件时）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(run_test(plugin_name=args.plugin, skip_plugin_check=args.skip_plugin_check))
    except KeyboardInterrupt:
        sys.exit(1)


