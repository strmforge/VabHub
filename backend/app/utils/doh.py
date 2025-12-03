"""
DNS over HTTPS (DOH) 支持
减少DNS污染，提升网络连通性
参考VabHub-1的实现
"""

import base64
import socket
import struct
import urllib.request
import urllib.error
from threading import Lock
from typing import Dict, Optional, List, Any
from loguru import logger

from app.core.config import settings

# DOH缓存
_doh_cache: Dict[str, str] = {}
_doh_lock = Lock()
_doh_timeout = 5

# 保存原始的 socket.getaddrinfo 方法
_orig_getaddrinfo = socket.getaddrinfo


def _doh_query(resolver: str, host: str) -> Optional[str]:
    """
    使用给定的DoH解析器查询给定主机的IP地址（RFC 8484）
    
    Args:
        resolver: DoH解析器地址（如 1.0.0.1）
        host: 要解析的域名
    
    Returns:
        IP地址字符串，如果失败返回None
    """
    try:
        # 构造DNS查询消息（RFC 1035）
        header = b"".join([
            b"\x00\x00",  # ID: 0
            b"\x01\x00",  # FLAGS: 标准递归查询
            b"\x00\x01",  # QDCOUNT: 1
            b"\x00\x00",  # ANCOUNT: 0
            b"\x00\x00",  # NSCOUNT: 0
            b"\x00\x00",  # ARCOUNT: 0
        ])
        
        question = b"".join([
            b"".join([
                struct.pack("B", len(item)) + item.encode("utf-8")
                for item in host.split(".")
            ]) + b"\x00",  # QNAME: 域名序列
            b"\x00\x01",  # QTYPE: A
            b"\x00\x01",  # QCLASS: IN
        ])
        
        message = header + question
        
        # 发送GET请求到DoH解析器（RFC 8484）
        b64message = base64.b64encode(message).decode("utf-8").rstrip("=")
        url = f"https://{resolver}/dns-query?dns={b64message}"
        headers = {"Content-Type": "application/dns-message"}
        
        logger.debug(f"DoH请求: {url}")
        
        request = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request, timeout=_doh_timeout) as response:
            logger.debug(f"解析器({resolver})响应: {response.status}")
            if response.status != 200:
                return None
            resp_body = response.read()
        
        # 解析DNS响应消息（RFC 1035）
        # name（压缩）:2 + type:2 + class:2 + ttl:4 + rdlength:2 = 12字节
        first_rdata_start = len(header) + len(question) + 12
        # rdata（A记录）= 4字节
        first_rdata_end = first_rdata_start + 4
        # 将rdata转换为IP地址
        ip = socket.inet_ntoa(resp_body[first_rdata_start:first_rdata_end])
        logger.debug(f"解析器({resolver})解析 {host} 为 {ip}")
        return ip
        
    except Exception as e:
        logger.error(f"解析器({resolver})请求错误: {e}")
        return None


def _doh_query_json(resolver: str, host: str) -> Optional[str]:
    """
    使用JSON格式的DoH查询（备用方案）
    
    Args:
        resolver: DoH解析器地址
        host: 要解析的域名
    
    Returns:
        IP地址字符串，如果失败返回None
    """
    try:
        url = f"https://{resolver}/dns-query?name={host}&type=A"
        headers = {"Accept": "application/dns-json"}
        
        logger.debug(f"DoH JSON请求: {url}")
        
        request = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request, timeout=_doh_timeout) as response:
            logger.debug(f"解析器({resolver})响应: {response.status}")
            if response.status != 200:
                return None
            
            import json
            response_body = response.read().decode("utf-8")
            logger.debug(f"<== body: {response_body}")
            answer = json.loads(response_body)["Answer"]
            if answer and len(answer) > 0:
                ip = answer[0]["data"]
                logger.debug(f"解析器({resolver})解析 {host} 为 {ip}")
                return ip
            return None
            
    except Exception as e:
        logger.error(f"解析器({resolver})JSON请求错误: {e}")
        return None


def enable_doh(enable: bool):
    """
    启用或禁用DNS over HTTPS
    
    Args:
        enable: 是否启用DOH
    """
    if not enable:
        # 恢复原始的socket.getaddrinfo
        socket.getaddrinfo = _orig_getaddrinfo
        logger.info("DNS over HTTPS已禁用")
        return
    
    # 获取DOH域名列表
    doh_domains = settings.DOH_DOMAINS.split(",")
    doh_domains = [domain.strip() for domain in doh_domains if domain.strip()]
    
    if not doh_domains:
        logger.warning("DOH域名列表为空，DOH功能未启用")
        return
    
    def _patched_getaddrinfo(host, *args, **kwargs):
        """
        socket.getaddrinfo的补丁版本，对指定域名使用DOH解析
        """
        # 检查是否在DOH域名列表中
        host_lower = host.lower()
        use_doh = any(domain.lower() in host_lower or host_lower.endswith(f".{domain.lower()}") 
                     for domain in doh_domains)
        
        if not use_doh:
            # 不在列表中，使用原始DNS解析
            return _orig_getaddrinfo(host, *args, **kwargs)
        
        # 检查缓存
        with _doh_lock:
            ip = _doh_cache.get(host)
        
        if ip is not None:
            logger.debug(f"已解析 [{host}] 为 [{ip}] (缓存)")
            try:
                return _orig_getaddrinfo(ip, *args, **kwargs)
            except Exception:
                # 缓存失效，清除缓存并重新解析
                with _doh_lock:
                    _doh_cache.pop(host, None)
        
        # 使用DoH解析
        resolvers = settings.DOH_RESOLVERS.split(",")
        resolvers = [r.strip() for r in resolvers if r.strip()]
        
        if not resolvers:
            logger.warning("DOH解析器列表为空，使用原始DNS解析")
            return _orig_getaddrinfo(host, *args, **kwargs)
        
        # 尝试多个解析器
        ip = None
        for resolver in resolvers:
            # 先尝试二进制格式
            ip = _doh_query(resolver, host)
            if ip is None:
                # 尝试JSON格式
                ip = _doh_query_json(resolver, host)
            
            if ip is not None:
                logger.info(f"已解析 [{host}] 为 [{ip}] (DoH: {resolver})")
                # 缓存结果
                with _doh_lock:
                    _doh_cache[host] = ip
                break
        
        if ip is None:
            logger.warning(f"DoH解析失败，使用原始DNS解析: {host}")
            return _orig_getaddrinfo(host, *args, **kwargs)
        
        # 使用解析到的IP地址
        try:
            return _orig_getaddrinfo(ip, *args, **kwargs)
        except Exception as e:
            logger.error(f"使用DoH解析的IP地址失败: {e}")
            return _orig_getaddrinfo(host, *args, **kwargs)
    
    # 替换 socket.getaddrinfo 方法
    socket.getaddrinfo = _patched_getaddrinfo
    logger.info(f"DNS over HTTPS已启用，域名列表: {doh_domains}")


def clear_doh_cache():
    """清除DOH缓存"""
    with _doh_lock:
        _doh_cache.clear()
    logger.info("DOH缓存已清除")


def get_doh_cache_stats() -> Dict[str, Any]:
    """获取DOH缓存统计信息"""
    with _doh_lock:
        return {
            "cache_size": len(_doh_cache),
            "cached_domains": list(_doh_cache.keys())
        }

