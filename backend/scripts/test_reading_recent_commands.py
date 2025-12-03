#!/usr/bin/env python3
"""
TG-BOT-BOOK-2 阅读最近活动命令测试脚本
测试 /reading_recent 和 /reading_recent_open 命令的核心功能
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.modules.bots.telegram_bot_state import reading_activity_cache, UserReadingActivityState
from app.schemas.reading_hub import ReadingActivityItem
from app.models.enums.reading_media_type import ReadingMediaType
from app.modules.bots.commands.reading import _format_activity_item_line, _format_relative_time, _build_web_url_unified
from app.core.config import settings


def test_relative_time_formatting():
    """测试相对时间格式化功能"""
    print("=== 测试相对时间格式化 ===")
    
    now = datetime.utcnow()
    
    # 测试各种时间差
    test_cases = [
        (now - timedelta(seconds=30), "刚刚"),
        (now - timedelta(minutes=1), "1分钟前"),
        (now - timedelta(minutes=5), "5分钟前"),
        (now - timedelta(hours=1), "1小时前"),
        (now - timedelta(hours=3), "3小时前"),
        (now - timedelta(days=1), f"昨天 {now.strftime('%H:%M')}"),
        (now - timedelta(days=3), "3天前"),
        (now - timedelta(days=10), now.strftime('%m-%d')),
        (None, "未知时间"),
    ]
    
    for occurred_at, expected_pattern in test_cases:
        result = _format_relative_time(occurred_at)
        print(f"  {occurred_at} -> {result}")
        
        # 简单验证
        if occurred_at is None:
            assert result == "未知时间", f"Expected '未知时间', got '{result}'"
        else:
            assert result != "未知时间", f"Expected not '未知时间', got '{result}'"
            assert len(result) > 0, f"Expected non-empty result"
    
    print("✅ 相对时间格式化测试通过\n")


def test_activity_item_formatting():
    """测试活动条目格式化功能"""
    print("=== 测试活动条目格式化 ===")
    
    # 创建测试活动项
    test_items = [
        ReadingActivityItem(
            media_type=ReadingMediaType.NOVEL,
            item_id=1,
            title="三体",
            sub_title="刘慈欣",
            activity_type="read",
            activity_label="阅读了第 12 章",
            occurred_at=datetime.utcnow() - timedelta(minutes=5),
            route_name="NovelReader",
            route_params={"ebookId": 1},
            status="in_progress"
        ),
        ReadingActivityItem(
            media_type=ReadingMediaType.AUDIOBOOK,
            item_id=2,
            title="明朝那些事儿",
            sub_title="当年明月",
            activity_type="listen",
            activity_label="收听了 22 分钟",
            occurred_at=datetime.utcnow() - timedelta(hours=2),
            route_name="WorkDetail",
            route_params={"ebookId": 2},
            status="in_progress"
        ),
        ReadingActivityItem(
            media_type=ReadingMediaType.MANGA,
            item_id=3,
            title="进击的巨人",
            sub_title=None,
            activity_type="read",
            activity_label="阅读了第 28 话",
            occurred_at=datetime.utcnow() - timedelta(days=1),
            route_name="MangaReaderPage",
            route_params={"series_id": 3, "chapter_id": 28},
            status="finished"
        ),
    ]
    
    for idx, item in enumerate(test_items, start=1):
        formatted = _format_activity_item_line(idx, item)
        print(f"  {formatted}")
        
        # 验证格式
        assert formatted.startswith(f"[{idx}]"), f"Expected to start with '[{idx}]'"
        assert "《" in formatted and "》" in formatted, f"Expected title brackets"
        assert "·" in formatted, f"Expected separator"
        assert len(formatted) > 20, f"Expected reasonable length"
    
    print("✅ 活动条目格式化测试通过\n")


def test_unified_url_building():
    """测试统一URL构建功能"""
    print("=== 测试统一URL构建 ===")
    
    base_url = settings.WEB_BASE_URL.rstrip('/')
    
    test_cases = [
        ("NovelReader", {"ebookId": 123}, f"{base_url}/novel-center/ebook/123"),
        ("WorkDetail", {"ebookId": 456}, f"{base_url}/audiobook/456"),
        ("MangaReaderPage", {"series_id": 789}, f"{base_url}/manga/789"),
        ("MangaReaderPage", {"series_id": 789, "chapter_id": 12}, f"{base_url}/manga/789/chapter/12"),
        ("UnknownRoute", {"test": "value"}, f"{base_url}/"),
    ]
    
    for route_name, route_params, expected in test_cases:
        result = _build_web_url_unified(settings, route_name, route_params)
        print(f"  {route_name} + {route_params} -> {result}")
        
        if route_name != "UnknownRoute":
            assert result == expected, f"Expected '{expected}', got '{result}'"
        else:
            assert result == f"{settings.WEB_BASE_URL.rstrip('/')}/", f"Expected fallback URL, got '{result}'"
    
    print("✅ 统一URL构建测试通过\n")


def test_reading_activity_cache():
    """测试阅读活动缓存功能"""
    print("=== 测试阅读活动缓存 ===")
    
    # 创建测试数据
    test_items = [
        ReadingActivityItem(
            media_type=ReadingMediaType.NOVEL,
            item_id=1,
            title="测试小说",
            activity_type="read",
            activity_label="测试活动",
            occurred_at=datetime.utcnow(),
            route_name="NovelReader",
            route_params={"ebookId": 1},
            status="in_progress"
        )
    ]
    
    # 测试缓存设置
    tg_user_id = 12345
    user_id = 1
    
    reading_activity_cache.set_results(tg_user_id, user_id, test_items)
    
    # 测试缓存获取
    cached_state = reading_activity_cache.get_results(tg_user_id)
    assert cached_state is not None, "Expected cached state"
    assert len(cached_state.items) == 1, "Expected 1 cached item"
    assert cached_state.items[0].title == "测试小说", "Expected correct title"
    
    # 测试索引获取
    item = reading_activity_cache.get_item(tg_user_id, 1)
    assert item is not None, "Expected item by index"
    assert item.title == "测试小说", "Expected correct item"
    
    # 测试无效索引
    item = reading_activity_cache.get_item(tg_user_id, 999)
    assert item is None, "Expected None for invalid index"
    
    print("✅ 阅读活动缓存测试通过\n")


def test_cache_stats():
    """测试缓存统计功能"""
    print("=== 测试缓存统计 ===")
    
    stats = reading_activity_cache.get_cache_stats()
    print(f"  缓存统计: {stats}")
    
    assert "total_cached_users" in stats, "Expected total_cached_users"
    assert "cached_items_total" in stats, "Expected cached_items_total"
    assert isinstance(stats["total_cached_users"], int), "Expected integer"
    assert isinstance(stats["cached_items_total"], int), "Expected integer"
    
    print("✅ 缓存统计测试通过\n")


async def main():
    """主测试函数"""
    print("TG-BOT-BOOK-2 阅读最近活动命令功能测试")
    print("=" * 50)
    
    try:
        test_relative_time_formatting()
        test_activity_item_formatting()
        test_unified_url_building()
        test_reading_activity_cache()
        test_cache_stats()
        
        print("🎉 所有测试通过！TG-BOT-BOOK-2 功能正常")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
