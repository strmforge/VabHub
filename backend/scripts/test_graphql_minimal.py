"""
GraphQL 最小可用性测试脚本
"""
import asyncio
import os
import sys

import httpx

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


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
        print("GraphQL subscriptions sample:", data.get("subscriptions", {}))
        print("GraphQL dashboard stats:", data.get("dashboardStats", {}))
        print("GraphQL music subscriptions:", data.get("musicSubscriptions", []))
        print("GraphQL music charts:", data.get("musicCharts", []))


if __name__ == "__main__":
    asyncio.run(main())

