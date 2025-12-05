"""
过滤规则组服务基础测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.filter_rule_group import FilterRuleGroup
from app.modules.filter_rule_group.service import FilterRuleGroupService


class TestFilterRuleGroupService:
    """过滤规则组服务测试类"""
    
    @pytest.fixture
    def service(self, db_session: AsyncSession) -> FilterRuleGroupService:
        """创建服务实例"""
        return FilterRuleGroupService(db_session)
    
    @pytest.fixture
    def test_user_id(self) -> int:
        """测试用户ID"""
        return 1
    
    @pytest.fixture
    def sample_rule_data(self) -> dict:
        """示例规则数据"""
        return {
            "name": "测试规则组",
            "description": "这是一个测试规则组",
            "media_types": ["movie", "tv"],
            "priority": 100,
            "rules": {
                "rules": [
                    {"type": "include", "pattern": "CHD", "logic": "or"},
                    {"type": "include", "pattern": "WiKi", "logic": "or"}
                ]
            },
            "enabled": True
        }
    
    @pytest.mark.asyncio
    async def test_create_group_success(self, service, test_user_id, sample_rule_data):
        """测试创建规则组成功"""
        group = await service.create_group(test_user_id, sample_rule_data, "test_user")
        
        assert group is not None
        assert group.id is not None
        assert group.name == sample_rule_data["name"]
        assert group.user_id == test_user_id
        assert group.media_types == sample_rule_data["media_types"]
        assert group.priority == sample_rule_data["priority"]
        assert group.rules == sample_rule_data["rules"]
        assert group.enabled == sample_rule_data["enabled"]
        assert group.created_by == "test_user"
        assert group.updated_by == "test_user"
        assert group.is_system is False
        assert group.rule_count == 2
    
    @pytest.mark.asyncio
    async def test_create_group_duplicate_name(self, service, test_user_id, sample_rule_data):
        """测试创建重复名称的规则组"""
        # 创建第一个规则组
        await service.create_group(test_user_id, sample_rule_data)
        
        # 尝试创建同名规则组
        with pytest.raises(ValueError, match="规则组名称.*已存在"):
            await service.create_group(test_user_id, sample_rule_data)
    
    @pytest.mark.asyncio
    async def test_create_group_invalid_rules(self, service, test_user_id, sample_rule_data):
        """测试创建无效规则的规则组"""
        invalid_data = sample_rule_data.copy()
        invalid_data["rules"] = {"invalid": "structure"}
        
        with pytest.raises(ValueError, match="规则必须包含.*rules.*字段"):
            await service.create_group(test_user_id, invalid_data)
    
    @pytest.mark.asyncio
    async def test_get_group_success(self, service, test_user_id, sample_rule_data):
        """测试获取规则组成功"""
        created_group = await service.create_group(test_user_id, sample_rule_data)
        
        retrieved_group = await service.get_group(created_group.id)
        
        assert retrieved_group is not None
        assert retrieved_group.id == created_group.id
        assert retrieved_group.name == created_group.name
    
    @pytest.mark.asyncio
    async def test_get_group_not_found(self, service):
        """测试获取不存在的规则组"""
        group = await service.get_group(99999)
        assert group is None
    
    @pytest.mark.asyncio
    async def test_list_groups_empty(self, service, test_user_id):
        """测试空规则组列表"""
        groups = await service.list_groups(test_user_id)
        assert groups == []
    
    @pytest.mark.asyncio
    async def test_list_groups_with_data(self, service, test_user_id, sample_rule_data):
        """测试获取规则组列表"""
        # 创建多个规则组
        await service.create_group(test_user_id, sample_rule_data)
        
        group2_data = sample_rule_data.copy()
        group2_data["name"] = "测试规则组2"
        group2_data["priority"] = 50
        await service.create_group(test_user_id, group2_data)
        
        groups = await service.list_groups(test_user_id)
        
        assert len(groups) == 2
        # 按优先级排序
        assert groups[0].priority == 50
        assert groups[1].priority == 100
    
    @pytest.mark.asyncio
    async def test_list_groups_with_media_type_filter(self, service, test_user_id, sample_rule_data):
        """测试按媒体类型过滤规则组"""
        # 创建只支持电影的规则组
        movie_only_data = sample_rule_data.copy()
        movie_only_data["name"] = "电影专用规则组"
        movie_only_data["media_types"] = ["movie"]
        await service.create_group(test_user_id, movie_only_data)
        
        # 创建支持电影的规则组
        await service.create_group(test_user_id, sample_rule_data)
        
        # 过滤电影类型
        movie_groups = await service.list_groups(test_user_id, media_type="movie")
        assert len(movie_groups) == 2
        
        # 过滤电视剧类型
        tv_groups = await service.list_groups(test_user_id, media_type="tv")
        assert len(tv_groups) == 1
        assert tv_groups[0].name == "测试规则组"
    
    @pytest.mark.asyncio
    async def test_update_group_success(self, service, test_user_id, sample_rule_data):
        """测试更新规则组成功"""
        created_group = await service.create_group(test_user_id, sample_rule_data)
        
        update_data = {
            "name": "更新后的规则组",
            "description": "更新后的描述",
            "priority": 200,
            "enabled": False
        }
        
        updated_group = await service.update_group(created_group.id, update_data, "test_user")
        
        assert updated_group.id == created_group.id
        assert updated_group.name == "更新后的规则组"
        assert updated_group.description == "更新后的描述"
        assert updated_group.priority == 200
        assert updated_group.enabled is False
        assert updated_group.updated_by == "test_user"
    
    @pytest.mark.asyncio
    async def test_update_group_not_found(self, service):
        """测试更新不存在的规则组"""
        with pytest.raises(ValueError, match="规则组不存在"):
            await service.update_group(99999, {"name": "新名称"})
    
    @pytest.mark.asyncio
    async def test_delete_group_success(self, service, test_user_id, sample_rule_data):
        """测试删除规则组成功"""
        created_group = await service.create_group(test_user_id, sample_rule_data)
        
        result = await service.delete_group(created_group.id)
        assert result is True
        
        # 验证已删除
        deleted_group = await service.get_group(created_group.id)
        assert deleted_group is None
    
    @pytest.mark.asyncio
    async def test_delete_group_not_found(self, service):
        """测试删除不存在的规则组"""
        with pytest.raises(ValueError, match="规则组不存在"):
            await service.delete_group(99999)
    
    @pytest.mark.asyncio
    async def test_resolve_groups_for_subscription_empty(self, service, test_user_id):
        """测试解析空规则组列表"""
        resolved = await service.resolve_groups_for_subscription(test_user_id, [], "movie")
        assert resolved == []
    
    @pytest.mark.asyncio
    async def test_resolve_groups_for_subscription_success(self, service, test_user_id, sample_rule_data):
        """测试解析规则组成功"""
        # 创建规则组
        group = await service.create_group(test_user_id, sample_rule_data)
        
        # 解析规则组
        resolved = await service.resolve_groups_for_subscription(test_user_id, [group.id], "movie")
        
        assert len(resolved) == 1
        assert resolved[0]["name"] == sample_rule_data["name"]
        assert resolved[0]["priority"] == sample_rule_data["priority"]
        # 服务返回完整的 rules dict，而不是内部的 rules 列表
        assert resolved[0]["rules"] == sample_rule_data["rules"]
    
    @pytest.mark.asyncio
    async def test_resolve_groups_for_backward_compatibility(self, service, test_user_id, sample_rule_data):
        """测试向后兼容性处理"""
        # 创建规则组
        group = await service.create_group(test_user_id, sample_rule_data)
        
        # 测试混合ID列表（包含字符串和无效项）
        mixed_ids = [group.id, "invalid", "123", "string_id"]
        resolved = await service.resolve_groups_for_subscription(test_user_id, mixed_ids, "movie")
        
        # 应该只解析有效的整数ID
        assert len(resolved) == 1
        assert resolved[0]["name"] == sample_rule_data["name"]
    
    @pytest.mark.asyncio
    async def test_resolve_groups_media_type_filter(self, service, test_user_id, sample_rule_data):
        """测试解析规则组时媒体类型过滤"""
        # 创建只支持电影的规则组
        movie_only_data = sample_rule_data.copy()
        movie_only_data["name"] = "电影专用"
        movie_only_data["media_types"] = ["movie"]
        movie_group = await service.create_group(test_user_id, movie_only_data)
        
        # 创建支持电影的规则组
        general_group = await service.create_group(test_user_id, sample_rule_data)
        
        # 解析电视剧类型（应该只返回通用规则组）
        resolved = await service.resolve_groups_for_subscription(
            test_user_id, [movie_group.id, general_group.id], "tv"
        )
        
        assert len(resolved) == 1
        assert resolved[0]["name"] == sample_rule_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_enabled_groups_by_ids(self, service, test_user_id, sample_rule_data):
        """测试根据ID获取启用的规则组"""
        # 创建规则组
        enabled_group = await service.create_group(test_user_id, sample_rule_data)
        
        # 创建禁用的规则组
        disabled_data = sample_rule_data.copy()
        disabled_data["name"] = "禁用规则组"
        disabled_data["enabled"] = False
        disabled_group = await service.create_group(test_user_id, disabled_data)
        
        # 获取启用的规则组
        enabled_groups = await service.get_enabled_groups_by_ids(
            [enabled_group.id, disabled_group.id]
        )
        
        assert len(enabled_groups) == 1
        assert enabled_groups[0].id == enabled_group.id
        assert enabled_groups[0].enabled is True
