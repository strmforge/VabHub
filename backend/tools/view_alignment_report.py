#!/usr/bin/env python3
"""查看对齐检查报告"""
import json
import sys
from pathlib import Path

def main():
    report_path = Path("alignment_report.json")
    if not report_path.exists():
        print(f"报告文件不存在: {report_path}")
        sys.exit(1)
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    summary = report.get('summary', {})
    
    print("="*60)
    print("前后端对齐检查报告摘要")
    print("="*60)
    print(f"期望端点总数: {summary.get('total_expected', 0)}")
    print(f"实际端点总数: {summary.get('total_actual', 0)}")
    print(f"匹配端点数量: {summary.get('matched', 0)}")
    print(f"覆盖率: {summary.get('coverage', 0):.2f}%")
    print(f"缺失端点数量: {summary.get('missing', 0)}")
    print(f"额外端点数量: {summary.get('extra', 0)}")
    
    matched = report.get('matched_endpoints', [])
    missing = report.get('missing_endpoints', [])
    
    if matched:
        print(f"\n匹配的端点（前10个）:")
        for ep in matched[:10]:
            print(f"  [OK] {ep}")
    
    if missing:
        print(f"\n缺失的端点（前20个）:")
        for ep in missing[:20]:
            print(f"  [MISSING] {ep}")
        if len(missing) > 20:
            print(f"  ... 还有 {len(missing) - 20} 个缺失端点")

if __name__ == "__main__":
    main()

