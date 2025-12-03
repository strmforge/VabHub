"""
External Indexer 搜索结果合并与 source 标记测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.ext_indexer.search_provider import ExternalIndexerSearchProvider
from app.core.ext_indexer.models import ExternalTorrentResult
from app.core.ext_indexer.interfaces import ExternalIndexerRuntime, ExternalAuthBridge
from app.core.ext_indexer.auth_bridge import ExternalAuthState


class FakeExternalRuntime(ExternalIndexerRuntime):
    """用于测试的假外部索引运行时"""
    
    def __init__(self, search_results: list = None):
        self.search_results = search_results or []
        self.search_call_count = 0
    
    async def search_torrents(
        self,
        site_id: str,
        keyword: str,
        media_type: str = None,
        page: int = 1,
    ) -> list:
        """模拟搜索"""
        self.search_call_count += 1
        return self.search_results


class FakeAuthBridge(ExternalAuthBridge):
    """用于测试的假授权桥接"""
    
    def __init__(self, logged_in: bool = True, has_challenge: bool = False):
        self.logged_in = logged_in
        self.has_challenge = has_challenge
    
    async def get_auth_state(self, site_id: str) -> ExternalAuthState:
        """返回授权状态"""
        from datetime import datetime
        return ExternalAuthState(
            logged_in=self.logged_in,
            last_checked_at=datetime.utcnow(),
            has_challenge=self.has_challenge,
        )


@pytest.mark.asyncio
async def test_search_merges_results_with_source(db_session):
    """
    测试搜索结果合并并正确标记 source
    """
    # 创建假运行时，返回一些搜索结果
    fake_results = [
        {
            "torrent_id": "1",
            "title": "Test Torrent 1",
            "size": "1.0 GB",
            "seeds": 10,
            "peers": 5,
        },
        {
            "torrent_id": "2",
            "title": "Test Torrent 2",
            "size": "2.0 GB",
            "seeds": 20,
            "peers": 10,
        },
    ]
    
    runtime = FakeExternalRuntime(search_results=fake_results)
    auth_bridge = FakeAuthBridge(logged_in=True, has_challenge=False)
    provider = ExternalIndexerSearchProvider(runtime=runtime, auth_bridge=auth_bridge)
    
    # Mock 站点配置加载（当 sites=None 时会调用）
    with patch("app.core.ext_indexer.site_importer.load_all_site_configs", return_value=[]):
        # 执行搜索
        results = await provider.search("test", sites=["site1"])
        
        # 验证结果
        assert len(results) == 2
        assert all(isinstance(r, ExternalTorrentResult) for r in results)
        assert results[0].site_id == "site1"
        assert results[0].title == "Test Torrent 1"
        assert results[1].title == "Test Torrent 2"


@pytest.mark.asyncio
async def test_search_deduplicates_by_site_and_torrent_id(db_session):
    """
    测试搜索结果按 site_id + torrent_id 去重
    """
    # 创建包含重复项的搜索结果
    fake_results = [
        {
            "torrent_id": "1",
            "title": "Duplicate Torrent",
            "size": "1.0 GB",
        },
        {
            "torrent_id": "1",  # 相同的 torrent_id
            "title": "Duplicate Torrent",
            "size": "1.0 GB",
        },
        {
            "torrent_id": "2",
            "title": "Unique Torrent",
            "size": "2.0 GB",
        },
    ]
    
    runtime = FakeExternalRuntime(search_results=fake_results)
    auth_bridge = FakeAuthBridge(logged_in=True, has_challenge=False)
    provider = ExternalIndexerSearchProvider(runtime=runtime, auth_bridge=auth_bridge)
    
    # Mock 站点配置加载（当 sites=None 时会调用）
    with patch("app.core.ext_indexer.site_importer.load_all_site_configs", return_value=[]):
        # 执行搜索
        results = await provider.search("test", sites=["site1"])
        
        # 验证去重：应该只有 2 条结果（去除了重复的 torrent_id=1）
        assert len(results) == 2
        torrent_ids = [r.torrent_id for r in results]
        assert "1" in torrent_ids
        assert "2" in torrent_ids
        # 确保 "1" 只出现一次
        assert torrent_ids.count("1") == 1


@pytest.mark.asyncio
async def test_search_skips_site_with_challenge(db_session):
    """
    测试搜索跳过需要人机验证的站点
    """
    # 创建假运行时
    runtime = FakeExternalRuntime(search_results=[{"torrent_id": "1", "title": "Test"}])
    
    # 创建需要验证的授权桥接
    auth_bridge = FakeAuthBridge(logged_in=True, has_challenge=True)
    provider = ExternalIndexerSearchProvider(runtime=runtime, auth_bridge=auth_bridge)
    
    # Mock 站点配置加载（当 sites=None 时会调用）
    with patch("app.core.ext_indexer.site_importer.load_all_site_configs", return_value=[]):
        # 执行搜索
        results = await provider.search("test", sites=["site1"])
        
        # 验证结果：应该为空，因为站点需要验证
        assert len(results) == 0
        # 验证运行时未被调用
        assert runtime.search_call_count == 0


@pytest.mark.asyncio
async def test_search_handles_multiple_sites(db_session):
    """
    测试搜索多个站点并合并结果
    """
    # 为不同站点创建不同的运行时结果
    runtime1 = FakeExternalRuntime(search_results=[
        {"torrent_id": "1", "title": "Site1 Torrent"},
    ])
    runtime2 = FakeExternalRuntime(search_results=[
        {"torrent_id": "2", "title": "Site2 Torrent"},
    ])
    
    auth_bridge = FakeAuthBridge(logged_in=True, has_challenge=False)
    
    # 注意：这里我们需要一个能够为不同站点返回不同结果的运行时
    # 为了简化，我们使用一个可以切换结果的运行时
    class MultiSiteRuntime(ExternalIndexerRuntime):
        def __init__(self):
            self.site_results = {
                "site1": [{"torrent_id": "1", "title": "Site1 Torrent"}],
                "site2": [{"torrent_id": "2", "title": "Site2 Torrent"}],
            }
            self.search_call_count = 0
        
        async def search_torrents(self, site_id: str, keyword: str, media_type: str = None, page: int = 1) -> list:
            self.search_call_count += 1
            return self.site_results.get(site_id, [])
    
    runtime = MultiSiteRuntime()
    provider = ExternalIndexerSearchProvider(runtime=runtime, auth_bridge=auth_bridge)
    
    # Mock 站点配置加载（当 sites=None 时会调用）
    with patch("app.core.ext_indexer.site_importer.load_all_site_configs", return_value=[]):
        # 执行搜索
        results = await provider.search("test", sites=["site1", "site2"])
        
        # 验证结果：应该包含两个站点的结果
        assert len(results) == 2
        site_ids = [r.site_id for r in results]
        assert "site1" in site_ids
        assert "site2" in site_ids
        assert runtime.search_call_count == 2

