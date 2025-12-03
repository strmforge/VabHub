"""
站点签到模块
支持多种PT站点的自动签到
支持OCR验证码识别（OpenCD、HDSky等）
"""

import re
import asyncio
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup
from lxml import etree


class SiteCheckin:
    """站点签到处理器"""
    
    def __init__(self, site_url: str, cookies: str):
        """
        初始化站点签到处理器
        
        Args:
            site_url: 站点URL
            cookies: Cookie字符串
        """
        self.site_url = site_url.rstrip('/')
        self.cookies = self._parse_cookies(cookies)
        self.cookie_str = cookies  # 保存原始Cookie字符串，用于OCR
        self.client = None
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def _parse_cookies(self, cookie_str: str) -> Dict[str, str]:
        """解析Cookie字符串"""
        cookies = {}
        if not cookie_str:
            return cookies
        
        # 解析Cookie字符串（格式：key1=value1; key2=value2）
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        return cookies
    
    async def checkin(self) -> Dict[str, Any]:
        """
        执行签到
        
        Returns:
            签到结果字典，包含success、message等信息
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                self.client = client
                
                # 检测站点类型并执行相应的签到逻辑
                site_type = await self._detect_site_type()
                
                # 优先检测需要验证码的站点
                if "open.cd" in self.site_url.lower():
                    return await self._checkin_opencd()
                elif "hdsky.me" in self.site_url.lower() or "hdsky" in self.site_url.lower():
                    return await self._checkin_hdsky()
                elif site_type == "nexusphp":
                    return await self._checkin_nexusphp()
                elif site_type == "unit3d":
                    return await self._checkin_unit3d()
                elif site_type == "ttg":
                    return await self._checkin_ttg()
                elif site_type == "mteam":
                    return await self._checkin_mteam()
                else:
                    # 通用签到尝试
                    return await self._checkin_generic()
        
        except Exception as e:
            logger.error(f"站点签到异常: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def _detect_site_type(self) -> str:
        """检测站点类型"""
        try:
            response = await self.client.get(
                self.site_url,
                cookies=self.cookies,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            html = response.text.lower()
            
            # 检测NexusPHP
            if "nexusphp" in html or "nexus" in html:
                return "nexusphp"
            
            # 检测Unit3D
            if "unit3d" in html or "laravel" in html:
                return "unit3d"
            
            # 检测TTG
            if "ttg" in html or "torrentgui" in html:
                return "ttg"
            
            # 检测M-Team
            if "m-team" in html or "mteam" in html:
                return "mteam"
            
            return "generic"
        
        except Exception as e:
            logger.warning(f"检测站点类型失败: {e}")
            return "generic"
    
    async def _checkin_nexusphp(self) -> Dict[str, Any]:
        """NexusPHP站点签到"""
        try:
            # NexusPHP签到通常是在index.php页面点击签到按钮
            # 或者访问特定的签到URL
            
            # 尝试方法1: 访问签到页面
            checkin_urls = [
                f"{self.site_url}/attendance.php",
                f"{self.site_url}/index.php?action=attendance",
                f"{self.site_url}/plugin.php?id=checkin",
            ]
            
            for url in checkin_urls:
                try:
                    response = await self.client.get(
                        url,
                        cookies=self.cookies,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": self.site_url
                        }
                    )
                    
                    if response.status_code == 200:
                        # 检查是否已经签到
                        if "已经签到" in response.text or "already checked" in response.text.lower():
                            return {
                                "success": True,
                                "message": "今日已签到",
                                "already_checked": True
                            }
                        
                        # 尝试提交签到表单
                        soup = BeautifulSoup(response.text, 'html.parser')
                        form = soup.find('form', {'action': re.compile(r'attendance|checkin', re.I)})
                        
                        if form:
                            form_action = form.get('action', '')
                            if not form_action.startswith('http'):
                                form_action = f"{self.site_url}/{form_action}"
                            
                            # 提取表单数据
                            form_data = {}
                            for input_tag in form.find_all('input'):
                                input_name = input_tag.get('name')
                                input_value = input_tag.get('value', '')
                                if input_name:
                                    form_data[input_name] = input_value
                            
                            # 提交签到
                            post_response = await self.client.post(
                                form_action,
                                cookies=self.cookies,
                                data=form_data,
                                headers={
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                    "Referer": url,
                                    "Content-Type": "application/x-www-form-urlencoded"
                                }
                            )
                            
                            if post_response.status_code == 200:
                                if "签到成功" in post_response.text or "check in success" in post_response.text.lower():
                                    return {
                                        "success": True,
                                        "message": "签到成功",
                                        "already_checked": False
                                    }
                
                except Exception as e:
                    logger.debug(f"尝试签到URL {url} 失败: {e}")
                    continue
            
            return {
                "success": False,
                "message": "未找到签到入口"
            }
        
        except Exception as e:
            logger.error(f"NexusPHP签到失败: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def _checkin_unit3d(self) -> Dict[str, Any]:
        """Unit3D站点签到"""
        try:
            # Unit3D签到通常是通过AJAX请求
            checkin_url = f"{self.site_url}/api/v1/checkin"
            
            response = await self.client.post(
                checkin_url,
                cookies=self.cookies,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": self.site_url,
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/json"
                },
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") or "message" in data:
                    return {
                        "success": True,
                        "message": data.get("message", "签到成功"),
                        "already_checked": "already" in data.get("message", "").lower()
                    }
            
            return {
                "success": False,
                "message": "签到失败"
            }
        
        except Exception as e:
            logger.error(f"Unit3D签到失败: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def _checkin_ttg(self) -> Dict[str, Any]:
        """TTG站点签到"""
        try:
            # TTG签到
            checkin_url = f"{self.site_url}/attendance.php"
            
            response = await self.client.get(
                checkin_url,
                cookies=self.cookies,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": self.site_url
                }
            )
            
            if response.status_code == 200:
                if "已经签到" in response.text:
                    return {
                        "success": True,
                        "message": "今日已签到",
                        "already_checked": True
                    }
                elif "签到成功" in response.text:
                    return {
                        "success": True,
                        "message": "签到成功",
                        "already_checked": False
                    }
            
            return {
                "success": False,
                "message": "签到失败"
            }
        
        except Exception as e:
            logger.error(f"TTG签到失败: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def _checkin_mteam(self) -> Dict[str, Any]:
        """M-Team站点签到"""
        try:
            # M-Team签到
            checkin_url = f"{self.site_url}/api/member/signin"
            
            response = await self.client.post(
                checkin_url,
                cookies=self.cookies,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": self.site_url,
                    "Content-Type": "application/json"
                },
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 or data.get("success"):
                    return {
                        "success": True,
                        "message": data.get("message", "签到成功"),
                        "already_checked": False
                    }
            
            return {
                "success": False,
                "message": "签到失败"
            }
        
        except Exception as e:
            logger.error(f"M-Team签到失败: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def _checkin_generic(self) -> Dict[str, Any]:
        """通用签到尝试"""
        try:
            # 尝试常见的签到URL
            common_urls = [
                f"{self.site_url}/attendance.php",
                f"{self.site_url}/checkin",
                f"{self.site_url}/signin",
                f"{self.site_url}/index.php?action=attendance",
            ]
            
            for url in common_urls:
                try:
                    response = await self.client.get(
                        url,
                        cookies=self.cookies,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": self.site_url
                        }
                    )
                    
                    if response.status_code == 200:
                        # 检查响应内容
                        text = response.text.lower()
                        if "签到成功" in response.text or "check in success" in text:
                            return {
                                "success": True,
                                "message": "签到成功",
                                "already_checked": False
                            }
                        elif "已经签到" in response.text or "already checked" in text:
                            return {
                                "success": True,
                                "message": "今日已签到",
                                "already_checked": True
                            }
                
                except Exception:
                    continue
            
            return {
                "success": False,
                "message": "未找到签到入口或签到方式不支持"
            }
        
        except Exception as e:
            logger.error(f"通用签到失败: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def _checkin_opencd(self) -> Dict[str, Any]:
        """
        OpenCD（皇后）站点签到
        需要OCR识别6位验证码
        """
        try:
            from app.core.ocr import OcrHelper
            
            # 1. 检查是否已签到
            response = await self.client.get(
                "https://www.open.cd",
                cookies=self.cookies,
                headers={
                    "User-Agent": self.ua,
                    "Referer": self.site_url
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": "无法访问站点"
                }
            
            if "login.php" in response.text:
                return {
                    "success": False,
                    "message": "Cookie已失效"
                }
            
            if "/plugin_sign-in.php?cmd=show-log" in response.text:
                return {
                    "success": True,
                    "message": "今日已签到",
                    "already_checked": True
                }
            
            # 2. 获取签到页面和验证码
            signin_page = await self.client.get(
                "https://www.open.cd/plugin_sign-in.php",
                cookies=self.cookies,
                headers={
                    "User-Agent": self.ua,
                    "Referer": "https://www.open.cd"
                }
            )
            
            if signin_page.status_code != 200:
                return {
                    "success": False,
                    "message": "无法访问签到页面"
                }
            
            # 3. 解析HTML获取验证码信息
            html = etree.HTML(signin_page.text)
            if not html:
                return {
                    "success": False,
                    "message": "无法解析签到页面"
                }
            
            try:
                img_urls = html.xpath('//form[@id="frmSignin"]//img/@src')
                img_hashes = html.xpath('//form[@id="frmSignin"]//input[@name="imagehash"]/@value')
                
                if not img_urls or not img_hashes:
                    return {
                        "success": False,
                        "message": "无法获取验证码参数"
                    }
                
                img_url = img_urls[0]
                img_hash = img_hashes[0]
            except Exception as e:
                logger.error(f"解析验证码参数失败: {e}")
                return {
                    "success": False,
                    "message": "无法解析验证码参数"
                }
            
            # 4. 构建完整验证码URL
            if not img_url.startswith('http'):
                img_get_url = f"https://www.open.cd/{img_url}"
            else:
                img_get_url = img_url
            
            logger.info(f"获取到OpenCD验证码链接: {img_get_url}")
            
            # 5. OCR识别验证码（最多重试3次）
            ocr_helper = OcrHelper()
            ocr_result = None
            max_retries = 3
            
            for attempt in range(max_retries):
                ocr_result = await ocr_helper.get_captcha_text(
                    image_url=img_get_url,
                    cookie=self.cookie_str,
                    ua=self.ua
                )
                
                if ocr_result and len(ocr_result) == 6:
                    logger.info(f"OCR识别OpenCD验证码成功: {ocr_result} (尝试 {attempt + 1}/{max_retries})")
                    break
                else:
                    logger.warning(f"OCR识别OpenCD验证码失败: {ocr_result} (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
            
            if not ocr_result or len(ocr_result) != 6:
                return {
                    "success": False,
                    "message": f"验证码识别失败: {ocr_result}"
                }
            
            # 6. 提交签到
            signin_data = {
                'imagehash': img_hash,
                'imagestring': ocr_result
            }
            
            signin_response = await self.client.post(
                "https://www.open.cd/plugin_sign-in.php?cmd=signin",
                cookies=self.cookies,
                data=signin_data,
                headers={
                    "User-Agent": self.ua,
                    "Referer": "https://www.open.cd/plugin_sign-in.php",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if signin_response.status_code == 200:
                try:
                    import json
                    result = json.loads(signin_response.text)
                    if result.get('state') == 'success':
                        logger.info(f"OpenCD签到成功: {result}")
                        return {
                            "success": True,
                            "message": "签到成功",
                            "already_checked": False,
                            "data": result
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"签到失败: {result.get('message', '未知错误')}"
                        }
                except json.JSONDecodeError:
                    if "签到成功" in signin_response.text or "success" in signin_response.text.lower():
                        return {
                            "success": True,
                            "message": "签到成功",
                            "already_checked": False
                        }
            
            return {
                "success": False,
                "message": "签到失败"
            }
            
        except Exception as e:
            logger.error(f"OpenCD签到异常: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def _checkin_hdsky(self) -> Dict[str, Any]:
        """
        HDSky（天空）站点签到
        需要OCR识别6位验证码
        """
        try:
            from app.core.ocr import OcrHelper
            
            # 1. 检查是否已签到
            response = await self.client.get(
                "https://hdsky.me",
                cookies=self.cookies,
                headers={
                    "User-Agent": self.ua,
                    "Referer": self.site_url
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": "无法访问站点"
                }
            
            if "login.php" in response.text:
                return {
                    "success": False,
                    "message": "Cookie已失效"
                }
            
            if "已签到" in response.text:
                return {
                    "success": True,
                    "message": "今日已签到",
                    "already_checked": True
                }
            
            # 2. 获取验证码hash
            img_hash = None
            max_hash_retries = 3
            
            for attempt in range(max_hash_retries):
                hash_response = await self.client.post(
                    "https://hdsky.me/image_code_ajax.php",
                    cookies=self.cookies,
                    data={'action': 'new'},
                    headers={
                        "User-Agent": self.ua,
                        "Referer": "https://hdsky.me/index.php",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "Accept": "*/*"
                    }
                )
                
                if hash_response.status_code == 200:
                    try:
                        import json
                        result = json.loads(hash_response.text)
                        if result.get('success') and result.get('code'):
                            img_hash = result['code']
                            logger.info(f"获取到HDSky验证码hash: {img_hash}")
                            break
                    except json.JSONDecodeError:
                        pass
                
                if attempt < max_hash_retries - 1:
                    await asyncio.sleep(1)
            
            if not img_hash:
                return {
                    "success": False,
                    "message": "无法获取验证码hash"
                }
            
            # 3. 构建验证码图片URL
            img_get_url = f"https://hdsky.me/image.php?action=regimage&imagehash={img_hash}"
            logger.info(f"获取到HDSky验证码链接: {img_get_url}")
            
            # 4. OCR识别验证码（最多重试3次）
            ocr_helper = OcrHelper()
            ocr_result = None
            max_retries = 3
            
            for attempt in range(max_retries):
                ocr_result = await ocr_helper.get_captcha_text(
                    image_url=img_get_url,
                    cookie=self.cookie_str,
                    ua=self.ua
                )
                
                if ocr_result and len(ocr_result) == 6:
                    logger.info(f"OCR识别HDSky验证码成功: {ocr_result} (尝试 {attempt + 1}/{max_retries})")
                    break
                else:
                    logger.warning(f"OCR识别HDSky验证码失败: {ocr_result} (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
            
            if not ocr_result or len(ocr_result) != 6:
                return {
                    "success": False,
                    "message": f"验证码识别失败: {ocr_result}"
                }
            
            # 5. 提交签到
            signin_data = {
                'action': 'showup',
                'imagehash': img_hash,
                'imagestring': ocr_result
            }
            
            signin_response = await self.client.post(
                "https://hdsky.me/showup.php",
                cookies=self.cookies,
                data=signin_data,
                headers={
                    "User-Agent": self.ua,
                    "Referer": self.site_url,
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if signin_response.status_code == 200:
                try:
                    import json
                    result = json.loads(signin_response.text)
                    if result.get('success'):
                        logger.info(f"HDSky签到成功: {result}")
                        return {
                            "success": True,
                            "message": "签到成功",
                            "already_checked": False,
                            "data": result
                        }
                    elif result.get('message') == 'date_unmatch':
                        return {
                            "success": True,
                            "message": "今日已签到",
                            "already_checked": True
                        }
                    elif result.get('message') == 'invalid_imagehash':
                        return {
                            "success": False,
                            "message": "验证码错误"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"签到失败: {result.get('message', '未知错误')}"
                        }
                except json.JSONDecodeError:
                    if "签到成功" in signin_response.text or "success" in signin_response.text.lower():
                        return {
                            "success": True,
                            "message": "签到成功",
                            "already_checked": False
                        }
            
            return {
                "success": False,
                "message": "签到失败"
            }
            
        except Exception as e:
            logger.error(f"HDSky签到异常: {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }

