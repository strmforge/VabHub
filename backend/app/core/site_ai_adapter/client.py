"""
站点 AI 适配 Cloudflare API 客户端

封装对 Cloudflare Pages Functions API 的 HTTP 调用。
"""

import httpx
from typing import Optional
from loguru import logger

from app.core.config import settings
from app.core.site_ai_adapter.models import (
    AISiteAdapterConfig,
    SiteAIAdapterResult,
)
from datetime import datetime


class AIAdapterClientError(Exception):
    """AI 适配客户端错误"""
    pass


async def call_cf_adapter(
    *,
    site_id: str,
    site_name: str,
    site_url: str,
    engine: str,
    login_html: str,
    torrents_html: str,
    detail_html: str,
) -> Optional[SiteAIAdapterResult]:
    """
    调用 Cloudflare AI 适配 API
    
    Args:
        site_id: 站点 ID
        site_name: 站点名称
        site_url: 站点基础 URL
        engine: 站点框架类型（如 "nexusphp"）
        login_html: 登录页 HTML
        torrents_html: 种子列表页 HTML
        detail_html: 种子详情页 HTML
        
    Returns:
        SiteAIAdapterResult 或 None（如果调用失败）
        
    Raises:
        AIAdapterClientError: 当配置错误或 API 调用失败时
    """
    if not settings.AI_ADAPTER_ENABLED:
        logger.warning("AI 适配功能已禁用，跳过调用")
        return None
    
    endpoint = settings.AI_ADAPTER_ENDPOINT
    if not endpoint:
        logger.error("AI_ADAPTER_ENDPOINT 未配置")
        raise AIAdapterClientError("AI_ADAPTER_ENDPOINT 未配置")
    
    timeout = settings.AI_ADAPTER_TIMEOUT_SECONDS
    max_html_bytes = settings.AI_ADAPTER_MAX_HTML_BYTES
    
    # 截断过长的 HTML
    def truncate_html(html: str) -> str:
        if len(html.encode('utf-8')) > max_html_bytes:
            truncated = html[:max_html_bytes]
            logger.warning(f"HTML 内容过长，已截断到 {max_html_bytes} 字节")
            return truncated
        return html
    
    login_html = truncate_html(login_html)
    torrents_html = truncate_html(torrents_html)
    detail_html = truncate_html(detail_html)
    
    # 构建请求体
    request_body = {
        "site_id": site_id,
        "engine": engine,
        "samples": {
            "search_html": torrents_html,
            "detail_html": detail_html,
        },
        "hints": {
            "language": "zh-CN",
            "notes": f"站点名称: {site_name}, URL: {site_url}",
        },
    }
    
    # 如果有登录页 HTML，也包含进去（用于认证配置）
    if login_html:
        request_body["samples"]["login_html"] = login_html
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"调用 AI 适配 API: {endpoint} (site_id: {site_id})")
            response = await client.post(
                endpoint,
                json=request_body,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("ok"):
                error_msg = data.get("error", "未知错误")
                logger.error(f"AI 适配 API 返回错误: {error_msg}")
                raise AIAdapterClientError(f"API 返回错误: {error_msg}")
            
            # 解析配置
            config_dict = data.get("config", {})
            if not config_dict:
                raise AIAdapterClientError("API 返回的配置为空")
            
            # 验证并构建配置对象
            try:
                config = AISiteAdapterConfig(**config_dict)
            except Exception as e:
                logger.error(f"解析 AI 适配配置失败: {e}")
                logger.debug(f"原始配置: {config_dict}")
                raise AIAdapterClientError(f"配置格式错误: {e}")
            
            # 构建结果对象
            result = SiteAIAdapterResult(
                site_id=data.get("site_id", site_id),
                engine=data.get("engine", engine),
                config=config,
                raw_model_output=data.get("raw_model_output", ""),
                created_at=datetime.utcnow(),
            )
            
            logger.info(f"AI 适配分析成功 (site_id: {site_id})")
            return result
            
    except httpx.TimeoutException:
        logger.error(f"AI 适配 API 调用超时 (site_id: {site_id}, timeout: {timeout}s)")
        raise AIAdapterClientError(f"API 调用超时（{timeout} 秒）")
    except httpx.HTTPStatusError as e:
        logger.error(f"AI 适配 API HTTP 错误: {e.response.status_code} - {e.response.text}")
        raise AIAdapterClientError(f"HTTP 错误: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"AI 适配 API 请求错误: {e}")
        raise AIAdapterClientError(f"请求失败: {str(e)}")
    except AIAdapterClientError:
        raise
    except Exception as e:
        logger.error(f"AI 适配 API 调用时发生未知错误: {e}")
        raise AIAdapterClientError(f"未知错误: {str(e)}")

