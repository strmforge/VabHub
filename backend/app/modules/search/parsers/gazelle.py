"""
Gazelle框架解析器
支持使用Gazelle框架的PT站点（如PTP、BTN等）
"""
from typing import List, Dict, Any
from lxml import etree
from loguru import logger
import re
from urllib.parse import urljoin, urlparse

from .base import ParserBase


class GazelleParser(ParserBase):
    """Gazelle框架解析器"""
    
    def __init__(self, site_name: str = "", base_url: str = ""):
        """
        初始化Gazelle解析器
        
        Args:
            site_name: 站点名称
            base_url: 站点基础URL
        """
        super().__init__(site_name)
        self.base_url = base_url
    
    def parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """
        解析Gazelle搜索结果页面
        
        Gazelle通常使用表格显示搜索结果
        """
        results = []
        
        try:
            # 使用lxml解析HTML
            tree = etree.HTML(html)
            if tree is None:
                return results
            
            # Gazelle搜索结果通常在 <table class="torrent_table"> 中
            # 或者 <table id="torrent_table"> 中
            tables = tree.xpath('//table[contains(@class, "torrent") or contains(@id, "torrent")]')
            
            if not tables:
                # 尝试查找任何包含torrent链接的表格
                tables = tree.xpath('//table//a[contains(@href, "torrents.php")]')
                if tables:
                    # 找到父表格
                    parent = tables[0].getparent()
                    while parent is not None and parent.tag != 'table':
                        parent = parent.getparent()
                    if parent is not None:
                        tables = [parent]
            
            for table in tables:
                # 查找所有行（跳过表头）
                rows = table.xpath('.//tr[position() > 1]')
                
                for row in rows:
                    try:
                        result = self._parse_torrent_row(row)
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.debug(f"解析Gazelle行失败: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"解析Gazelle搜索结果失败: {e}")
        
        return results
    
    def _parse_torrent_row(self, row) -> Dict[str, Any]:
        """
        解析单个种子行
        
        Args:
            row: lxml元素
        
        Returns:
            解析后的结果字典
        """
        result = {}
        
        # 查找标题链接
        title_links = row.xpath('.//a[contains(@href, "torrents.php?id=") or contains(@href, "torrents.php?torrentid=")]')
        if title_links:
            title_link = title_links[0]
            result['title'] = title_link.text_content().strip()
            href = title_link.get('href', '')
            if href:
                result['torrent_url'] = urljoin(self.base_url, href)
                # 提取torrent ID
                match = re.search(r'[?&](?:id|torrentid)=(\d+)', href)
                if match:
                    result['torrent_id'] = match.group(1)
        
        # 查找磁力链接
        magnet_links = row.xpath('.//a[starts-with(@href, "magnet:")]')
        if magnet_links:
            result['magnet_link'] = magnet_links[0].get('href', '')
            result['info_hash'] = self.extract_info_hash(result['magnet_link'])
        
        # 查找大小
        size_cells = row.xpath('.//td[contains(@class, "size") or contains(@class, "number_column")]')
        for cell in size_cells:
            size_text = cell.text_content().strip()
            if any(unit in size_text.upper() for unit in ['GB', 'MB', 'TB', 'KB']):
                result['size_gb'] = self.parse_size(size_text)
                break
        
        # 查找做种数和下载数
        # Gazelle通常在特定的列中显示这些信息
        cells = row.xpath('.//td')
        for i, cell in enumerate(cells):
            text = cell.text_content().strip()
            # 做种数通常是一个数字
            if re.match(r'^\d+$', text) and i > 0:
                # 根据位置判断是做种数还是下载数
                # 通常做种数在下载数之前
                if 'seeders' not in result:
                    try:
                        result['seeders'] = int(text)
                    except ValueError:
                        pass
                elif 'leechers' not in result:
                    try:
                        result['leechers'] = int(text)
                    except ValueError:
                        pass
        
        # 查找上传日期
        date_cells = row.xpath('.//td[contains(@class, "time") or contains(@class, "date")]')
        if date_cells:
            date_text = date_cells[0].text_content().strip()
            result['upload_date'] = self.parse_date(date_text)
        
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
        解析Gazelle种子详情页面
        
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
            
            # 标题通常在 <h2> 或 <h3> 中
            title_elements = tree.xpath('//h2 | //h3 | //div[contains(@class, "title")]')
            for elem in title_elements:
                text = elem.text_content().strip()
                if text and len(text) > 5:  # 标题应该有一定长度
                    result['title'] = text
                    break
            
            # 描述
            desc_elements = tree.xpath('//div[contains(@class, "description")] | //div[contains(@id, "description")]')
            if desc_elements:
                result['description'] = desc_elements[0].text_content().strip()
            
            # 磁力链接
            magnet_links = tree.xpath('//a[starts-with(@href, "magnet:")]')
            if magnet_links:
                result['magnet_link'] = magnet_links[0].get('href', '')
                result['info_hash'] = self.extract_info_hash(result['magnet_link'])
            
            # 种子下载链接
            download_links = tree.xpath('//a[contains(@href, "torrents.php?action=download")]')
            if download_links:
                href = download_links[0].get('href', '')
                result['torrent_url'] = urljoin(self.base_url, href)
            
            # 大小、做种数、下载数等信息
            # 通常在详情页面的特定位置
            info_sections = tree.xpath('//div[contains(@class, "stats")] | //div[contains(@class, "info")]')
            for section in info_sections:
                text = section.text_content()
                
                # 提取大小
                size_match = re.search(r'Size[:\s]+([\d.]+)\s*([KMGT]?B)', text, re.IGNORECASE)
                if size_match:
                    result['size_gb'] = self.parse_size(f"{size_match.group(1)} {size_match.group(2)}")
                
                # 提取做种数
                seeders_match = re.search(r'Seeders[:\s]+(\d+)', text, re.IGNORECASE)
                if seeders_match:
                    result['seeders'] = int(seeders_match.group(1))
                
                # 提取下载数
                leechers_match = re.search(r'Leechers[:\s]+(\d+)', text, re.IGNORECASE)
                if leechers_match:
                    result['leechers'] = int(leechers_match.group(1))
            
            # 上传者
            uploader_links = tree.xpath('//a[contains(@href, "user.php?id=")]')
            if uploader_links:
                result['uploader'] = uploader_links[0].text_content().strip()
            
            # 分类
            category_elements = tree.xpath('//div[contains(@class, "category")] | //span[contains(@class, "category")]')
            if category_elements:
                result['category'] = category_elements[0].text_content().strip()
        
        except Exception as e:
            logger.error(f"解析Gazelle种子详情失败: {e}")
        
        return result

