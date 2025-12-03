"""
外部索引桥接数据模型

定义外部索引引擎返回的数据结构。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ExternalTorrentResult(BaseModel):
    """
    外部索引引擎返回的种子搜索结果
    """
    site_id: str = Field(..., description="站点 ID")
    site_name: Optional[str] = Field(None, description="站点名称")
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
    raw: Dict[str, Any] = Field(default_factory=dict, description="外部原始数据")
    
    @property
    def size_gb(self) -> Optional[float]:
        """计算大小（GB）"""
        if self.size_bytes is None:
            return None
        return round(self.size_bytes / (1024 ** 3), 2)
    
    @property
    def is_free(self) -> bool:
        """判断是否完全免费"""
        return self.free_percent == 100
    
    @property
    def is_half_free(self) -> bool:
        """判断是否半免费"""
        return self.free_percent == 50


class ExternalTorrentDetail(BaseModel):
    """
    外部索引引擎返回的种子详细信息
    """
    site_id: str = Field(..., description="站点 ID")
    torrent_id: str = Field(..., description="种子 ID")
    title: str = Field(..., description="种子标题")
    description_html: Optional[str] = Field(None, description="描述（HTML）")
    screenshots: List[str] = Field(default_factory=list, description="截图 URL 列表")
    media_info: Optional[str] = Field(None, description="媒体信息")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    raw: Dict[str, Any] = Field(default_factory=dict, description="外部原始数据")


class ExternalSiteConfig(BaseModel):
    """
    外部站点配置
    """
    site_id: str = Field(..., description="站点 ID")
    name: str = Field(..., description="站点名称")
    base_url: str = Field(..., description="站点基础 URL")
    framework: Optional[str] = Field(None, description="站点框架（如 nexusphp/gazelle）")
    enabled: bool = Field(True, description="是否启用")
    capabilities: List[str] = Field(default_factory=list, description="支持的能力列表（如 search/rss/detail）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "site_id": "example_site",
                "name": "Example Site",
                "base_url": "https://example.com",
                "framework": "nexusphp",
                "enabled": True,
                "capabilities": ["search", "rss", "detail"],
            }
        }

