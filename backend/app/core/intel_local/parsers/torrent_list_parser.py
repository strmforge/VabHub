"""
种子列表页面解析（Phase 9）
用于从 PT 站点的种子列表页面（如 browse.php, torrents.php）解析种子信息
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import re
from bs4 import BeautifulSoup
from loguru import logger

from ..site_profiles import IntelSiteProfile


@dataclass
class ParsedTorrentRow:
    """解析后的种子行数据"""
    torrent_id: str
    title_raw: str
    category: str | None = None
    is_hr: bool = False
    is_free: bool = False
    is_half_free: bool = False
    size_bytes: int | None = None
    seeders: int = 0
    leechers: int = 0
    completed: int | None = None
    published_at: datetime | None = None


def parse_torrent_list_page_generic(
    *,
    site: str,
    html: str,
    profile: IntelSiteProfile
) -> List[ParsedTorrentRow]:
    """
    通用种子列表解析（NexusPHP 格式）
    
    适用于大多数 NexusPHP 站点的 browse.php 或 torrents.php 页面
    """
    rows = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找种子列表表格（通常是包含 "torrent" 或 "种子" 关键词的表格）
        tables = soup.find_all("table")
        torrent_table = None
        
        for table in tables:
            # 检查表头是否包含种子相关关键词
            headers = table.find_all(["th", "td"])
            if len(headers) < 3:
                continue
            header_text = " ".join([h.get_text(strip=True) for h in headers[:5]])
            if any(keyword in header_text.lower() for keyword in ["torrent", "种子", "title", "标题", "size", "大小"]):
                torrent_table = table
                break
        
        if not torrent_table:
            logger.debug(f"LocalIntel: 站点 {site} 种子列表页面未找到种子表格")
            return rows
        
        # 解析表格行（跳过表头）
        tbody = torrent_table.find("tbody") or torrent_table
        trs = tbody.find_all("tr", recursive=False)
        
        for tr in trs[1:]:  # 跳过第一行（通常是表头）
            tds = tr.find_all(["td", "th"])
            if len(tds) < 3:
                continue
            
            try:
                # 提取种子ID和标题（通常在链接中）
                torrent_id = None
                title_raw = None
                
                links = tr.find_all("a", href=True)
                for link in links:
                    href = link.get("href", "")
                    # 匹配类似 detail.php?id=12345 或 torrents.php?id=12345 的链接
                    match = re.search(r"[?&]id=(\d+)", href)
                    if match:
                        torrent_id = match.group(1)
                        title_raw = link.get_text(strip=True)
                        break
                
                if not torrent_id or not title_raw:
                    continue
                
                # 提取分类（通常在第二列或第一列）
                category = None
                if len(tds) > 1:
                    category_text = tds[0].get_text(strip=True)
                    # 简单的分类提取（可以根据实际站点调整）
                    category = category_text if category_text and len(category_text) < 50 else None
                
                # 提取 HR/Free 标记（通常在标题附近或特殊列）
                is_hr = False
                is_free = False
                is_half_free = False
                
                # 检查标题或整行是否包含 HR/Free 标记
                row_text = tr.get_text()
                if any(marker in row_text.lower() for marker in ["hr", "h&r", "hit&run"]):
                    is_hr = True
                if "free" in row_text.lower() or "免费" in row_text:
                    if "50%" in row_text or "半" in row_text:
                        is_half_free = True
                    else:
                        is_free = True
                
                # 提取大小（通常在 "大小" 或 "Size" 列）
                size_bytes = None
                for td in tds:
                    text = td.get_text(strip=True)
                    # 匹配大小格式：如 "10.5 GB", "1.2 TB", "500 MB"
                    size_match = re.search(r"(\d+(?:\.\d+)?)\s*(GB|TB|MB|KB)", text, re.I)
                    if size_match:
                        size_value = float(size_match.group(1))
                        unit = size_match.group(2).upper()
                        if unit == "TB":
                            size_bytes = int(size_value * 1024 * 1024 * 1024 * 1024)
                        elif unit == "GB":
                            size_bytes = int(size_value * 1024 * 1024 * 1024)
                        elif unit == "MB":
                            size_bytes = int(size_value * 1024 * 1024)
                        elif unit == "KB":
                            size_bytes = int(size_value * 1024)
                        break
                
                # 提取做种数、下载数、完成数
                seeders = 0
                leechers = 0
                completed = None
                
                for td in tds:
                    text = td.get_text(strip=True)
                    # 匹配数字（可能是做种数、下载数等）
                    numbers = re.findall(r"\d+", text)
                    if numbers:
                        # 通常做种数在前，下载数在后
                        if seeders == 0 and len(numbers) > 0:
                            seeders = int(numbers[0])
                        if leechers == 0 and len(numbers) > 1:
                            leechers = int(numbers[1])
                        if completed is None and len(numbers) > 2:
                            completed = int(numbers[2])
                
                # 提取发布时间（通常在最后一列或倒数第二列）
                published_at = None
                for td in tds[-2:]:  # 检查最后两列
                    text = td.get_text(strip=True)
                    # 尝试解析日期时间（格式可能多样）
                    # 这里简化处理，实际可能需要根据站点格式调整
                    date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
                    if date_match:
                        try:
                            date_str = date_match.group(1).replace("/", "-")
                            published_at = datetime.strptime(date_str, "%Y-%m-%d")
                        except:
                            pass
                
                rows.append(
                    ParsedTorrentRow(
                        torrent_id=torrent_id,
                        title_raw=title_raw,
                        category=category,
                        is_hr=is_hr,
                        is_free=is_free,
                        is_half_free=is_half_free,
                        size_bytes=size_bytes,
                        seeders=seeders,
                        leechers=leechers,
                        completed=completed,
                        published_at=published_at,
                    )
                )
            except Exception as e:
                logger.warning(f"LocalIntel: 解析站点 {site} 种子行失败: {e}")
                continue
        
        logger.info(f"LocalIntel: 站点 {site} 种子列表解析完成，找到 {len(rows)} 条记录")
    except Exception as e:
        logger.error(f"LocalIntel: 解析站点 {site} 种子列表页面失败: {e}", exc_info=True)
    
    return rows


def parse_torrent_list_page_hdsky(
    *,
    site: str,
    html: str,
    profile: IntelSiteProfile
) -> List[ParsedTorrentRow]:
    """
    HDsky 种子列表解析（基于通用解析，可扩展站点特定逻辑）
    """
    # HDsky 使用标准的 NexusPHP 格式，可以直接使用通用解析
    return parse_torrent_list_page_generic(site=site, html=html, profile=profile)

