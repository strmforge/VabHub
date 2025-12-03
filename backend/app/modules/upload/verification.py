"""
上传验证模块
实现文件完整性验证和ETag对比
"""

import hashlib
import os
from typing import Dict, Optional, Any
from pathlib import Path
from loguru import logger

try:
    import oss2
    OSS2_AVAILABLE = True
except ImportError:
    OSS2_AVAILABLE = False
    logger.warning("oss2库未安装，上传验证功能受限")


def calculate_file_sha1(file_path: str, chunk_size: int = 8192) -> str:
    """
    计算文件的SHA1值
    
    Args:
        file_path: 文件路径
        chunk_size: 块大小（字节）
    
    Returns:
        SHA1值（十六进制字符串）
    """
    sha1 = hashlib.sha1()
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha1.update(chunk)
    
    return sha1.hexdigest()


def calculate_file_md5(file_path: str, chunk_size: int = 8192) -> str:
    """
    计算文件的MD5值
    
    Args:
        file_path: 文件路径
        chunk_size: 块大小（字节）
    
    Returns:
        MD5值（十六进制字符串）
    """
    md5 = hashlib.md5()
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    
    return md5.hexdigest()


def calculate_file_etag(file_path: str, part_size: int = 8388608) -> str:
    """
    计算文件的ETag（兼容OSS的ETag算法）
    
    OSS的ETag算法：
    - 如果文件小于part_size，ETag = MD5(file)
    - 如果文件大于part_size，ETag = MD5(part1_MD5 + part2_MD5 + ...) + "-" + part_count
    
    Args:
        file_path: 文件路径
        part_size: 分片大小（字节，默认8MB）
    
    Returns:
        ETag值
    """
    file_size = os.path.getsize(file_path)
    
    if file_size < part_size:
        # 小文件，直接计算MD5
        return calculate_file_md5(file_path)
    
    # 大文件，计算各分片的MD5，然后计算这些MD5的MD5
    md5_list = []
    part_count = 0
    
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(part_size)
            if not chunk:
                break
            
            md5 = hashlib.md5(chunk).hexdigest()
            md5_list.append(md5)
            part_count += 1
    
    # 计算所有MD5的MD5
    combined_md5 = hashlib.md5(''.join(md5_list).encode()).hexdigest()
    
    return f"{combined_md5}-{part_count}"


def verify_file_integrity(
    local_file_path: str,
    remote_etag: str,
    part_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    验证文件完整性（通过ETag对比）
    
    Args:
        local_file_path: 本地文件路径
        remote_etag: 远程文件的ETag
        part_size: 分片大小（字节，可选，用于计算ETag）
    
    Returns:
        验证结果
    """
    if not os.path.exists(local_file_path):
        return {
            "success": False,
            "verified": False,
            "error": "本地文件不存在"
        }
    
    try:
        # 计算本地文件的ETag
        if part_size:
            local_etag = calculate_file_etag(local_file_path, part_size)
        else:
            # 如果没有指定分片大小，尝试从ETag中推断
            if '-' in remote_etag:
                # 大文件ETag格式：MD5-part_count
                # 假设使用8MB分片（OSS默认）
                local_etag = calculate_file_etag(local_file_path, 8388608)
            else:
                # 小文件，直接计算MD5
                local_etag = calculate_file_md5(local_file_path)
        
        # 对比ETag（去除引号，如果有的中文）
        local_etag = local_etag.strip('"')
        remote_etag = remote_etag.strip('"')
        
        verified = local_etag.lower() == remote_etag.lower()
        
        if verified:
            logger.info(f"文件完整性验证成功: {local_file_path}, ETag: {local_etag}")
        else:
            logger.warning(f"文件完整性验证失败: {local_file_path}, 本地ETag: {local_etag}, 远程ETag: {remote_etag}")
        
        return {
            "success": True,
            "verified": verified,
            "local_etag": local_etag,
            "remote_etag": remote_etag,
            "match": verified
        }
        
    except Exception as e:
        logger.error(f"文件完整性验证异常: {e}")
        return {
            "success": False,
            "verified": False,
            "error": str(e)
        }


def verify_file_size(local_file_path: str, remote_size: int) -> Dict[str, Any]:
    """
    验证文件大小
    
    Args:
        local_file_path: 本地文件路径
        remote_size: 远程文件大小（字节）
    
    Returns:
        验证结果
    """
    if not os.path.exists(local_file_path):
        return {
            "success": False,
            "verified": False,
            "error": "本地文件不存在"
        }
    
    try:
        local_size = os.path.getsize(local_file_path)
        verified = local_size == remote_size
        
        if verified:
            logger.info(f"文件大小验证成功: {local_file_path}, 大小: {local_size} 字节")
        else:
            logger.warning(f"文件大小验证失败: {local_file_path}, 本地大小: {local_size} 字节, 远程大小: {remote_size} 字节")
        
        return {
            "success": True,
            "verified": verified,
            "local_size": local_size,
            "remote_size": remote_size,
            "match": verified
        }
        
    except Exception as e:
        logger.error(f"文件大小验证异常: {e}")
        return {
            "success": False,
            "verified": False,
            "error": str(e)
        }


def verify_upload_complete(
    local_file_path: str,
    remote_etag: str,
    remote_size: Optional[int] = None,
    part_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    完整的上传验证（ETag + 文件大小）
    
    Args:
        local_file_path: 本地文件路径
        remote_etag: 远程文件的ETag
        remote_size: 远程文件大小（字节，可选）
        part_size: 分片大小（字节，可选）
    
    Returns:
        验证结果
    """
    results = {
        "success": True,
        "verified": True,
        "checks": {}
    }
    
    # 验证ETag
    etag_result = verify_file_integrity(local_file_path, remote_etag, part_size)
    results["checks"]["etag"] = etag_result
    results["verified"] = results["verified"] and etag_result.get("verified", False)
    
    # 验证文件大小（如果提供）
    if remote_size is not None:
        size_result = verify_file_size(local_file_path, remote_size)
        results["checks"]["size"] = size_result
        results["verified"] = results["verified"] and size_result.get("verified", False)
    
    if not results["verified"]:
        results["success"] = False
        logger.error(f"上传验证失败: {local_file_path}")
    else:
        logger.info(f"上传验证成功: {local_file_path}")
    
    return results

