"""
HR 页面解析（Phase 4）
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Protocol
import re
from bs4 import BeautifulSoup
from loguru import logger

from ..site_profiles import IntelSiteProfile


@dataclass
class ParsedHRRow:
    torrent_id: str
    title: str | None
    required_seed_hours: float | None
    seeded_hours: float | None
    deadline: datetime | None
    raw_columns: dict[str, Any] | None = None


class HRHtmlParser(Protocol):
    def parse(self, *, site: str, html: str, profile: IntelSiteProfile) -> Iterable[ParsedHRRow]:
        ...


def parse_hr_page_generic(*, site: str, html: str, profile: IntelSiteProfile) -> list[ParsedHRRow]:
    """通用 HR 解析（NexusPHP 格式）。"""
    rows = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # NexusPHP 通常使用 <table> 包含 HR 列表
        # 查找包含 "HR" 或 "H&R" 的表格
        tables = soup.find_all("table")
        hr_table = None
        
        for table in tables:
            # 检查表头是否包含 HR 相关关键词
            headers = table.find_all(["th", "td"])
            header_text = " ".join([h.get_text(strip=True) for h in headers[:5]])
            if any(keyword in header_text.lower() for keyword in ["hr", "h&r", "hit", "run", "保种"]):
                hr_table = table
                break
        
        if not hr_table:
            logger.debug(f"LocalIntel: 站点 {site} HR 页面未找到 HR 表格")
            return rows
        
        # 解析表格行（跳过表头）
        tbody = hr_table.find("tbody") or hr_table
        trs = tbody.find_all("tr", recursive=False)
        
        for tr in trs[1:]:  # 跳过第一行（通常是表头）
            tds = tr.find_all(["td", "th"])
            if len(tds) < 3:
                continue
            
            try:
                # 尝试从第一列或链接中提取 torrent_id
                torrent_id = None
                title = None
                
                # 查找链接（通常包含 torrent_id）
                links = tr.find_all("a", href=True)
                for link in links:
                    href = link.get("href", "")
                    # 匹配类似 detail.php?id=12345 的链接
                    match = re.search(r"[?&]id=(\d+)", href)
                    if match:
                        torrent_id = match.group(1)
                        title = link.get_text(strip=True)
                        break
                
                if not torrent_id:
                    # 如果没找到，尝试从第一列提取
                    first_td = tds[0].get_text(strip=True)
                    match = re.search(r"(\d+)", first_td)
                    if match:
                        torrent_id = match.group(1)
                        title = first_td
                
                if not torrent_id:
                    continue
                
                # 解析保种时长和需求时长（通常在中间几列）
                required_hours = None
                seeded_hours = None
                deadline = None
                
                for td in tds[1:-1]:  # 跳过第一列和最后一列
                    text = td.get_text(strip=True)
                    
                    # 尝试解析时长（格式可能是 "72 小时" 或 "3 天"）
                    hour_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:小时|h|hour)", text, re.I)
                    if hour_match:
                        hours = float(hour_match.group(1))
                        if "需要" in text or "要求" in text or "required" in text.lower():
                            required_hours = hours
                        elif "已" in text or "seeded" in text.lower():
                            seeded_hours = hours
                    
                    # 尝试解析截止时间
                    date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s\d:]+)", text)
                    if date_match:
                        try:
                            date_str = date_match.group(1).replace("/", "-")
                            deadline = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            try:
                                deadline = datetime.strptime(date_str, "%Y-%m-%d")
                            except:
                                pass
                
                rows.append(
                    ParsedHRRow(
                        torrent_id=torrent_id,
                        title=title,
                        required_seed_hours=required_hours,
                        seeded_hours=seeded_hours,
                        deadline=deadline,
                        raw_columns={f"col_{i}": td.get_text(strip=True) for i, td in enumerate(tds)},
                    )
                )
            except Exception as e:
                logger.warning(f"LocalIntel: 解析站点 {site} HR 行失败: {e}")
                continue
        
        logger.info(f"LocalIntel: 站点 {site} HR 页面解析完成，找到 {len(rows)} 条记录")
        
    except Exception as e:
        logger.error(f"LocalIntel: 解析站点 {site} HR 页面失败: {e}", exc_info=True)
    
    return rows


def parse_hr_page_hdsky(*, site: str, html: str, profile: IntelSiteProfile) -> list[ParsedHRRow]:
    """HDsky HR 页面解析（基于 NexusPHP 通用解析）。"""
    # HDsky 使用标准的 NexusPHP HR 页面格式
    return parse_hr_page_generic(site=site, html=html, profile=profile)

