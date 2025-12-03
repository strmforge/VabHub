"""
通知动作模型
BOT-EXT-2 实现

统一描述通知可执行的操作，供各渠道适配器使用。
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class NotificationActionType(str, Enum):
    """通知动作类型"""
    
    # 基础动作
    OPEN_WEB_URL = "open_web_url"          # 打开纯 URL
    OPEN_WEB_ROUTE = "open_web_route"      # 打开前端路由
    API_CALL = "api_call"                  # 调用后端 API
    MARK_AS_READ = "mark_as_read"          # 标记通知已读
    
    # 媒体相关动作
    OPEN_READING_CENTER = "open_reading_center"   # 打开阅读中心
    OPEN_MANGA = "open_manga"                     # 打开漫画详情
    OPEN_NOVEL = "open_novel"                     # 打开小说详情
    OPEN_AUDIOBOOK = "open_audiobook"             # 打开有声书详情
    OPEN_MUSIC_CENTER = "open_music_center"       # 打开音乐中心
    
    # 操作动作
    DOWNLOAD = "download"                  # 触发下载
    SUBSCRIBE = "subscribe"                # 订阅
    RETRY = "retry"                        # 重试任务


class NotificationAction(BaseModel):
    """通知动作结构"""
    
    id: str = Field(..., description="动作唯一 ID，如 'open_detail'")
    label: str = Field(..., description="按钮/操作显示名称")
    type: NotificationActionType = Field(..., description="动作类型")
    
    # 显示相关
    icon: Optional[str] = Field(None, description="图标名称（前端 mdi- 图标）")
    primary: bool = Field(False, description="是否为主要动作（影响降级优先级）")
    
    # OPEN_WEB_URL 用
    url: Optional[str] = Field(None, description="直接打开的 URL")
    
    # OPEN_WEB_ROUTE 用
    route_name: Optional[str] = Field(None, description="前端路由名称")
    route_params: Optional[dict[str, Any]] = Field(None, description="路由参数")
    route_query: Optional[dict[str, Any]] = Field(None, description="路由查询参数")
    
    # API_CALL 用
    api_path: Optional[str] = Field(None, description="API 路径")
    api_method: str = Field("POST", description="HTTP 方法")
    api_body: Optional[dict[str, Any]] = Field(None, description="请求体")
    
    # 媒体动作用
    media_type: Optional[str] = Field(None, description="媒体类型")
    target_id: Optional[int] = Field(None, description="目标资源 ID")
    
    # 备用字段
    extra: Optional[dict[str, Any]] = Field(None, description="额外数据")
    
    def to_url(self, base_url: str = "") -> Optional[str]:
        """
        将动作转换为 URL（用于不支持按钮的渠道）
        
        Args:
            base_url: 前端基础 URL
            
        Returns:
            可点击的 URL，或 None
        """
        if self.type == NotificationActionType.OPEN_WEB_URL and self.url:
            return self.url
        
        if self.type == NotificationActionType.OPEN_WEB_ROUTE and self.route_name:
            # 简单的路由转 URL
            path = _route_to_path(self.route_name, self.route_params)
            if path:
                url = f"{base_url.rstrip('/')}{path}"
                if self.route_query:
                    query = "&".join(f"{k}={v}" for k, v in self.route_query.items())
                    url = f"{url}?{query}"
                return url
        
        # 媒体动作转 URL
        if self.type == NotificationActionType.OPEN_MANGA and self.target_id:
            return f"{base_url.rstrip('/')}/manga/{self.target_id}"
        
        if self.type == NotificationActionType.OPEN_NOVEL and self.target_id:
            return f"{base_url.rstrip('/')}/work/{self.target_id}"
        
        if self.type == NotificationActionType.OPEN_AUDIOBOOK and self.target_id:
            return f"{base_url.rstrip('/')}/audiobook/{self.target_id}"
        
        if self.type == NotificationActionType.OPEN_READING_CENTER:
            return f"{base_url.rstrip('/')}/reading"
        
        if self.type == NotificationActionType.OPEN_MUSIC_CENTER:
            return f"{base_url.rstrip('/')}/music"
        
        return None
    
    def to_legacy_action(self) -> dict[str, Any]:
        """转换为旧版动作格式（兼容现有 Telegram 按钮）"""
        legacy = {
            "id": self.id,
            "label": self.label,
        }
        
        # 映射动作类型到旧格式
        if self.type in (NotificationActionType.OPEN_WEB_URL, NotificationActionType.OPEN_WEB_ROUTE):
            legacy["type"] = "open"
            legacy["url"] = self.url
        elif self.type == NotificationActionType.DOWNLOAD:
            legacy["type"] = "download"
        elif self.type == NotificationActionType.MARK_AS_READ:
            legacy["type"] = "mark_read"
        elif self.type == NotificationActionType.SUBSCRIBE:
            legacy["type"] = "subscribe"
        else:
            legacy["type"] = "open"
        
        legacy["target"] = self.media_type or ""
        if self.target_id:
            legacy["id"] = self.target_id
        
        return legacy


def _route_to_path(route_name: str, params: Optional[dict[str, Any]] = None) -> str:
    """将路由名称转换为路径（简化映射）"""
    params = params or {}
    
    route_map = {
        "WorkDetail": f"/work/{params.get('ebookId', '')}",
        "MangaReaderPage": f"/manga/{params.get('series_id', '')}",
        "MangaChapterPage": f"/manga/{params.get('series_id', '')}/chapter/{params.get('chapter_id', '')}",
        "AudiobookDetail": f"/audiobook/{params.get('id', '')}",
        "ReadingHub": "/reading",
        "MusicCenter": "/music",
        "Dashboard": "/",
        "Downloads": "/downloads",
        "Subscriptions": "/subscriptions",
    }
    
    return route_map.get(route_name, "/")


# ============== 辅助函数：创建常用动作 ==============

def action_open_url(url: str, label: str = "打开链接", icon: str = "mdi-open-in-new", primary: bool = False) -> NotificationAction:
    """创建打开 URL 动作"""
    return NotificationAction(
        id="open_url",
        label=label,
        type=NotificationActionType.OPEN_WEB_URL,
        url=url,
        icon=icon,
        primary=primary,
    )


def action_open_route(
    route_name: str,
    label: str = "查看详情",
    route_params: Optional[dict] = None,
    route_query: Optional[dict] = None,
    icon: str = "mdi-eye",
    primary: bool = True,
) -> NotificationAction:
    """创建打开路由动作"""
    return NotificationAction(
        id="open_route",
        label=label,
        type=NotificationActionType.OPEN_WEB_ROUTE,
        route_name=route_name,
        route_params=route_params,
        route_query=route_query,
        icon=icon,
        primary=primary,
    )


def action_open_manga(series_id: int, label: str = "打开漫画", icon: str = "mdi-book-open-page-variant") -> NotificationAction:
    """创建打开漫画动作"""
    return NotificationAction(
        id="open_manga",
        label=label,
        type=NotificationActionType.OPEN_MANGA,
        target_id=series_id,
        media_type="manga",
        icon=icon,
        primary=True,
    )


def action_open_novel(ebook_id: int, label: str = "打开小说", icon: str = "mdi-book") -> NotificationAction:
    """创建打开小说动作"""
    return NotificationAction(
        id="open_novel",
        label=label,
        type=NotificationActionType.OPEN_NOVEL,
        target_id=ebook_id,
        media_type="novel",
        icon=icon,
        primary=True,
    )


def action_open_audiobook(audiobook_id: int, label: str = "打开有声书", icon: str = "mdi-headphones") -> NotificationAction:
    """创建打开有声书动作"""
    return NotificationAction(
        id="open_audiobook",
        label=label,
        type=NotificationActionType.OPEN_AUDIOBOOK,
        target_id=audiobook_id,
        media_type="audiobook",
        icon=icon,
        primary=True,
    )


def action_mark_read(
    notification_id: Optional[int] = None,
    target_id: Optional[int] = None,
    media_type: Optional[str] = None,
    label: str = "标记已读",
    icon: str = "mdi-check",
) -> NotificationAction:
    """创建标记已读动作"""
    api_body = {}
    if notification_id:
        api_body["notification_id"] = notification_id
    if target_id:
        api_body["target_id"] = target_id
    if media_type:
        api_body["media_type"] = media_type
    
    return NotificationAction(
        id="mark_read",
        label=label,
        type=NotificationActionType.MARK_AS_READ,
        api_path="/api/notifications/mark_read",
        api_method="POST",
        api_body=api_body,
        icon=icon,
    )


def action_download(
    target_id: int,
    media_type: str,
    label: str = "下载",
    icon: str = "mdi-download",
) -> NotificationAction:
    """创建下载动作"""
    return NotificationAction(
        id="download",
        label=label,
        type=NotificationActionType.DOWNLOAD,
        target_id=target_id,
        media_type=media_type,
        icon=icon,
    )


def action_subscribe(
    target_id: int,
    media_type: str,
    label: str = "订阅",
    icon: str = "mdi-bell-plus",
) -> NotificationAction:
    """创建订阅动作"""
    return NotificationAction(
        id="subscribe",
        label=label,
        type=NotificationActionType.SUBSCRIBE,
        target_id=target_id,
        media_type=media_type,
        icon=icon,
    )


def action_api_call(
    api_path: str,
    label: str,
    api_method: str = "POST",
    api_body: Optional[dict] = None,
    icon: str = "mdi-api",
) -> NotificationAction:
    """创建 API 调用动作"""
    return NotificationAction(
        id="api_call",
        label=label,
        type=NotificationActionType.API_CALL,
        api_path=api_path,
        api_method=api_method,
        api_body=api_body,
        icon=icon,
    )
