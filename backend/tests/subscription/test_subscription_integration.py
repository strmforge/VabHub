"""
订阅服务集成测试 - 规则组与订阅过滤的完整流程测试
验证FilterRuleGroupService与SubscriptionService._filter_search_results的集成
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.subscription.service import SubscriptionService
from app.modules.filter_rule_group.service import FilterRuleGroupService
from app.models.subscription import Subscription
from app.models.filter_rule_group import FilterRuleGroup
from app.models.user import User


@pytest.mark.asyncio
async def test_subscription_filter_no_rule_groups(db_session: AsyncSession, test_user: User):
    """测试没有规则组的订阅过滤 - 应该使用原有的include/exclude规则"""
    # 创建订阅（使用Subscription模型）
    subscription = Subscription(
        title="测试电影",
        media_type="movie",
        user_id=test_user.id,
        include="1080p,4K",
        exclude="CAM,TS",
        filter_group_ids=None  # 没有规则组
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # 模拟搜索结果
    search_results = [
        {"title": "Movie.2023.1080p.BluRay.x264", "link": "http://example.com/1", "seeders": 10},
        {"title": "Movie.2023.4K.UHD.BluRay.x265", "link": "http://example.com/2", "seeders": 10},
        {"title": "Movie.2023.CAM.HDCAM", "link": "http://example.com/3", "seeders": 10},
        {"title": "Movie.2023.TELESYNC.TS", "link": "http://example.com/4", "seeders": 10},
    ]
    
    # 测试订阅服务过滤
    subscription_service = SubscriptionService(db_session)
    filtered_results = await subscription_service._filter_search_results(search_results, subscription)
    
    # 验证过滤结果（应该包含1080p和4K，排除CAM和TS）
    assert len(filtered_results) == 2
    titles = [result["title"] for result in filtered_results]
    assert "Movie.2023.1080p.BluRay.x264" in titles
    assert "Movie.2023.4K.UHD.BluRay.x265" in titles
    assert "Movie.2023.CAM.HDCAM" not in titles
    assert "Movie.2023.TELESYNC.TS" not in titles


@pytest.mark.asyncio
async def test_subscription_filter_single_rule_group(db_session: AsyncSession, test_user: User):
    """测试单个规则组的订阅过滤 - 验证规则正确合并并应用"""
    # 创建规则组
    rule_group = FilterRuleGroup(
        name="质量规则组",
        description="视频质量偏好",
        user_id=test_user.id,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={
            "include": ["BluRay", "WEB-DL"],
            "exclude": ["HDTV", "DVD"]
        }
    )
    db_session.add(rule_group)
    await db_session.commit()
    
    # 创建订阅
    subscription = Subscription(
        title="测试电影",
        media_type="movie",
        user_id=test_user.id,
        include="1080p",  # 原有规则
        exclude="CAM",    # 原有规则
        filter_group_ids=[rule_group.id]
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # 模拟搜索结果
    search_results = [
        {"title": "Movie.2023.1080p.BluRay.x264", "link": "http://example.com/1", "seeders": 10},      # 应该通过（1080p + BluRay）
        {"title": "Movie.2023.4K.WEB-DL.x265", "link": "http://example.com/2", "seeders": 10},        # 应该通过（WEB-DL）
        {"title": "Movie.2023.1080p.HDTV.x264", "link": "http://example.com/3", "seeders": 10},        # 应该被排除（HDTV）
        {"title": "Movie.2023.720p.DVD.x264", "link": "http://example.com/4", "seeders": 10},          # 应该被排除（DVD）
        {"title": "Movie.2023.1080p.CAM.HDCAM", "link": "http://example.com/5", "seeders": 10},        # 应该被排除（CAM）
        {"title": "Movie.2023.720p.TELESYNC.TS", "link": "http://example.com/6", "seeders": 10},       # 应该被排除（TS，不在任何规则中但通常被排除）
    ]
    
    # 测试订阅服务过滤
    subscription_service = SubscriptionService(db_session)
    filtered_results = await subscription_service._filter_search_results(search_results, subscription)
    
    # 验证过滤结果
    assert len(filtered_results) == 2
    titles = [result["title"] for result in filtered_results]
    assert "Movie.2023.1080p.BluRay.x264" in titles
    assert "Movie.2023.4K.WEB-DL.x265" in titles
    assert "Movie.2023.1080p.HDTV.x264" not in titles
    assert "Movie.2023.720p.DVD.x264" not in titles
    assert "Movie.2023.1080p.CAM.HDCAM" not in titles


@pytest.mark.asyncio
async def test_subscription_filter_multiple_rule_groups_priority_order(db_session: AsyncSession, test_user: User):
    """测试多个规则组的订阅过滤 - 验证优先级排序和规则合并"""
    # 创建多个规则组
    quality_group = FilterRuleGroup(
        name="质量规则组",
        description="视频质量偏好",
        user_id=test_user.id,
        media_types=["movie"],
        priority=2,  # 中等优先级
        enabled=True,
        rules={
            "include": ["1080p", "4K"],
            "exclude": ["720p", "480p"]
        }
    )
    
    source_group = FilterRuleGroup(
        name="片源规则组",
        description="片源偏好",
        user_id=test_user.id,
        media_types=["movie"],
        priority=1,  # 高优先级
        enabled=True,
        rules={
            "include": ["BluRay", "WEB-DL"],
            "exclude": ["CAM", "TS"]
        }
    )
    
    codec_group = FilterRuleGroup(
        name="编码规则组",
        description="编码偏好",
        user_id=test_user.id,
        media_types=["movie"],
        priority=3,  # 低优先级
        enabled=True,
        rules={
            "include": ["x264", "x265"],
            "exclude": ["XVID", "DIVX"]
        }
    )
    
    db_session.add_all([quality_group, source_group, codec_group])
    await db_session.commit()
    
    # 创建订阅
    subscription = Subscription(
        title="测试电影",
        media_type="movie",
        user_id=test_user.id,
        include="HDTV",  # 原有规则
        exclude="TC",    # 原有规则
        filter_group_ids=[quality_group.id, source_group.id, codec_group.id]
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # 模拟搜索结果
    search_results = [
        {"title": "Movie.2023.1080p.BluRay.x264", "link": "http://example.com/1", "seeders": 10},      # 应该通过（所有include条件满足）
        {"title": "Movie.2023.4K.WEB-DL.x265", "link": "http://example.com/2", "seeders": 10},        # 应该通过（所有include条件满足）
        {"title": "Movie.2023.1080p.CAM.x264", "link": "http://example.com/3", "seeders": 10},        # 应该被排除（CAM）
        {"title": "Movie.2023.720p.BluRay.x265", "link": "http://example.com/4", "seeders": 10},      # 应该被排除（720p）
        {"title": "Movie.2023.1080p.BluRay.XVID", "link": "http://example.com/5", "seeders": 10},      # 应该被排除（XVID）
        {"title": "Movie.2023.HDTV.BluRay.x264", "link": "http://example.com/6", "seeders": 10},      # 应该通过（HDTV在include中）
    ]
    
    # 测试订阅服务过滤
    subscription_service = SubscriptionService(db_session)
    filtered_results = await subscription_service._filter_search_results(search_results, subscription)
    
    # 验证过滤结果
    assert len(filtered_results) == 3
    titles = [result["title"] for result in filtered_results]
    assert "Movie.2023.1080p.BluRay.x264" in titles
    assert "Movie.2023.4K.WEB-DL.x265" in titles
    assert "Movie.2023.HDTV.BluRay.x264" in titles
    assert "Movie.2023.1080p.CAM.x264" not in titles
    assert "Movie.2023.720p.BluRay.x265" not in titles


@pytest.mark.asyncio
async def test_subscription_filter_media_type_filtering(db_session: AsyncSession, test_user: User):
    """测试媒体类型过滤 - 只有匹配的规则组会被应用"""
    # 创建不同媒体类型的规则组
    movie_group = FilterRuleGroup(
        name="电影规则组",
        description="电影专用规则",
        user_id=test_user.id,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={
            "include": ["1080p", "4K"],
            "exclude": ["CAM"]
        }
    )
    
    tv_group = FilterRuleGroup(
        name="电视剧规则组",
        description="电视剧专用规则",
        user_id=test_user.id,
        media_types=["tv"],
        priority=1,
        enabled=True,
        rules={
            "include": ["HDTV", "720p"],
            "exclude": ["TS"]
        }
    )
    
    universal_group = FilterRuleGroup(
        name="通用规则组",
        description="所有媒体类型",
        user_id=test_user.id,
        media_types=["movie", "tv", "anime"],
        priority=2,
        enabled=True,
        rules={
            "include": ["x264", "x265"],
            "exclude": ["XVID"]
        }
    )
    
    db_session.add_all([movie_group, tv_group, universal_group])
    await db_session.commit()
    
    # 创建电影订阅
    subscription = Subscription(
        title="测试电影",
        media_type="movie",
        user_id=test_user.id,
        include="",
        exclude="",
        filter_group_ids=[movie_group.id, tv_group.id, universal_group.id]
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # 模拟搜索结果
    search_results = [
        {"title": "Movie.2023.1080p.BluRay.x264", "link": "http://example.com/1", "seeders": 10},
        {"title": "Movie.2023.4K.UHD.BluRay.x265", "link": "http://example.com/2", "seeders": 10},
        {"title": "Movie.2023.CAM.HDCAM", "link": "http://example.com/3", "seeders": 10},
    ]
    
    # 测试订阅服务过滤
    subscription_service = SubscriptionService(db_session)
    filtered_results = await subscription_service._filter_search_results(search_results, subscription)
    
    # 验证只应用电影规则组和通用组
    assert len(filtered_results) == 2
    titles = [result["title"] for result in filtered_results]
    assert "Movie.2023.1080p.BluRay.x264" in titles
    assert "Movie.2023.4K.UHD.BluRay.x265" in titles
    assert "Movie.2023.CAM.HDCAM" not in titles


@pytest.mark.asyncio
async def test_subscription_filter_system_rule_groups(db_session: AsyncSession, test_user: User):
    """测试系统级规则组（user_id为null）可以被所有用户访问"""
    # 创建系统级规则组
    system_group = FilterRuleGroup(
        name="系统级规则组",
        description="所有用户可用的系统规则",
        user_id=None,  # 系统级规则组
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={
            "include": ["1080p", "4K"],
            "exclude": ["CAM", "TS"]
        }
    )
    
    # 创建用户级规则组
    user_group = FilterRuleGroup(
        name="用户级规则组",
        description="用户专用规则",
        user_id=test_user.id,
        media_types=["movie"],
        priority=2,
        enabled=True,
        rules={
            "include": ["BluRay"],
            "exclude": ["HDTV"]
        }
    )
    
    db_session.add_all([system_group, user_group])
    await db_session.commit()
    
    # 创建订阅
    subscription = Subscription(
        title="测试电影",
        media_type="movie",
        user_id=test_user.id,
        include="WEB-DL",  # 原有规则
        exclude="TC",
        filter_group_ids=[system_group.id, user_group.id]
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # 模拟搜索结果
    search_results = [
        {"title": "Movie.2023.1080p.BluRay.x264", "link": "http://example.com/1", "seeders": 10},      # 应该通过（1080p + BluRay + WEB-DL）
        {"title": "Movie.2023.4K.WEB-DL.x265", "link": "http://example.com/2", "seeders": 10},        # 应该通过（4K + WEB-DL）
        {"title": "Movie.2023.CAM.HDCAM", "link": "http://example.com/3", "seeders": 10},              # 应该被排除（CAM）
        {"title": "Movie.2023.HDTV.BluRay.x264", "link": "http://example.com/4", "seeders": 10},      # 应该被排除（HDTV）
        {"title": "Movie.2023.TELESYNC.TS", "link": "http://example.com/5", "seeders": 10},            # 应该被排除（TS）
    ]
    
    # 测试订阅服务过滤
    subscription_service = SubscriptionService(db_session)
    filtered_results = await subscription_service._filter_search_results(search_results, subscription)
    
    # 验证系统级和用户级规则组都被应用
    assert len(filtered_results) == 2
    titles = [result["title"] for result in filtered_results]
    assert "Movie.2023.1080p.BluRay.x264" in titles
    assert "Movie.2023.4K.WEB-DL.x265" in titles
    assert "Movie.2023.CAM.HDCAM" not in titles
    assert "Movie.2023.HDTV.BluRay.x264" not in titles


@pytest.mark.asyncio
async def test_subscription_filter_permission_denied(db_session: AsyncSession):
    """测试权限验证 - 用户无法访问其他用户的规则组"""
    # 创建两个用户
    user1 = User(id=1, username="user1", email="user1@example.com", hashed_password="hashed_test_password_1")
    user2 = User(id=2, username="user2", email="user2@example.com", hashed_password="hashed_test_password_2")
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    # 创建user2的规则组
    rule_group = FilterRuleGroup(
        name="用户2的规则组",
        description="只能user2访问",
        user_id=2,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={
            "include": ["1080p"],
            "exclude": ["CAM"]
        }
    )
    db_session.add(rule_group)
    await db_session.commit()
    
    # 创建user1的订阅，但引用user2的规则组
    subscription = Subscription(
        title="用户1电影",
        media_type="movie",
        user_id=1,
        include="",
        exclude="",
        filter_group_ids=[rule_group.id]
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # 模拟搜索结果
    search_results = [
        {"title": "Movie.2023.1080p.BluRay.x264", "link": "http://example.com/1", "seeders": 10},
        {"title": "Movie.2023.CAM.HDCAM", "link": "http://example.com/2", "seeders": 10},
    ]
    
    # 测试订阅服务过滤
    subscription_service = SubscriptionService(db_session)
    filtered_results = await subscription_service._filter_search_results(search_results, subscription)
    
    # 验证规则组被忽略，所有结果都应该通过（因为没有有效的过滤规则）
    assert len(filtered_results) == 2
    titles = [result["title"] for result in filtered_results]
    assert "Movie.2023.1080p.BluRay.x264" in titles
    assert "Movie.2023.CAM.HDCAM" in titles


@pytest.mark.asyncio
async def test_subscription_filter_complex_rule_merging(db_session: AsyncSession, test_user: User):
    """测试复杂规则结构的合并，包含多个include/exclude规则"""
    # 创建包含多个规则的规则组
    complex_group = FilterRuleGroup(
        name="复杂规则组",
        description="包含多个过滤规则",
        user_id=test_user.id,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={
            "include": ["1080p", "4K"],
            "exclude": ["CAM", "TS", "HDRip"]  # 将HDRip添加到基础exclude规则中
        }
    )
    
    db_session.add(complex_group)
    await db_session.commit()
    
    # 创建订阅
    subscription = Subscription(
        title="测试电影",
        media_type="movie",
        user_id=test_user.id,
        include="BluRay",
        exclude="HDTV",
        filter_group_ids=[complex_group.id]
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # 模拟搜索结果
    search_results = [
        {"title": "Movie.2023.1080p.BluRay.x264", "link": "http://example.com/1", "seeders": 10},      # 应该通过
        {"title": "Movie.2023.4K.BluRay.x265", "link": "http://example.com/2", "seeders": 10},        # 应该通过
        {"title": "Movie.2023.CAM.HDCAM", "link": "http://example.com/3", "seeders": 10},              # 应该被排除（CAM）
        {"title": "Movie.2023.HDRip.BluRay.x264", "link": "http://example.com/4", "seeders": 10},      # 应该被排除（HDRip）
        {"title": "Movie.2023.HDTV.BluRay.x264", "link": "http://example.com/5", "seeders": 10},       # 应该被排除（HDTV）
    ]
    
    # 测试订阅服务过滤
    subscription_service = SubscriptionService(db_session)
    filtered_results = await subscription_service._filter_search_results(search_results, subscription)
    
    # 验证基础规则合并应用
    assert len(filtered_results) == 2
    titles = [result["title"] for result in filtered_results]
    assert "Movie.2023.1080p.BluRay.x264" in titles
    assert "Movie.2023.4K.BluRay.x265" in titles
    assert "Movie.2023.CAM.HDCAM" not in titles
    assert "Movie.2023.HDRip.BluRay.x264" not in titles
    assert "Movie.2023.HDTV.BluRay.x264" not in titles
