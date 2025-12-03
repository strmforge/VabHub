"""
测试HMAC签名功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.strm.hmac_signer import STRMHMACSigner, get_hmac_signer
from loguru import logger


async def test_hmac_signer():
    """测试HMAC签名器"""
    print("\n" + "="*60)
    print("HMAC签名功能测试")
    print("="*60)
    
    # 1. 测试签名器初始化
    print("\n[1] 测试签名器初始化...")
    signer = get_hmac_signer("test-secret-key")
    print("[OK] HMAC签名器初始化成功")
    
    # 2. 测试签名生成
    print("\n[2] 测试签名生成...")
    path = "/api/strm/stream/115/token123"
    import time
    timestamp = int(time.time()) + 3600  # 当前时间 + 1小时（未来时间戳，用于测试）
    signature = signer.sign_path(path, timestamp)
    print(f"路径: {path}")
    print(f"时间戳: {timestamp}")
    print(f"签名: {signature}")
    print("[OK] 签名生成成功")
    
    # 3. 测试签名验证（有效签名）
    print("\n[3] 测试签名验证（有效签名）...")
    is_valid = signer.verify(path, timestamp, signature, ttl=3600)
    if is_valid:
        print("[OK] 有效签名验证通过")
    else:
        print("[FAIL] 有效签名验证失败")
        return False
    
    # 4. 测试签名验证（无效签名）
    print("\n[4] 测试签名验证（无效签名）...")
    invalid_signature = "invalid_signature"
    is_valid = signer.verify(path, timestamp, invalid_signature, ttl=3600)
    if not is_valid:
        print("[OK] 无效签名验证失败（符合预期）")
    else:
        print("[FAIL] 无效签名验证通过（不符合预期）")
        return False
    
    # 5. 测试签名验证（过期签名）
    print("\n[5] 测试签名验证（过期签名）...")
    old_timestamp = 1703980800  # 2023-12-31 00:00:00 (1天前)
    old_signature = signer.sign_path(path, old_timestamp)
    is_valid = signer.verify(path, old_timestamp, old_signature, ttl=3600)
    if not is_valid:
        print("[OK] 过期签名验证失败（符合预期）")
    else:
        print("[FAIL] 过期签名验证通过（不符合预期）")
        return False
    
    # 6. 测试URL生成
    print("\n[6] 测试URL生成...")
    url, ts, sig = signer.generate_signed_url(
        path=path,
        ttl=3600,
        base_url="http://localhost:8000"
    )
    print(f"生成的URL: {url}")
    print(f"时间戳: {ts}")
    print(f"签名: {sig}")
    print("[OK] URL生成成功")
    
    # 7. 测试生成的URL验证
    print("\n[7] 测试生成的URL验证...")
    # 从URL中提取路径、时间戳和签名
    import re
    match = re.search(r'(/api/strm/stream/[^?]+)\?ts=(\d+)&sig=([a-f0-9]+)', url)
    if match:
        extracted_path = match.group(1)
        extracted_ts = int(match.group(2))
        extracted_sig = match.group(3)
        
        is_valid = signer.verify(extracted_path, extracted_ts, extracted_sig, ttl=3600)
        if is_valid:
            print("[OK] 生成的URL验证通过")
        else:
            print("[FAIL] 生成的URL验证失败")
            return False
    else:
        print("[FAIL] 无法从URL中提取参数")
        return False
    
    # 8. 测试参数篡改
    print("\n[8] 测试参数篡改...")
    tampered_url = url.replace("token123", "token456")  # 篡改路径
    match = re.search(r'(/api/strm/stream/[^?]+)\?ts=(\d+)&sig=([a-f0-9]+)', tampered_url)
    if match:
        tampered_path = match.group(1)
        tampered_ts = int(match.group(2))
        tampered_sig = match.group(3)
        
        is_valid = signer.verify(tampered_path, tampered_ts, tampered_sig, ttl=3600)
        if not is_valid:
            print("[OK] 参数篡改检测成功（符合预期）")
        else:
            print("[FAIL] 参数篡改检测失败（不符合预期）")
            return False
    else:
        print("[FAIL] 无法从篡改的URL中提取参数")
        return False
    
    print("\n" + "="*60)
    print("[OK] 所有HMAC签名测试通过！")
    print("="*60)
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_hmac_signer())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

