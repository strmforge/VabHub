"""
CookieCloud同步功能
"""
import httpx
from typing import List, Dict, Optional
from loguru import logger
import json
import base64

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    import hashlib
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("pycryptodome未安装，CookieCloud密码解密功能将不可用")


class CookieCloudClient:
    """CookieCloud客户端"""
    
    def __init__(self, server_url: str, uuid: str, password: str = ""):
        self.server_url = server_url.rstrip('/')
        self.uuid = uuid
        self.password = password
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _derive_key(self) -> str:
        """根据官方标准派生AES密钥：md5(uuid-password)[:16]"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("pycryptodome未安装，无法进行密码解密")
        # CookieCloud官方算法：md5(uuid-password)取前16位
        key_string = hashlib.md5(f"{self.uuid}-{self.password}".encode()).hexdigest()[:16]
        return key_string
    
    def _decrypt(self, encrypted_data: str) -> Dict:
        """使用官方标准解密Cookie数据"""
        if not CRYPTO_AVAILABLE:
            logger.error("pycryptodome未安装，无法解密")
            return {}
        try:
            # 根据官方标准派生密钥
            key_string = self._derive_key()
            
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # AES解密（CryptoJS兼容模式）
            cipher = AES.new(key_string.encode(), AES.MODE_CBC, encrypted_bytes[:16])
            decrypted = unpad(cipher.decrypt(encrypted_bytes[16:]), AES.block_size)
            
            # JSON解析
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            logger.error(f"CookieCloud解密失败: {e}")
            return {}
    
    async def get_cookies(self) -> Optional[Dict]:
        """获取Cookie数据"""
        try:
            # CookieCloud API端点
            url = f"{self.server_url}/get/{self.uuid}"
            
            # 发送请求
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # 官方API返回格式：{"encrypted": "base64_string"}
                if data.get("encrypted"):
                    encrypted_data = data["encrypted"]
                    
                    # 如果提供了密码，需要解密
                    if self.password and CRYPTO_AVAILABLE:
                        try:
                            cookie_data = self._decrypt(encrypted_data)
                            logger.info(f"CookieCloud解密成功，获取到{len(cookie_data.get('cookie_data', {}))}个域名的Cookie")
                            return self._parse_cookies(cookie_data)
                        except Exception as e:
                            logger.error(f"CookieCloud解密失败: {e}")
                            return None
                    elif self.password and not CRYPTO_AVAILABLE:
                        logger.error("CookieCloud需要密码解密，但pycryptodome未安装")
                        return None
                    else:
                        # 如果没有密码，返回空数据
                        logger.warning("未提供密码，无法解密CookieCloud数据")
                        return {}
                
                # 兼容旧格式或无加密数据
                elif data.get("cookie_data"):
                    cookie_data = data["cookie_data"]
                    return self._parse_cookies(cookie_data)
                
                else:
                    logger.warning("CookieCloud返回数据格式不正确")
                    return None
            else:
                logger.error(f"获取CookieCloud数据失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"CookieCloud同步异常: {e}")
            return None
    
    def _parse_cookies(self, cookie_data: Dict) -> Dict:
        """解析Cookie数据，处理官方API返回的{cookie_data, local_storage_data}结构"""
        parsed = {}
        
        if not isinstance(cookie_data, dict):
            return parsed
        
        # 官方API返回格式：{cookie_data: {...}, local_storage_data: {...}}
        # 我们只需要cookie_data部分
        cookie_content = cookie_data.get("cookie_data", {})
        
        if not isinstance(cookie_content, dict):
            return parsed
        
        for domain, cookies in cookie_content.items():
            if isinstance(cookies, list):
                # 提取Cookie字符串
                cookie_strings = []
                for cookie in cookies:
                    if isinstance(cookie, dict):
                        name = cookie.get("name", "")
                        value = cookie.get("value", "")
                        if name and value:
                            cookie_strings.append(f"{name}={value}")
                
                if cookie_strings:
                    parsed[domain] = "; ".join(cookie_strings)
            elif isinstance(cookies, str):
                # 如果已经是字符串，直接使用
                parsed[domain] = cookies
        
        logger.debug(f"解析Cookie完成，获取到{len(parsed)}个域名的Cookie")
        return parsed
    
    async def sync_to_sites(self, sites: List[Dict]) -> Dict[str, bool]:
        """同步Cookie到站点"""
        cookies = await self.get_cookies()
        
        if not cookies:
            return {}
        
        results = {}
        for site in sites:
            site_url = site.get("url", "")
            site_name = site.get("name", "")
            
            # 匹配域名
            matched_cookie = None
            for domain, cookie_string in cookies.items():
                # 提取域名部分进行匹配
                domain_clean = domain.replace("http://", "").replace("https://", "").split("/")[0]
                site_domain = site_url.replace("http://", "").replace("https://", "").split("/")[0]
                
                if domain_clean in site_domain or site_domain in domain_clean:
                    matched_cookie = cookie_string
                    break
            
            if matched_cookie:
                results[site_name] = True
                logger.info(f"成功同步Cookie到站点: {site_name}")
            else:
                results[site_name] = False
                logger.warning(f"未找到匹配的Cookie: {site_name}")
        
        return results
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

