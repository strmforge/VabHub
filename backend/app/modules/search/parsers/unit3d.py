"""
Unit3D框架解析器
支持使用Unit3D框架的PT站点
"""
from typing import List, Dict, Any
from lxml import etree
from loguru import logger
import re
from urllib.parse import urljoin

from .base import ParserBase


class Unit3DParser(ParserBase):
    """Unit3D框架解析器"""
    
    def __init__(self, site_name: str = "", base_url: str = ""):
        """
        初始化Unit3D解析器
        
        Args:
            site_name: 站点名称
            base_url: 站点基础URL
        """
        super().__init__(site_name)
        self.base_url = base_url
    
    def parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """
        解析Unit3D搜索结果页面
        
        Unit3D通常使用现代化的表格或卡片布局
        """
        results = []
        
        try:
            tree = etree.HTML(html)
            if tree is None:
                return results
            
            # Unit3D搜索结果可能在表格或div容器中
            # 查找包含torrent链接的元素
            containers = tree.xpath('//table[.//a[contains(@href, "torrents/")]] | //div[contains(@class, "torrent")]//a[contains(@href, "torrents/")]')
            
            if containers:
                # 找到父容器
                parent_map = {}
                for container in containers:
                    parent = container.getparent()
                    while parent is not None and parent.tag not in ['table', 'div', 'tr']:
                        parent = parent.getparent()
                    if parent is not None:
                        parent_map[id(parent)] = parent
                
                containers = list(parent_map.values())
            
            # 如果没有找到，尝试查找所有包含torrent链接的行
            if not containers:
                rows = tree.xpath('//tr[.//a[contains(@href, "torrents/")]] | //div[contains(@class, "torrent-item")]')
                containers = rows
            
            for container in containers:
                try:
                    result = self._parse_torrent_item(container)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"解析Unit3D项失败: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"解析Unit3D搜索结果失败: {e}")
        
        return results
    
    def _parse_torrent_item(self, item) -> Dict[str, Any]:
        """
        解析单个种子项
        
        Args:
            item: lxml元素
        
        Returns:
            解析后的结果字典
        """
        result = {}
        
        # 查找标题链接（Unit3D通常使用 /torrents/{id} 格式）
        title_links = item.xpath('.//a[contains(@href, "torrents/")]')
        if title_links:
            title_link = title_links[0]
            result['title'] = title_link.text_content().strip()
            href = title_link.get('href', '')
            if href:
                result['torrent_url'] = urljoin(self.base_url, href)
                # 提取torrent ID
                match = re.search(r'torrents/(\d+)', href)
                if match:
                    result['torrent_id'] = match.group(1)
        
        # 查找磁力链接
        magnet_links = item.xpath('.//a[starts-with(@href, "magnet:")]')
        if magnet_links:
            result['magnet_link'] = magnet_links[0].get('href', '')
            result['info_hash'] = self.extract_info_hash(result['magnet_link'])
        
        # 查找大小
        size_elements = item.xpath('.//span[contains(@class, "size")] | .//div[contains(@class, "size")] | .//td[contains(@class, "size")]')
        for elem in size_elements:
            text = elem.text_content().strip()
            if any(unit in text.upper() for unit in ['GB', 'MB', 'TB', 'KB']):
                result['size_gb'] = self.parse_size(text)
                break
        
        # 如果没有找到，尝试从所有文本中提取
        if 'size_gb' not in result:
            text = item.text_content()
            size_match = re.search(r'([\d.]+)\s*([KMGT]?B)', text.upper())
            if size_match:
                result['size_gb'] = self.parse_size(f"{size_match.group(1)} {size_match.group(2)}")
        
        # 查找做种数和下载数
        # Unit3D通常在特定的span或div中显示
        text = item.text_content()
        
        # 做种数
        seeders_match = re.search(r'Seeders?[:\s]+(\d+)', text, re.IGNORECASE)
        if seeders_match:
            result['seeders'] = int(seeders_match.group(1))
        
        # 下载数
        leechers_match = re.search(r'Leechers?[:\s]+(\d+)', text, re.IGNORECASE)
        if leechers_match:
            result['leechers'] = int(leechers_match.group(1))
        
        # 查找上传日期
        date_elements = item.xpath('.//time | .//span[contains(@class, "time")] | .//div[contains(@class, "time")]')
        if date_elements:
            date_text = date_elements[0].text_content().strip()
            result['upload_date'] = self.parse_date(date_text)
        else:
            # 尝试从文本中提取日期
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
            if date_match:
                result['upload_date'] = self.parse_date(date_match.group(1))
        
        # 如果没有找到标题，跳过这个结果
        if 'title' not in result:
            return {}
        
        # 设置默认值
        result.setdefault('seeders', 0)
        result.setdefault('leechers', 0)
        result.setdefault('size_gb', 0.0)
        result.setdefault('site', self.site_name)
        
        return result
    
    def parse_torrent_detail(self, html: str) -> Dict[str, Any]:
        """
        解析Unit3D种子详情页面
        
        Args:
            html: HTML内容
        
        Returns:
            解析后的详情字典
        """
        result = {}
        
        try:
            tree = etree.HTML(html)
            if tree is None:
                return result
            
            # 标题通常在 <h1> 或特定的div中
            title_elements = tree.xpath('//h1 | //div[contains(@class, "title")] | //div[contains(@id, "title")]')
            for elem in title_elements:
                text = elem.text_content().strip()
                if text and len(text) > 5:
                    result['title'] = text
                    break
            
            # 描述
            desc_elements = tree.xpath('//div[contains(@class, "description")] | //div[contains(@id, "description")] | //div[@id="kdescr"]')
            if desc_elements:
                result['description'] = desc_elements[0].text_content().strip()
            
            # 磁力链接
            magnet_links = tree.xpath('//a[starts-with(@href, "magnet:")]')
            if magnet_links:
                result['magnet_link'] = magnet_links[0].get('href', '')
                result['info_hash'] = self.extract_info_hash(result['magnet_link'])
            
            # 种子下载链接
            download_links = tree.xpath('//a[contains(@href, "download")] | //a[contains(@class, "download")]')
            if download_links:
                href = download_links[0].get('href', '')
                result['torrent_url'] = urljoin(self.base_url, href)
            
            # 提取详细信息
            info_text = tree.text_content()
            
            # 提取大小
            size_match = re.search(r'Size[:\s]+([\d.]+)\s*([KMGT]?B)', info_text, re.IGNORECASE)
            if size_match:
                result['size_gb'] = self.parse_size(f"{size_match.group(1)} {size_match.group(2)}")
            
            # 提取做种数
            seeders_match = re.search(r'Seeders?[:\s]+(\d+)', info_text, re.IGNORECASE)
            if seeders_match:
                result['seeders'] = int(seeders_match.group(1))
            
            # 提取下载数
            leechers_match = re.search(r'Leechers?[:\s]+(\d+)', info_text, re.IGNORECASE)
            if leechers_match:
                result['leechers'] = int(leechers_match.group(1))
            
            # 上传者
            uploader_links = tree.xpath('//a[contains(@href, "users/") or contains(@href, "user/")]')
            if uploader_links:
                result['uploader'] = uploader_links[0].text_content().strip()
            
            # 分类
            category_elements = tree.xpath('//div[contains(@class, "category")] | //span[contains(@class, "category")] | //a[contains(@class, "category")]')
            if category_elements:
                result['category'] = category_elements[0].text_content().strip()
        
        except Exception as e:
            logger.error(f"解析Unit3D种子详情失败: {e}")
        
        return result

