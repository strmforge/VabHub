"""
OCR验证码识别助手
支持多种OCR引擎：外部OCR服务、PaddleOCR、Tesseract
主要用于PT站点签到时识别验证码
支持多种OCR引擎
"""

import base64
import asyncio
from typing import Optional, Tuple, Dict, Any
from loguru import logger
import httpx

from app.core.config import settings


class OcrHelper:
    """OCR验证码识别助手"""
    
    def __init__(self, ocr_host: Optional[str] = None):
        """
        初始化OCR助手
        
        Args:
            ocr_host: OCR服务地址（可选，默认从配置读取）
        """
        # 优先使用传入的OCR_HOST，否则从配置读取
        self.ocr_host = ocr_host or getattr(settings, 'OCR_HOST', None) or "https://movie-pilot.org"
        self.ocr_b64_url = f"{self.ocr_host}/captcha/base64"
        
        # 尝试初始化本地OCR引擎（PaddleOCR）
        self.paddle_ocr = None
        self._init_paddle_ocr()
    
    def _init_paddle_ocr(self):
        """初始化PaddleOCR（如果可用）"""
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                use_gpu=False,
                show_log=False
            )
            logger.info("PaddleOCR引擎初始化成功（本地OCR）")
        except ImportError:
            logger.debug("PaddleOCR未安装，将使用外部OCR服务")
            self.paddle_ocr = None
        except Exception as e:
            logger.warning(f"PaddleOCR初始化失败: {e}，将使用外部OCR服务")
            self.paddle_ocr = None
    
    async def get_captcha_text(
        self,
        image_url: Optional[str] = None,
        image_b64: Optional[str] = None,
        cookie: Optional[str] = None,
        ua: Optional[str] = None,
        use_local_ocr: bool = False,
        site_name: Optional[str] = None,
        expected_length: Optional[int] = None,
        record_statistics: bool = True
    ) -> Optional[str]:
        """
        识别验证码文本
        
        Args:
            image_url: 验证码图片URL
            image_b64: 验证码图片Base64编码（如果提供，跳过下载）
            cookie: 下载图片时使用的Cookie
            ua: 下载图片时使用的User-Agent
            use_local_ocr: 是否优先使用本地OCR（PaddleOCR）
            site_name: 站点名称（用于统计）
            expected_length: 期望长度（如6位验证码）
            record_statistics: 是否记录统计信息
        
        Returns:
            识别出的验证码文本，失败返回None
        """
        import time
        import hashlib
        
        start_time = time.time()
        retry_count = 0
        original_result = None
        cleaned_result = None
        engine_used = None
        confidence = None
        error_message = None
        image_hash = None
        
        try:
            # 1. 获取图片数据
            image_b64_data = image_b64
            image_data = None
            
            if not image_b64_data and image_url:
                # 下载图片
                image_data = await self._download_image(image_url, cookie, ua)
                if not image_data:
                    logger.warning(f"下载验证码图片失败: {image_url}")
                    error_message = "下载图片失败"
                    if record_statistics:
                        await self._record_statistics(
                            site_name=site_name,
                            image_url=image_url,
                            image_hash=image_hash,
                            original_text=None,
                            cleaned_text=None,
                            expected_length=expected_length,
                            success=False,
                            confidence=None,
                            engine=engine_used,
                            retry_count=retry_count,
                            duration_ms=int((time.time() - start_time) * 1000),
                            error_message=error_message
                        )
                    return None
                
                # 计算图片hash（用于缓存）
                image_hash = hashlib.md5(image_data).hexdigest()
                
                # 检查缓存（相同hash的图片）
                if image_hash and record_statistics:
                    cached_result = await self._get_cached_result(image_hash)
                    if cached_result and cached_result.cleaned_text:
                        logger.info(f"OCR缓存命中: {cached_result.cleaned_text} (hash: {image_hash[:8]}...)")
                        # 验证长度（如果指定了期望长度）
                        if expected_length and len(cached_result.cleaned_text) == expected_length:
                            return cached_result.cleaned_text
                        elif not expected_length:
                            return cached_result.cleaned_text
                
                # 转换为Base64
                image_b64_data = base64.b64encode(image_data).decode()
            
            if not image_b64_data:
                logger.warning("未提供验证码图片数据")
                error_message = "未提供图片数据"
                if record_statistics:
                    await self._record_statistics(
                        site_name=site_name,
                        image_url=image_url,
                        image_hash=image_hash,
                        original_text=None,
                        cleaned_text=None,
                        expected_length=expected_length,
                        success=False,
                        confidence=None,
                        engine=engine_used,
                        retry_count=retry_count,
                        duration_ms=int((time.time() - start_time) * 1000),
                        error_message=error_message
                    )
                return None
            
            # 2. 识别验证码
            if use_local_ocr and self.paddle_ocr:
                # 使用本地PaddleOCR
                engine_used = "paddleocr"
                result = await self._recognize_with_paddleocr(image_b64_data)
                confidence = 0.9  # PaddleOCR默认置信度
            else:
                # 使用外部OCR服务
                engine_used = "external_service"
                result = await self._recognize_with_external_service(image_b64_data)
                confidence = 0.8  # 外部服务默认置信度
            
            original_result = result
            
            if result:
                # 清理识别结果
                cleaned_result = self._clean_text(result)
                
                # 验证长度（如果指定了期望长度）
                success = True
                if expected_length and len(cleaned_result) != expected_length:
                    success = False
                    error_message = f"长度不匹配: 期望{expected_length}位，实际{len(cleaned_result)}位"
                    logger.warning(f"OCR识别长度不匹配: {cleaned_result} (期望{expected_length}位)")
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                if success:
                    logger.info(f"OCR识别成功: {cleaned_result} (耗时{duration_ms}ms)")
                else:
                    logger.warning(f"OCR识别失败: {error_message}")
                
                # 记录统计
                if record_statistics:
                    await self._record_statistics(
                        site_name=site_name,
                        image_url=image_url,
                        image_hash=image_hash,
                        original_text=original_result,
                        cleaned_text=cleaned_result,
                        expected_length=expected_length,
                        success=success,
                        confidence=confidence,
                        engine=engine_used,
                        retry_count=retry_count,
                        duration_ms=duration_ms,
                        error_message=error_message
                    )
                
                return cleaned_result if success else None
            else:
                error_message = "识别结果为空"
                logger.warning("OCR识别失败")
                duration_ms = int((time.time() - start_time) * 1000)
                
                if record_statistics:
                    await self._record_statistics(
                        site_name=site_name,
                        image_url=image_url,
                        image_hash=image_hash,
                        original_text=None,
                        cleaned_text=None,
                        expected_length=expected_length,
                        success=False,
                        confidence=None,
                        engine=engine_used,
                        retry_count=retry_count,
                        duration_ms=duration_ms,
                        error_message=error_message
                    )
                return None
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"OCR识别异常: {e}")
            duration_ms = int((time.time() - start_time) * 1000)
            
            if record_statistics:
                await self._record_statistics(
                    site_name=site_name,
                    image_url=image_url,
                    image_hash=image_hash,
                    original_text=original_result,
                    cleaned_text=cleaned_result,
                    expected_length=expected_length,
                    success=False,
                    confidence=confidence,
                    engine=engine_used,
                    retry_count=retry_count,
                    duration_ms=duration_ms,
                    error_message=error_message
                )
            return None
    
    async def _get_cached_result(self, image_hash: str) -> Optional[Any]:
        """从缓存中获取OCR结果"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.modules.ocr.statistics import OCRStatisticsService
            
            async with AsyncSessionLocal() as db:
                stats_service = OCRStatisticsService(db)
                return await stats_service.get_cached_result(image_hash)
        except Exception as e:
            logger.debug(f"获取OCR缓存失败（不影响功能）: {e}")
            return None
    
    async def _record_statistics(
        self,
        site_name: Optional[str] = None,
        image_url: Optional[str] = None,
        image_hash: Optional[str] = None,
        original_text: Optional[str] = None,
        cleaned_text: Optional[str] = None,
        expected_length: Optional[int] = None,
        success: bool = False,
        confidence: Optional[float] = None,
        engine: Optional[str] = None,
        retry_count: int = 0,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """记录OCR统计信息（异步）"""
        try:
            # 延迟导入，避免循环依赖
            from app.core.database import AsyncSessionLocal
            from app.modules.ocr.statistics import OCRStatisticsService
            
            async with AsyncSessionLocal() as db:
                stats_service = OCRStatisticsService(db)
                await stats_service.record_ocr_attempt(
                    site_name=site_name,
                    site_url=None,  # 可以从image_url提取
                    image_hash=image_hash,
                    image_url=image_url,
                    original_text=original_text,
                    cleaned_text=cleaned_text,
                    expected_length=expected_length,
                    success=success,
                    confidence=confidence,
                    engine=engine,
                    retry_count=retry_count,
                    duration_ms=duration_ms,
                    error_message=error_message
                )
        except Exception as e:
            logger.debug(f"记录OCR统计失败（不影响功能）: {e}")
    
    async def _download_image(
        self,
        image_url: str,
        cookie: Optional[str] = None,
        ua: Optional[str] = None
    ) -> Optional[bytes]:
        """下载验证码图片"""
        try:
            headers = {}
            if ua:
                headers["User-Agent"] = ua
            
            cookies = {}
            if cookie:
                # 解析Cookie字符串
                for item in cookie.split(';'):
                    item = item.strip()
                    if '=' in item:
                        key, value = item.split('=', 1)
                        cookies[key.strip()] = value.strip()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(image_url, headers=headers, cookies=cookies)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"下载验证码图片失败: HTTP {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"下载验证码图片异常: {e}")
            return None
    
    async def _recognize_with_external_service(self, image_b64: str) -> Optional[str]:
        """使用外部OCR服务识别"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.ocr_b64_url,
                    json={"base64_img": image_b64},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result")
                else:
                    logger.warning(f"外部OCR服务返回错误: HTTP {response.status_code}")
                    return None
        except httpx.TimeoutException:
            logger.warning("外部OCR服务请求超时")
            return None
        except Exception as e:
            logger.error(f"外部OCR服务调用异常: {e}")
            return None
    
    async def _recognize_with_paddleocr(self, image_b64: str) -> Optional[str]:
        """使用本地PaddleOCR识别"""
        try:
            import cv2
            import numpy as np
            from io import BytesIO
            
            # 解码Base64
            image_data = base64.b64decode(image_b64)
            
            # 转换为OpenCV格式
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.warning("PaddleOCR: 图像解码失败")
                return None
            
            # 图像预处理
            processed_image = self._preprocess_image(image)
            
            # 使用PaddleOCR识别
            # 注意：PaddleOCR是同步的，需要在线程池中运行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.paddle_ocr.ocr(processed_image, cls=True)
            )
            
            # 提取文本
            text = self._extract_text_from_paddleocr(result)
            return text
            
        except Exception as e:
            logger.error(f"PaddleOCR识别异常: {e}")
            return None
    
    def _preprocess_image(self, image):
        """图像预处理（提高识别率）"""
        try:
            import cv2
            import numpy as np
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 去噪
            denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
            
            return denoised
        except Exception as e:
            logger.warning(f"图像预处理失败: {e}，使用原图")
            return image
    
    def _extract_text_from_paddleocr(self, ocr_result) -> str:
        """从PaddleOCR结果中提取文本"""
        if not ocr_result or not ocr_result[0]:
            return ""
        
        texts = []
        for line in ocr_result[0]:
            if len(line) >= 2:
                text_info = line[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                    text = text_info[0]
                else:
                    text = str(text_info)
                texts.append(text)
        
        return ''.join(texts)
    
    def _clean_text(self, text: str) -> str:
        """清理识别结果"""
        if not text:
            return ""
        
        import re
        # 移除空格和特殊字符，只保留字母和数字
        cleaned = re.sub(r'[^A-Za-z0-9]', '', text)
        # 转换为大写
        cleaned = cleaned.upper()
        # 限制长度（验证码通常4-8位）
        if len(cleaned) > 8:
            cleaned = cleaned[:8]
        
        return cleaned
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取OCR引擎状态"""
        return {
            "external_service": {
                "available": True,
                "url": self.ocr_b64_url
            },
            "paddleocr": {
                "available": self.paddle_ocr is not None,
                "initialized": self.paddle_ocr is not None
            },
            "preferred_engine": "paddleocr" if self.paddle_ocr else "external_service"
        }

