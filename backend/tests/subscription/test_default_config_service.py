"""
默认订阅配置服务测试
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.modules.subscription.defaults import (
    DefaultSubscriptionConfig,
    DefaultSubscriptionConfigService
)
from app.models.settings import SystemSetting


class TestDefaultSubscriptionConfigService:
    """默认订阅配置服务测试类"""
    
    @pytest.fixture
    def service(self, db_session: AsyncSession) -> DefaultSubscriptionConfigService:
        """创建服务实例"""
        return DefaultSubscriptionConfigService(db_session)
    
    @pytest.fixture
    def sample_config_data(self) -> dict:
        """示例配置数据"""
        return {
            "quality": "4K",
            "resolution": "2160p",
            "effect": "HDR",
            "min_seeders": 10,
            "auto_download": False,
            "best_version": True,
            "include": "CHD,WiKi",
            "exclude": "HDTV",
            "filter_group_ids": [1, 2, 3],
            "allow_hr": True,
            "allow_h3h5": True,
            "strict_free_only": True,
            "sites": [1, 2],
            "downloader": "qbittorrent",
            "save_path": "/downloads/movies"
        }
    
    @pytest.mark.asyncio
    async def test_get_default_config_builtin(self, service):
        """测试获取内置默认配置"""
        config = await service.get_default_config("movie")
        
        assert isinstance(config, DefaultSubscriptionConfig)
        assert config.quality == "1080p"
        assert config.min_seeders == 5
        assert config.auto_download is True
        assert config.best_version is False
    
    @pytest.mark.asyncio
    async def test_get_default_config_from_database(self, service, sample_config_data):
        """测试从数据库获取配置"""
        # 模拟数据库中存在配置
        mock_setting = AsyncMock()
        mock_setting.value = sample_config_data
        
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_setting
            mock_execute.return_value = mock_result
            
            config = await service.get_default_config("movie")
            
            assert config.quality == "4K"
            assert config.min_seeders == 10
            assert config.auto_download is False
            assert config.best_version is True
    
    @pytest.mark.asyncio
    async def test_get_default_config_invalid_media_type(self, service):
        """测试获取无效媒体类型的配置"""
        with pytest.raises(ValueError, match="不支持的媒体类型"):
            await service.get_default_config("invalid_type")
    
    @pytest.mark.asyncio
    async def test_get_default_config_database_error(self, service):
        """测试数据库错误时的处理"""
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute', side_effect=Exception("Database error")):
            config = await service.get_default_config("movie")
            
            # 应该返回基础配置
            assert isinstance(config, DefaultSubscriptionConfig)
            assert config.quality == ""
            assert config.min_seeders == 5
    
    @pytest.mark.asyncio
    async def test_save_default_config_success(self, service, sample_config_data):
        """测试保存默认配置成功"""
        # 模拟数据库中不存在现有配置
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.commit') as mock_commit, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.refresh') as mock_refresh, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.add') as mock_add:
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None  # 不存在现有配置
            mock_execute.return_value = mock_result
            
            config = await service.save_default_config("movie", sample_config_data)
            
            assert isinstance(config, DefaultSubscriptionConfig)
            assert config.quality == "4K"
            assert config.min_seeders == 10
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_default_config_update_existing(self, service, sample_config_data):
        """测试更新现有配置"""
        # 模拟数据库中存在现有配置
        mock_existing = AsyncMock()
        mock_existing.value = json.dumps(sample_config_data)
        
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.commit') as mock_commit, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.refresh') as mock_refresh, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.add') as mock_add:
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_existing
            mock_execute.return_value = mock_result
            
            config = await service.save_default_config("movie", sample_config_data)
            
            assert isinstance(config, DefaultSubscriptionConfig)
            assert config.quality == "4K"
            mock_add.assert_called_once()  # 更新时也会调用 add
            mock_commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_default_config_invalid_media_type(self, service, sample_config_data):
        """测试保存无效媒体类型的配置"""
        with pytest.raises(ValueError, match="不支持的媒体类型"):
            await service.save_default_config("invalid_type", sample_config_data)
    
    @pytest.mark.asyncio
    async def test_save_default_config_validation_error(self, service):
        """测试保存无效配置数据"""
        invalid_data = {
            "min_seeders": "invalid_number"  # 应该是整数
        }
        
        with pytest.raises(Exception):  # Pydantic验证错误
            await service.save_default_config("movie", invalid_data)
    
    @pytest.mark.asyncio
    async def test_reset_default_config_success(self, service):
        """测试重置默认配置成功"""
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.commit') as mock_commit:
            
            config = await service.reset_default_config("movie")
            
            assert isinstance(config, DefaultSubscriptionConfig)
            assert config.quality == "1080p"  # 内置默认值
            assert config.min_seeders == 5
            mock_execute.assert_called_once()
            mock_commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_default_config_invalid_media_type(self, service):
        """测试重置无效媒体类型的配置"""
        with pytest.raises(ValueError, match="不支持的媒体类型"):
            await service.reset_default_config("invalid_type")
    
    @pytest.mark.asyncio
    async def test_get_all_configs_success(self, service):
        """测试获取所有配置成功"""
        configs = await service.get_all_configs()
        
        assert isinstance(configs, dict)
        assert len(configs) == len(service.CONFIG_KEYS)
        for media_type, config in configs.items():
            assert media_type in service.CONFIG_KEYS
            assert isinstance(config, DefaultSubscriptionConfig)
    
    @pytest.mark.asyncio
    async def test_get_all_configs_with_error(self, service):
        """测试获取所有配置时的错误处理"""
        with patch.object(service, 'get_default_config', side_effect=Exception("Error")):
            configs = await service.get_all_configs()
            
            # 应该返回基础配置
            assert isinstance(configs, dict)
            assert len(configs) == len(service.CONFIG_KEYS)
            for config in configs.values():
                assert isinstance(config, DefaultSubscriptionConfig)
    
    @pytest.mark.asyncio
    async def test_apply_default_to_subscription_data(self, service, sample_config_data):
        """测试将默认配置应用到订阅数据"""
        # 模拟数据库中有默认配置
        with patch.object(service, 'get_default_config', return_value=DefaultSubscriptionConfig(**sample_config_data)):
            subscription_data = {
                "title": "测试电影",
                "media_type": "movie",
                "quality": "",  # 空字段应该被填充
                "min_seeders": 20,  # 非空字段应该保持不变
                "auto_download": None,  # None应该被填充
            }
            
            updated_data = await service.apply_default_to_subscription_data("movie", subscription_data)
            
            assert updated_data["quality"] == "4K"  # 被默认值填充
            assert updated_data["min_seeders"] == 20  # 保持原值
            assert updated_data["auto_download"] is False  # 被默认值填充
            assert updated_data["title"] == "测试电影"  # 保持原值
    
    @pytest.mark.asyncio
    async def test_apply_default_to_subscription_data_error(self, service):
        """测试应用默认配置时的错误处理"""
        subscription_data = {"title": "测试电影"}
        
        with patch.object(service, 'get_default_config', side_effect=Exception("Error")):
            # 应该返回原始数据
            updated_data = await service.apply_default_to_subscription_data("movie", subscription_data)
            assert updated_data == subscription_data
    
    def test_get_supported_media_types(self, service):
        """测试获取支持的媒体类型"""
        media_types = service.get_supported_media_types()
        
        assert isinstance(media_types, list)
        assert "movie" in media_types
        assert "tv" in media_types
        assert "short_drama" in media_types
        assert "anime" in media_types
        assert "music" in media_types
    
    def test_validate_media_type(self, service):
        """测试验证媒体类型"""
        assert service.validate_media_type("movie") is True
        assert service.validate_media_type("tv") is True
        assert service.validate_media_type("invalid_type") is False
    
    @pytest.mark.asyncio
    async def test_config_keys_constants(self, service):
        """测试配置键常量"""
        expected_keys = {
            "movie": "subscription.default.movie",
            "tv": "subscription.default.tv",
            "short_drama": "subscription.default.short_drama",
            "anime": "subscription.default.anime",
            "music": "subscription.default.music",
        }
        
        assert service.CONFIG_KEYS == expected_keys
    
    @pytest.mark.asyncio
    async def test_builtin_defaults_constants(self, service):
        """测试内置默认配置常量"""
        for media_type in service.CONFIG_KEYS.keys():
            assert media_type in service.BUILTIN_DEFAULTS
            config = service.BUILTIN_DEFAULTS[media_type]
            assert isinstance(config, DefaultSubscriptionConfig)
    
    @pytest.mark.asyncio
    async def test_get_default_config_json_string_value(self, service, sample_config_data):
        """测试从数据库获取JSON字符串格式的配置"""
        # 模拟数据库中存储的是JSON字符串
        mock_setting = AsyncMock()
        mock_setting.value = json.dumps(sample_config_data)
        
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_setting
            mock_execute.return_value = mock_result
            
            config = await service.get_default_config("movie")
            
            assert config.quality == "4K"
            assert config.min_seeders == 10
            assert isinstance(config.filter_group_ids, list)
    
    @pytest.mark.asyncio
    async def test_get_default_config_invalid_json(self, service):
        """测试从数据库获取无效JSON格式的配置"""
        # 模拟数据库中存储的是无效JSON
        mock_setting = AsyncMock()
        mock_setting.value = "invalid json string"
        
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_setting
            mock_execute.return_value = mock_result
            
            config = await service.get_default_config("movie")
            
            # 应该回退到内置默认配置
            assert config.quality == "1080p"
            assert config.min_seeders == 5
    
    @pytest.mark.asyncio
    async def test_save_default_config_exclude_none(self, service, sample_config_data):
        """测试保存配置时排除None值"""
        config_data_with_none = sample_config_data.copy()
        config_data_with_none["quality"] = None
        config_data_with_none["resolution"] = None
        
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.commit') as mock_commit, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.refresh') as mock_refresh, \
             patch('sqlalchemy.ext.asyncio.AsyncSession.add') as mock_add, \
             patch('json.dumps') as mock_json_dumps:
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            mock_json_dumps.return_value = json.dumps(config_data_with_none)
            
            await service.save_default_config("movie", config_data_with_none)
            
            # 验证json.dumps被调用
            mock_json_dumps.assert_called_once_with(config_data_with_none, ensure_ascii=False)
