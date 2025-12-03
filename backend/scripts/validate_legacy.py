#!/usr/bin/env python3
"""
验证过往版本功能可用性
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "VabHub" / "backend"))

from app.core.legacy_validator import LegacyValidator


def main():
    """主函数"""
    print("=" * 80)
    print("过往版本功能可用性检测")
    print("=" * 80)
    
    validator = LegacyValidator()
    
    # 验证所有功能
    results = validator.validate_all()
    
    # 打印报告
    validator.print_report()
    
    # 返回结果
    summary = validator.get_summary()
    
    if summary["availability_rate"] > 0.5:
        print("\n✅ 大部分功能可用")
        return 0
    else:
        print("\n⚠️  部分功能不可用，请检查路径和依赖")
        return 1


if __name__ == "__main__":
    sys.exit(main())

