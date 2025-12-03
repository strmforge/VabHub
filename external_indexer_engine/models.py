"""
外部索引引擎数据模型

用于解析远程服务返回的 JSON 数据。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RemoteTorrentItem(BaseModel):
    """
    远程服务返回的种子项
    """
    site_id: str = Field(..., description="站点 ID")
    torrent_id: str = Field(..., description="种子 ID")
    title: str = Field(..., description="种子标题")
    size_bytes: Optional[int] = Field(None, description="文件大小（字节）")
    seeders: Optional[int] = Field(None, description="做种数")
    leechers: Optional[int] = Field(None, description="下载数")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    categories: List[str] = Field(default_factory=list, description="分类列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    is_hr: bool = Field(False, description="是否 HR（Hit & Run）")
    free_percent: Optional[int] = Field(None, description="免费百分比（0/30/50/100 等）")
    extra: Dict[str, Any] = Field(default_factory=dict, description="额外字段")


class RemoteTorrentDetail(BaseModel):
    """
    远程服务返回的种子详细信息
    """
    site_id: str = Field(..., description="站点 ID")
    torrent_id: str = Field(..., description="种子 ID")
    title: str = Field(..., description="种子标题")
    description_html: Optional[str] = Field(None, description="描述（HTML）")
    screenshots: List[str] = Field(default_factory=list, description="截图 URL 列表")
    media_info: Optional[str] = Field(None, description="媒体信息")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    extra: Dict[str, Any] = Field(default_factory=dict, description="额外字段")

