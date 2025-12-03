"""
FilterRuleGroupService 单元测试
测试规则组解析、权限验证、优先级排序和规则合并功能
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.modules.filter_rule_group.service import FilterRuleGroupService
from app.models.filter_rule_group import FilterRuleGroup
from app.models.user import User


@pytest.mark.asyncio
async def test_resolve_groups_for_subscription_basic(db_session: AsyncSession, test_user: User):
    """测试基本的规则组解析功能"""
    # 创建测试规则组
    rule_group = FilterRuleGroup(
        name="测试规则组",
        description="测试用规则组",
        user_id=test_user.id,
        media_types=["movie"],  # 使用media_types数组而不是media_type字符串
        priority=1,
        enabled=True,
        rules={
            "include": ["1080p", "4K"],
            "exclude": ["CAM", "TS"]
        }
    )
    db_session.add(rule_group)
    await db_session.commit()
    
    # 测试服务
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=test_user.id,
        group_ids=[rule_group.id],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    assert len(result) == 1
    assert result[0]["id"] == rule_group.id
    assert result[0]["name"] == "测试规则组"
    assert result[0]["priority"] == 1
    assert result[0]["rules"]["include"] == ["1080p", "4K"]
    assert result[0]["rules"]["exclude"] == ["CAM", "TS"]


@pytest.mark.asyncio
async def test_resolve_groups_permission_denied(db_session: AsyncSession):
    """测试权限验证 - 用户无法访问其他用户的规则组"""
    # 创建两个测试用户
    user1 = User(id=1, username="user1", email="user1@example.com", hashed_password="hashed_test_password_1")
    user2 = User(id=2, username="user2", email="user2@example.com", hashed_password="hashed_test_password_2")
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    # 创建user2的规则组
    rule_group = FilterRuleGroup(
        name="用户2的规则组",
        description="只能用户2访问",
        user_id=2,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={"include": ["1080p"]}
    )
    db_session.add(rule_group)
    await db_session.commit()
    
    # 测试user1尝试访问user2的规则组
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[rule_group.id],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    # 应该返回空列表，因为权限不足
    assert len(result) == 0


@pytest.mark.asyncio
async def test_resolve_groups_priority_sorting(db_session: AsyncSession):
    """测试规则组按优先级排序"""
    # 创建测试用户
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed_test_password")
    db_session.add(user)
    await db_session.commit()
    
    # 创建多个不同优先级的规则组
    group1 = FilterRuleGroup(
        name="低优先级规则组",
        description="优先级3",
        user_id=1,
        media_types=["movie"],
        priority=3,
        enabled=True,
        rules={"include": ["720p"]}
    )
    group2 = FilterRuleGroup(
        name="高优先级规则组",
        description="优先级1",
        user_id=1,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={"include": ["4K"]}
    )
    group3 = FilterRuleGroup(
        name="中优先级规则组",
        description="优先级2",
        user_id=1,
        media_types=["movie"],
        priority=2,
        enabled=True,
        rules={"include": ["1080p"]}
    )
    db_session.add_all([group1, group2, group3])
    await db_session.commit()
    
    # 测试服务，故意乱序传入ID
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[group3.id, group1.id, group2.id],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    # 验证按优先级排序（1, 2, 3）
    assert len(result) == 3
    assert result[0]["priority"] == 1
    assert result[1]["priority"] == 2
    assert result[2]["priority"] == 3
    assert result[0]["name"] == "高优先级规则组"
    assert result[1]["name"] == "中优先级规则组"
    assert result[2]["name"] == "低优先级规则组"
    # 验证规则内容
    assert result[0]["rules"]["include"] == ["4K"]
    assert result[1]["rules"]["include"] == ["1080p"]
    assert result[2]["rules"]["include"] == ["720p"]


@pytest.mark.asyncio
async def test_resolve_groups_media_type_filtering(db_session: AsyncSession):
    """测试媒体类型过滤"""
    # 创建测试用户
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed_test_password")
    db_session.add(user)
    await db_session.commit()
    
    # 创建不同媒体类型的规则组
    movie_group = FilterRuleGroup(
        name="电影规则组",
        description="电影专用",
        user_id=1,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={"include": ["1080p"]}
    )
    tv_group = FilterRuleGroup(
        name="电视剧规则组",
        description="电视剧专用",
        user_id=1,
        media_types=["tv"],
        priority=1,
        enabled=True,
        rules={"include": ["HDTV"]}
    )
    universal_group = FilterRuleGroup(
        name="通用规则组",
        description="所有媒体类型",
        user_id=1,
        media_types=["movie", "tv", "anime"],
        priority=1,
        enabled=True,
        rules={"exclude": ["CAM"]}
    )
    db_session.add_all([movie_group, tv_group, universal_group])
    await db_session.commit()
    
    # 测试电影媒体类型
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[movie_group.id, tv_group.id, universal_group.id],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    # 应该返回电影组和通用组，排除电视剧组
    assert len(result) == 2
    result_names = [group["name"] for group in result]
    assert "电影规则组" in result_names
    assert "通用规则组" in result_names
    assert "电视剧规则组" not in result_names


@pytest.mark.asyncio
async def test_resolve_groups_disabled_groups(db_session: AsyncSession):
    """测试禁用的规则组不会被返回"""
    # 创建测试用户
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed_test_password")
    db_session.add(user)
    await db_session.commit()
    
    # 创建启用和禁用的规则组
    enabled_group = FilterRuleGroup(
        name="启用的规则组",
        description="正常使用",
        user_id=1,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={"include": ["1080p"]}
    )
    disabled_group = FilterRuleGroup(
        name="禁用的规则组",
        description="已禁用",
        user_id=1,
        media_types=["movie"],
        priority=2,
        enabled=False,
        rules={"include": ["4K"]}
    )
    db_session.add_all([enabled_group, disabled_group])
    await db_session.commit()
    
    # 测试服务
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[enabled_group.id, disabled_group.id],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    # 应该只返回启用的规则组
    assert len(result) == 1
    assert result[0]["name"] == "启用的规则组"


@pytest.mark.asyncio
async def test_resolve_groups_invalid_ids(db_session: AsyncSession):
    """测试无效的规则组ID处理"""
    # 创建测试用户
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed_test_password")
    db_session.add(user)
    await db_session.commit()
    
    # 创建一个有效的规则组
    valid_group = FilterRuleGroup(
        name="有效规则组",
        description="正常规则组",
        user_id=1,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={"include": ["1080p"]}
    )
    db_session.add(valid_group)
    await db_session.commit()
    
    # 测试包含无效ID的请求
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[valid_group.id, 99999, 88888],  # 使用正确的参数名group_ids，包含无效ID
        media_type="movie"
    )
    
    # 应该只返回有效的规则组，忽略无效ID
    assert len(result) == 1
    assert result[0]["id"] == valid_group.id


@pytest.mark.asyncio
async def test_resolve_groups_empty_list(db_session: AsyncSession):
    """测试空的规则组ID列表"""
    # 创建测试用户
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed_test_password")
    db_session.add(user)
    await db_session.commit()
    
    # 测试空列表
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    # 应该返回空列表
    assert len(result) == 0


@pytest.mark.asyncio
async def test_resolve_groups_complex_rules(db_session: AsyncSession):
    """测试复杂规则结构的处理"""
    # 创建测试用户
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed_test_password")
    db_session.add(user)
    await db_session.commit()
    
    # 创建包含复杂规则的规则组
    complex_group = FilterRuleGroup(
        name="复杂规则组",
        description="包含各种规则类型",
        user_id=1,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={
            "include": ["1080p", "4K", "BluRay"],
            "exclude": ["CAM", "TS", "HC"],
            "custom_rules": {
                "min_size": "1GB",
                "max_size": "50GB",
                "required_codecs": ["x264", "x265"]
            }
        }
    )
    db_session.add(complex_group)
    await db_session.commit()
    
    # 测试服务
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[complex_group.id],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    # 验证复杂规则结构完整保留
    assert len(result) == 1
    rules = result[0]["rules"]
    assert rules["include"] == ["1080p", "4K", "BluRay"]
    assert rules["exclude"] == ["CAM", "TS", "HC"]
    assert rules["custom_rules"]["min_size"] == "1GB"
    assert rules["custom_rules"]["required_codecs"] == ["x264", "x265"]


@pytest.mark.asyncio
async def test_resolve_groups_rule_merging_simulation(db_session: AsyncSession):
    """测试多个规则组的规则合并模拟（模拟订阅服务中的合并逻辑）"""
    # 创建测试用户
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="hashed_test_password")
    db_session.add(user)
    await db_session.commit()
    
    # 创建多个规则组，模拟实际使用场景
    quality_group = FilterRuleGroup(
        name="质量规则组",
        description="定义视频质量偏好",
        user_id=1,
        media_types=["movie"],
        priority=1,
        enabled=True,
        rules={
            "include": ["1080p", "4K"],
            "exclude": ["720p", "480p"]
        }
    )
    
    source_group = FilterRuleGroup(
        name="片源规则组",
        description="定义片源偏好",
        user_id=1,
        media_types=["movie"],
        priority=2,
        enabled=True,
        rules={
            "include": ["BluRay", "WEB-DL"],
            "exclude": ["CAM", "TS", "TC"]
        }
    )
    
    codec_group = FilterRuleGroup(
        name="编码规则组",
        description="定义编码偏好",
        user_id=1,
        media_types=["movie"],
        priority=3,
        enabled=True,
        rules={
            "include": ["x264", "x265"],
            "exclude": ["XVID", "DIVX"]
        }
    )
    
    db_session.add_all([quality_group, source_group, codec_group])
    await db_session.commit()
    
    # 测试服务
    service = FilterRuleGroupService(db_session)
    result = await service.resolve_groups_for_subscription(
        user_id=1,
        group_ids=[quality_group.id, source_group.id, codec_group.id],  # 使用正确的参数名group_ids
        media_type="movie"
    )
    
    # 验证返回了所有规则组并按优先级排序
    assert len(result) == 3
    assert result[0]["name"] == "质量规则组"
    assert result[1]["name"] == "片源规则组"
    assert result[2]["name"] == "编码规则组"
    
    # 模拟订阅服务中的规则合并逻辑
    merged_include = ""
    merged_exclude = ""
    
    for group in result:
        if group.get('rules'):
            rules = group['rules']
            if rules.get('include'):
                if merged_include:
                    merged_include += "\n"
                merged_include += "\n".join(rules['include']) if isinstance(rules['include'], list) else str(rules['include'])
            if rules.get('exclude'):
                if merged_exclude:
                    merged_exclude += "\n"
                merged_exclude += "\n".join(rules['exclude']) if isinstance(rules['exclude'], list) else str(rules['exclude'])
    
    # 验证合并结果
    expected_include = "1080p\n4K\nBluRay\nWEB-DL\nx264\nx265"
    expected_exclude = "720p\n480p\nCAM\nTS\nTC\nXVID\nDIVX"
    
    assert merged_include == expected_include
    assert merged_exclude == expected_exclude
    
    # 验证合并后的规则可以用于过滤
    assert "1080p" in merged_include
    assert "4K" in merged_include
    assert "CAM" in merged_exclude
    assert "x265" in merged_include
    assert "XVID" in merged_exclude
