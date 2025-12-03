"""
115网盘OAuth2认证客户端
基于115网盘官方API文档实现OAuth2 + PKCE模式认证
参考：115网盘开放平台官方文档
"""

import httpx
import secrets
import hashlib
import base64
from typing import Dict, Optional, Tuple, Any
from loguru import logger


class Cloud115OAuth:
    """115网盘OAuth2认证客户端"""
    
    def __init__(self, client_id: str):
        """
        初始化115网盘OAuth2认证客户端
        
        Args:
            client_id: 应用ID（AppID）
        """
        self.client_id = client_id
        self.passport_url = "https://passportapi.115.com"
        self.qrcode_url = "https://qrcodeapi.115.com"
        
        # PKCE参数
        self.code_verifier: Optional[str] = None
        self.code_challenge: Optional[str] = None
        self.code_challenge_method: str = "sha256"
        
        # 设备码授权状态
        self.auth_state: Dict[str, Any] = {}
    
    def generate_pkce_params(self) -> Tuple[str, str]:
        """
        生成PKCE参数
        
        Returns:
            (code_verifier, code_challenge)
        """
        # 生成43-128位的随机字符串作为code_verifier
        # 使用secrets.token_urlsafe生成安全的随机字符串
        code_verifier = secrets.token_urlsafe(96)[:128]
        
        # 计算code_challenge
        # code_challenge = url_safe(base64_encode(sha256(code_verifier)))
        sha256_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(sha256_hash).decode("utf-8").replace('=', '')
        
        self.code_verifier = code_verifier
        self.code_challenge = code_challenge
        
        logger.debug(f"生成PKCE参数: code_verifier长度={len(code_verifier)}, code_challenge={code_challenge[:20]}...")
        
        return code_verifier, code_challenge
    
    async def get_device_code(self) -> Dict[str, Any]:
        """
        获取设备码和二维码内容
        
        API: POST https://passportapi.115.com/open/authDeviceCode
        
        Returns:
            设备码和二维码信息
        """
        url = f"{self.passport_url}/open/authDeviceCode"
        
        # 生成PKCE参数
        if not self.code_verifier or not self.code_challenge:
            self.generate_pkce_params()
        
        # 请求参数
        data = {
            "client_id": self.client_id,
            "code_challenge": self.code_challenge,
            "code_challenge_method": self.code_challenge_method
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") == 0:
                    data = result.get("data", {})
                    
                    # 保存授权状态
                    self.auth_state = {
                        "uid": data.get("uid"),
                        "time": data.get("time"),
                        "sign": data.get("sign"),
                        "qrcode": data.get("qrcode")
                    }
                    
                    logger.info("获取设备码和二维码成功")
                    return {
                        "uid": data.get("uid"),
                        "qrcode": data.get("qrcode"),
                        "time": data.get("time"),
                        "sign": data.get("sign"),
                        "qr_url": f"https://115.com/?qr_code={data.get('qrcode')}"
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    logger.error(f"获取设备码失败: {error_msg} (code: {result.get('code')})")
                    return {}
                    
            except Exception as e:
                logger.error(f"获取设备码异常: {e}")
                return {}
    
    async def poll_qr_status(self, timeout: int = 300) -> Dict[str, Any]:
        """
        轮询二维码状态（长轮询接口）
        
        API: GET https://qrcodeapi.115.com/get/status/
        
        Args:
            timeout: 超时时间（秒），默认300秒
        
        Returns:
            二维码状态信息
        """
        if not self.auth_state:
            logger.error("请先获取设备码")
            return {"status": -1, "message": "请先获取设备码"}
        
        url = f"{self.qrcode_url}/get/status/"
        
        params = {
            "uid": self.auth_state.get("uid"),
            "time": self.auth_state.get("time"),
            "sign": self.auth_state.get("sign")
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
                
                # 解析响应
                if result.get("code") == 0:
                    data = result.get("data", {})
                    status = data.get("status", -1)
                    message = data.get("msg", "")
                    
                    # 状态说明:
                    # 0: 未扫码/二维码无效
                    # 1: 扫码成功，等待确认
                    # 2: 确认登录/授权，结束轮询
                    
                    return {
                        "status": status,
                        "message": message,
                        "state": result.get("state", 1),  # 1:继续轮询, 0:结束轮询
                        "data": data
                    }
                else:
                    # code != 0 表示二维码无效，结束轮询
                    error_msg = result.get("message", "未知错误")
                    logger.warning(f"轮询二维码状态失败: {error_msg} (code: {result.get('code')})")
                    return {
                        "status": -1,
                        "message": error_msg,
                        "state": 0  # 结束轮询
                    }
                    
            except httpx.TimeoutException:
                logger.warning("轮询二维码状态超时，继续轮询")
                return {
                    "status": 0,
                    "message": "等待扫码",
                    "state": 1  # 继续轮询
                }
            except Exception as e:
                logger.error(f"轮询二维码状态异常: {e}")
                return {
                    "status": -1,
                    "message": str(e),
                    "state": 0  # 结束轮询
                }
    
    async def get_access_token(self) -> Dict[str, Any]:
        """
        用设备码换取access_token
        
        API: POST https://passportapi.115.com/open/deviceCodeToToken
        
        Returns:
            访问令牌信息
        """
        if not self.auth_state or not self.code_verifier:
            logger.error("请先获取设备码并确认授权")
            return {}
        
        url = f"{self.passport_url}/open/deviceCodeToToken"
        
        data = {
            "uid": self.auth_state.get("uid"),
            "code_verifier": self.code_verifier
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回code=0或state=1
                if result.get("code") == 0:
                    data = result.get("data", {})
                    
                    # 根据官方文档，返回access_token和refresh_token
                    # access_token: 用于访问资源接口的凭证
                    # refresh_token: 用于刷新access_token，有效期1年
                    # expires_in: access_token有效期，单位秒（mock值7200，即2小时）
                    access_token = data.get("access_token")
                    refresh_token = data.get("refresh_token")
                    expires_in = data.get("expires_in", 7200)  # 默认7200秒（2小时）
                    
                    logger.info(f"获取访问令牌成功: expires_in={expires_in}秒")
                    return {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_in": expires_in,
                        "token_type": "Bearer"
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code") or result.get("errno")
                    logger.error(f"获取访问令牌失败: {error_msg} (code: {error_code})")
                    return {}
                    
            except Exception as e:
                logger.error(f"获取访问令牌异常: {e}")
                return {}
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌
        
        API: POST https://passportapi.115.com/open/refreshToken
        参考：115网盘开放平台官方文档
        
        注意事项：
        - 请勿频繁刷新，否则列入频控
        - access_token: 新的access_token，同时刷新有效期
        - refresh_token: 新的refresh_token，有效期不延长不改变
        - expires_in: access_token有效期，单位秒（默认2592000，即30天）
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的访问令牌信息
        """
        url = f"{self.passport_url}/open/refreshToken"
        
        data = {
            "refresh_token": refresh_token
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回code=0或state=1
                if result.get("code") == 0:
                    data = result.get("data", {})
                    
                    # 根据官方文档，返回新的access_token和refresh_token
                    # refresh_token: 新的refresh_token，有效期不延长不改变
                    # access_token: 新的access_token，同时刷新有效期
                    # expires_in: access_token有效期，单位秒（mock值2592000，即30天）
                    new_access_token = data.get("access_token")
                    new_refresh_token = data.get("refresh_token")
                    expires_in = data.get("expires_in", 2592000)  # 默认30天
                    
                    logger.info(f"刷新访问令牌成功: expires_in={expires_in}秒")
                    return {
                        "access_token": new_access_token,
                        "refresh_token": new_refresh_token,  # 使用新的refresh_token
                        "expires_in": expires_in,
                        "token_type": "Bearer"
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code") or result.get("errno")
                    logger.error(f"刷新访问令牌失败: {error_msg} (code: {error_code})")
                    return {}
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"刷新访问令牌HTTP错误: {e.response.status_code}")
                return {}
            except Exception as e:
                logger.error(f"刷新访问令牌异常: {e}")
                return {}
    
    async def authorize(self, poll_interval: int = 2, max_polls: int = 150) -> Dict[str, Any]:
        """
        完整的授权流程
        
        Args:
            poll_interval: 轮询间隔（秒），默认2秒
            max_polls: 最大轮询次数，默认150次（5分钟）
        
        Returns:
            访问令牌信息
        """
        import asyncio
        
        # Step 1: 获取设备码和二维码
        logger.info("Step 1: 获取设备码和二维码")
        device_info = await self.get_device_code()
        
        if not device_info:
            return {}
        
        qrcode = device_info.get("qrcode")
        qr_url = device_info.get("qr_url")
        
        logger.info(f"二维码已生成，请使用115客户端扫码: {qr_url}")
        logger.info(f"二维码内容: {qrcode}")
        
        # Step 2: 轮询二维码状态
        logger.info("Step 2: 开始轮询二维码状态")
        poll_count = 0
        
        while poll_count < max_polls:
            await asyncio.sleep(poll_interval)
            poll_count += 1
            
            status_info = await self.poll_qr_status(timeout=30)
            status = status_info.get("status", -1)
            message = status_info.get("message", "")
            state = status_info.get("state", 1)
            
            if status == 2:
                # 确认登录/授权，结束轮询
                logger.info("用户已确认授权，开始获取访问令牌")
                break
            elif status == 1:
                # 扫码成功，等待确认
                logger.info(f"用户已扫码，等待确认... ({message})")
            elif status == 0:
                # 未扫码
                if poll_count % 10 == 0:  # 每10次轮询打印一次
                    logger.info(f"等待用户扫码... ({poll_count}/{max_polls})")
            elif state == 0:
                # 二维码无效，结束轮询
                logger.error(f"二维码无效或已过期: {message}")
                return {}
            else:
                logger.warning(f"未知状态: {status}, {message}")
        
        if poll_count >= max_polls:
            logger.error("轮询超时，用户未在规定时间内完成授权")
            return {}
        
        # Step 3: 获取访问令牌
        logger.info("Step 3: 获取访问令牌")
        token_info = await self.get_access_token()
        
        if token_info:
            logger.info("授权成功，已获取访问令牌")
        else:
            logger.error("授权失败，无法获取访问令牌")
        
        return token_info

