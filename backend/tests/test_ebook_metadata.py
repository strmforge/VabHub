"""
测试电子书元数据增强功能
"""

import pytest
from app.models.ebook import EBook
from app.modules.ebook.metadata_service import EBookMetadataService, get_metadata_service
from app.modules.ebook.metadata_providers.dummy import DummyMetadataProvider
from app.modules.ebook.metadata_providers import EBookMetadataUpdate
from app.core.config import settings


@pytest.mark.asyncio
async def test_dummy_provider_enrich_metadata():
    """测试 Dummy 提供者生成元数据"""
    provider = DummyMetadataProvider()
    
    # 创建测试电子书（只有书名）
    ebook = EBook(
        title="测试电子书",
        author=None,
        description=None,
        publish_year=None,
        isbn=None,
    )
    
    update = await provider.enrich_metadata(ebook)
    
    assert update is not None
    assert update.provider_name == "dummy"
    assert update.confidence == 0.3
    assert update.description is not None
    assert update.publish_year is not None
    assert update.isbn is not None
    assert update.tags is not None


@pytest.mark.asyncio
async def test_dummy_provider_no_title():
    """测试 Dummy 提供者在缺少书名时返回 None"""
    provider = DummyMetadataProvider()
    
    ebook = EBook(
        title="",  # 空书名
        author=None,
    )
    
    update = await provider.enrich_metadata(ebook)
    
    assert update is None


@pytest.mark.asyncio
async def test_metadata_service_merge_fill_empty():
    """测试元数据服务合并逻辑（只填补空字段）"""
    service = EBookMetadataService()
    
    # 创建已有部分字段的电子书
    ebook = EBook(
        title="测试电子书",
        author="已有作者",  # 已有值
        description=None,  # 空字段
        publish_year=None,  # 空字段
        isbn=None,  # 空字段
    )
    
    # 创建元数据更新（包含已有字段和新字段）
    update = EBookMetadataUpdate(
        author="新作者",  # 尝试覆盖已有字段
        description="新描述",  # 填补空字段
        publish_year=2024,  # 填补空字段
        isbn="9781234567890",  # 填补空字段
        provider_name="test",
    )
    
    # 合并元数据
    updated = service.merge_metadata(ebook, update, strategy="fill_empty")
    
    # 验证：只填补了空字段，没有覆盖已有字段
    assert updated is True
    assert ebook.author == "已有作者"  # 未被覆盖
    assert ebook.description == "新描述"  # 已填补
    assert ebook.publish_year == 2024  # 已填补
    assert ebook.isbn == "9781234567890"  # 已填补


@pytest.mark.asyncio
async def test_metadata_service_disabled():
    """测试元数据服务在禁用时返回 None"""
    # 临时禁用元数据增强
    original_value = settings.SMART_EBOOK_METADATA_ENABLED
    settings.SMART_EBOOK_METADATA_ENABLED = False
    
    try:
        service = EBookMetadataService()
        ebook = EBook(title="测试电子书")
        
        update = await service.enrich_ebook_metadata(ebook)
        
        assert update is None
    finally:
        # 恢复原值
        settings.SMART_EBOOK_METADATA_ENABLED = original_value


@pytest.mark.asyncio
async def test_metadata_update_to_dict():
    """测试 EBookMetadataUpdate 转换为字典"""
    update = EBookMetadataUpdate(
        title="测试书名",
        author="测试作者",
        description="测试描述",
        provider_name="test",
        confidence=0.8,
    )
    
    result = update.to_dict()
    
    assert "title" in result
    assert "author" in result
    assert "description" in result
    assert "provider_name" in result
    assert "confidence" in result
    assert result["title"] == "测试书名"
    assert result["confidence"] == 0.8

