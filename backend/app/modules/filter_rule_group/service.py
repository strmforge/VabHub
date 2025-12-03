"""
过滤规则组服务
"""

from typing import Dict, List, Optional
from datetime import datetime

from loguru import logger
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.filter_rule_group import FilterRuleGroup


class FilterRuleGroupService:
    """过滤规则组服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_groups(
        self, 
        user_id: Optional[int] = None, 
        media_type: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[FilterRuleGroup]:
        """
        获取规则组列表
        
        Args:
            user_id: 用户ID，None表示获取系统级规则组
            media_type: 媒体类型过滤
            enabled_only: 是否只返回启用的规则组
            
        Returns:
            规则组列表
        """
        try:
            query = select(FilterRuleGroup)
            
            # 用户过滤：用户自己的规则组 + 系统级规则组
            if user_id is not None:
                query = query.where(
                    or_(
                        FilterRuleGroup.user_id == user_id,
                        FilterRuleGroup.user_id.is_(None)
                    )
                )
            
            # 启用状态过滤
            if enabled_only:
                query = query.where(FilterRuleGroup.enabled == True)
            
            # 按优先级排序
            query = query.order_by(FilterRuleGroup.priority.asc(), FilterRuleGroup.id.asc())
            
            result = await self.db.execute(query)
            groups = result.scalars().all()
            
            # 媒体类型过滤（在Python中处理，因为media_types是JSON字段）
            if media_type:
                filtered_groups = []
                for group in groups:
                    if group.media_types and media_type in group.media_types:
                        filtered_groups.append(group)
                groups = filtered_groups
            
            return list(groups)
            
        except Exception as e:
            logger.error(f"获取规则组列表失败: {e}")
            raise
    
    async def get_group(self, group_id: int) -> Optional[FilterRuleGroup]:
        """
        获取单个规则组
        
        Args:
            group_id: 规则组ID
            
        Returns:
            规则组对象或None
        """
        try:
            query = select(FilterRuleGroup).where(FilterRuleGroup.id == group_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"获取规则组失败: {e}")
            raise
    
    async def create_group(self, user_id: int, data: dict, created_by: str = None) -> FilterRuleGroup:
        """
        创建规则组
        
        Args:
            user_id: 用户ID
            data: 规则组数据
            created_by: 创建者
            
        Returns:
            创建的规则组对象
        """
        try:
            # 验证规则格式
            self._validate_rules(data.get("rules", {}))
            
            # 检查名称重复（同一用户下）
            existing_query = select(FilterRuleGroup).where(
                and_(
                    FilterRuleGroup.user_id == user_id,
                    FilterRuleGroup.name == data["name"]
                )
            )
            existing_result = await self.db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise ValueError(f"规则组名称 '{data['name']}' 已存在")
            
            group = FilterRuleGroup(
                user_id=user_id,
                name=data["name"],
                description=data.get("description", ""),
                media_types=data.get("media_types", ["movie", "tv"]),
                priority=data.get("priority", 100),
                rules=data["rules"],
                enabled=data.get("enabled", True),
                created_by=created_by,
                updated_by=created_by,
            )
            
            self.db.add(group)
            await self.db.commit()
            await self.db.refresh(group)
            
            logger.info(f"创建规则组成功: {group.name} (ID: {group.id})")
            return group
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建规则组失败: {e}")
            raise
    
    async def update_group(
        self, 
        group_id: int, 
        data: dict, 
        updated_by: str = None
    ) -> FilterRuleGroup:
        """
        更新规则组
        
        Args:
            group_id: 规则组ID
            data: 更新数据
            updated_by: 更新者
            
        Returns:
            更新后的规则组对象
        """
        try:
            group = await self.get_group(group_id)
            if not group:
                raise ValueError(f"规则组不存在: {group_id}")
            
            # 验证规则格式
            if "rules" in data:
                self._validate_rules(data["rules"])
            
            # 检查名称重复（排除自己）
            if "name" in data and data["name"] != group.name:
                existing_query = select(FilterRuleGroup).where(
                    and_(
                        FilterRuleGroup.user_id == group.user_id,
                        FilterRuleGroup.name == data["name"],
                        FilterRuleGroup.id != group_id
                    )
                )
                existing_result = await self.db.execute(existing_query)
                if existing_result.scalar_one_or_none():
                    raise ValueError(f"规则组名称 '{data['name']}' 已存在")
            
            # 更新字段
            for field, value in data.items():
                if hasattr(group, field) and field not in ["id", "user_id", "created_at", "created_by"]:
                    setattr(group, field, value)
            
            group.updated_by = updated_by
            group.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(group)
            
            logger.info(f"更新规则组成功: {group.name} (ID: {group.id})")
            return group
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新规则组失败: {e}")
            raise
    
    async def delete_group(self, group_id: int) -> bool:
        """
        删除规则组
        
        Args:
            group_id: 规则组ID
            
        Returns:
            是否删除成功
        """
        try:
            group = await self.get_group(group_id)
            if not group:
                raise ValueError(f"规则组不存在: {group_id}")
            
            await self.db.delete(group)
            await self.db.commit()
            
            logger.info(f"删除规则组成功: {group.name} (ID: {group.id})")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除规则组失败: {e}")
            raise
    
    async def resolve_groups_for_subscription(
        self, 
        user_id: int, 
        group_ids: List[int], 
        media_type: str
    ) -> List[dict]:
        """
        为订阅解析规则组，返回RuleEngine可用结构
        
        Args:
            user_id: 用户ID
            group_ids: 规则组ID列表
            media_type: 媒体类型
            
        Returns:
            规则组列表，格式为RuleEngine期望的结构
        """
        try:
            if not group_ids:
                return []
            
            # 处理向后兼容：过滤非整数ID
            valid_ids = []
            for item in group_ids:
                if isinstance(item, int):
                    valid_ids.append(item)
                elif isinstance(item, str) and item.isdigit():
                    valid_ids.append(int(item))
                else:
                    logger.warning(f"忽略无效的规则组ID: {item}")
            
            if not valid_ids:
                logger.warning("没有有效的规则组ID")
                return []
            
            # 查询规则组
            query = select(FilterRuleGroup).where(
                and_(
                    FilterRuleGroup.id.in_(valid_ids),
                    FilterRuleGroup.enabled == True,
                    or_(
                        FilterRuleGroup.user_id == user_id,
                        FilterRuleGroup.user_id.is_(None)
                    )
                )
            )
            
            result = await self.db.execute(query)
            groups = result.scalars().all()
            
            # 按优先级排序并转换为RuleEngine格式
            sorted_groups = sorted(groups, key=lambda x: x.priority)
            
            resolved_groups = []
            for group in sorted_groups:
                if not group.media_types or media_type in group.media_types:
                    resolved_groups.append({
                        "id": group.id,
                        "name": group.name,
                        "priority": group.priority,
                        "rules": group.rules if isinstance(group.rules, dict) else {},
                    })
            
            logger.info(f"为订阅解析规则组: 用户={user_id}, 媒体类型={media_type}, "
                       f"规则组=[{', '.join(g['name'] for g in resolved_groups)}]")
            
            return resolved_groups
            
        except Exception as e:
            logger.error(f"解析规则组失败: {e}")
            return []
    
    async def get_enabled_groups_by_ids(
        self, 
        group_ids: List[int], 
        media_type: str = None
    ) -> List[FilterRuleGroup]:
        """
        根据ID列表获取启用的规则组
        
        Args:
            group_ids: 规则组ID列表
            media_type: 媒体类型过滤
            
        Returns:
            规则组列表
        """
        try:
            if not group_ids:
                return []
            
            query = select(FilterRuleGroup).where(
                and_(
                    FilterRuleGroup.id.in_(group_ids),
                    FilterRuleGroup.enabled == True
                )
            )
            
            result = await self.db.execute(query)
            groups = result.scalars().all()
            
            # 媒体类型过滤
            if media_type:
                filtered_groups = []
                for group in groups:
                    if not group.media_types or media_type in group.media_types:
                        filtered_groups.append(group)
                groups = filtered_groups
            
            return list(groups)
            
        except Exception as e:
            logger.error(f"获取规则组失败: {e}")
            return []
    
    def _validate_rules(self, rules: dict) -> None:
        """
        验证规则格式
        
        Args:
            rules: 规则配置
            
        Raises:
            ValueError: 规则格式不正确
        """
        if not isinstance(rules, dict):
            raise ValueError("规则必须是字典格式")
        
        if "rules" not in rules:
            raise ValueError("规则必须包含 'rules' 字段")
        
        rules_list = rules["rules"]
        if not isinstance(rules_list, list):
            raise ValueError("rules 字段必须是列表格式")
        
        for i, rule in enumerate(rules_list):
            if not isinstance(rule, dict):
                raise ValueError(f"规则 {i} 必须是字典格式")
            
            required_fields = ["type", "pattern", "logic"]
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"规则 {i} 缺少必需字段: {field}")
            
            if rule["type"] not in ["include", "exclude"]:
                raise ValueError(f"规则 {i} 的 type 必须是 'include' 或 'exclude'")
            
            if rule["logic"] not in ["and", "or"]:
                raise ValueError(f"规则 {i} 的 logic 必须是 'and' 或 'or'")
            
            if not rule["pattern"]:
                raise ValueError(f"规则 {i} 的 pattern 不能为空")
        
        logger.debug("规则格式验证通过")
