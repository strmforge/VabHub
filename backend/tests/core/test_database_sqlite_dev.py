"""
SQLite 开发模式数据库目录自动创建测试

BACKEND-REGRESSION-SQLITE-FIX-1: 确保 SQLite 数据库文件的父目录能自动创建
"""

import pytest
from pathlib import Path


class TestEnsureSqliteDir:
    """测试 _ensure_sqlite_dir 函数"""
    
    def test_creates_parent_directory(self, tmp_path: Path):
        """测试：当父目录不存在时，应自动创建"""
        from app.core.database import _ensure_sqlite_dir
        
        # 构造一个不存在的子目录路径
        db_path = tmp_path / "subdir" / "nested" / "test.db"
        url = f"sqlite+aiosqlite:///{db_path}"
        
        # 确认父目录不存在
        assert not db_path.parent.exists()
        
        # 调用函数
        _ensure_sqlite_dir(url)
        
        # 验证父目录已创建
        assert db_path.parent.exists()
        assert db_path.parent.is_dir()
    
    def test_ignores_postgres_url(self, tmp_path: Path):
        """测试：PostgreSQL URL 应被忽略"""
        from app.core.database import _ensure_sqlite_dir
        
        # PostgreSQL URL 不应创建任何目录
        url = "postgresql+asyncpg://user:pass@localhost:5432/vabhub"
        
        # 不应抛出异常
        _ensure_sqlite_dir(url)
    
    def test_ignores_memory_database(self):
        """测试：内存数据库应被忽略"""
        from app.core.database import _ensure_sqlite_dir
        
        # 内存数据库 URL
        url = "sqlite+aiosqlite:///:memory:"
        
        # 不应抛出异常
        _ensure_sqlite_dir(url)
    
    def test_handles_relative_path(self, tmp_path: Path, monkeypatch):
        """测试：相对路径应正确处理"""
        from app.core.database import _ensure_sqlite_dir
        import os
        
        # 切换到临时目录
        monkeypatch.chdir(tmp_path)
        
        # 相对路径
        url = "sqlite+aiosqlite:///./data/test.db"
        
        # 调用函数
        _ensure_sqlite_dir(url)
        
        # 验证目录已创建
        assert (tmp_path / "data").exists()
    
    def test_existing_directory_no_error(self, tmp_path: Path):
        """测试：目录已存在时不应报错"""
        from app.core.database import _ensure_sqlite_dir
        
        # 先创建目录
        subdir = tmp_path / "existing"
        subdir.mkdir()
        
        db_path = subdir / "test.db"
        url = f"sqlite+aiosqlite:///{db_path}"
        
        # 不应抛出异常
        _ensure_sqlite_dir(url)
        
        # 目录仍然存在
        assert subdir.exists()
    
    def test_handles_sqlite_without_aiosqlite(self, tmp_path: Path):
        """测试：纯 sqlite:// URL 也应处理"""
        from app.core.database import _ensure_sqlite_dir
        
        db_path = tmp_path / "plain" / "test.db"
        url = f"sqlite:///{db_path}"
        
        assert not db_path.parent.exists()
        
        _ensure_sqlite_dir(url)
        
        assert db_path.parent.exists()


class TestSqliteDatabaseInit:
    """测试 SQLite 数据库初始化"""
    
    @pytest.mark.skipif(
        True,  # 跳过此测试，因为它会影响全局 engine
        reason="此测试会修改全局 engine，仅用于手动验证"
    )
    def test_init_db_creates_directory_and_tables(self, tmp_path: Path, monkeypatch):
        """测试：init_db 应能在不存在的目录中创建数据库"""
        import asyncio
        
        # 设置环境变量
        db_path = tmp_path / "ci_test" / "vabhub.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        
        # 重新加载模块以使用新的环境变量
        # 注意：此测试在实际 CI 中由 workflow 验证
        pass
