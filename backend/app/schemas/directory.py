"""
目录配置模型
"""
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class DirectoryConfig(BaseModel):
    """目录配置（参考MoviePilot）"""
    
    # 目录路径
    download_path: Optional[str] = Field(
        default=None,
        description="下载目录路径"
    )
    library_path: Optional[str] = Field(
        default=None,
        description="媒体库目录路径"
    )
    
    # 存储类型
    storage: str = Field(
        default="local",
        description="源存储类型（local/115/123等）"
    )
    library_storage: str = Field(
        default="local",
        description="目标存储类型（local/115/123等）"
    )
    
    # 监控类型（决定文件操作模式）
    # "downloader": 下载器监控（定时扫描下载器中的任务）
    # "directory": 目录监控（文件系统实时监控）
    # null: 不监控（手动整理或不整理）
    monitor_type: Optional[str] = Field(
        default=None,
        description="监控类型: downloader(下载器监控) | directory(目录监控) | null(不监控)"
    )
    
    # 整理方式（transfer_type）
    # "copy": 复制
    # "move": 移动
    # "link": 硬链接（仅本地存储到本地存储）
    # "softlink": 软链接（仅本地存储到本地存储）
    transfer_type: Optional[str] = Field(
        default=None,
        description="整理方式: copy(复制) | move(移动) | link(硬链接) | softlink(软链接)"
    )
    
    # 媒体类型和类别
    media_type: Optional[str] = Field(
        default=None,
        description="媒体类型: movie(电影) | tv(电视剧) | anime(动漫)"
    )
    media_category: Optional[str] = Field(
        default=None,
        description="媒体类别（自定义分类）"
    )
    
    # 优先级（数字越小优先级越高）
    priority: int = Field(
        default=0,
        description="优先级（数字越小优先级越高）"
    )
    
    # 是否启用
    enabled: bool = Field(
        default=True,
        description="是否启用此目录配置"
    )
    
    # STRM 支持
    enable_strm: bool = Field(
        default=False,
        description="是否启用 STRM 模式（仅对支持的媒体类型有效，书籍类型强制禁用）"
    )
    
    @model_validator(mode="after")
    def apply_strm_rules(self):
        """应用 STRM 规则：书籍类型强制禁用 STRM"""
        from app.models.enums.media_type import MediaType
        
        # 如果媒体类型是书籍，强制禁用 STRM
        if self.media_type == MediaType.BOOK:
            self.enable_strm = False
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "download_path": "/downloads/movies",
                "library_path": "/media/movies",
                "storage": "local",
                "library_storage": "local",
                "monitor_type": "downloader",
                "transfer_type": "link",
                "media_type": "movie",
                "media_category": None,
                "priority": 0,
                "enabled": True
            }
        }

