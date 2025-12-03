"""
STRM刮削配置
支持115网盘刮削和本地STRM媒体库刮削
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ScrapeConfig(BaseModel):
    """刮削配置"""
    
    # 115网盘刮削
    scrape_on_cloud: bool = Field(
        default=False,
        description="是否在115网盘刮削（可选，由用户决定）"
    )
    download_scrape_files: bool = Field(
        default=True,
        description="如果115网盘已开启刮削并完成刮削，是否下载刮削文件到本地"
    )
    
    # 本地STRM媒体库刮削
    scrape_on_local: bool = Field(
        default=False,
        description="是否在本地STRM媒体库刮削（可选，由用户决定）"
    )
    
    # 刮削文件类型
    scrape_file_types: List[str] = Field(
        default_factory=lambda: ["nfo", "jpg", "png", "poster.jpg", "fanart.jpg", "banner.jpg"],
        description="刮削文件类型列表"
    )
    
    # 刮削配置（TMDB等）
    tmdb_api_key: Optional[str] = Field(
        default=None,
        description="TMDB API密钥（用于本地刮削）"
    )
    tmdb_language: str = Field(
        default="zh-CN",
        description="TMDB语言设置"
    )

