"""
WeChat通知渠道（企业微信）
"""
import httpx
from typing import Dict, Optional, Any
from datetime import datetime
from loguru import logger

from .base import NotificationChannelBase


class WeChatChannel(NotificationChannelBase):
    """WeChat通知渠道（企业微信）"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化WeChat渠道
        
        Args:
            config: 配置字典，包含：
                - webhook_url: 企业微信机器人Webhook URL（推荐方式）
                或
                - corpid: 企业ID
                - app_secret: 应用密钥
                - app_id: 应用ID
                - api_url: 自定义API URL（可选，用于代理）
        """
        super().__init__(config)
        
        # Webhook方式（推荐，更简单）
        self.webhook_url = config.get("webhook_url")
        
        # 企业微信API方式（需要corpid、app_secret、app_id）
        self.corpid = config.get("corpid")
        self.app_secret = config.get("app_secret")
        self.app_id = config.get("app_id")
        self.api_url = config.get("api_url", "https://qyapi.weixin.qq.com")
        
        # Token缓存
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        # Webhook方式或API方式都可以
        return bool(self.webhook_url) or bool(self.corpid and self.app_secret and self.app_id)
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """验证配置"""
        if self.webhook_url:
            # Webhook方式
            return True, None
        elif self.corpid and self.app_secret and self.app_id:
            # API方式
            return True, None
        else:
            return False, "WeChat配置不完整：需要webhook_url或(corpid、app_secret、app_id)"
    
    async def _get_access_token(self) -> Optional[str]:
        """
        获取企业微信Access Token（仅API方式需要）
        
        Returns:
            Access Token或None
        """
        if self.webhook_url:
            # Webhook方式不需要Token
            return None
        
        if not self.corpid or not self.app_secret:
            return None
        
        # 检查Token是否过期
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        try:
            # 获取新Token
            token_url = f"{self.api_url}/cgi-bin/gettoken"
            params = {
                "corpid": self.corpid,
                "corpsecret": self.app_secret
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(token_url, params=params)
                
                if response.is_success:
                    result = response.json()
                    if result.get("errcode") == 0:
                        self._access_token = result.get("access_token")
                        expires_in = result.get("expires_in", 7200)
                        self._token_expires_at = datetime.now().replace(
                            second=0, microsecond=0
                        ).replace(second=expires_in - 300)  # 提前5分钟过期
                        return self._access_token
                    else:
                        logger.error(f"获取WeChat Token失败: {result.get('errmsg')}")
                        return None
                else:
                    logger.error(f"获取WeChat Token HTTP错误: {response.status_code}")
                    return None
        
        except Exception as e:
            logger.error(f"获取WeChat Token异常: {e}")
            return None
    
    def _format_message(self, title: str, message: str, notification_type: str) -> str:
        """
        格式化消息
        
        Args:
            title: 标题
            message: 内容
            notification_type: 通知类型
        
        Returns:
            格式化后的消息
        """
        # 根据通知类型添加emoji
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }
        emoji = emoji_map.get(notification_type, "📢")
        
        return f"{emoji} {title}\n\n{message}"
    
    async def _send_via_webhook(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        通过Webhook发送消息（推荐方式）
        
        Args:
            title: 标题
            message: 内容
            notification_type: 通知类型
            metadata: 额外元数据
        
        Returns:
            发送结果
        """
        try:
            # 格式化消息
            text = self._format_message(title, message, notification_type)
            
            # 添加链接（如果有）
            if metadata and metadata.get("link"):
                text = f"{text}\n\n查看详情: {metadata.get('link')}"
            
            # 构建请求数据
            payload = {
                "msgtype": "text",
                "text": {
                    "content": text
                }
            }
            
            # 发送请求
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                
                if response.is_success:
                    result = response.json()
                    if result.get("errcode") == 0:
                        return {
                            "success": True,
                            "channel": "wechat",
                            "message": "WeChat消息已发送"
                        }
                    else:
                        error_msg = result.get("errmsg", "未知错误")
                        return {
                            "success": False,
                            "channel": "wechat",
                            "error": f"WeChat API错误: {error_msg}"
                        }
                else:
                    return {
                        "success": False,
                        "channel": "wechat",
                        "error": f"HTTP错误: {response.status_code} - {response.text}"
                    }
        
        except httpx.TimeoutException:
            logger.error("WeChat通知发送超时")
            return {
                "success": False,
                "channel": "wechat",
                "error": "请求超时"
            }
        except Exception as e:
            logger.error(f"发送WeChat通知失败: {e}")
            return {
                "success": False,
                "channel": "wechat",
                "error": str(e)
            }
    
    async def _send_via_api(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        通过企业微信API发送消息
        
        Args:
            title: 标题
            message: 内容
            notification_type: 通知类型
            metadata: 额外元数据
        
        Returns:
            发送结果
        """
        # 获取Access Token
        access_token = await self._get_access_token()
        if not access_token:
            return {
                "success": False,
                "channel": "wechat",
                "error": "获取WeChat Access Token失败"
            }
        
        try:
            # 格式化消息
            text = self._format_message(title, message, notification_type)
            
            # 添加链接（如果有）
            if metadata and metadata.get("link"):
                text = f"{text}\n\n查看详情: {metadata.get('link')}"
            
            # 构建请求数据
            payload = {
                "touser": "@all",  # 发送给所有人，可以通过metadata指定userid
                "msgtype": "text",
                "agentid": self.app_id,
                "text": {
                    "content": text
                },
                "safe": 0
            }
            
            # 如果指定了用户ID
            if metadata and metadata.get("userid"):
                payload["touser"] = metadata.get("userid")
            
            # 发送请求
            send_url = f"{self.api_url}/cgi-bin/message/send"
            params = {"access_token": access_token}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(send_url, params=params, json=payload)
                
                if response.is_success:
                    result = response.json()
                    if result.get("errcode") == 0:
                        return {
                            "success": True,
                            "channel": "wechat",
                            "message": "WeChat消息已发送"
                        }
                    else:
                        error_msg = result.get("errmsg", "未知错误")
                        # Token过期，清除缓存
                        if result.get("errcode") == 42001:
                            self._access_token = None
                            self._token_expires_at = None
                        return {
                            "success": False,
                            "channel": "wechat",
                            "error": f"WeChat API错误: {error_msg}"
                        }
                else:
                    return {
                        "success": False,
                        "channel": "wechat",
                        "error": f"HTTP错误: {response.status_code} - {response.text}"
                    }
        
        except httpx.TimeoutException:
            logger.error("WeChat通知发送超时")
            return {
                "success": False,
                "channel": "wechat",
                "error": "请求超时"
            }
        except Exception as e:
            logger.error(f"发送WeChat通知失败: {e}")
            return {
                "success": False,
                "channel": "wechat",
                "error": str(e)
            }
    
    async def send(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送WeChat通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型
            metadata: 额外元数据
        
        Returns:
            发送结果
        """
        if not self.is_configured():
            return {
                "success": False,
                "channel": "wechat",
                "error": "WeChat配置不完整"
            }
        
        # 优先使用Webhook方式
        if self.webhook_url:
            return await self._send_via_webhook(title, message, notification_type, metadata)
        else:
            return await self._send_via_api(title, message, notification_type, metadata)
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接
        
        Returns:
            测试结果
        """
        return await self.send(
            title="测试通知",
            message="这是一条测试消息，用于验证WeChat配置是否正确。",
            notification_type="info"
        )

