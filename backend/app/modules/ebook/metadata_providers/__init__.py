"""
电子书元数据提供者模块

提供可插拔的元数据增强能力，支持从多个数据源获取电子书元数据。
"""

from typing import Protocol, Optional
from app.models.ebook import EBook


class EBookMetadataUpdate:
    """元数据更新建议"""
    
    def __init__(
        self,
        title: Optional[str] = None,
        original_title: Optional[str] = None,
        author: Optional[str] = None,
        series: Optional[str] = None,
        volume_index: Optional[str] = None,
        language: Optional[str] = None,
        publish_year: Optional[int] = None,
        isbn: Optional[str] = None,
        tags: Optional[str] = None,
        description: Optional[str] = None,
        cover_url: Optional[str] = None,
        provider_name: Optional[str] = None,
        confidence: float = 0.0,  # 0.0 - 1.0，表示元数据的可信度
    ):
        self.title = title
        self.original_title = original_title
        self.author = author
        self.series = series
        self.volume_index = volume_index
        self.language = language
        self.publish_year = publish_year
        self.isbn = isbn
        self.tags = tags
        self.description = description
        self.cover_url = cover_url
        self.provider_name = provider_name
        self.confidence = confidence
    
    def to_dict(self) -> dict:
        """转换为字典，仅包含非 None 的字段"""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result


class EBookMetadataProvider(Protocol):
    """
    电子书元数据提供者协议
    
    所有元数据提供者必须实现此接口。
    """
    
    async def enrich_metadata(self, ebook: EBook) -> Optional[EBookMetadataUpdate]:
        """
        基于现有电子书信息，获取增强的元数据
        
        Args:
            ebook: 当前的电子书对象（可能只有部分字段有值）
        
        Returns:
            EBookMetadataUpdate 对象，包含建议更新的字段；如果无法获取元数据，返回 None
        """
        ...

