"""
LLM 客户端抽象层

FUTURE-AI-ORCHESTRATOR-1 P1 实现
提供统一的 LLM 调用接口，支持 HTTP API 和 Dummy 测试模式
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import json
import httpx
from loguru import logger


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """聊天消息"""
    role: MessageRole
    content: str
    name: Optional[str] = None  # 工具调用时的工具名
    tool_call_id: Optional[str] = None  # 工具调用 ID


class LLMToolSpec(BaseModel):
    """LLM 工具定义规范"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: dict = Field(default_factory=dict, description="JSON Schema 格式的参数定义")


class LLMToolCall(BaseModel):
    """LLM 返回的工具调用"""
    id: str = Field(..., description="工具调用 ID")
    name: str = Field(..., description="工具名称")
    arguments: dict = Field(default_factory=dict, description="工具参数")


class LLMResponse(BaseModel):
    """LLM 响应"""
    content: Optional[str] = Field(None, description="文本回复内容")
    tool_calls: list[LLMToolCall] = Field(default_factory=list, description="工具调用列表")
    finish_reason: Optional[str] = Field(None, description="结束原因")
    usage: Optional[dict] = Field(None, description="token 使用情况")
    raw_response: Optional[dict] = Field(None, description="原始响应（调试用）")


class LLMClient(ABC):
    """LLM 客户端抽象基类"""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[LLMToolSpec]] = None,
    ) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            tools: 可选的工具定义列表
            
        Returns:
            LLM 响应
        """
        ...


class HttpLLMClient(LLMClient):
    """
    HTTP LLM 客户端
    
    通过 HTTP API 调用外部 LLM 服务
    支持 OpenAI 兼容的 API 格式
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
        max_tokens: int = 2048,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        
    def _build_headers(self) -> dict:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _build_tools_payload(self, tools: list[LLMToolSpec]) -> list[dict]:
        """将工具定义转换为 OpenAI 格式"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in tools
        ]
    
    def _parse_tool_calls(self, raw_tool_calls: list[dict]) -> list[LLMToolCall]:
        """解析工具调用响应"""
        result = []
        for tc in raw_tool_calls:
            try:
                func = tc.get("function", {})
                arguments_str = func.get("arguments", "{}")
                
                # 尝试解析 JSON 参数
                try:
                    arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                except json.JSONDecodeError:
                    logger.warning(f"[llm_client] 无法解析工具参数 JSON: {arguments_str[:100]}")
                    arguments = {}
                
                result.append(LLMToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=arguments,
                ))
            except Exception as e:
                logger.warning(f"[llm_client] 解析工具调用失败: {e}")
                continue
        return result
    
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[LLMToolSpec]] = None,
    ) -> LLMResponse:
        """发送聊天请求"""
        # 构建请求体
        payload: dict[str, Any] = {
            "messages": [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ],
            "max_tokens": self.max_tokens,
        }
        
        if self.model:
            payload["model"] = self.model
            
        if tools:
            payload["tools"] = self._build_tools_payload(tools)
            payload["tool_choice"] = "auto"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    headers=self._build_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                
            # 解析响应
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            
            return LLMResponse(
                content=message.get("content"),
                tool_calls=self._parse_tool_calls(message.get("tool_calls", [])),
                finish_reason=choice.get("finish_reason"),
                usage=data.get("usage"),
                raw_response=data if logger.level("DEBUG").no <= logger.level("INFO").no else None,
            )
            
        except httpx.TimeoutException:
            logger.error(f"[llm_client] LLM 请求超时: {self.endpoint}")
            return LLMResponse(
                content="[ERROR] LLM 请求超时",
                finish_reason="error",
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[llm_client] LLM 请求失败: {e.response.status_code} - {e.response.text[:200]}")
            return LLMResponse(
                content=f"[ERROR] LLM 请求失败: {e.response.status_code}",
                finish_reason="error",
            )
        except Exception as e:
            logger.error(f"[llm_client] LLM 请求异常: {e}")
            return LLMResponse(
                content=f"[ERROR] LLM 请求异常: {str(e)[:100]}",
                finish_reason="error",
            )


class DummyLLMClient(LLMClient):
    """
    Dummy LLM 客户端
    
    用于测试和离线开发，根据简单规则返回预定义的工具调用
    """
    
    def __init__(self):
        pass
    
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[LLMToolSpec]] = None,
    ) -> LLMResponse:
        """
        根据简单规则返回预定义响应
        
        规则:
        - 包含「韩剧」+「订阅」→ 返回 get_site_and_sub_overview 工具调用
        - 包含「错误」/「报错」/「为什么」+ 站点相关 → 返回 get_health_status + get_log_snapshot
        - 包含「推荐」/「热门」→ 返回 get_recommendation_preview
        - 包含「搜索」/「找」→ 返回 get_search_preview
        - 其它 → 返回简单文本回复
        """
        # 获取用户最后一条消息
        user_prompt = ""
        for msg in reversed(messages):
            if msg.role == MessageRole.USER:
                user_prompt = msg.content.lower()
                break
        
        tool_calls: list[LLMToolCall] = []
        tool_names = [t.name for t in (tools or [])]
        
        # 规则匹配
        if ("韩剧" in user_prompt or "订阅" in user_prompt) and "get_site_and_sub_overview" in tool_names:
            tool_calls.append(LLMToolCall(
                id="dummy_call_1",
                name="get_site_and_sub_overview",
                arguments={"media_type": "tv"},
            ))
            if "get_search_preview" in tool_names and "韩剧" in user_prompt:
                tool_calls.append(LLMToolCall(
                    id="dummy_call_2",
                    name="get_search_preview",
                    arguments={"keyword": "韩剧", "media_type": "tv"},
                ))
                
        elif any(kw in user_prompt for kw in ["错误", "报错", "为什么", "问题", "异常"]):
            if "get_health_status" in tool_names:
                tool_calls.append(LLMToolCall(
                    id="dummy_call_1",
                    name="get_health_status",
                    arguments={},
                ))
            if "get_log_snapshot" in tool_names:
                tool_calls.append(LLMToolCall(
                    id="dummy_call_2",
                    name="get_log_snapshot",
                    arguments={"level": "error"},
                ))
                
        elif any(kw in user_prompt for kw in ["推荐", "热门", "猜你"]):
            if "get_recommendation_preview" in tool_names:
                tool_calls.append(LLMToolCall(
                    id="dummy_call_1",
                    name="get_recommendation_preview",
                    arguments={"media_type": "movie"},
                ))
                
        elif any(kw in user_prompt for kw in ["搜索", "找", "查"]):
            if "get_search_preview" in tool_names:
                # 提取可能的关键词
                keyword = user_prompt.replace("搜索", "").replace("找", "").replace("查", "").strip()[:20]
                tool_calls.append(LLMToolCall(
                    id="dummy_call_1",
                    name="get_search_preview",
                    arguments={"keyword": keyword or "测试"},
                ))
        
        # 如果有工具调用，返回工具调用响应
        if tool_calls:
            return LLMResponse(
                content=None,
                tool_calls=tool_calls,
                finish_reason="tool_calls",
            )
        
        # 没有匹配到规则，返回简单文本回复
        return LLMResponse(
            content="[Dummy Mode] 这是一个测试响应。在实际使用中，请配置外部 LLM Endpoint。\n\n"
                    "我理解您的请求是关于 VabHub 系统的。请尝试以下类型的问题：\n"
                    "- 「帮我分析一下当前站点和订阅情况」\n"
                    "- 「系统最近有什么错误吗」\n"
                    "- 「给我推荐一些热门内容」\n"
                    "- 「搜索 XXX」",
            finish_reason="stop",
        )
