"""
测试 Open Library 元数据提供者
"""

import pytest
from unittest.mock import AsyncMock, patch
import httpx
from app.models.ebook import EBook
from app.modules.ebook.metadata_providers.openlibrary import OpenLibraryMetadataProvider
from app.modules.ebook.metadata_service import EBookMetadataService
from app.core.config import settings


@pytest.mark.asyncio
async def test_openlibrary_provider_by_isbn():
    """测试通过 ISBN 查询元数据"""
    provider = OpenLibraryMetadataProvider()
    
    # Mock HTTP 响应
    mock_response_data = {
        "title": "The Lord of the Rings",
        "subtitle": "The Fellowship of the Ring",
        "authors": [{"key": "/authors/OL123456A"}],
        "author_name": ["J.R.R. Tolkien"],
        "publish_date": "1954",
        "isbn_13": ["9780261103573"],
        "description": {"value": "A great fantasy novel."},
        "covers": [123456],
        "subjects": ["Fantasy", "Fiction"],
        "languages": [{"key": "/languages/eng"}],
    }
    
    ebook = EBook(
        title="测试书名",
        isbn="9780261103573",
        author=None,
        description=None,
    )
    
    with patch("app.modules.ebook.metadata_providers.openlibrary.httpx.AsyncClient") as mock_client_class:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: mock_response_data  # json() 是同步方法
        mock_response.raise_for_status = lambda: None  # raise_for_status() 是同步方法
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        update = await provider.enrich_metadata(ebook)
        
        assert update is not None
        assert update.provider_name == "openlibrary"
        assert update.confidence == 0.8
        assert "The Lord of the Rings" in update.title
        assert update.author == "J.R.R. Tolkien"
        assert update.publish_year == 1954
        # 注意：ebook 已有 isbn，所以 update.isbn 可能为 None（符合 fill_empty 策略）
        # 但我们可以验证其他字段被正确填充
        assert update.description is not None
        assert "123456" in update.cover_url
        assert update.tags is not None


@pytest.mark.asyncio
async def test_openlibrary_provider_by_title_author():
    """测试通过 title+author 搜索元数据"""
    provider = OpenLibraryMetadataProvider()
    
    # Mock 搜索响应
    mock_search_response = {
        "docs": [
            {
                "title": "1984",
                "author_name": ["George Orwell"],
                "first_publish_year": 1949,
                "isbn": ["9780451524935"],
                "cover_i": 789012,
                "subject": ["Dystopian", "Fiction"],
                "edition_key": ["OL123456M"],
            }
        ]
    }
    
    # Mock edition 响应
    mock_edition_response = {
        "title": "1984",
        "authors": [{"key": "/authors/OL789012A"}],
        "author_name": ["George Orwell"],
        "publish_date": "1949",
        "isbn_13": ["9780451524935"],
        "description": "A dystopian novel.",
        "covers": [789012],
        "subjects": ["Dystopian", "Fiction"],
    }
    
    ebook = EBook(
        title="1984",
        author=None,  # 没有 author，会从 Open Library 获取
        isbn=None,  # 没有 ISBN，会通过搜索获取
        description=None,
    )
    
    with patch("app.modules.ebook.metadata_providers.openlibrary.httpx.AsyncClient") as mock_client_class:
        # 第一次调用：搜索
        mock_search = AsyncMock()
        mock_search.status_code = 200
        mock_search.json = lambda: mock_search_response
        mock_search.raise_for_status = lambda: None
        
        # 第二次调用：获取 edition
        mock_edition = AsyncMock()
        mock_edition.status_code = 200
        mock_edition.json = lambda: mock_edition_response
        mock_edition.raise_for_status = lambda: None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(side_effect=[mock_search, mock_edition])
        mock_client_class.return_value = mock_client_instance
        
        update = await provider.enrich_metadata(ebook)
        
        assert update is not None
        assert update.provider_name == "openlibrary"
        assert update.confidence == 0.8  # 因为获取了 edition 详细信息
        assert update.title == "1984"
        assert update.author == "George Orwell"  # 从 edition 数据中获取
        assert update.publish_year == 1949
        assert update.isbn == "9780451524935"  # 从 edition 数据中获取


