#!/usr/bin/env python3
"""
测试推荐系统API
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import init_db, close_db
from app.modules.recommendation.service import RecommendationService


async def test_recommendation_service():
    """测试推荐服务"""
    print("=" * 60)
    print("测试推荐服务")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    try:
        # 获取数据库会话
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            service = RecommendationService(db)
            
            # 测试1: 获取用户推荐
            print("\n1. 测试获取用户推荐...")
            try:
                recommendations = await service.get_recommendations(
                    user_id=1,
                    limit=10,
                    algorithm="hybrid"
                )
                print(f"[OK] 获取推荐成功: {len(recommendations)} 条推荐")
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"   {i}. {rec.get('media_id')} - 分数: {rec.get('score'):.2f} - 理由: {rec.get('reason')}")
            except Exception as e:
                print(f"[FAIL] 获取推荐失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 测试2: 获取热门推荐
            print("\n2. 测试获取热门推荐...")
            try:
                popular = await service.get_popular_recommendations(limit=10)
                print(f"[OK] 获取热门推荐成功: {len(popular)} 条推荐")
                for i, rec in enumerate(popular[:5], 1):
                    print(f"   {i}. {rec.get('media_id')} - 分数: {rec.get('score'):.2f}")
            except Exception as e:
                print(f"[FAIL] 获取热门推荐失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 测试3: 获取相似内容
            print("\n3. 测试获取相似内容...")
            try:
                similar = await service.get_similar_content(
                    media_id="test_media_1",
                    limit=5
                )
                print(f"[OK] 获取相似内容成功: {len(similar)} 条")
                for i, item in enumerate(similar[:5], 1):
                    print(f"   {i}. {item.get('media_id')} - 相似度: {item.get('similarity', 0):.2f}")
            except Exception as e:
                print(f"[FAIL] 获取相似内容失败: {e}")
                import traceback
                traceback.print_exc()
    
    finally:
        await close_db()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_recommendation_service())

