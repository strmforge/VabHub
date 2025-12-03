"""
网络工具函数
用于获取本机IP地址等信息
"""

import socket
import ipaddress
from typing import Optional, List
from loguru import logger


def get_local_ip() -> Optional[str]:
    """
    获取本机内网IP地址
    
    Returns:
        内网IP地址，如果获取失败则返回None
    """
    try:
        # 方法1: 通过连接外部地址获取本机IP（推荐）
        # 连接到Google DNS服务器，不会实际发送数据
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 不实际连接，只是获取路由信息
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            s.close()
            raise
    except Exception as e:
        logger.debug(f"方法1获取内网IP失败: {e}")
    
    try:
        # 方法2: 获取主机名对应的IP地址
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        # 检查是否是内网IP
        if _is_private_ip(ip):
            return ip
    except Exception as e:
        logger.debug(f"方法2获取内网IP失败: {e}")
    
    try:
        # 方法3: 遍历所有网络接口
        import netifaces
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for addr_info in addresses[netifaces.AF_INET]:
                    ip = addr_info.get("addr")
                    if ip and _is_private_ip(ip) and ip != "127.0.0.1":
                        return ip
    except ImportError:
        logger.debug("netifaces库未安装，跳过方法3")
    except Exception as e:
        logger.debug(f"方法3获取内网IP失败: {e}")
    
    logger.warning("无法获取内网IP地址，使用localhost")
    return None


def _is_private_ip(ip: str) -> bool:
    """
    检查IP地址是否是内网IP
    
    Args:
        ip: IP地址
    
    Returns:
        是否是内网IP
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False


def get_all_local_ips() -> List[str]:
    """
    获取所有本机内网IP地址
    
    Returns:
        内网IP地址列表
    """
    ips = []
    
    try:
        # 方法1: 通过连接外部地址获取
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip not in ips:
                ips.append(ip)
            s.close()
        except Exception:
            s.close()
    except Exception as e:
        logger.debug(f"获取内网IP失败: {e}")
    
    try:
        # 方法2: 使用netifaces获取所有接口的IP
        import netifaces
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for addr_info in addresses[netifaces.AF_INET]:
                    ip = addr_info.get("addr")
                    if ip and _is_private_ip(ip) and ip != "127.0.0.1" and ip not in ips:
                        ips.append(ip)
    except ImportError:
        logger.debug("netifaces库未安装")
    except Exception as e:
        logger.debug(f"获取所有内网IP失败: {e}")
    
    return ips

