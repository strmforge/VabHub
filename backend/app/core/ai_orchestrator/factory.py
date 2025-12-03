"""
LLM 客户端工厂

FUTURE-AI-ORCHESTRATOR-1 P1 实现
根据配置创建对应的 LLM 客户端实例
"""

from typing import Optional
from loguru import logger

from .llm_client import LLMClient, HttpLLMClient, DummyLLMClient


# 全局缓存的 LLM 客户端实例
_llm_client_instance: Optional[LLMClient] = None


def get_llm_client(force_dummy: bool = False) -> LLMClient:
    """
    获取 LLM 客户端实例
    
    Args:
        force_dummy: 是否强制使用 Dummy 客户端（用于测试）
        
    Returns:
        LLM 客户端实例
        
    工厂逻辑:
    1. 如果 force_dummy=True，返回 DummyLLMClient
    2. 如果 AI_ORCH_ENABLED=False，返回 DummyLLMClient 并警告
    3. 如果未配置 AI_ORCH_LLM_ENDPOINT，返回 DummyLLMClient 并警告
    4. 否则根据 AI_ORCH_LLM_PROVIDER 返回对应客户端（目前仅支持 http）
    """
    global _llm_client_instance
    
    # 强制使用 Dummy
    if force_dummy:
        logger.debug("[ai_orch] 使用 DummyLLMClient (force_dummy=True)")
        return DummyLLMClient()
    
    # 延迟导入配置，避免循环依赖
    from app.core.config import settings
    
    # 检查是否启用
    if not settings.AI_ORCH_ENABLED:
        logger.warning(
            "[ai_orch] AI Orchestrator 未启用 (AI_ORCH_ENABLED=false)，"
            "使用 DummyLLMClient。如需使用真实 LLM，请在配置中启用。"
        )
        return DummyLLMClient()
    
    # 检查 Endpoint 配置
    if not settings.AI_ORCH_LLM_ENDPOINT:
        logger.warning(
            "[ai_orch] 未配置 AI_ORCH_LLM_ENDPOINT，使用 DummyLLMClient。"
            "请配置 LLM API 端点以使用完整功能。"
        )
        return DummyLLMClient()
    
    # 检查缓存
    if _llm_client_instance is not None:
        return _llm_client_instance
    
    # 根据 provider 创建客户端
    provider = settings.AI_ORCH_LLM_PROVIDER.lower()
    
    if provider == "http":
        _llm_client_instance = HttpLLMClient(
            endpoint=settings.AI_ORCH_LLM_ENDPOINT,
            api_key=settings.AI_ORCH_LLM_API_KEY,
            model=settings.AI_ORCH_LLM_MODEL,
            timeout=settings.AI_ORCH_LLM_TIMEOUT,
            max_tokens=settings.AI_ORCH_LLM_MAX_TOKENS,
        )
        logger.info(
            f"[ai_orch] 已创建 HttpLLMClient: "
            f"endpoint={settings.AI_ORCH_LLM_ENDPOINT[:50]}..., "
            f"model={settings.AI_ORCH_LLM_MODEL}"
        )
    else:
        logger.warning(
            f"[ai_orch] 不支持的 LLM provider: {provider}，使用 DummyLLMClient。"
            f"目前仅支持: http"
        )
        _llm_client_instance = DummyLLMClient()
    
    return _llm_client_instance


def reset_llm_client() -> None:
    """
    重置 LLM 客户端实例
    
    用于配置变更后重新创建客户端
    """
    global _llm_client_instance
    _llm_client_instance = None
    logger.debug("[ai_orch] LLM 客户端实例已重置")
