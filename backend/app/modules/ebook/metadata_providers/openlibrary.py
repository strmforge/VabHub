"""
Open Library 元数据提供者

从 Open Library 公共 API 获取电子书元数据。
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from loguru import logger
import httpx

from app.core.config import settings
from app.models.ebook import EBook
from . import EBookMetadataUpdate, EBookMetadataProvider


class OpenLibraryMetadataProvider:
    """
    Open Library 元数据提供者
    
    通过 Open Library 公共 API 获取电子书元数据。
    优先使用 ISBN 查询，如果没有 ISBN 则使用 title+author 搜索。
    """
    
    BASE_URL = "https://openlibrary.org"
    
    def __init__(self):
        self.name = "openlibrary"
        self.timeout = settings.SMART_EBOOK_METADATA_TIMEOUT
    
    async def enrich_metadata(self, ebook: EBook) -> Optional[EBookMetadataUpdate]:
        """
        从 Open Library 获取增强的元数据
        
        Args:
            ebook: 当前的电子书对象
        
        Returns:
            EBookMetadataUpdate 对象，如果无法获取则返回 None
        """
        try:
            # 优先使用 ISBN 查询
            if ebook.isbn:
                # 清理 ISBN（移除连字符和空格）
                clean_isbn = re.sub(r'[-\s]', '', ebook.isbn)
                if clean_isbn:
                    return await self._fetch_by_isbn(clean_isbn, ebook)
            
            # 如果没有 ISBN，使用 title+author 搜索
            if ebook.title:
                return await self._search_by_title_author(ebook)
            
            logger.debug("OpenLibraryMetadataProvider: 缺少必要信息（ISBN 或 title），无法查询")
            return None
            
        except Exception as e:
            logger.warning(f"OpenLibraryMetadataProvider: 获取元数据失败: {e}")
            return None
    
    async def _fetch_by_isbn(self, isbn: str, ebook: EBook) -> Optional[EBookMetadataUpdate]:
        """
        通过 ISBN 查询图书信息
        
        Args:
            isbn: ISBN 号码
            ebook: 当前电子书对象（用于补充信息）
        
        Returns:
            EBookMetadataUpdate 对象，如果查询失败返回 None
        """
        url = f"{self.BASE_URL}/isbn/{isbn}.json"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    logger.debug(f"OpenLibraryMetadataProvider: ISBN {isbn} 在 Open Library 中未找到")
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                return self._parse_edition_data(data, ebook)
                
        except httpx.TimeoutException:
            logger.warning(f"OpenLibraryMetadataProvider: 查询 ISBN {isbn} 超时")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"OpenLibraryMetadataProvider: HTTP 错误 {e.response.status_code} 查询 ISBN {isbn}")
            return None
        except Exception as e:
            logger.warning(f"OpenLibraryMetadataProvider: 查询 ISBN {isbn} 失败: {e}")
            return None
    
    async def _search_by_title_author(self, ebook: EBook) -> Optional[EBookMetadataUpdate]:
        """
        通过 title+author 搜索图书
        
        Args:
            ebook: 当前电子书对象
        
        Returns:
            EBookMetadataUpdate 对象，如果搜索失败返回 None
        """
        # 构建搜索参数
        params = {"title": ebook.title}
        if ebook.author:
            params["author"] = ebook.author
        
        url = f"{self.BASE_URL}/search.json"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # 获取第一个结果（通常是最相关的）
                docs = data.get("docs", [])
                if not docs:
                    logger.debug(f"OpenLibraryMetadataProvider: 未找到匹配的图书: {ebook.title}")
                    return None
                
                # 使用第一个结果
                first_result = docs[0]
                
                # 如果有 edition_key，尝试获取更详细的 edition 信息
                edition_keys = first_result.get("edition_key", [])
                if edition_keys:
                    edition_key = edition_keys[0]
                    edition_data = await self._fetch_edition(edition_key)
                    if edition_data:
                        return self._parse_edition_data(edition_data, ebook)
                
                # 否则直接解析搜索结果
                return self._parse_search_result(first_result, ebook)
                
        except httpx.TimeoutException:
            logger.warning(f"OpenLibraryMetadataProvider: 搜索超时: {ebook.title}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"OpenLibraryMetadataProvider: HTTP 错误 {e.response.status_code} 搜索: {ebook.title}")
            return None
        except Exception as e:
            logger.warning(f"OpenLibraryMetadataProvider: 搜索失败: {ebook.title}: {e}")
            return None
    
    async def _fetch_edition(self, edition_key: str) -> Optional[Dict[str, Any]]:
        """
        获取 edition 详细信息
        
        Args:
            edition_key: edition key（例如 "OL123456M"）
        
        Returns:
            edition 数据字典，如果获取失败返回 None
        """
        url = f"{self.BASE_URL}/books/{edition_key}.json"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.debug(f"OpenLibraryMetadataProvider: 获取 edition {edition_key} 失败: {e}")
            return None
    
    def _parse_edition_data(self, data: Dict[str, Any], ebook: EBook) -> EBookMetadataUpdate:
        """
        解析 edition 数据为 EBookMetadataUpdate
        
        Args:
            data: Open Library edition 数据
            ebook: 当前电子书对象（用于补充信息）
        
        Returns:
            EBookMetadataUpdate 对象
        """
        update = EBookMetadataUpdate(
            provider_name=self.name,
            confidence=0.8,  # ISBN 查询结果可信度较高
        )
        
        # 标题
        title = data.get("title")
        if title:
            # 如果有 subtitle，可以拼接到 title 或写入 description
            subtitle = data.get("subtitle")
            if subtitle:
                update.title = f"{title}: {subtitle}"
            else:
                update.title = title
        
        # 原始标题（如果有）
        if not ebook.original_title:
            # Open Library 可能没有单独的 original_title，这里可以留空或使用 title
            pass
        
        # 作者
        authors = data.get("authors", [])
        if authors and not ebook.author:
            # 尝试获取作者名称
            author_names = []
            for author_ref in authors:
                if isinstance(author_ref, dict):
                    author_key = author_ref.get("key", "")
                    if author_key:
                        # 简化处理：从 key 中提取名称（实际应该再请求一次获取完整信息）
                        # 例如 "/authors/OL123456A" -> "OL123456A"
                        author_name = author_key.split("/")[-1]
                        # 如果有 name 字段，直接使用
                        if "name" in author_ref:
                            author_names.append(author_ref["name"])
                        else:
                            # 否则尝试从 key 推断（这里简化处理）
                            pass
            
            # 如果搜索结果中有 author_name 字段，使用它
            if not author_names and "author_name" in data:
                author_names = data.get("author_name", [])
            
            if author_names:
                update.author = ", ".join(author_names[:3])  # 最多取前3个作者
        
        # 系列（如果有）
        if not ebook.series:
            # Open Library 可能没有直接的 series 字段，可以从 subjects 或其他字段推断
            # 这里暂时留空，后续可以扩展
            pass
        
        # 出版年份
        if not ebook.publish_year:
            publish_date = data.get("publish_date")
            if publish_date:
                # 尝试提取年份
                year_match = re.search(r'\d{4}', str(publish_date))
                if year_match:
                    try:
                        update.publish_year = int(year_match.group())
                    except ValueError:
                        pass
            
            # 如果没有 publish_date，尝试 first_publish_year
            if not update.publish_year:
                first_publish_year = data.get("first_publish_year")
                if first_publish_year:
                    try:
                        update.publish_year = int(first_publish_year)
                    except ValueError:
                        pass
        
        # ISBN
        if not ebook.isbn:
            # 尝试获取 ISBN-13 或 ISBN-10
            isbn_13 = data.get("isbn_13", [])
            isbn_10 = data.get("isbn_10", [])
            
            if isbn_13:
                update.isbn = isbn_13[0]
            elif isbn_10:
                update.isbn = isbn_10[0]
        
        # 描述
        if not ebook.description:
            description = data.get("description")
            if description:
                # description 可能是字符串或对象（带 value 字段）
                if isinstance(description, dict):
                    description_text = description.get("value", "")
                else:
                    description_text = str(description)
                
                # 清理 HTML 标签（如果有）
                description_text = re.sub(r'<[^>]+>', '', description_text)
                update.description = description_text.strip()
        
        # 封面
        if not ebook.cover_url:
            covers = data.get("covers", [])
            if covers:
                cover_id = covers[0]
                update.cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        
        # 标签（subjects）
        if not ebook.tags:
            subjects = data.get("subjects", [])
            subject_places = data.get("subject_places", [])
            subject_people = data.get("subject_people", [])
            
            tags_list = []
            
            # 添加 subjects
            if subjects:
                tags_list.extend([str(s) for s in subjects[:5]])  # 最多取前5个
            
            # 添加 subject_places
            if subject_places:
                tags_list.extend([f"地点:{s}" for s in subject_places[:3]])
            
            # 添加 subject_people
            if subject_people:
                tags_list.extend([f"人物:{s}" for s in subject_people[:3]])
            
            if tags_list:
                update.tags = ", ".join(tags_list)
        
        # 语言
        if not ebook.language:
            languages = data.get("languages", [])
            if languages:
                # languages 通常是 key 列表，例如 ["/languages/eng"]
                lang_key = languages[0] if isinstance(languages[0], str) else languages[0].get("key", "")
                if lang_key:
                    # 简化映射：eng -> en, chi -> zh-CN
                    lang_code = lang_key.split("/")[-1]
                    lang_map = {
                        "eng": "en",
                        "chi": "zh-CN",
                        "jpn": "ja",
                        "fre": "fr",
                        "ger": "de",
                        "spa": "es",
                    }
                    update.language = lang_map.get(lang_code, lang_code)
        
        logger.debug(f"OpenLibraryMetadataProvider: 成功获取元数据: {update.title or ebook.title}")
        return update
    
    def _parse_search_result(self, result: Dict[str, Any], ebook: EBook) -> EBookMetadataUpdate:
        """
        解析搜索结果数据为 EBookMetadataUpdate
        
        Args:
            result: Open Library 搜索结果数据
            ebook: 当前电子书对象
        
        Returns:
            EBookMetadataUpdate 对象
        """
        update = EBookMetadataUpdate(
            provider_name=self.name,
            confidence=0.7,  # 搜索结果可信度略低于 ISBN 查询
        )
        
        # 标题
        title = result.get("title")
        if title:
            update.title = title
        
        # 作者
        if not ebook.author:
            author_names = result.get("author_name", [])
            if author_names:
                update.author = ", ".join(author_names[:3])
        
        # 出版年份
        if not ebook.publish_year:
            first_publish_year = result.get("first_publish_year")
            if first_publish_year:
                try:
                    update.publish_year = int(first_publish_year)
                except ValueError:
                    pass
        
        # ISBN
        if not ebook.isbn:
            isbn = result.get("isbn", [])
            if isbn:
                update.isbn = isbn[0]
        
        # 封面
        if not ebook.cover_url:
            cover_i = result.get("cover_i")
            if cover_i:
                update.cover_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
        
        # 标签
        if not ebook.tags:
            subject = result.get("subject", [])
            if subject:
                update.tags = ", ".join([str(s) for s in subject[:5]])
        
        logger.debug(f"OpenLibraryMetadataProvider: 从搜索结果获取元数据: {update.title or ebook.title}")
        return update

