"""
音乐闭环最小自测脚本
1. 获取榜单
2. 创建音乐订阅
3. 检查订阅列表是否包含音乐类型
4. 触发自动下载（预览模式）
"""

import argparse
import asyncio
import sys
from pathlib import Path
from pprint import pprint

import httpx

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.api_test_config import API_BASE_URL, api_url


async def run_test(execute_download: bool = False) -> None:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        print("==> 步骤1: 获取音乐榜单")
        charts_resp = await client.get(
            api_url("/music/charts"),
            params={
                "platform": "qq_music",
                "chart_type": "hot",
                "region": "CN",
                "limit": 10,
            },
        )
        charts_resp.raise_for_status()
        charts_data = charts_resp.json()
        charts = charts_data.get("charts") or charts_data.get("data", {}).get("charts") or []
        if not charts:
            raise SystemExit("未获取到榜单数据，无法继续")
        first_entry = charts[0]
        pprint(first_entry)

        print("==> 步骤2: 创建音乐订阅")
        create_resp = await client.post(
            api_url("/music/subscriptions"),
            json={
                "name": f"{first_entry.get('title')} - {first_entry.get('artist')}",
                "type": "track",
                "platform": "qq_music",
                "target_id": first_entry.get("id") or f"qq_music_{first_entry.get('title')}",
                "target_name": first_entry.get("title"),
                "auto_download": True,
                "quality": "flac",
                "search_keywords": [
                    f"{first_entry.get('artist')} - {first_entry.get('title')}"
                ],
                "chart_entry": first_entry,
            },
        )
        create_resp.raise_for_status()
        create_data = create_resp.json()
        subscription_payload = create_data.get("data") if isinstance(create_data.get("success"), bool) else create_data
        if subscription_payload is None:
            subscription_payload = create_data
        subscription_data = subscription_payload
        subscription_id = subscription_data.get("id")
        if not subscription_id:
            raise SystemExit("创建音乐订阅失败：未返回订阅ID")
        print(f"创建音乐订阅成功，ID={subscription_id}")

        print("==> 步骤3: 检查音乐订阅列表")
        list_resp = await client.get(api_url("/music/subscriptions"))
        list_resp.raise_for_status()
        list_data = list_resp.json()
        subscriptions = (
            list_data.get("items")
            or list_data.get("data", {}).get("items")
            or list_data.get("data")
            or list_data
        )
        music_items = [item for item in subscriptions if item.get("id") == subscription_id]
        if not music_items:
            raise SystemExit("音乐订阅未出现在列表中")
        pprint(music_items[0])

        mode_label = "执行下载" if execute_download else "预览模式"
        print(f"==> 步骤4: 触发自动下载（{mode_label}）")
        autodl_resp = await client.post(
            api_url("/music/autodownload"),
            json={
                "subscription_id": subscription_id,
                "preview_only": not execute_download,
                "limit": 3,
            },
        )
        autodl_resp.raise_for_status()
        autodl_data = autodl_resp.json()
        result = autodl_data.get("data") if isinstance(autodl_data.get("success"), bool) else autodl_data
        pprint(result)

        if execute_download:
            downloads_resp = await client.get(api_url("/downloads/"))
            downloads_resp.raise_for_status()
            downloads_payload = downloads_resp.json()
            downloads_data = downloads_payload.get("data") or downloads_payload
            if isinstance(downloads_data, dict):
                downloads = downloads_data.get("items") or downloads_data.get("downloads") or []
            else:
                downloads = downloads_data
            matched = []
            if isinstance(downloads, list):
                for item in downloads:
                    if isinstance(item, dict) and subscription_data.get("name") in (item.get("title") or ""):
                        matched.append(item)
            print(f"下载任务匹配数量: {len(matched)}")

        print("音乐最小闭环自测完成")


def parse_args():
    parser = argparse.ArgumentParser(description="音乐闭环最小自测")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="执行真实下载（默认仅预览）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(run_test(execute_download=args.execute))
    except KeyboardInterrupt:
        sys.exit(1)

