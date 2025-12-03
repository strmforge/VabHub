"""
站内信页面解析（Phase 4）
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol
import re
from bs4 import BeautifulSoup
from loguru import logger

from ..site_profiles import IntelSiteProfile


@dataclass
class ParsedInboxMessage:
    message_id: str
    subject: str | None
    body: str | None
    created_at: datetime | None


class InboxHtmlParser(Protocol):
    def parse(self, *, site: str, html: str, profile: IntelSiteProfile) -> Iterable[ParsedInboxMessage]:
        ...


def parse_inbox_page_generic(*, site: str, html: str, profile: IntelSiteProfile) -> list[ParsedInboxMessage]:
    """通用站内信解析（NexusPHP 格式）。"""
    messages = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # NexusPHP 站内信通常在表格中
        tables = soup.find_all("table")
        inbox_table = None
        
        for table in tables:
            # 查找包含 "消息"、"站内信"、"PM" 等关键词的表格
            headers = table.find_all(["th", "td"])
            header_text = " ".join([h.get_text(strip=True) for h in headers[:5]])
            if any(keyword in header_text.lower() for keyword in ["消息", "站内信", "pm", "message", "inbox"]):
                inbox_table = table
                break
        
        if not inbox_table:
            logger.debug(f"LocalIntel: 站点 {site} 站内信页面未找到消息表格")
            return messages
        
        # 解析表格行
        tbody = inbox_table.find("tbody") or inbox_table
        trs = tbody.find_all("tr", recursive=False)
        
        for tr in trs[1:]:  # 跳过表头
            tds = tr.find_all(["td", "th"])
            if len(tds) < 2:
                continue
            
            try:
                # 提取消息 ID（通常从链接或第一列）
                message_id = None
                subject = None
                body = None
                created_at = None
                
                # 查找链接（通常包含 message_id）
                links = tr.find_all("a", href=True)
                for link in links:
                    href = link.get("href", "")
                    # 匹配类似 messages.php?id=12345 或 viewmail.php?pmid=12345
                    match = re.search(r"[?&](?:id|pmid|mid)=(\d+)", href, re.I)
                    if match:
                        message_id = match.group(1)
                        subject = link.get_text(strip=True)
                        break
                
                if not message_id:
                    # 尝试从第一列提取
                    first_td = tds[0].get_text(strip=True)
                    match = re.search(r"(\d+)", first_td)
                    if match:
                        message_id = match.group(1)
                
                if not message_id:
                    # 使用行索引作为临时 ID
                    message_id = str(len(messages) + 1)
                
                # 提取主题（通常在第二列或链接文本）
                if not subject:
                    for i, td in enumerate(tds):
                        text = td.get_text(strip=True)
                        if text and len(text) > 3:
                            subject = text
                            break
                
                # 提取时间（通常在最后一列）
                for td in reversed(tds):
                    text = td.get_text(strip=True)
                    # 尝试解析时间格式
                    date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s\d:]+)", text)
                    if date_match:
                        try:
                            date_str = date_match.group(1).replace("/", "-")
                            created_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            try:
                                created_at = datetime.strptime(date_str, "%Y-%m-%d")
                            except:
                                pass
                        break
                
                # 提取正文（如果有展开的内容）
                # 通常站内信列表页只显示主题，正文需要点击查看
                # 这里先提取可能的预览文本
                for td in tds:
                    text = td.get_text(strip=True)
                    if text and text != subject and len(text) > 10:
                        body = text[:200]  # 限制长度
                        break
                
                messages.append(
                    ParsedInboxMessage(
                        message_id=message_id,
                        subject=subject or "（无主题）",
                        body=body,
                        created_at=created_at,
                    )
                )
            except Exception as e:
                logger.warning(f"LocalIntel: 解析站点 {site} 站内信行失败: {e}")
                continue
        
        logger.info(f"LocalIntel: 站点 {site} 站内信页面解析完成，找到 {len(messages)} 条消息")
        
    except Exception as e:
        logger.error(f"LocalIntel: 解析站点 {site} 站内信页面失败: {e}", exc_info=True)
    
    return messages


def parse_inbox_page_ttg(*, site: str, html: str, profile: IntelSiteProfile) -> list[ParsedInboxMessage]:
    """TTG 站内信解析（特殊处理无主题消息）。"""
    messages = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # TTG 使用特殊的站内信格式
        # 查找消息列表（可能是 div 或 table）
        message_items = soup.find_all(["tr", "div"], class_=re.compile(r"message|pm|inbox", re.I))
        
        if not message_items:
            # 回退到通用解析
            return parse_inbox_page_generic(site=site, html=html, profile=profile)
        
        for item in message_items:
            try:
                # TTG 可能有无主题的消息，需要从正文中提取信息
                message_id = None
                subject = None
                body = None
                created_at = None
                
                # 查找消息 ID
                links = item.find_all("a", href=True)
                for link in links:
                    href = link.get("href", "")
                    match = re.search(r"[?&](?:id|pmid|mid)=(\d+)", href, re.I)
                    if match:
                        message_id = match.group(1)
                        break
                
                if not message_id:
                    # 尝试从 data-id 属性获取
                    message_id_attr = item.get("data-id") or item.get("id")
                    if message_id_attr:
                        match = re.search(r"(\d+)", str(message_id_attr))
                        if match:
                            message_id = match.group(1)
                
                if not message_id:
                    message_id = str(len(messages) + 1)
                
                # 提取主题和正文
                text_content = item.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in text_content.split("\n") if line.strip()]
                
                if lines:
                    # 第一行可能是主题或时间
                    first_line = lines[0]
                    
                    # 检查是否是时间格式
                    date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s\d:]+)", first_line)
                    if date_match:
                        try:
                            date_str = date_match.group(1).replace("/", "-")
                            created_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                            subject = "（无主题）"  # TTG 可能有无主题消息
                            body = "\n".join(lines[1:]) if len(lines) > 1 else first_line
                        except:
                            subject = first_line
                            body = "\n".join(lines[1:]) if len(lines) > 1 else None
                    else:
                        subject = first_line
                        body = "\n".join(lines[1:]) if len(lines) > 1 else None
                
                # 如果没有主题，尝试从正文中提取
                if not subject or subject == "（无主题）":
                    # TTG 删种通知通常在正文中
                    if body and any(keyword in body for keyword in ["删除", "deleted", "刪除"]):
                        subject = "种子删除通知"
                
                messages.append(
                    ParsedInboxMessage(
                        message_id=message_id,
                        subject=subject or "（无主题）",
                        body=body,
                        created_at=created_at,
                    )
                )
            except Exception as e:
                logger.warning(f"LocalIntel: 解析站点 {site} TTG 站内信项失败: {e}")
                continue
        
        logger.info(f"LocalIntel: 站点 {site} TTG 站内信解析完成，找到 {len(messages)} 条消息")
        
    except Exception as e:
        logger.error(f"LocalIntel: 解析站点 {site} TTG 站内信页面失败: {e}", exc_info=True)
        # 失败时回退到通用解析
        return parse_inbox_page_generic(site=site, html=html, profile=profile)
    
    return messages

