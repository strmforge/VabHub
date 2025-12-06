"""
GraphQL 最小可用性测试脚本
"""
import asyncio
import os
import sys
from pathlib import Path

import httpx

# 确保 scripts 目录在 sys.path（支持 CI 环境）
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from api_test_config import API_BASE_URL, api_url


def safe_print(label: str, data) -> None:
    """安全打印，处理 Windows 编码问题"""
    try:
        print(f"{label}: {data}")
    except UnicodeEncodeError:
        # 将非 ASCII 字符替换为 ?
        text = str(data)
        safe_text = text.encode("ascii", errors="replace").decode("ascii")
        print(f"{label}: {safe_text}")


async def main() -> None:
    query = """
    query ($page: Int!, $pageSize: Int!) {
      subscriptions(page: $page, pageSize: $pageSize) {
        total
        page
        items {
          id
          title
          mediaType
          status
        }
      }
      dashboardStats {
        totalSubscriptions
        activeDownloads
        musicSubscriptions
        hnrRisks
      }
      musicSubscriptions(limit: 3) {
        id
        name
        platform
        status
        subscriptionId
      }
      musicCharts(batches: 1) {
        batchId
        capturedAt
        platform
        chartType
        region
        entries {
          rank
          title
          artist
        }
      }
    }
    """
    variables = {"page": 1, "pageSize": 5}

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=20.0) as client:
        await client.get(
            "/api/music/charts",
            params={
                "platform": "qq_music",
                "chart_type": "hot",
                "region": "CN",
                "limit": 10,
            },
        )
        response = await client.post("/graphql", json={"query": query, "variables": variables})
        response.raise_for_status()
        payload = response.json()
        if "errors" in payload:
            print("GraphQL errors:", payload["errors"])
            sys.exit(1)
        data = payload.get("data") or {}
        safe_print("GraphQL subscriptions sample", data.get("subscriptions", {}))
        safe_print("GraphQL dashboard stats", data.get("dashboardStats", {}))
        safe_print("GraphQL music subscriptions", data.get("musicSubscriptions", []))
        safe_print("GraphQL music charts", data.get("musicCharts", []))
        print("[OK] GraphQL 最小可用性测试通过")


if __name__ == "__main__":
    asyncio.run(main())

