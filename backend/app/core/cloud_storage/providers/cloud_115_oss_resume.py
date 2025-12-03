"""
115网盘OSS断点续传上传
支持从未完成的分片上传中恢复
"""

import os
import asyncio
from functools import partial
from typing import Dict, Optional, Any, Callable, List
from loguru import logger

try:
    import oss2
    from oss2 import determine_part_size
    from oss2.utils import b64encode_as_string
    from oss2.models import PartInfo
    OSS2_AVAILABLE = True
except ImportError:
    OSS2_AVAILABLE = False
    logger.warning("oss2库未安装，115网盘OSS上传功能不可用")

try:
    from app.modules.upload.speed_limiter import SpeedLimiter, calculate_optimal_part_size
    SPEED_LIMITER_AVAILABLE = True
except ImportError:
    SPEED_LIMITER_AVAILABLE = False


class Cloud115OSSResume:
    """115网盘OSS断点续传上传客户端"""
    
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
    
    async def resume_multipart_upload(
        self,
        file_path: str,
        bucket: str,
        object_key: str,
        upload_id: str,
        completed_parts: List[Dict[str, Any]],
        callback: Optional[str] = None,
        callback_var: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        speed_limit: Optional[int] = None,
        part_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        恢复分片上传
        
        Args:
            file_path: 本地文件路径
            bucket: OSS bucket名称
            object_key: OSS object key
            upload_id: 上传ID
            completed_parts: 已完成的分片信息列表 [{"part_number": 1, "etag": "..."}, ...]
            callback: 上传完成回调URL（可选）
            callback_var: 上传完成回调参数（可选）
            progress_callback: 进度回调函数（可选）
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
                    part_size = calculate_optimal_part_size(
                        file_size=file_size,
                        speed_limit=speed_limit
                    )
                else:
                    part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)
            
            # 构建已完成分片字典（part_number -> etag）
            completed_parts_dict = {part["part_number"]: part["etag"] for part in completed_parts}
            
            # 计算总需上传的分片数
            total_parts = (file_size + part_size - 1) // part_size
            
            logger.info(f"恢复分片上传: {object_key}, 文件大小: {file_size}, 分片大小: {part_size}, 总片数: {total_parts}, 已完成: {len(completed_parts)}")
            
            # 初始化速度限制器
            speed_limiter = None
            if speed_limit and SPEED_LIMITER_AVAILABLE:
                speed_limiter = SpeedLimiter(speed_limit)
                speed_limiter.start()
            
            # 上传未完成的分片
            parts = []
            uploaded_bytes = sum(part_size for part_num in completed_parts_dict.keys() if part_num <= total_parts)
            
            # 先添加已完成的分片
            for part_num in sorted(completed_parts_dict.keys()):
                if part_num <= total_parts:
                    parts.append(PartInfo(part_num, completed_parts_dict[part_num]))
            
            with open(file_path, 'rb') as fileobj:
                for part_number in range(1, total_parts + 1):
                    # 如果分片已完成，跳过
                    if part_number in completed_parts_dict:
                        continue
                    
                    # 计算分片偏移量
                    offset = (part_number - 1) * part_size
                    fileobj.seek(offset)
                    
                    # 读取分片
                    chunk = fileobj.read(part_size)
                    if not chunk:
                        break
                    
                    # 速度限制：如果需要，等待以限制速度
                    if speed_limiter:
                        await speed_limiter.wait_if_needed(len(chunk))
                    
                    # 上传分片
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
                    
                    parts.append(PartInfo(part_number, part_result.etag))
                    uploaded_bytes += len(chunk)
                    
                    # 更新速度限制器的已上传字节数
                    if speed_limiter:
                        current_speed = speed_limiter.get_current_speed()
                        logger.debug(f"分片 {part_number} 上传完成: {len(chunk)} 字节, ETag: {part_result.etag}, 当前速度: {current_speed/1024/1024:.2f} MB/s")
                    else:
                        logger.debug(f"分片 {part_number} 上传完成: {len(chunk)} 字节, ETag: {part_result.etag}")
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(uploaded_bytes, file_size)
            
            # 按分片编号排序
            parts.sort(key=lambda x: x.part_number)
            
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
            
            # 获取最终速度
            final_speed = speed_limiter.get_current_speed() if speed_limiter else None
            
            logger.info(f"文件断点续传成功: {object_key}, ETag: {complete_result.etag}")
            
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
            logger.error(f"OSS断点续传错误: {e}")
            return {
                "success": False,
                "error": f"OSS断点续传错误: {str(e)}",
                "code": getattr(e, 'status', None)
            }
        except Exception as e:
            logger.error(f"断点续传异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }

