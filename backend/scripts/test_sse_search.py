#!/usr/bin/env python3
"""
测试SSE搜索功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal, init_db
from app.modules.search.service import SearchService
from loguru import logger

async def test_sse_search():
    """测试SSE搜索功能"""
    print("\n" + "="*60)
    print("SSE搜索功能测试")
    print("="*60)
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        service = SearchService(db)
        
        # 1. 测试基础搜索（支持查询扩展、去重、缓存）
        print("\n[1] 测试基础搜索功能...")
        results = await service.search(
            query="钢铁侠",
            media_type="movie",
            enable_query_expansion=True
        )
        if results:
            print(f"[OK] 搜索成功，找到 {len(results)} 条结果")
            print(f"    第一条结果: {results[0].get('title', 'N/A')}")
        else:
            print("[FAIL] 搜索失败或未找到结果")
        
        # 2. 测试索引器管理器
        print("\n[2] 测试索引器管理器...")
        indexer_manager = service.indexer_manager
        all_indexers = indexer_manager.get_all_indexers()
        healthy_indexers = [idx for idx in all_indexers if idx.is_healthy()]
        print(f"[OK] 索引器总数: {len(all_indexers)}, 健康索引器: {len(healthy_indexers)}")
        
        # 3. 测试多源索引器搜索（如果指定了sites）
        print("\n[3] 测试多源索引器搜索...")
        if healthy_indexers:
            indexer_names = [idx.name for idx in healthy_indexers[:3]]  # 取前3个
            indexer_results = await indexer_manager.search_all(
                query="钢铁侠",
                media_type="movie",
                indexer_names=indexer_names
            )
            print(f"[OK] 多源索引器搜索完成，找到 {len(indexer_results)} 条结果")
        else:
            print("[SKIP] 没有健康的索引器，跳过多源搜索测试")
        
        # 4. 测试去重功能
        print("\n[4] 测试去重功能...")
        test_results = [
            {"title": "钢铁侠", "site": "站点A", "seeders": 100},
            {"title": "钢铁侠", "site": "站点B", "seeders": 100},  # 重复
            {"title": "钢铁侠2", "site": "站点A", "seeders": 50},
        ]
        deduplicated = service.deduplicator.deduplicate(test_results)
        print(f"[OK] 去重测试: 原始 {len(test_results)} 条，去重后 {len(deduplicated)} 条")
        
        # 5. 测试查询扩展
        print("\n[5] 测试查询扩展...")
        expanded = await service.query_expander.expand("三体", "tv", 2023)
        print(f"[OK] 查询扩展: 原始查询 '三体'，扩展为 {len(expanded)} 个查询")
        print(f"    扩展查询: {expanded}")
    
    print("\n" + "="*60)
    print("SSE搜索功能测试完成")
    print("="*60)
    print("\n注意: SSE流式推送需要在HTTP请求中测试")
    print("可以使用浏览器或Postman测试 /api/search/stream 端点")

if __name__ == "__main__":
    try:
        asyncio.run(test_sse_search())
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

