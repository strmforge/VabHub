"""
RSS订阅高级规则匹配引擎
使用订阅服务中的高级规则系统来匹配RSS项
"""

import re
from typing import Any, Dict, List, Optional

from loguru import logger

from app.constants.media_types import is_tv_like
from app.models.subscription import Subscription
from .media_extractor import ExtractedMediaInfo
from .parser import RSSItem as ParserRSSItem


class RSSRuleEngine:
    """RSS订阅规则匹配引擎"""
    
    def __init__(self):
        """初始化规则引擎"""
        pass
    
    def evaluate_rss_item(
        self,
        rss_item: ParserRSSItem,
        extracted_info: ExtractedMediaInfo,
        subscription: Subscription
    ) -> Dict[str, Any]:
        """
        评估RSS项是否符合订阅的高级规则
        
        Args:
            rss_item: RSS项
            extracted_info: 提取的媒体信息
            subscription: 订阅对象
            
        Returns:
            评估结果字典：
            {
                "matched": bool,  # 是否匹配
                "score": float,   # 匹配分数（0-1）
                "reason": str,    # 匹配原因
                "failed_rules": List[str]  # 未通过的规则列表
            }
        """
        # 将RSS项转换为搜索结果格式（用于复用订阅服务的规则匹配逻辑）
        search_result = self._convert_rss_item_to_search_result(rss_item, extracted_info)
        
        # 评估结果
        matched = True
        score = 1.0
        failed_rules = []
        matched_rules = []
        
        # 1. 检查质量要求
        if subscription.quality:
            quality_lower = subscription.quality.lower()
            title_lower = search_result.get("title", "").lower()
            quality_field = search_result.get("quality", "").lower()
            if quality_lower not in title_lower and quality_lower not in quality_field:
                matched = False
                failed_rules.append(f"质量不匹配: 需要 {subscription.quality}")
            else:
                matched_rules.append(f"质量匹配: {subscription.quality}")
                score += 0.1
        
        # 2. 检查分辨率要求
        if subscription.resolution:
            resolution_lower = subscription.resolution.lower()
            title_lower = search_result.get("title", "").lower()
            resolution_field = search_result.get("resolution", "").lower()
            if resolution_lower not in title_lower and resolution_lower not in resolution_field:
                matched = False
                failed_rules.append(f"分辨率不匹配: 需要 {subscription.resolution}")
            else:
                matched_rules.append(f"分辨率匹配: {subscription.resolution}")
                score += 0.1
        
        # 3. 检查特效要求（HDR、DV等）
        if subscription.effect:
            effect_lower = subscription.effect.lower()
            title_lower = search_result.get("title", "").lower()
            if effect_lower not in title_lower:
                matched = False
                failed_rules.append(f"特效不匹配: 需要 {subscription.effect}")
            else:
                matched_rules.append(f"特效匹配: {subscription.effect}")
                score += 0.1
        
        # 4. 检查做种数要求（如果RSS项包含做种数信息）
        if subscription.min_seeders:
            seeders = search_result.get("seeders", 0)
            if seeders < subscription.min_seeders:
                matched = False
                failed_rules.append(f"做种数不足: 需要至少 {subscription.min_seeders}，当前 {seeders}")
            else:
                matched_rules.append(f"做种数满足: {seeders} >= {subscription.min_seeders}")
                score += 0.1
        
        # 5. 检查包含规则（支持关键字和正则表达式）
        if subscription.include:
            if not self._check_include_rule(subscription.include, search_result.get("title", "")):
                matched = False
                failed_rules.append(f"不满足包含规则: {subscription.include}")
            else:
                matched_rules.append(f"包含规则匹配: {subscription.include}")
                score += 0.15
        
        # 6. 检查排除规则（支持关键字和正则表达式）
        if subscription.exclude:
            if self._check_exclude_rule(subscription.exclude, search_result.get("title", "")):
                matched = False
                failed_rules.append(f"触发排除规则: {subscription.exclude}")
            else:
                matched_rules.append(f"排除规则通过")
                score += 0.15
        
        # 7. 检查发布组过滤
        if subscription.filter_groups:
            if not self._check_filter_groups(subscription.filter_groups, search_result.get("title", "")):
                matched = False
                failed_rules.append(f"发布组不匹配: {subscription.filter_groups}")
            else:
                matched_rules.append(f"发布组匹配")
                score += 0.1
        
        # 8. 电视剧特殊处理：检查季数和集数
        if is_tv_like(subscription.media_type):
            if subscription.season:
                season_pattern = f"s{subscription.season:02d}"
                season_pattern_alt = f"season {subscription.season}"
                title_lower = search_result.get("title", "").lower()
                if season_pattern not in title_lower and season_pattern_alt not in title_lower:
                    # 检查提取的媒体信息中的季数
                    if extracted_info.season and extracted_info.season != subscription.season:
                        matched = False
                        failed_rules.append(f"季数不匹配: 需要 S{subscription.season:02d}，当前 S{extracted_info.season:02d}")
                    elif not extracted_info.season:
                        matched = False
                        failed_rules.append(f"季数不匹配: 需要 S{subscription.season:02d}")
                    else:
                        matched_rules.append(f"季数匹配: S{subscription.season:02d}")
                        score += 0.15
        
        # 9. 检查搜索规则（如果存在）
        if subscription.search_rules:
            if not self._check_search_rules(subscription.search_rules, search_result):
                matched = False
                failed_rules.append(f"搜索规则不匹配: {subscription.search_rules}")
            else:
                matched_rules.append(f"搜索规则匹配")
                score += 0.1
        
        # 归一化分数（0-1）
        score = min(score, 1.0)
        
        # 生成匹配原因
        if matched:
            reason = f"匹配规则: {', '.join(matched_rules)}"
        else:
            reason = f"未通过规则: {', '.join(failed_rules)}"
        
        return {
            "matched": matched,
            "score": score,
            "reason": reason,
            "failed_rules": failed_rules,
            "matched_rules": matched_rules
        }
    
    def _convert_rss_item_to_search_result(
        self,
        rss_item: ParserRSSItem,
        extracted_info: ExtractedMediaInfo
    ) -> Dict[str, Any]:
        """
        将RSS项转换为搜索结果格式
        
        Args:
            rss_item: RSS项
            extracted_info: 提取的媒体信息
            
        Returns:
            搜索结果字典
        """
        return {
            "title": rss_item.title,
            "quality": extracted_info.quality or "",
            "resolution": extracted_info.resolution or "",
            "codec": extracted_info.codec or "",
            "group": extracted_info.group or "",
            "seeders": 0,  # RSS项通常不包含做种数信息
            "size_gb": 0,  # RSS项通常不包含大小信息
            "magnet_link": rss_item.link if rss_item.link.startswith("magnet:") else None,
            "torrent_url": rss_item.link if not rss_item.link.startswith("magnet:") else None,
            "description": rss_item.description or ""
        }
    
    def _check_include_rule(self, include_rule: str, title: str) -> bool:
        """
        检查包含规则
        
        Args:
            include_rule: 包含规则（可以是关键字或正则表达式）
            title: 标题
            
        Returns:
            是否匹配
        """
        if not include_rule:
            return True
        
        title_lower = title.lower()
        include_lower = include_rule.lower()
        
        # 尝试作为正则表达式匹配
        try:
            pattern = re.compile(include_lower, re.IGNORECASE)
            if pattern.search(title):
                return True
        except re.error:
            # 如果不是有效的正则表达式，作为关键字匹配
            pass
        
        # 作为关键字匹配
        if include_lower in title_lower:
            return True
        
        # 支持多关键字（用 | 分隔）
        if "|" in include_rule:
            keywords = [k.strip() for k in include_rule.split("|")]
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return True
        
        return False
    
    def _check_exclude_rule(self, exclude_rule: str, title: str) -> bool:
        """
        检查排除规则
        
        Args:
            exclude_rule: 排除规则（可以是关键字或正则表达式）
            title: 标题
            
        Returns:
            是否触发排除规则（True表示应该排除）
        """
        if not exclude_rule:
            return False
        
        title_lower = title.lower()
        exclude_lower = exclude_rule.lower()
        
        # 尝试作为正则表达式匹配
        try:
            pattern = re.compile(exclude_lower, re.IGNORECASE)
            if pattern.search(title):
                return True
        except re.error:
            # 如果不是有效的正则表达式，作为关键字匹配
            pass
        
        # 作为关键字匹配
        if exclude_lower in title_lower:
            return True
        
        # 支持多关键字（用 | 分隔）
        if "|" in exclude_rule:
            keywords = [k.strip() for k in exclude_rule.split("|")]
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return True
        
        return False
    
    def _check_filter_groups(self, filter_groups: Any, title: str) -> bool:
        """
        检查发布组过滤规则
        
        Args:
            filter_groups: 发布组过滤规则（可以是列表或JSON）
            title: 标题
            
        Returns:
            是否匹配
        """
        if not filter_groups:
            return True
        
        title_lower = title.lower()
        
        # 如果filter_groups是字符串，尝试解析为JSON
        if isinstance(filter_groups, str):
            try:
                import json
                filter_groups = json.loads(filter_groups)
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，作为单个发布组名称处理
                filter_groups = [filter_groups]
        
        # 如果filter_groups是列表
        if isinstance(filter_groups, list):
            # 检查标题中是否包含任何允许的发布组
            for group in filter_groups:
                if isinstance(group, dict):
                    # 如果是字典，可能有更复杂的规则
                    group_name = group.get("name") or group.get("group")
                    if group_name and group_name.lower() in title_lower:
                        return True
                elif isinstance(group, str):
                    if group.lower() in title_lower:
                        return True
            return False
        
        # 如果是字典，可能有更复杂的规则结构
        if isinstance(filter_groups, dict):
            # 支持白名单和黑名单
            whitelist = filter_groups.get("whitelist", [])
            blacklist = filter_groups.get("blacklist", [])
            
            # 检查黑名单
            for group in blacklist:
                if isinstance(group, str) and group.lower() in title_lower:
                    return False
            
            # 检查白名单
            if whitelist:
                for group in whitelist:
                    if isinstance(group, str) and group.lower() in title_lower:
                        return True
                return False
            
            return True
        
        return True
    
    def _check_search_rules(self, search_rules: Any, search_result: Dict[str, Any]) -> bool:
        """
        检查搜索规则
        
        Args:
            search_rules: 搜索规则（JSON格式）
            search_result: 搜索结果字典
            
        Returns:
            是否匹配
        """
        if not search_rules:
            return True
        
        # 如果search_rules是字符串，尝试解析为JSON
        if isinstance(search_rules, str):
            try:
                import json
                search_rules = json.loads(search_rules)
            except (json.JSONDecodeError, ValueError):
                return True
        
        # 如果search_rules是字典，检查各种规则
        if isinstance(search_rules, dict):
            # 检查最小文件大小
            min_size = search_rules.get("min_size_gb")
            if min_size:
                size_gb = search_result.get("size_gb", 0)
                if size_gb < min_size:
                    return False
            
            # 检查最大文件大小
            max_size = search_rules.get("max_size_gb")
            if max_size:
                size_gb = search_result.get("size_gb", 0)
                if size_gb > max_size:
                    return False
            
            # 检查编码要求
            required_codec = search_rules.get("codec")
            if required_codec:
                codec = search_result.get("codec", "").lower()
                if required_codec.lower() not in codec:
                    return False
            
            # 检查发布组要求
            required_group = search_rules.get("group")
            if required_group:
                group = search_result.get("group", "").lower()
                if required_group.lower() not in group:
                    return False
        
        return True

