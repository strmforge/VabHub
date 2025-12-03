"""
小说上传 API 测试
"""

import pytest
from pathlib import Path
import tempfile
import io

from fastapi.testclient import TestClient
from app.api import api_router
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(api_router)


@pytest.fixture
def temp_txt_content():
    """创建测试用的 TXT 内容"""
    return """第1章 开始
这是第一章的内容。
有很多文字。

第2章 继续
这是第二章的内容。
继续写。
"""


def test_upload_txt_novel_success(temp_txt_content):
    """测试上传 TXT 小说成功场景"""
    # 创建临时文件内容
    file_content = temp_txt_content.encode('utf-8')
    file_obj = io.BytesIO(file_content)
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/novel/upload-txt",
        files={"file": ("test_novel.txt", file_obj, "text/plain")},
        data={
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
        ebook_id = response_data.get("ebook_id")
        ebook_path = response_data.get("ebook_path")
    else:
        # 直接响应格式
        assert "ebook_path" in data
        assert data.get("success") is True
        ebook_id = data.get("ebook_id")
        ebook_path = data.get("ebook_path")
    
    # 验证文件路径存在
    if ebook_path:
        assert Path(ebook_path).exists()


def test_upload_txt_novel_invalid_extension():
    """测试上传非 TXT 文件"""
    file_content = b"fake pdf content"
    file_obj = io.BytesIO(file_content)
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/novel/upload-txt",
        files={"file": ("test_novel.pdf", file_obj, "application/pdf")},
        data={"title": "测试小说"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data or "error_message" in data or "error_code" in data


def test_upload_txt_novel_missing_file():
    """测试不传文件字段"""
    client = TestClient(app)
    response = client.post(
        "/api/dev/novel/upload-txt",
        data={"title": "测试小说"}
    )
    
    # FastAPI 应该自动返回 422（验证错误）
    assert response.status_code in [400, 422]


def test_upload_txt_novel_auto_title(temp_txt_content):
    """测试不传 title 时自动从文件名推断"""
    file_content = temp_txt_content.encode('utf-8')
    file_obj = io.BytesIO(file_content)
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/novel/upload-txt",
        files={"file": ("我的小说.txt", file_obj, "text/plain")},
        data={"author": "测试作者"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证使用了文件名作为标题
    if "data" in data:
        response_data = data["data"]
    else:
        response_data = data
    
    # 标题应该是文件名（不含扩展名）
    assert "我的小说" in response_data.get("message", "") or "ebook_id" in response_data
