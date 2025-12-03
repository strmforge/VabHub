#!/usr/bin/env python3
"""
版本号管理脚本
RELEASE-1 R5-1 实现

用法:
    python tools/bump_version.py --patch   # 0.9.0 -> 0.9.1
    python tools/bump_version.py --minor   # 0.9.0 -> 0.10.0
    python tools/bump_version.py --major   # 0.9.0 -> 1.0.0
    python tools/bump_version.py --set 1.0.0  # 直接设置版本
"""

import argparse
import re
import sys
from pathlib import Path


VERSION_FILE = Path(__file__).parent.parent / "backend" / "app" / "core" / "version.py"


def read_version() -> str:
    """读取当前版本号"""
    content = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("无法从 version.py 中读取版本号")
    return match.group(1)


def write_version(new_version: str):
    """写入新版本号"""
    content = VERSION_FILE.read_text(encoding="utf-8")
    new_content = re.sub(
        r'(APP_VERSION\s*=\s*["\'])[^"\']+(["\'])',
        f'\\g<1>{new_version}\\g<2>',
        content
    )
    VERSION_FILE.write_text(new_content, encoding="utf-8")


def bump_version(current: str, bump_type: str) -> str:
    """计算新版本号"""
    parts = current.split(".")
    if len(parts) != 3:
        raise ValueError(f"无效的版本号格式: {current}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"无效的 bump 类型: {bump_type}")


def main():
    parser = argparse.ArgumentParser(description="VabHub 版本号管理")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_true", help="升级主版本号")
    group.add_argument("--minor", action="store_true", help="升级次版本号")
    group.add_argument("--patch", action="store_true", help="升级修订版本号")
    group.add_argument("--set", type=str, metavar="VERSION", help="直接设置版本号")
    group.add_argument("--get", action="store_true", help="只获取当前版本号")
    
    args = parser.parse_args()
    
    try:
        current = read_version()
        
        if args.get:
            print(current)
            return
        
        if args.set:
            new_version = args.set
        elif args.major:
            new_version = bump_version(current, "major")
        elif args.minor:
            new_version = bump_version(current, "minor")
        elif args.patch:
            new_version = bump_version(current, "patch")
        
        write_version(new_version)
        print(f"版本号已更新: {current} -> {new_version}")
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
