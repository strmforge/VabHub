"""
下载通知 Payload Schema

定义下载相关通知的 payload 数据结构，确保前端和 Telegram 端都能结构化消费
"""

from datetime import datetime
from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field


class DownloadBasePayload(BaseModel):
    """下载通知基础 payload"""
    # 统一字段
    title: str = Field(..., description="媒体标题，如 '三体 S01E01'")
    site_name: Optional[str] = Field(None, description="来自哪个 PT 站/源")
    category_label: Optional[str] = Field(None, description="电影/剧集/音乐 等人类可读标签")
    resolution: Optional[str] = Field(None, description="1080p / 2160p / FLAC / ...")
    source_label: Optional[str] = Field(None, description="'订阅引擎' / '手动添加' 等")
    route_name: str = Field(..., description="前端路由名，如 'download-tasks' / 'media-detail'")
    route_params: Dict[str, Any] = Field(default_factory=dict, description="路由参数")


class DownloadSubscriptionMatchedPayload(DownloadBasePayload):
    """订阅命中通知 payload"""
    notification_type: Literal["DOWNLOAD_SUBSCRIPTION_MATCHED"] = "DOWNLOAD_SUBSCRIPTION_MATCHED"
    subscription_id: int = Field(..., description="订阅规则 ID")
    subscription_name: str = Field(..., description="订阅规则名称")
    torrent_id: Optional[int] = Field(None, description="种子内部标识（如果有）")
    rule_labels: Optional[list[str]] = Field(None, description="命中的规则标签，方便调试和展示")


class DownloadTaskCompletedPayload(DownloadBasePayload):
    """下载任务完成通知 payload"""
    notification_type: Literal["DOWNLOAD_TASK_COMPLETED"] = "DOWNLOAD_TASK_COMPLETED"
    task_id: int = Field(..., description="下载任务 ID")
    success: bool = Field(..., description="是否成功入库")
    media_type: Optional[str] = Field(None, description="movie / tv / music / ...")
    season_number: Optional[int] = Field(None, description="季数（电视剧）")
    episode_number: Optional[int] = Field(None, description="集数（电视剧）")
    library_path: Optional[str] = Field(None, description="最终落地路径（可选）")
    file_size_gb: Optional[float] = Field(None, description="文件大小（GB）")
    download_duration_minutes: Optional[int] = Field(None, description="下载耗时（分钟）")


class DownloadHrRiskPayload(DownloadBasePayload):
    """HR 风险预警通知 payload"""
    notification_type: Literal["DOWNLOAD_HR_RISK"] = "DOWNLOAD_HR_RISK"
    risk_level: str = Field(..., description="风险等级：'H&R' / 'HR' / 'H3' / 'H5' / 'WARN'")
    reason: Optional[str] = Field(None, description="风险原因：'站点标记为 H&R' / '需要保种72小时' 等")
    min_seed_time_hours: Optional[int] = Field(None, description="最小保种时长要求（小时）")
    downloaded_bytes: Optional[int] = Field(None, description="已下载字节数")
    uploaded_bytes: Optional[int] = Field(None, description="已上传字节数")
    ratio: Optional[float] = Field(None, description="分享率")
    deadline: Optional[datetime] = Field(None, description="HR 截止时间")
    task_id: Optional[int] = Field(None, description="关联的下载任务 ID")


# 联合类型，用于类型注解
DownloadNotificationPayload = (
    DownloadSubscriptionMatchedPayload | 
    DownloadTaskCompletedPayload | 
    DownloadHrRiskPayload
)


# 工厂函数：根据通知类型创建对应的 payload
def create_download_payload(
    notification_type: str,
    **kwargs
) -> DownloadNotificationPayload:
    """
    根据通知类型创建对应的 payload
    
    Args:
        notification_type: 通知类型字符串
        **kwargs: payload 字段
        
    Returns:
        对应的 payload 实例
        
    Raises:
        ValueError: 不支持的通知类型
    """
    if notification_type == "DOWNLOAD_SUBSCRIPTION_MATCHED":
        return DownloadSubscriptionMatchedPayload(**kwargs)
    elif notification_type == "DOWNLOAD_TASK_COMPLETED":
        return DownloadTaskCompletedPayload(**kwargs)
    elif notification_type == "DOWNLOAD_HR_RISK":
        return DownloadHrRiskPayload(**kwargs)
    else:
        raise ValueError(f"Unsupported download notification type: {notification_type}")


# 验证函数：检查 payload 是否为下载相关通知
def is_download_notification_payload(payload: Dict[str, Any]) -> bool:
    """
    检查 payload 是否为下载相关通知
    
    Args:
        payload: payload 字典
        
    Returns:
        是否为下载相关通知
    """
    notification_type = payload.get("notification_type", "")
    return notification_type in [
        "DOWNLOAD_SUBSCRIPTION_MATCHED",
        "DOWNLOAD_TASK_COMPLETED", 
        "DOWNLOAD_HR_RISK"
    ]


# 风险等级优先级映射（用于去重逻辑）
RISK_LEVEL_PRIORITY = {
    "H&R": 4,
    "HR": 3,
    "H3": 2,
    "H5": 2,
    "WARN": 1,
}


def get_risk_level_priority(risk_level: str) -> int:
    """
    获取风险等级优先级
    
    Args:
        risk_level: 风险等级
        
    Returns:
        优先级数值，越高越危险
    """
    return RISK_LEVEL_PRIORITY.get(risk_level, 0)


def should_upgrade_hr_notification(old_level: Optional[str], new_level: str) -> bool:
    """
    判断是否应该升级 HR 通知
    
    Args:
        old_level: 之前通知的风险等级
        new_level: 新的风险等级
        
    Returns:
        是否应该发送新通知
    """
    if not old_level:
        return True
    
    old_priority = get_risk_level_priority(old_level)
    new_priority = get_risk_level_priority(new_level)
    
    return new_priority > old_priority
