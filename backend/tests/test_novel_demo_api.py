"""
小说导入 Demo API 测试
"""

import pytest
from httpx import AsyncClient
from pathlib import Path
import tempfile

from app.main import app


@pytest.fixture
def temp_txt_file():
    """创建临时 TXT 文件"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    content = """第1章 开始
这是第一章的内容。
有很多文字。

第2章 继续
这是第二章的内容。
继续写。
"""
    temp_file.write(content)
    temp_file.close()
    yield Path(temp_file.name)
    Path(temp_file.name).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_import_local_txt_api_success(temp_txt_file):
    """测试本地 TXT 导入 API（成功场景）"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/dev/novel/import-local-txt",
            json={
                "file_path": str(temp_txt_file),
                "title": "测试小说",
                "author": "测试作者",
                "description": "这是一本测试小说"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应结构
    assert "success" in data or "data" in data
    
    # 如果使用统一响应格式
    if "data" in data:
        response_data = data["data"]
        assert "ebook_path" in response_data
        assert response_data.get("success") is True or data.get("success") is True
    else:
        # 直接响应格式
        assert "ebook_path" in data
        assert data.get("success") is True


@pytest.mark.asyncio
async def test_import_local_txt_api_file_not_found():
    """测试本地 TXT 导入 API（文件不存在）"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/dev/novel/import-local-txt",
            json={
                "file_path": "/nonexistent/file.txt",
                "title": "测试小说"
            }
        )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_local_txt_api_invalid_file():
    """测试本地 TXT 导入 API（路径不是文件）"""
    import tempfile as tf
    temp_dir = Path(tf.mkdtemp())
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/dev/novel/import-local-txt",
                json={
                    "file_path": str(temp_dir),  # 传入目录而不是文件
                    "title": "测试小说"
                }
            )
        
        assert response.status_code == 400
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

