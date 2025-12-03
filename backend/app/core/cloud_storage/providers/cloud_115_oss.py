"""
115网盘OSS文件上传客户端
基于115网盘官方API文档实现OSS文件上传功能
参考：115网盘开放平台官方文档 - 上传流程
使用oss2库（阿里云OSS SDK）进行实际上传
"""

import os
import asyncio
from functools import partial
from typing import Dict, Optional, Any, Callable
from loguru import logger
from pathlib import Path

# 导入速度限制器
try:
    from app.modules.upload.speed_limiter import SpeedLimiter, calculate_optimal_part_size
    SPEED_LIMITER_AVAILABLE = True
except ImportError:
    SPEED_LIMITER_AVAILABLE = False
    logger.warning("速度限制器模块未找到，速度限制功能不可用")

try:
    import oss2
    from oss2 import determine_part_size
    from oss2.utils import b64encode_as_string
    OSS2_AVAILABLE = True
except ImportError:
    OSS2_AVAILABLE = False
    logger.warning("oss2库未安装，115网盘OSS上传功能不可用")


class Cloud115OSS:
    """115网盘OSS文件上传客户端"""
    
    def __init__(
        self,
        endpoint: str,
        access_key_id: str,
        access_key_secret: str,
        security_token: str
    ):
        """
        初始化115网盘OSS客户端
        
        Args:
            endpoint: OSS上传域名
            access_key_id: 访问密钥ID
            access_key_secret: 访问密钥
            security_token: 安全令牌
        """
        if not OSS2_AVAILABLE:
            raise ImportError("oss2库未安装，无法使用OSS上传功能。请运行: pip install oss2")
        
        self.endpoint = endpoint
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.security_token = security_token
        
        # 移除endpoint的协议前缀（如果有）
        if self.endpoint.startswith("http://"):
            self.endpoint = self.endpoint[7:]
        elif self.endpoint.startswith("https://"):
            self.endpoint = self.endpoint[8:]
        
        # 创建OSS认证（使用STS临时凭证）
        self.auth = oss2.StsAuth(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            security_token=security_token
        )
    
    async def upload_file(
        self,
        file_path: str,
        bucket: str,
        object_key: str,
        callback: Optional[str] = None,
        callback_var: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        speed_limit: Optional[int] = None,
        part_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        上传文件到OSS（使用分片上传）
        
        Args:
            file_path: 本地文件路径
            bucket: OSS bucket名称
            object_key: OSS object key
            callback: 上传完成回调URL（可选）
            callback_var: 上传完成回调参数（可选）
            progress_callback: 进度回调函数（可选，参数: 已上传字节数, 总字节数）
            speed_limit: 速度限制（字节/秒，可选）
            part_size: 分片大小（字节，可选，如果未指定则根据速度限制自动计算）
        
        Returns:
            上传结果
        """
        file_size = os.path.getsize(file_path)
        
        # 使用分片上传（推荐，支持大文件）
        return await self._multipart_upload(
            file_path=file_path,
            bucket=bucket,
            object_key=object_key,
            callback=callback,
            callback_var=callback_var,
            progress_callback=progress_callback,
            speed_limit=speed_limit,
            part_size=part_size
        )
    
    
    async def _multipart_upload(
        self,
        file_path: str,
        bucket: str,
        object_key: str,
        callback: Optional[str] = None,
        callback_var: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        speed_limit: Optional[int] = None,
        part_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        分片上传（使用oss2库）
        
        Args:
            file_path: 本地文件路径
            bucket: OSS bucket名称
            object_key: OSS object key
            callback: 上传完成回调URL（可选）
            callback_var: 上传完成回调参数（可选）
            progress_callback: 进度回调函数（可选，参数: 已上传字节数, 总字节数）
            speed_limit: 速度限制（字节/秒，可选）
            part_size: 分片大小（字节，可选）
        
        Returns:
            上传结果
        """
        file_size = os.path.getsize(file_path)
        
        # 在线程池中执行同步的OSS操作
        loop = asyncio.get_event_loop()
        
        try:
            # 创建Bucket客户端
            bucket_client = oss2.Bucket(self.auth, self.endpoint, bucket)
            
            # 确定分片大小
            if part_size is None:
                if speed_limit and SPEED_LIMITER_AVAILABLE:
                    # 根据速度限制计算最优分片大小
                    part_size = calculate_optimal_part_size(
                        file_size=file_size,
                        speed_limit=speed_limit
                    )
                else:
                    # 使用默认分片大小（10MB，与VabHub-1一致）
                    part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)
            
            logger.info(f"开始分片上传: {object_key}, 文件大小: {file_size}, 分片大小: {part_size}, 速度限制: {speed_limit/1024/1024:.2f} MB/s" if speed_limit else f"开始分片上传: {object_key}, 文件大小: {file_size}, 分片大小: {part_size}")
            
            # 初始化速度限制器
            speed_limiter = None
            if speed_limit and SPEED_LIMITER_AVAILABLE:
                speed_limiter = SpeedLimiter(speed_limit)
                speed_limiter.start()
            
            # 初始化分片上传
            upload_params = {
                "encoding-type": "url",
                "sequential": ""  # 顺序上传
            }
            
            # 添加回调参数（初始化时不需要，完成时需要）
            upload_id_result = await loop.run_in_executor(
                None,
                lambda: bucket_client.init_multipart_upload(object_key, params=upload_params)
            )
            upload_id = upload_id_result.upload_id
            
            # 上传分片
            parts = []
            uploaded_bytes = 0
            
            with open(file_path, 'rb') as fileobj:
                part_number = 1
                while True:
                    # 读取分片
                    chunk = fileobj.read(part_size)
                    if not chunk:
                        break
                    
                    # 速度限制：如果需要，等待以限制速度
                    if speed_limiter:
                        await speed_limiter.wait_if_needed(len(chunk))
                    
                    # 上传分片（在线程池中执行，使用functools.partial避免闭包问题）
                    part_result = await loop.run_in_executor(
                        None,
                        partial(
                            bucket_client.upload_part,
                            object_key,
                            upload_id,
                            part_number,
                            chunk
                        )
                    )
                    
                    parts.append(oss2.models.PartInfo(part_number, part_result.etag))
                    uploaded_bytes += len(chunk)
                    
                    # 更新速度限制器（在wait_if_needed中已经更新了uploaded_bytes，这里只需要记录）
                    if speed_limiter:
                        # 速度限制器会在 wait_if_needed 中更新，这里只需要记录当前速度
                        current_speed = speed_limiter.get_current_speed()
                        if current_speed > 0:
                            logger.debug(f"分片 {part_number} 上传完成: {len(chunk)} 字节, ETag: {part_result.etag}, 当前速度: {current_speed/1024/1024:.2f} MB/s")
                        else:
                            logger.debug(f"分片 {part_number} 上传完成: {len(chunk)} 字节, ETag: {part_result.etag}")
                    else:
                        logger.debug(f"分片 {part_number} 上传完成: {len(chunk)} 字节, ETag: {part_result.etag}")
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(uploaded_bytes, file_size)
                    
                    part_number += 1
            
            # 完成分片上传（添加回调参数）
            complete_headers = {}
            if callback:
                complete_headers['X-oss-callback'] = b64encode_as_string(callback)
            if callback_var:
                complete_headers['x-oss-callback-var'] = b64encode_as_string(callback_var)
            complete_headers['x-oss-forbid-overwrite'] = 'false'
            
            complete_result = await loop.run_in_executor(
                None,
                lambda: bucket_client.complete_multipart_upload(
                    object_key,
                    upload_id,
                    parts,
                    headers=complete_headers
                )
            )
            
            logger.info(f"文件上传成功: {object_key}, ETag: {complete_result.etag}")
            
            # 获取最终速度
            final_speed = speed_limiter.get_current_speed() if speed_limiter else None
            
            return {
                "success": True,
                "object_key": object_key,
                "etag": complete_result.etag,
                "file_size": file_size,
                "parts_count": len(parts),
                "part_size": part_size,
                "final_speed": final_speed
            }
            
        except oss2.exceptions.OssError as e:
            logger.error(f"OSS上传错误: {e}")
            return {
                "success": False,
                "error": f"OSS上传错误: {str(e)}",
                "code": getattr(e, 'status', None)
            }
        except Exception as e:
            logger.error(f"文件上传异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    

