"""
订阅相关 Schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SubscriptionBase(BaseModel):
    """订阅基础模型"""
    title: str = Field(..., description="订阅标题")
    original_title: Optional[str] = Field(None, description="原始标题")
    year: Optional[int] = Field(None, description="年份")
    media_type: str = Field(..., description="媒体类型: movie, tv")
    tmdb_id: Optional[int] = Field(None, description="TMDB ID")
    tvdb_id: Optional[int] = Field(None, description="TVDB ID")
    imdb_id: Optional[str] = Field(None, description="IMDB ID")
    poster: Optional[str] = Field(None, description="海报URL")
    backdrop: Optional[str] = Field(None, description="背景图URL")
    status: str = Field("active", description="状态: active, paused, completed")
    
    # 电视剧相关字段
    season: Optional[int] = Field(None, description="季数")
    total_episode: Optional[int] = Field(None, description="总集数")
    start_episode: Optional[int] = Field(None, description="起始集数")
    episode_group: Optional[str] = Field(None, description="剧集组ID")
    
    # 基础规则
    quality: Optional[str] = Field(None, description="质量: 4K, 1080p, 720p等")
    resolution: Optional[str] = Field(None, description="分辨率")
    effect: Optional[str] = Field(None, description="特效: HDR, Dolby Vision等")
    sites: Optional[List[str]] = Field(None, description="订阅站点ID列表")
    downloader: Optional[str] = Field(None, description="下载器")
    save_path: Optional[str] = Field(None, description="保存路径")
    min_seeders: int = Field(5, description="最小做种数")
    auto_download: bool = Field(True, description="自动下载")
    best_version: bool = Field(False, description="洗版")
    search_imdbid: bool = Field(False, description="使用IMDB ID搜索")
    
    # 进阶规则
    include: Optional[str] = Field(None, description="包含规则")
    exclude: Optional[str] = Field(None, description="排除规则")
    filter_groups: Optional[List[Dict[str, Any]]] = Field(None, description="优先级规则组")
    search_rules: Optional[Dict[str, Any]] = Field(None, description="其他搜索规则")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="附加元数据")
    
    # 安全策略字段（默认安全）
    allow_hr: bool = Field(False, description="是否允许 HR/H&R")
    allow_h3h5: bool = Field(False, description="是否允许 H3/H5 等扩展规则")
    strict_free_only: bool = Field(False, description="只下载 free/促销种")


class SubscriptionCreate(SubscriptionBase):
    """创建订阅"""
    model_config = ConfigDict(from_attributes=True)


class SubscriptionUpdate(BaseModel):
    """更新订阅"""
    title: Optional[str] = Field(None, description="订阅标题")
    original_title: Optional[str] = Field(None, description="原始标题")
    year: Optional[int] = Field(None, description="年份")
    media_type: Optional[str] = Field(None, description="媒体类型")
    tmdb_id: Optional[int] = Field(None, description="TMDB ID")
    tvdb_id: Optional[int] = Field(None, description="TVDB ID")
    imdb_id: Optional[str] = Field(None, description="IMDB ID")
    poster: Optional[str] = Field(None, description="海报URL")
    backdrop: Optional[str] = Field(None, description="背景图URL")
    status: Optional[str] = Field(None, description="状态")
    
    # 电视剧相关字段
    season: Optional[int] = Field(None, description="季数")
    total_episode: Optional[int] = Field(None, description="总集数")
    start_episode: Optional[int] = Field(None, description="起始集数")
    episode_group: Optional[str] = Field(None, description="剧集组ID")
    
    # 基础规则
    quality: Optional[str] = Field(None, description="质量")
    resolution: Optional[str] = Field(None, description="分辨率")
    effect: Optional[str] = Field(None, description="特效")
    sites: Optional[List[str]] = Field(None, description="订阅站点ID列表")
    downloader: Optional[str] = Field(None, description="下载器")
    save_path: Optional[str] = Field(None, description="保存路径")
    min_seeders: Optional[int] = Field(None, description="最小做种数")
    auto_download: Optional[bool] = Field(None, description="自动下载")
    best_version: Optional[bool] = Field(None, description="洗版")
    search_imdbid: Optional[bool] = Field(None, description="使用IMDB ID搜索")
    
    # 进阶规则
    include: Optional[str] = Field(None, description="包含规则")
    exclude: Optional[str] = Field(None, description="排除规则")
    filter_groups: Optional[List[Dict[str, Any]]] = Field(None, description="优先级规则组")
    search_rules: Optional[Dict[str, Any]] = Field(None, description="其他搜索规则")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="附加元数据")
    
    # 安全策略字段
    allow_hr: Optional[bool] = Field(None, description="是否允许 HR/H&R")
    allow_h3h5: Optional[bool] = Field(None, description="是否允许 H3/H5 等扩展规则")
    strict_free_only: Optional[bool] = Field(None, description="只下载 free/促销种")
    
    enabled: Optional[bool] = Field(None, description="是否启用")


class SubscriptionRead(SubscriptionBase):
    """订阅读取"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="订阅ID")
    user_id: int = Field(..., description="用户ID")
    
    # 运行状态字段
    last_check_at: Optional[datetime] = Field(None, description="最后检查时间")
    last_success_at: Optional[datetime] = Field(None, description="最后成功时间")
    last_error: Optional[str] = Field(None, description="最后错误信息")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_search: Optional[datetime] = Field(None, description="最后搜索时间")
    next_search: Optional[datetime] = Field(None, description="下次搜索时间")


class SubscriptionCheckResult(BaseModel):
    """订阅检查结果"""
    created_tasks: int = Field(0, description="创建的下载任务数")
    filtered_by_hr: int = Field(0, description="因HR/H&R被过滤的数量")
    filtered_by_quality: int = Field(0, description="因质量被过滤的数量")
    filtered_by_site: int = Field(0, description="因站点被过滤的数量")
    filtered_by_h3h5: int = Field(0, description="因H3/H5被过滤的数量")
    filtered_by_free: int = Field(0, description="因非free被过滤的数量")
    total_candidates: int = Field(0, description="总候选数")
    reason: Optional[str] = Field(None, description="失败原因")
    success: bool = Field(False, description="是否成功")


# 分页响应
class SubscriptionResponse(BaseModel):
    """订阅响应"""
    items: List[SubscriptionRead] = Field(..., description="订阅列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


# 简化订阅信息（用于媒体详情页显示）
class SubscriptionSimple(BaseModel):
    """简化订阅信息"""
    id: int = Field(..., description="订阅ID")
    title: str = Field(..., description="订阅标题")
    media_type: str = Field(..., description="媒体类型")
    quality: Optional[str] = Field(None, description="质量要求")
    allow_hr: bool = Field(False, description="是否允许HR")
    allow_h3h5: bool = Field(False, description="是否允许H3H5")
    strict_free_only: bool = Field(False, description="是否只下free")
    enabled: bool = Field(True, description="是否启用")
    last_check_at: Optional[datetime] = Field(None, description="最后检查时间")
    last_success_at: Optional[datetime] = Field(None, description="最后成功时间")
