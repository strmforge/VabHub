"""
电子书元数据服务

协调多个元数据提供者，为电子书提供增强的元数据信息。
"""

from typing import List, Optional
from loguru import logger
import asyncio

from app.core.config import settings
from app.models.ebook import EBook
from app.modules.ebook.metadata_providers import EBookMetadataUpdate, EBookMetadataProvider
from app.modules.ebook.metadata_providers.dummy import DummyMetadataProvider


class EBookMetadataService:
    """
    电子书元数据服务
    
    负责协调多个元数据提供者，按优先级尝试获取元数据。
    """
    
    def __init__(self):
        self.providers: List[EBookMetadataProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化元数据提供者列表"""
        if not settings.SMART_EBOOK_METADATA_ENABLED:
            logger.debug("电子书元数据增强已禁用，不初始化提供者")
            return
        
        provider_names = [
            name.strip() 
            for name in settings.SMART_EBOOK_METADATA_PROVIDERS.split(",")
            if name.strip()
        ]
        
        for name in provider_names:
            try:
                provider = self._create_provider(name)
                if provider:
                    self.providers.append(provider)
                    logger.info(f"已加载电子书元数据提供者: {name}")
            except Exception as e:
                logger.warning(f"加载元数据提供者 {name} 失败: {e}")
        
        if not self.providers:
            logger.debug("没有可用的元数据提供者")
    
    def _create_provider(self, name: str) -> Optional[EBookMetadataProvider]:
        """
        根据名称创建元数据提供者
        
        Args:
            name: 提供者名称（dummy, openlibrary, googlebooks 等）
        
        Returns:
            元数据提供者实例，如果名称无效返回 None
        """
        if name == "dummy":
            return DummyMetadataProvider()
        elif name == "openlibrary":
            from app.modules.ebook.metadata_providers.openlibrary import OpenLibraryMetadataProvider
            return OpenLibraryMetadataProvider()
        elif name == "googlebooks":
            # TODO: 实现 Google Books 提供者
            logger.debug("Google Books 提供者尚未实现")
            return None
        else:
            logger.warning(f"未知的元数据提供者: {name}")
            return None
    
    async def enrich_ebook_metadata(
        self,
        ebook: EBook,
        merge_strategy: str = "fill_empty"
    ) -> Optional[EBookMetadataUpdate]:
        """
        为电子书获取增强的元数据
        
        Args:
            ebook: 当前的电子书对象
            merge_strategy: 合并策略
                - "fill_empty": 只填补空字段（默认，保守策略）
                - "overwrite": 覆盖所有字段（激进策略，暂未实现）
        
        Returns:
            合并后的元数据更新建议，如果无法获取或已禁用则返回 None
        """
        if not settings.SMART_EBOOK_METADATA_ENABLED:
            logger.debug("电子书元数据增强已禁用")
            return None
        
        if not self.providers:
            logger.debug("没有可用的元数据提供者")
            return None
        
        # 按优先级尝试各个提供者
        for provider in self.providers:
            try:
                # 设置超时
                update = await asyncio.wait_for(
                    provider.enrich_metadata(ebook),
                    timeout=settings.SMART_EBOOK_METADATA_TIMEOUT
                )
                
                if update:
                    logger.info(
                        f"成功从 {update.provider_name} 获取元数据 "
                        f"（可信度: {update.confidence:.2f}）"
                    )
                    return update
            except asyncio.TimeoutError:
                logger.warning(f"元数据提供者 {provider.name if hasattr(provider, 'name') else 'unknown'} 超时")
                continue
            except Exception as e:
                logger.warning(f"元数据提供者 {provider.name if hasattr(provider, 'name') else 'unknown'} 出错: {e}")
                continue
        
        logger.debug("所有元数据提供者均无法获取元数据")
        return None
    
    def merge_metadata(
        self,
        ebook: EBook,
        update: EBookMetadataUpdate,
        strategy: str = "fill_empty"
    ) -> bool:
        """
        将元数据更新合并到电子书对象中
        
        Args:
            ebook: 电子书对象
            update: 元数据更新建议
            strategy: 合并策略
                - "fill_empty": 只填补空字段（默认）
                - "overwrite": 覆盖所有字段（暂未实现）
        
        Returns:
            是否进行了任何更新
        """
        if strategy != "fill_empty":
            logger.warning(f"不支持的合并策略: {strategy}，使用 fill_empty")
            strategy = "fill_empty"
        
        updated = False
        
        # 只填补空字段
        if strategy == "fill_empty":
            if update.original_title and not ebook.original_title:
                ebook.original_title = update.original_title
                updated = True
            
            if update.author and not ebook.author:
                ebook.author = update.author
                updated = True
            
            if update.series and not ebook.series:
                ebook.series = update.series
                updated = True
            
            if update.volume_index and not ebook.volume_index:
                ebook.volume_index = update.volume_index
                updated = True
            
            if update.language and not ebook.language:
                ebook.language = update.language
                updated = True
            
            if update.publish_year and not ebook.publish_year:
                ebook.publish_year = update.publish_year
                updated = True
            
            if update.isbn and not ebook.isbn:
                ebook.isbn = update.isbn
                updated = True
            
            if update.tags and not ebook.tags:
                ebook.tags = update.tags
                updated = True
            
            if update.description and not ebook.description:
                ebook.description = update.description
                updated = True
            
            if update.cover_url and not ebook.cover_url:
                ebook.cover_url = update.cover_url
                updated = True
        
        # 记录元数据来源（TODO: 将来可以在 extra_metadata 中记录）
        if updated and update.provider_name:
            if not ebook.extra_metadata:
                ebook.extra_metadata = {}
            if "metadata_sources" not in ebook.extra_metadata:
                ebook.extra_metadata["metadata_sources"] = []
            ebook.extra_metadata["metadata_sources"].append({
                "provider": update.provider_name,
                "confidence": update.confidence,
            })
        
        return updated


# 全局元数据服务实例
_metadata_service: Optional[EBookMetadataService] = None


def get_metadata_service() -> EBookMetadataService:
    """获取全局元数据服务实例"""
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = EBookMetadataService()
    return _metadata_service

