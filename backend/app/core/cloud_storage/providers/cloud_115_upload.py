"""
115网盘文件上传管理器
整合上传凭证获取、上传初始化、二次认证、OSS上传等功能
参考：115网盘开放平台官方文档 - 上传流程
"""

import os
import hashlib
import asyncio
from typing import Dict, Optional, Any, Callable
from pathlib import Path
from loguru import logger

from .cloud_115_api import Cloud115API
from .cloud_115_oss import Cloud115OSS


class Cloud115UploadManager:
    """115网盘文件上传管理器"""
    
    def __init__(self, api_client: Cloud115API):
        """
        初始化文件上传管理器
        
        Args:
            api_client: 115网盘API客户端
        """
        self.api = api_client
        self.oss_client: Optional[Cloud115OSS] = None
    
    async def upload_file(
        self,
        file_path: str,
        target_parent_id: str = "0",
        file_name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        speed_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        上传文件到115网盘（完整流程）
        
        流程：
        1. 计算文件sha1值
        2. 调用文件上传初始化接口
        3. 如果是秒传（status=2），直接返回成功
        4. 如果需要二次认证，进行二次认证
        5. 如果是非秒传（status=1），获取上传凭证，然后上传到OSS
        6. 如果是断点续传，使用pick_code调用断点续传接口，然后上传到OSS
        
        Args:
            file_path: 本地文件路径
            target_parent_id: 目标目录ID（默认0，根目录）
            file_name: 文件名（可选，默认使用本地文件名）
            progress_callback: 进度回调函数（可选，参数: 已上传字节数, 总字节数, 状态）
        
        Returns:
            上传结果
        """
        # 验证文件是否存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }
        
        # 获取文件信息
        file_path_obj = Path(file_path)
        file_size = file_path_obj.stat().st_size
        file_name = file_name or file_path_obj.name
        
        # 计算文件sha1值
        if progress_callback:
            progress_callback(0, file_size, "计算文件sha1值...")
        
        file_sha1 = await self._calculate_sha1(file_path, progress_callback)
        pre_sha1 = await self._calculate_pre_sha1(file_path)
        
        # Step 1: 调用文件上传初始化接口
        if progress_callback:
            progress_callback(0, file_size, "初始化上传...")
        
        init_result = await self.api.init_upload(
            file_name=file_name,
            file_size=file_size,
            target_parent_id=target_parent_id,
            file_sha1=file_sha1,
            pre_sha1=pre_sha1
        )
        
        if not init_result.get("success"):
            # 检查是否需要二次认证
            error_code = init_result.get("code")
            
            if error_code in [700, 701, 702]:
                # 需要二次认证
                return await self._handle_secondary_auth(
                    file_path=file_path,
                    file_name=file_name,
                    file_size=file_size,
                    target_parent_id=target_parent_id,
                    file_sha1=file_sha1,
                    pre_sha1=pre_sha1,
                    init_result=init_result,
                    progress_callback=progress_callback
                )
            else:
                # 其他错误
                return init_result
        
        # Step 2: 处理上传结果
        status = init_result.get("status")
        
        if status == 2:
            # 秒传成功
            file_id = init_result.get("file_id")
            if progress_callback:
                progress_callback(file_size, file_size, "秒传成功")
            
            logger.info(f"文件秒传成功: {file_name}, file_id={file_id}")
            return {
                "success": True,
                "file_id": file_id,
                "method": "instant",
                "file_name": file_name
            }
        elif status == 1:
            # 非秒传，需要实际上传
            pick_code = init_result.get("pick_code")
            return await self._upload_to_oss(
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                init_result=init_result,
                progress_callback=progress_callback,
                speed_limit=speed_limit,
                pick_code=pick_code
            )
        else:
            return {
                "success": False,
                "error": f"未知的上传状态: {status}"
            }
    
    async def _handle_secondary_auth(
        self,
        file_path: str,
        file_name: str,
        file_size: int,
        target_parent_id: str,
        file_sha1: str,
        pre_sha1: Optional[str],
        init_result: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int, str], None]]
    ) -> Dict[str, Any]:
        """
        处理二次认证
        
        Args:
            file_path: 本地文件路径
            file_name: 文件名
            file_size: 文件大小
            target_parent_id: 目标目录ID
            file_sha1: 文件sha1值
            pre_sha1: 文件前128K sha1值
            init_result: 初始化结果
            progress_callback: 进度回调函数
        
        Returns:
            上传结果
        """
        error_code = init_result.get("code")
        sign_key = init_result.get("sign_key")
        sign_check = init_result.get("sign_check")
        
        if progress_callback:
            progress_callback(0, file_size, "进行二次认证...")
        
        if error_code == 701:
            # 需要认证签名
            # sign_check: "2392148-2392298"
            # 取2392148-2392298之间的内容(包含2392148、2392298)的sha1
            
            try:
                # 解析字节范围
                start_byte, end_byte = map(int, sign_check.split("-"))
                
                # 读取文件指定范围的内容
                with open(file_path, 'rb') as f:
                    f.seek(start_byte)
                    chunk = f.read(end_byte - start_byte + 1)  # 包含start_byte和end_byte
                
                # 计算sha1值（大写）
                chunk_sha1 = hashlib.sha1(chunk).hexdigest().upper()
                
                # 第二次上传初始化，提供sign_val
                init_result = await self.api.init_upload(
                    file_name=file_name,
                    file_size=file_size,
                    target_parent_id=target_parent_id,
                    file_sha1=file_sha1,
                    pre_sha1=pre_sha1,
                    sign_key=sign_key,
                    sign_val=chunk_sha1
                )
                
                if not init_result.get("success"):
                    return init_result
                
                # 处理上传结果
                status = init_result.get("status")
                
                if status == 2:
                    # 秒传成功
                    file_id = init_result.get("file_id")
                    if progress_callback:
                        progress_callback(file_size, file_size, "秒传成功")
                    
                    return {
                        "success": True,
                        "file_id": file_id,
                        "method": "instant",
                        "file_name": file_name,
                        "file_size": file_size
                    }
                elif status == 1:
                    # 非秒传，需要实际上传
                    # 获取pick_code用于后续断点续传
                    pick_code = init_result.get("pick_code")
                    if not pick_code:
                        return {
                            "success": False,
                            "error": "初始化上传未返回pick_code"
                        }
                    
                    pick_code = init_result.get("pick_code")
                    return await self._upload_to_oss(
                        file_path=file_path,
                        file_name=file_name,
                        file_size=file_size,
                        init_result=init_result,
                        progress_callback=progress_callback,
                        speed_limit=speed_limit,
                        pick_code=pick_code
                    )
                else:
                    return {
                        "success": False,
                        "error": f"未知的上传状态: {status}"
                    }
                    
            except Exception as e:
                logger.error(f"二次认证处理异常: {e}")
                return {
                    "success": False,
                    "error": f"二次认证处理异常: {str(e)}"
                }
        else:
            # 其他二次认证错误码（700, 702）
            return {
                "success": False,
                "error": f"二次认证失败: code={error_code}",
                "code": error_code
            }
    
    async def _upload_to_oss(
        self,
        file_path: str,
        file_name: str,
        file_size: int,
        init_result: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int, str], None]],
        speed_limit: Optional[int] = None,
        pick_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传文件到OSS
        
        Args:
            file_path: 本地文件路径
            file_name: 文件名
            file_size: 文件大小
            init_result: 初始化结果
            progress_callback: 进度回调函数
        
        Returns:
            上传结果
        """
        # Step 1: 获取上传凭证
        if progress_callback:
            progress_callback(0, file_size, "获取上传凭证...")
        
        token_result = await self.api.get_upload_token()
        
        if not token_result.get("success"):
            return {
                "success": False,
                "error": "获取上传凭证失败",
                "details": token_result
            }
        
        # Step 2: 初始化OSS客户端
        self.oss_client = Cloud115OSS(
            endpoint=token_result.get("endpoint"),
            access_key_id=token_result.get("access_key_id"),
            access_key_secret=token_result.get("access_key_secret"),
            security_token=token_result.get("security_token")
        )
        
        # Step 3: 上传文件到OSS
        bucket = init_result.get("bucket")
        object_key = init_result.get("object")
        callback = init_result.get("callback")
        callback_var = init_result.get("callback_var")
        
        if progress_callback:
            progress_callback(0, file_size, "上传文件到OSS...")
        
        # 定义进度回调包装器
        def oss_progress_callback(uploaded: int, total: int):
            if progress_callback:
                progress_callback(uploaded, total, "上传中...")
        
        upload_result = await self.oss_client.upload_file(
            file_path=file_path,
            bucket=bucket,
            object_key=object_key,
            callback=callback,
            callback_var=callback_var,
            progress_callback=oss_progress_callback,
            speed_limit=speed_limit
        )
        
        if upload_result.get("success"):
            if progress_callback:
                progress_callback(file_size, file_size, "上传成功")
            
            logger.info(f"文件上传成功: {file_name}")
            return {
                "success": True,
                "method": "upload",
                "file_name": file_name,
                "file_size": file_size,
                "bucket": bucket,
                "object_key": object_key,
                "etag": upload_result.get("etag"),
                "parts_count": upload_result.get("parts_count", 0),
                "part_size": upload_result.get("part_size"),
                "pick_code": pick_code,
                "final_speed": upload_result.get("final_speed")
            }
        else:
            return {
                "success": False,
                "error": "OSS上传失败",
                "details": upload_result
            }
    
    async def resume_upload(
        self,
        file_path: str,
        target_parent_id: str,
        file_sha1: str,
        pick_code: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        speed_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        断点续传上传文件
        
        Args:
            file_path: 本地文件路径
            target_parent_id: 目标目录ID
            file_sha1: 文件sha1值
            pick_code: 上传任务key
            progress_callback: 进度回调函数（可选）
        
        Returns:
            上传结果
        """
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        # Step 1: 调用断点续传接口
        if progress_callback:
            progress_callback(0, file_size, "初始化断点续传...")
        
        resume_result = await self.api.resume_upload(
            file_size=file_size,
            target_parent_id=target_parent_id,
            file_sha1=file_sha1,
            pick_code=pick_code
        )
        
        if not resume_result.get("success"):
            return resume_result
        
        # Step 2: 获取上传凭证
        if progress_callback:
            progress_callback(0, file_size, "获取上传凭证...")
        
        token_result = await self.api.get_upload_token()
        
        if not token_result.get("success"):
            return {
                "success": False,
                "error": "获取上传凭证失败",
                "details": token_result
            }
        
        # Step 3: 初始化OSS客户端
        self.oss_client = Cloud115OSS(
            endpoint=token_result.get("endpoint"),
            access_key_id=token_result.get("access_key_id"),
            access_key_secret=token_result.get("access_key_secret"),
            security_token=token_result.get("security_token")
        )
        
        # Step 4: 上传文件到OSS
        bucket = resume_result.get("bucket")
        object_key = resume_result.get("object")
        callback = resume_result.get("callback")
        callback_var = resume_result.get("callback_var")
        
        if progress_callback:
            progress_callback(0, file_size, "上传文件到OSS...")
        
        # 定义进度回调包装器
        def oss_progress_callback(uploaded: int, total: int):
            if progress_callback:
                progress_callback(uploaded, total, "上传中...")
        
        upload_result = await self.oss_client.upload_file(
            file_path=file_path,
            bucket=bucket,
            object_key=object_key,
            callback=callback,
            callback_var=callback_var,
            progress_callback=oss_progress_callback,
            speed_limit=speed_limit
        )
        
        if upload_result.get("success"):
            if progress_callback:
                progress_callback(file_size, file_size, "上传成功")
            
            logger.info(f"文件断点续传成功: {file_name}")
            return {
                "success": True,
                "method": "resume",
                "file_name": file_name,
                "file_size": file_size,
                "bucket": bucket,
                "object_key": object_key,
                "etag": upload_result.get("etag"),
                "parts_count": upload_result.get("parts_count", 0)
            }
        else:
            return {
                "success": False,
                "error": "OSS上传失败",
                "details": upload_result
            }
    
    async def _calculate_sha1(self, file_path: str, progress_callback: Optional[Callable] = None) -> str:
        """
        计算文件sha1值
        
        Args:
            file_path: 文件路径
            progress_callback: 进度回调函数（可选）
        
        Returns:
            sha1值（十六进制字符串）
        """
        sha1 = hashlib.sha1()
        file_size = os.path.getsize(file_path)
        chunk_size = 8192
        read_bytes = 0
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha1.update(chunk)
                read_bytes += len(chunk)
                
                if progress_callback:
                    progress_callback(read_bytes, file_size, f"计算sha1值: {read_bytes}/{file_size} 字节")
        
        return sha1.hexdigest()
    
    async def _calculate_pre_sha1(self, file_path: str) -> str:
        """
        计算文件前128K sha1值
        
        Args:
            file_path: 文件路径
        
        Returns:
            sha1值（十六进制字符串）
        """
        sha1 = hashlib.sha1()
        
        with open(file_path, 'rb') as f:
            chunk = f.read(128 * 1024)  # 128K
            if chunk:
                sha1.update(chunk)
        
        return sha1.hexdigest()

