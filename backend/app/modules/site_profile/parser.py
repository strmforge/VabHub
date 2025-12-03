"""
站点解析规则引擎
根据parse规则解析站点内容
"""

import re
from typing import Dict, Any, Optional, List
from lxml import html
from loguru import logger
import httpx


class SiteParser:
    """站点解析规则引擎"""
    
    def __init__(self, site_url: str, cookie: Optional[str] = None):
        """
        初始化解析器
        
        Args:
            site_url: 站点URL
            cookie: Cookie（可选）
        """
        self.site_url = site_url.rstrip('/')
        self.cookie = cookie
        self._html_cache: Dict[str, str] = {}
    
    async def parse(self, parse_rules: Dict[str, Any], page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        根据解析规则解析站点内容
        
        Args:
            parse_rules: 解析规则字典
            page_url: 要解析的页面URL（如果为None，使用站点首页）
            
        Returns:
            解析结果字典
        """
        if not parse_rules:
            return {}
        
        result = {}
        
        # 解析列表（种子列表等）
        if "list" in parse_rules:
            list_result = await self._parse_list(parse_rules["list"], page_url)
            result["list"] = list_result
        
        # 解析详情（种子详情等）
        if "detail" in parse_rules:
            detail_result = await self._parse_detail(parse_rules["detail"], page_url)
            result["detail"] = detail_result
        
        # 解析用户信息
        if "user" in parse_rules:
            user_result = await self._parse_user(parse_rules["user"], page_url)
            result["user"] = user_result
        
        return result
    
    async def _parse_list(self, list_rules: Dict[str, Any], page_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """解析列表"""
        html_content = await self._get_html(page_url or self.site_url)
        if not html_content:
            return []
        
        try:
            doc = html.fromstring(html_content)
            
            # 获取行选择器
            row_selector = list_rules.get("row", "")
            if not row_selector:
                return []
            
            rows = doc.cssselect(row_selector)
            if not rows:
                return []
            
            # 获取字段配置
            fields_config = list_rules.get("fields", {})
            if not fields_config:
                return []
            
            results = []
            for row in rows:
                item = {}
                for field_name, field_config in fields_config.items():
                    value = await self._extract_field(row, field_config)
                    if value is not None:
                        item[field_name] = value
                
                if item:
                    results.append(item)
            
            return results
            
        except Exception as e:
            logger.error(f"解析列表失败: {e}")
            return []
    
    async def _parse_detail(self, detail_rules: Dict[str, Any], page_url: Optional[str] = None) -> Dict[str, Any]:
        """解析详情"""
        html_content = await self._get_html(page_url or self.site_url)
        if not html_content:
            return {}
        
        try:
            doc = html.fromstring(html_content)
            
            fields_config = detail_rules.get("fields", {})
            if not fields_config:
                return {}
            
            result = {}
            for field_name, field_config in fields_config.items():
                value = await self._extract_field(doc, field_config)
                if value is not None:
                    result[field_name] = value
            
            return result
            
        except Exception as e:
            logger.error(f"解析详情失败: {e}")
            return {}
    
    async def _parse_user(self, user_rules: Dict[str, Any], page_url: Optional[str] = None) -> Dict[str, Any]:
        """解析用户信息"""
        html_content = await self._get_html(page_url or self.site_url)
        if not html_content:
            return {}
        
        try:
            doc = html.fromstring(html_content)
            
            fields_config = user_rules.get("fields", {})
            if not fields_config:
                return {}
            
            result = {}
            for field_name, field_config in fields_config.items():
                value = await self._extract_field(doc, field_config)
                if value is not None:
                    result[field_name] = value
            
            return result
            
        except Exception as e:
            logger.error(f"解析用户信息失败: {e}")
            return {}
    
    async def _extract_field(self, element: Any, field_config: Dict[str, Any]) -> Any:
        """提取字段值"""
        try:
            selector = field_config.get("selector", "")
            if not selector:
                return None
            
            # 查找元素
            elements = element.cssselect(selector)
            if not elements:
                return None
            
            target_element = elements[0]
            
            # 获取文本或属性
            if field_config.get("text", False):
                value = target_element.text_content().strip()
            elif "attr" in field_config:
                attr_name = field_config["attr"]
                value = target_element.get(attr_name, "")
            else:
                value = target_element.text_content().strip()
            
            # 转换
            if "transform" in field_config:
                transform_type = field_config["transform"]
                value = self._transform_value(value, transform_type)
            
            return value
            
        except Exception as e:
            logger.debug(f"提取字段失败: {field_config}, {e}")
            return None
    
    def _transform_value(self, value: str, transform_type: str) -> Any:
        """转换值"""
        if transform_type == "size":
            # 转换文件大小（如 "1.5 GB" -> 字节数）
            return self._parse_size(value)
        elif transform_type == "int":
            # 转换为整数
            try:
                return int(re.sub(r'[^\d]', '', value))
            except:
                return 0
        elif transform_type == "float":
            # 转换为浮点数
            try:
                return float(re.sub(r'[^\d.]', '', value))
            except:
                return 0.0
        elif transform_type == "date":
            # 转换日期（需要根据实际格式实现）
            return value
        else:
            return value
    
    def _parse_size(self, size_str: str) -> int:
        """解析文件大小字符串为字节数"""
        if not size_str:
            return 0
        
        # 移除空格并转换为小写
        size_str = size_str.strip().lower()
        
        # 提取数字和单位
        match = re.match(r'([\d.]+)\s*([kmgtp]?b?)', size_str)
        if not match:
            return 0
        
        number = float(match.group(1))
        unit = match.group(2) or 'b'
        
        multipliers = {
            'b': 1,
            'kb': 1024,
            'mb': 1024 ** 2,
            'gb': 1024 ** 3,
            'tb': 1024 ** 4,
            'pb': 1024 ** 5
        }
        
        multiplier = multipliers.get(unit, 1)
        return int(number * multiplier)
    
    async def _get_html(self, url: str) -> str:
        """获取页面HTML（带缓存）"""
        if url in self._html_cache:
            return self._html_cache[url]
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            if self.cookie:
                headers["Cookie"] = self.cookie
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    self._html_cache[url] = response.text
                    return self._html_cache[url]
        except Exception as e:
            logger.error(f"获取页面HTML失败: {url}, {e}")
        
        return ""

