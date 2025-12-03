#!/usr/bin/env python3
"""检查实际端点格式"""
import httpx
import json

from scripts.api_test_config import API_PREFIX as CONFIG_API_PREFIX


def main():
    try:
        response = httpx.get("http://localhost:8001/openapi.json", timeout=10)
        response.raise_for_status()
        spec = response.json()
        
        paths = list(spec.get("paths", {}).keys())
        prefix = CONFIG_API_PREFIX
        
        print(f"总端点数: {len(paths)}")
        print(f"\n包含 {prefix} 的端点: {sum(1 for p in paths if prefix in p)}")
        print(f"包含 /api 的端点: {sum(1 for p in paths if '/api' in p)}")
        print(f"不包含 /api 的端点: {sum(1 for p in paths if '/api' not in p)}")
        
        print("\n实际端点示例（前30个）:")
        for i, path in enumerate(paths[:30], 1):
            print(f"  {i:2d}. {path}")
        
        # 检查是否有认证相关端点
        print("\n检查认证相关端点:")
        auth_paths = [p for p in paths if 'auth' in p.lower() or 'login' in p.lower()]
        for path in auth_paths[:10]:
            print(f"  {path}")
            
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()

