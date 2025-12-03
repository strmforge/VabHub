"""
RSS解析器
"""

import hashlib
import feedparser
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
import httpx


class RSSItem:
    """RSS项数据模型"""
    
    def __init__(self, title: str, link: str, description: str = "", pub_date: Optional[datetime] = None):
        self.title = title
        self.link = link
        self.description = description
        self.pub_date = pub_date
        self.hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """生成RSS项的哈希值（用于去重）"""
        content = f"{self.title}{self.link}".encode('utf-8')
        return hashlib.md5(content).hexdigest()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "title": self.title,
            "link": self.link,
            "description": self.description,
            "pub_date": self.pub_date.isoformat() if self.pub_date else None,
            "hash": self.hash
        }


class RSSParser:
    """RSS解析器"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = 1  # 重试延迟（秒）
    
    async def parse(self, url: str) -> List[RSSItem]:
        """
        解析RSS Feed（带重试机制）
        
        Args:
            url: RSS Feed URL
            
        Returns:
            RSS项列表
        """
        import asyncio
        last_error = None
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                # 使用httpx异步获取RSS Feed
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    content = response.text
                    break  # 成功获取，退出重试循环
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"RSS Feed请求超时，重试 {attempt + 1}/{self.max_retries}: {url}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # 指数退避
                else:
                    logger.error(f"RSS Feed请求超时，已达最大重试次数: {url}")
                    raise
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    # 服务器错误，可以重试
                    logger.warning(f"RSS Feed服务器错误，重试 {attempt + 1}/{self.max_retries}: {url}, 状态码: {e.response.status_code}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    # 客户端错误，不重试
                    logger.error(f"RSS Feed请求失败: {url}, 状态码: {e.response.status_code}")
                    raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"RSS Feed请求失败，重试 {attempt + 1}/{self.max_retries}: {url}, 错误: {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"RSS Feed请求失败，已达最大重试次数: {url}, 错误: {e}")
                    raise
        else:
            # 所有重试都失败
            if last_error:
                raise last_error
            else:
                raise Exception(f"RSS Feed请求失败: {url}")
        
        # 使用feedparser解析
        try:
            feed = feedparser.parse(content)
            
            items = []
            for entry in feed.entries:
                try:
                    # 解析发布日期
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    # 获取描述
                    description = ""
                    if hasattr(entry, 'description'):
                        description = entry.description
                    elif hasattr(entry, 'summary'):
                        description = entry.summary
                    
                    # 获取链接
                    link = entry.link if hasattr(entry, 'link') else ""
                    
                    # 创建RSS项
                    item = RSSItem(
                        title=entry.title,
                        link=link,
                        description=description,
                        pub_date=pub_date
                    )
                    items.append(item)
                except Exception as e:
                    logger.warning(f"解析RSS项失败: {e}, entry: {entry.get('title', 'Unknown')}")
                    continue
            
            logger.info(f"成功解析RSS Feed: {url}, 获取 {len(items)} 项")
            return items
            
        except Exception as e:
            logger.error(f"解析RSS Feed内容失败: {url}, 错误: {e}")
            raise
    
    async def check_updates(
        self, 
        url: str, 
        last_item_hash: Optional[str] = None
    ) -> List[RSSItem]:
        """
        检查RSS Feed更新（增量更新）
        
        Args:
            url: RSS Feed URL
            last_item_hash: 最后处理的RSS项哈希
            
        Returns:
            新的RSS项列表
        """
        try:
            items = await self.parse(url)
            
            # 如果没有最后处理的哈希，返回所有项
            if not last_item_hash:
                return items
            
            # 只返回新的项（哈希不在已处理列表中的项）
            new_items = []
            for item in items:
                if item.hash != last_item_hash:
                    new_items.append(item)
                else:
                    # 找到最后处理的项，后续项都是新的
                    break
            
            logger.info(f"RSS Feed更新检查: {url}, 新项数: {len(new_items)}")
            return new_items
            
        except Exception as e:
            logger.error(f"检查RSS Feed更新失败: {url}, 错误: {e}")
            raise

