"""
远程插件协议定义
PLUGIN-REMOTE-1 实现

定义 VabHub 与远程插件之间的 HTTP 通信协议
"""

from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field
import httpx
from loguru import logger


class RemotePluginEventType(str, Enum):
    """远程插件事件类型"""
    MANGA_UPDATED = "manga.updated"
    AUDIOBOOK_TTS_FINISHED = "audiobook.tts_finished"
    DOWNLOAD_COMPLETED = "download.completed"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    # 可扩展...


class RemotePluginEvent(BaseModel):
    """推送到远程插件的事件"""
    plugin_id: str
    event: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RemotePluginResponse(BaseModel):
    """远程插件响应"""
    status: str  # "success" | "error" | "ignored"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class RemotePluginClient:
    """
    远程插件 HTTP 客户端
    
    负责向远程插件推送事件，包含超时、重试和熔断机制
    """
    
    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 5):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._is_circuit_open = False
        
    @property
    def events_endpoint(self) -> str:
        """事件推送端点"""
        return f"{self.base_url}/events"
    
    async def push_event(self, event: RemotePluginEvent) -> RemotePluginResponse:
        """
        推送事件到远程插件
        
        Args:
            event: 要推送的事件
            
        Returns:
            远程插件响应
            
        Raises:
            httpx.RequestError: 网络请求失败
            ValueError: 响应格式错误
        """
        # 检查熔断器状态
        if self._is_circuit_open:
            if self._should_attempt_reset():
                self._is_circuit_open = False
                self._failure_count = 0
                logger.info(f"[remote-protocol] Circuit breaker reset for {self.base_url}")
            else:
                raise RuntimeError(f"Circuit breaker is open for {self.base_url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Content-Type": "application/json"}
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                
                response = await client.post(
                    self.events_endpoint,
                    json=event.model_dump(),
                    headers=headers
                )
                response.raise_for_status()
                
                # 解析响应
                response_data = response.json()
                plugin_response = RemotePluginResponse(**response_data)
                
                # 成功则重置失败计数
                if plugin_response.status == "success":
                    self._failure_count = 0
                    self._last_failure_time = None
                else:
                    self._record_failure()
                
                logger.debug(f"[remote-protocol] Event pushed to {self.base_url}: {plugin_response.status}")
                return plugin_response
                
        except httpx.RequestError as e:
            self._record_failure()
            logger.error(f"[remote-protocol] Network error pushing to {self.base_url}: {e}")
            raise
        except Exception as e:
            self._record_failure()
            logger.error(f"[remote-protocol] Error pushing to {self.base_url}: {e}")
            raise
    
    def _record_failure(self):
        """记录失败"""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        # 失败次数达到阈值，打开熔断器
        if self._failure_count >= 5:  # 可配置
            self._is_circuit_open = True
            logger.warning(f"[remote-protocol] Circuit breaker opened for {self.base_url} after {self._failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        if not self._last_failure_time:
            return True
        
        # 5分钟后尝试重置
        reset_timeout = 300  # 可配置
        return (datetime.utcnow() - self._last_failure_time).total_seconds() > reset_timeout
    
    @property
    def is_healthy(self) -> bool:
        """检查客户端是否健康"""
        return not self._is_circuit_open and self._failure_count < 3


def create_remote_client(plugin_config: Dict[str, Any]) -> Optional[RemotePluginClient]:
    """
    从插件配置创建远程客户端
    
    Args:
        plugin_config: 插件远程配置
        
    Returns:
        RemotePluginClient 或 None
    """
    if not plugin_config:
        return None
    
    base_url = plugin_config.get("base_url")
    if not base_url:
        logger.error("[remote-protocol] Missing base_url in remote config")
        return None
    
    token = plugin_config.get("token")
    timeout = plugin_config.get("timeout", 5)
    
    return RemotePluginClient(base_url=base_url, token=token, timeout=timeout)
