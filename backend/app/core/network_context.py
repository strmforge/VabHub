"""
网络上下文检测模块

用于判断请求来自内网(LAN)还是外网(WAN)
支持 X-Forwarded-For 反代场景和 CIDR 网段匹配
"""

from enum import Enum
from typing import List
from fastapi import Request
import ipaddress
from loguru import logger

from app.core.config import Settings


class NetworkContext(str, Enum):
    """网络上下文枚举"""
    LAN = "lan"
    WAN = "wan"


def resolve_network_context(request: Request, config: Settings) -> NetworkContext:
    """
    根据 X-Forwarded-For / remote_addr 与 LAN_CIDR_LIST 判断当前请求来自内网还是外网
    
    Args:
        request: FastAPI 请求对象
        config: 应用配置对象
        
    Returns:
        NetworkContext: LAN 或 WAN
        
    处理逻辑：
    1. 优先使用 X-Forwarded-For 头的第一个 IP（反代场景）
    2. 如果没有 X-Forwarded-For，使用 request.client.host
    3. 验证 IP 格式有效性
    4. 与 LAN_CIDR_LIST 中的网段进行匹配
    5. 支持调试模式强制 LAN（FORCE_LAN_MODE 环境变量）
    """
    
    # 调试模式：强制返回 LAN（用于开发测试）
    force_lan_mode = getattr(config, 'FORCE_LAN_MODE', False)
    if force_lan_mode:
        logger.debug("FORCE_LAN_MODE enabled, treating request as LAN")
        return NetworkContext.LAN
    
    # 获取客户端真实 IP
    client_ip = _extract_client_ip(request)
    if not client_ip:
        logger.warning("Failed to extract client IP, defaulting to WAN")
        return NetworkContext.WAN
    
    # 验证 IP 格式
    try:
        ip_obj = ipaddress.ip_address(client_ip)
    except ValueError:
        logger.warning(f"Invalid IP address format: {client_ip}, defaulting to WAN")
        return NetworkContext.WAN
    
    # 检查是否在 LAN 网段内
    lan_cidrs = getattr(config, 'LAN_CIDR_LIST', ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"])
    
    for cidr in lan_cidrs:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            if ip_obj in network:
                logger.debug(f"Client IP {client_ip} matches LAN CIDR {cidr}")
                return NetworkContext.LAN
        except ValueError:
            logger.warning(f"Invalid CIDR format in LAN_CIDR_LIST: {cidr}")
            continue
    
    logger.debug(f"Client IP {client_ip} does not match any LAN CIDRs, treating as WAN")
    return NetworkContext.WAN


def _extract_client_ip(request: Request) -> str | None:
    """
    从请求中提取客户端真实 IP
    
    优先级：
    1. X-Forwarded-For 头的第一个 IP（反代场景）
    2. X-Real-IP 头（常见反代理头）
    3. request.client.host（直连场景）
    
    Returns:
        str | None: 客户端 IP，提取失败返回 None
    """
    
    # 检查 X-Forwarded-For 头
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # X-Forwarded-For 格式: "client, proxy1, proxy2"
        # 取第一个 IP 作为客户端真实 IP
        first_ip = x_forwarded_for.split(",")[0].strip()
        if first_ip:
            logger.debug(f"Using IP from X-Forwarded-For: {first_ip}")
            return first_ip
    
    # 检查 X-Real-IP 头
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        logger.debug(f"Using IP from X-Real-IP: {x_real_ip}")
        return x_real_ip.strip()
    
    # 使用直连 IP
    if request.client and request.client.host:
        logger.debug(f"Using direct connection IP: {request.client.host}")
        return request.client.host
    
    logger.warning("No client IP found in request")
    return None


def is_lan_request(request: Request, config: Settings) -> bool:
    """
    便捷函数：判断是否为内网请求
    
    Args:
        request: FastAPI 请求对象
        config: 应用配置对象
        
    Returns:
        bool: True 表示内网请求，False 表示外网请求
    """
    return resolve_network_context(request, config) == NetworkContext.LAN


def is_wan_request(request: Request, config: Settings) -> bool:
    """
    便捷函数：判断是否为外网请求
    
    Args:
        request: FastAPI 请求对象
        config: 应用配置对象
        
    Returns:
        bool: True 表示外网请求，False 表示内网请求
    """
    return resolve_network_context(request, config) == NetworkContext.WAN
