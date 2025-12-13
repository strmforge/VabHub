"""
公共 Metadata Key 配置测试

测试场景：
1. 只有 PUBLIC_* 配置
2. 只有私有 TMDB_API_KEY
3. 两者都有时优先公共
4. 全都没有时返回 None

Created: 0.0.3 DISCOVER-MUSIC-HOME P1
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestPublicMetadataKeys:
    """公共 Metadata Key 配置测试"""
    
    def setup_method(self):
        """每个测试前重置全局配置"""
        import app.core.public_metadata_config as pmc
        pmc._public_metadata_keys = None
    
    def test_only_public_key(self):
        """场景1: 只有公共 key"""
        with patch.dict(os.environ, {
            "PUBLIC_TMDB_DISCOVER_KEY": "public_test_key_123",
            "TMDB_API_KEY": "",
            "ENABLE_PUBLIC_METADATA_KEYS": "true"
        }, clear=False):
            # 重置配置
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            key = pmc.get_tmdb_key_for_discover()
            source = pmc.get_discover_key_source()
            
            assert key == "public_test_key_123"
            assert source == "public"
    
    def test_only_private_key(self):
        """场景2: 只有私有 key"""
        with patch.dict(os.environ, {
            "PUBLIC_TMDB_DISCOVER_KEY": "",
            "ENABLE_PUBLIC_METADATA_KEYS": "true"
        }, clear=False):
            # 重置配置
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            # Mock settings.TMDB_API_KEY
            with patch("app.core.public_metadata_config.settings") as mock_settings:
                mock_settings.TMDB_API_KEY = "private_test_key_456"
                
                key = pmc.get_tmdb_key_for_discover()
                source = pmc.get_discover_key_source()
                
                assert key == "private_test_key_456"
                assert source == "private"
    
    def test_both_keys_prefer_public(self):
        """场景3: 两者都有时优先公共"""
        with patch.dict(os.environ, {
            "PUBLIC_TMDB_DISCOVER_KEY": "public_key_789",
            "ENABLE_PUBLIC_METADATA_KEYS": "true"
        }, clear=False):
            # 重置配置
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            # Mock settings.TMDB_API_KEY
            with patch("app.core.public_metadata_config.settings") as mock_settings:
                mock_settings.TMDB_API_KEY = "private_key_abc"
                
                key = pmc.get_tmdb_key_for_discover()
                source = pmc.get_discover_key_source()
                
                # 应该优先使用公共 key
                assert key == "public_key_789"
                assert source == "public"
    
    def test_no_keys_returns_none(self):
        """场景4: 全都没有时返回 None"""
        with patch.dict(os.environ, {
            "PUBLIC_TMDB_DISCOVER_KEY": "",
            "ENABLE_PUBLIC_METADATA_KEYS": "true"
        }, clear=False):
            # 重置配置
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            # Mock settings.TMDB_API_KEY 为空
            with patch("app.core.public_metadata_config.settings") as mock_settings:
                mock_settings.TMDB_API_KEY = ""
                
                key = pmc.get_tmdb_key_for_discover()
                source = pmc.get_discover_key_source()
                
                assert key is None
                assert source == "none"
    
    def test_public_disabled_uses_private(self):
        """场景5: 公共配置被禁用时使用私有 key"""
        with patch.dict(os.environ, {
            "PUBLIC_TMDB_DISCOVER_KEY": "public_key_should_not_use",
            "ENABLE_PUBLIC_METADATA_KEYS": "false"
        }, clear=False):
            # 重置配置
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            # Mock settings.TMDB_API_KEY
            with patch("app.core.public_metadata_config.settings") as mock_settings:
                mock_settings.TMDB_API_KEY = "private_key_xyz"
                
                key = pmc.get_tmdb_key_for_discover()
                source = pmc.get_discover_key_source()
                
                # 应该使用私有 key
                assert key == "private_key_xyz"
                assert source == "private"
    
    def test_douban_always_available(self):
        """豆瓣无需 key，始终可用"""
        with patch.dict(os.environ, {
            "ENABLE_PUBLIC_METADATA_KEYS": "true"
        }, clear=False):
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            assert pmc.is_douban_available() is True
    
    def test_bangumi_can_be_disabled(self):
        """Bangumi 可以被禁用"""
        with patch.dict(os.environ, {
            "ENABLE_PUBLIC_METADATA_KEYS": "true",
            "PUBLIC_BANGUMI_ENABLED": "false"
        }, clear=False):
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            assert pmc.is_bangumi_available() is False
    
    def test_bangumi_enabled_by_default(self):
        """Bangumi 默认启用"""
        with patch.dict(os.environ, {
            "ENABLE_PUBLIC_METADATA_KEYS": "true",
            "PUBLIC_BANGUMI_ENABLED": "true"
        }, clear=False):
            import app.core.public_metadata_config as pmc
            pmc._public_metadata_keys = None
            
            assert pmc.is_bangumi_available() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
