"""
作品中心（Work Hub）Schema
"""

from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


class WorkEBookFile(BaseModel):
    """作品电子书文件"""
    id: int
    file_path: str
    format: Optional[str] = None
    file_size_mb: Optional[float] = None
    source_site_id: Optional[str] = None
    source_torrent_id: Optional[str] = None
    download_task_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkEBook(BaseModel):
    """作品电子书信息"""
    id: int
    title: str
    original_title: Optional[str] = None
    author: Optional[str] = None
    series: Optional[str] = None
    volume_index: Optional[str] = None
    language: Optional[str] = None
    publish_year: Optional[int] = None
    isbn: Optional[str] = None
    tags: Optional[str] = None  # 保持 str 格式，与现有实现一致
    description: Optional[str] = None
    cover_url: Optional[str] = None
    extra_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkAudiobookFile(BaseModel):
    """作品有声书文件"""
    id: int
    title: Optional[str] = None  # 从关联的 EBook 获取
    format: Optional[str] = None
    duration_seconds: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    channels: Optional[int] = None
    narrator: Optional[str] = None
    language: Optional[str] = None
    file_size_mb: Optional[float] = None
    source_site_id: Optional[str] = None
    download_task_id: Optional[int] = None
    is_tts_generated: bool = False  # 是否由 TTS 自动生成
    tts_provider: Optional[str] = None  # TTS 提供商（dummy/http/edge_tts 等）
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkComic(BaseModel):
    """作品相关漫画"""
    id: int
    title: str
    series: Optional[str] = None
    volume_index: Optional[int] = None
    author: Optional[str] = None
    illustrator: Optional[str] = None
    language: Optional[str] = None
    region: Optional[str] = None
    publish_year: Optional[int] = None
    cover_url: Optional[str] = None
    tags: Optional[str] = None
    
    class Config:
        from_attributes = True


class WorkComicFile(BaseModel):
    """作品漫画文件"""
    id: int
    comic_id: int
    file_path: str
    file_size_mb: Optional[float] = None
    format: Optional[str] = None
    page_count: Optional[int] = None
    source_site_id: Optional[str] = None
    source_torrent_id: Optional[str] = None
    download_task_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkVideoItem(BaseModel):
    """作品相关视频改编"""
    id: int
    media_type: str  # "movie" | "tv" | "anime" | "short_drama"
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    season_index: Optional[int] = None  # tv/anime 用
    poster_url: Optional[str] = None
    rating: Optional[float] = None
    source_site_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkMusicItem(BaseModel):
    """作品相关音乐"""
    id: int
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    cover_url: Optional[str] = None  # 如果 Music 有的话，可以先留 None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkDetailResponse(BaseModel):
    """作品详情响应"""
    ebook: WorkEBook
    ebook_files: List[WorkEBookFile]
    audiobooks: List[WorkAudiobookFile]
    comics: List[WorkComic]
    comic_files: List[WorkComicFile]
    videos: List[WorkVideoItem] = []  # 相关视频改编
    music: List[WorkMusicItem] = []  # 相关音乐
    links: List[Any] = []  # 手动关联列表（WorkLinkResponse），可选字段，向后兼容

