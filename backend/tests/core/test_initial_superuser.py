"""
初始管理员创建模块测试
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.initial_superuser import (
    generate_random_password,
    has_any_superuser,
    ensure_initial_superuser,
)


class TestGenerateRandomPassword:
    """测试随机密码生成"""
    
    def test_default_length(self):
        """默认长度应为16"""
        password = generate_random_password()
        assert len(password) == 16
    
    def test_custom_length(self):
        """自定义长度"""
        password = generate_random_password(20)
        assert len(password) == 20
    
    def test_contains_uppercase(self):
        """应包含大写字母"""
        password = generate_random_password(20)
        assert any(c.isupper() for c in password)
    
    def test_contains_lowercase(self):
        """应包含小写字母"""
        password = generate_random_password(20)
        assert any(c.islower() for c in password)
    
    def test_contains_digit(self):
        """应包含数字"""
        password = generate_random_password(20)
        assert any(c.isdigit() for c in password)
    
    def test_uniqueness(self):
        """多次生成应不同"""
        passwords = [generate_random_password() for _ in range(10)]
        assert len(set(passwords)) == 10


class TestHasAnySuperuser:
    """测试超级管理员检测"""
    
    @pytest.mark.asyncio
    async def test_no_superuser(self):
        """无超级管理员时返回 False"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result
        
        result = await has_any_superuser(mock_db)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_has_superuser(self):
        """有超级管理员时返回 True"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        mock_db.execute.return_value = mock_result
        
        result = await has_any_superuser(mock_db)
        assert result is True


class TestEnsureInitialSuperuser:
    """测试初始管理员创建"""
    
    @pytest.mark.asyncio
    async def test_skip_when_superuser_exists(self):
        """已有超级管理员时跳过创建"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        mock_db.execute.return_value = mock_result
        
        created, username, password = await ensure_initial_superuser(mock_db)
        
        assert created is False
        assert username is None
        assert password is None
        mock_db.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_with_random_password(self):
        """无 ENV 密码时生成随机密码"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        # 第一次查询：检查是否有超级管理员 (无)
        # 第二次查询：检查用户名是否存在 (不存在)
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [count_result, user_result]
        
        with patch.dict(os.environ, {"SUPERUSER_NAME": "", "SUPERUSER_PASSWORD": ""}, clear=False):
            # 清除可能存在的环境变量
            os.environ.pop("SUPERUSER_NAME", None)
            os.environ.pop("SUPERUSER_PASSWORD", None)
            
            created, username, password = await ensure_initial_superuser(mock_db)
        
        assert created is True
        assert username == "admin"
        assert password is not None
        assert len(password) == 16
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_with_env_password(self):
        """有 ENV 密码时使用指定密码"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [count_result, user_result]
        
        with patch.dict(os.environ, {
            "SUPERUSER_NAME": "myadmin",
            "SUPERUSER_PASSWORD": "mypassword123"
        }):
            created, username, password = await ensure_initial_superuser(mock_db)
        
        assert created is True
        assert username == "myadmin"
        assert password is None  # 使用 ENV 密码时不返回密码
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_default_username_is_admin(self):
        """默认用户名应为 admin"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [count_result, user_result]
        
        # 确保环境变量未设置
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SUPERUSER_NAME", None)
            os.environ.pop("SUPERUSER_PASSWORD", None)
            
            created, username, _ = await ensure_initial_superuser(mock_db)
        
        assert username == "admin"