@pytest.mark.asyncio
async def test_openlibrary_provider_isbn_not_found():
    """测试 ISBN 未找到的情况"""
    provider = OpenLibraryMetadataProvider()
    
    ebook = EBook(
        title="测试书名",
        isbn="9780000000000",  # 不存在的 ISBN
    )
    
    with patch("app.modules.ebook.metadata_providers.openlibrary.httpx.AsyncClient") as mock_client_class:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        update = await provider.enrich_metadata(ebook)
        
        # 应该返回 None（因为 ISBN 未找到，且没有 title 用于搜索）
        assert update is None


@pytest.mark.asyncio
async def test_openlibrary_provider_timeout():
    """测试超时情况"""
    provider = OpenLibraryMetadataProvider()
    
    ebook = EBook(
        title="测试书名",
        isbn="9780261103573",
    )
    
    with patch("app.modules.ebook.metadata_providers.openlibrary.httpx.AsyncClient") as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        mock_client_class.return_value = mock_client_instance
        
        update = await provider.enrich_metadata(ebook)
        
        # 超时应该返回 None，不抛异常
        assert update is None


@pytest.mark.asyncio
async def test_openlibrary_provider_http_error():
    """测试 HTTP 错误情况"""
    provider = OpenLibraryMetadataProvider()
    
    ebook = EBook(
        title="测试书名",
        isbn="9780261103573",
    )
    
    with patch("app.modules.ebook.metadata_providers.openlibrary.httpx.AsyncClient") as mock_client_class:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Server Error",
            request=AsyncMock(),
            response=mock_response
        ))
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        update = await provider.enrich_metadata(ebook)
        
        # HTTP 错误应该返回 None，不抛异常
        assert update is None


@pytest.mark.asyncio
async def test_metadata_service_with_openlibrary():
    """测试元数据服务集成 Open Library 提供者"""
    # 临时启用元数据增强
    original_enabled = settings.SMART_EBOOK_METADATA_ENABLED
    original_providers = settings.SMART_EBOOK_METADATA_PROVIDERS
    
    try:
        settings.SMART_EBOOK_METADATA_ENABLED = True
        settings.SMART_EBOOK_METADATA_PROVIDERS = "openlibrary"
        
        service = EBookMetadataService()
        
        # 验证 Open Library 提供者已加载
        assert len(service.providers) > 0
        assert any(hasattr(p, 'name') and p.name == 'openlibrary' for p in service.providers)
        
        ebook = EBook(
            title="1984",
            author="George Orwell",
            isbn="9780451524935",
        )
        
        # Mock HTTP 响应
        mock_response_data = {
            "title": "1984",
            "author_name": ["George Orwell"],
            "publish_date": "1949",
            "isbn_13": ["9780451524935"],
            "description": "A dystopian novel.",
            "covers": [789012],
        }
        
        with patch("app.modules.ebook.metadata_providers.openlibrary.httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: mock_response_data
            mock_response.raise_for_status = lambda: None
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance
            
            update = await service.enrich_ebook_metadata(ebook)
        
        assert update is not None
        assert update.provider_name == "openlibrary"
            
    finally:
        # 恢复原值
        settings.SMART_EBOOK_METADATA_ENABLED = original_enabled
        settings.SMART_EBOOK_METADATA_PROVIDERS = original_providers


@pytest.mark.asyncio
async def test_openlibrary_provider_empty_search_results():
    """测试搜索结果为空的情况"""
    provider = OpenLibraryMetadataProvider()
    
    ebook = EBook(
        title="不存在的书名",
        author="不存在的作者",
        isbn=None,
    )
    
    with patch("app.modules.ebook.metadata_providers.openlibrary.httpx.AsyncClient") as mock_client_class:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: {"docs": []}  # 空结果
        mock_response.raise_for_status = lambda: None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        update = await provider.enrich_metadata(ebook)
        
        # 空结果应该返回 None
        assert update is None

