"""
Nexus PHP框架解析器
支持使用Nexus PHP框架的PT站点
"""
from typing import List, Dict, Any
from lxml import etree
from loguru import logger
import re
from urllib.parse import urljoin

from .base import ParserBase


class NexusPHPParser(ParserBase):
    """Nexus PHP框架解析器"""
    
    def __init__(self, site_name: str = "", base_url: str = ""):
        """
        初始化Nexus PHP解析器
        
        Args:
            site_name: 站点名称
            base_url: 站点基础URL
        """
        super().__init__(site_name)
        self.base_url = base_url
    
    def parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """
        解析Nexus PHP搜索结果页面
        
        Nexus PHP通常使用表格显示搜索结果
        """
        results = []
        
        try:
            tree = etree.HTML(html)
            if tree is None:
                return results
            
            # Nexus PHP搜索结果通常在表格中
            # 查找包含torrent链接的表格
            tables = tree.xpath('//table[.//a[contains(@href, "details.php") or contains(@href, "download.php")]]')
            
            if not tables:
                # 尝试查找任何表格
                tables = tree.xpath('//table')
            
            for table in tables:
                rows = table.xpath('.//tr[position() > 1]')
                
                for row in rows:
                    try:
                        result = self._parse_torrent_row(row)
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.debug(f"解析Nexus PHP行失败: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"解析Nexus PHP搜索结果失败: {e}")
        
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
        
        # 查找标题链接（Nexus PHP通常使用details.php）
        title_links = row.xpath('.//a[contains(@href, "details.php?id=")]')
        if not title_links:
            # 尝试其他可能的链接格式
            title_links = row.xpath('.//a[contains(@href, "torrents.php?id=")]')
        
        if title_links:
            title_link = title_links[0]
            result['title'] = title_link.text_content().strip()
            href = title_link.get('href', '')
            if href:
                result['torrent_url'] = urljoin(self.base_url, href)
                # 提取torrent ID
                match = re.search(r'[?&]id=(\d+)', href)
                if match:
                    result['torrent_id'] = match.group(1)
        
        # 查找磁力链接
        magnet_links = row.xpath('.//a[starts-with(@href, "magnet:")]')
        if magnet_links:
            result['magnet_link'] = magnet_links[0].get('href', '')
            result['info_hash'] = self.extract_info_hash(result['magnet_link'])
        
        # 查找下载链接
        download_links = row.xpath('.//a[contains(@href, "download.php?id=")]')
        if download_links:
            href = download_links[0].get('href', '')
            if not result.get('torrent_url'):
                result['torrent_url'] = urljoin(self.base_url, href)
        
        # 查找大小（Nexus PHP通常在特定列中）
        cells = row.xpath('.//td')
        for cell in cells:
            text = cell.text_content().strip()
            # 检查是否包含大小单位
            if any(unit in text.upper() for unit in ['GB', 'MB', 'TB', 'KB', 'B']):
                size_match = re.search(r'([\d.]+)\s*([KMGT]?B)', text.upper())
                if size_match:
                    result['size_gb'] = self.parse_size(f"{size_match.group(1)} {size_match.group(2)}")
                    break
        
        # 查找做种数和下载数
        # Nexus PHP通常在数字列中显示
        for i, cell in enumerate(cells):
            text = cell.text_content().strip()
            # 检查是否是纯数字
            if re.match(r'^\d+$', text):
                try:
                    num = int(text)
                    # 根据位置和上下文判断
                    # 通常做种数在下载数之前
                    if 'seeders' not in result:
                        result['seeders'] = num
                    elif 'leechers' not in result:
                        result['leechers'] = num
                except ValueError:
                    pass
        
        # 查找上传日期
        # Nexus PHP通常显示相对时间（如"2天前"）或绝对时间
        for cell in cells:
            text = cell.text_content().strip()
            # 检查是否包含日期相关关键词
            if any(keyword in text.lower() for keyword in ['ago', '前', '年', '月', '日', '-', '/']):
                result['upload_date'] = self.parse_date(text)
                break
        
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
        解析Nexus PHP种子详情页面
        
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
            download_links = tree.xpath('//a[contains(@href, "download.php?id=")]')
            if download_links:
                href = download_links[0].get('href', '')
                result['torrent_url'] = urljoin(self.base_url, href)
            
            # 提取详细信息（大小、做种数、下载数等）
            # Nexus PHP通常在表格或特定div中显示
            info_text = tree.text_content()
            
            # 提取大小
            size_match = re.search(r'Size[:\s]+([\d.]+)\s*([KMGT]?B)', info_text, re.IGNORECASE)
            if size_match:
                result['size_gb'] = self.parse_size(f"{size_match.group(1)} {size_match.group(2)}")
            
            # 提取做种数
            seeders_match = re.search(r'Seeders[:\s]+(\d+)', info_text, re.IGNORECASE)
            if seeders_match:
                result['seeders'] = int(seeders_match.group(1))
            
            # 提取下载数
            leechers_match = re.search(r'Leechers[:\s]+(\d+)', info_text, re.IGNORECASE)
            if leechers_match:
                result['leechers'] = int(leechers_match.group(1))
            
            # 上传者
            uploader_links = tree.xpath('//a[contains(@href, "userdetails.php?id=")]')
            if uploader_links:
                result['uploader'] = uploader_links[0].text_content().strip()
            
            # 分类
            category_elements = tree.xpath('//div[contains(@class, "category")] | //span[contains(@class, "category")]')
            if category_elements:
                result['category'] = category_elements[0].text_content().strip()
        
        except Exception as e:
            logger.error(f"解析Nexus PHP种子详情失败: {e}")
        
        return result

