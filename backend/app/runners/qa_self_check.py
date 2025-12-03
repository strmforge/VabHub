"""
QA 自检 Runner
QA-1 实现

一键运行 VabHub 功能级自检

Usage:
    python -m app.runners.qa_self_check
    python -m app.runners.qa_self_check --json
    python -m app.runners.qa_self_check --fail-on-warn
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime

from loguru import logger


# ANSI 颜色码
class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def status_color(status: str) -> str:
    """获取状态对应的颜色"""
    colors = {
        "pass": Colors.GREEN,
        "warn": Colors.YELLOW,
        "fail": Colors.RED,
        "skipped": Colors.DIM,
    }
    return colors.get(status, Colors.RESET)


def status_icon(status: str) -> str:
    """获取状态对应的图标"""
    icons = {
        "pass": "✓",
        "warn": "⚠",
        "fail": "✗",
        "skipped": "○",
    }
    return icons.get(status, "?")


def print_result_table(result: dict) -> None:
    """打印结果表格"""
    print()
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}  VabHub 自检报告{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print()
    
    # 总体状态
    overall = result["overall_status"]
    color = status_color(overall)
    icon = status_icon(overall)
    print(f"  整体状态: {color}{icon} {overall.upper()}{Colors.RESET}")
    print(f"  开始时间: {result['started_at']}")
    print(f"  结束时间: {result['finished_at']}")
    print(f"  总耗时:   {result.get('duration_ms', 0)}ms")
    print()
    
    # 各组统计
    summary = result.get("summary", {})
    print(f"  统计: {Colors.GREEN}PASS={summary.get('pass', 0)}{Colors.RESET}, "
          f"{Colors.YELLOW}WARN={summary.get('warn', 0)}{Colors.RESET}, "
          f"{Colors.RED}FAIL={summary.get('fail', 0)}{Colors.RESET}, "
          f"{Colors.DIM}SKIP={summary.get('skipped', 0)}{Colors.RESET}")
    print()
    
    # 各组详情
    for group in result.get("groups", []):
        group_status = group["status"]
        group_color = status_color(group_status)
        group_icon = status_icon(group_status)
        
        # 计算组内通过数
        items = group.get("items", [])
        pass_count = sum(1 for i in items if i["status"] == "pass")
        total_count = len(items)
        
        print(f"{Colors.BOLD}[{group['name']}]{Colors.RESET} "
              f"{group_color}{group_icon} {group_status.upper()}{Colors.RESET} "
              f"({pass_count}/{total_count})")
        
        # 只显示非 PASS 的项目详情
        for item in items:
            item_status = item["status"]
            if item_status != "pass":
                item_color = status_color(item_status)
                item_icon = status_icon(item_status)
                duration = f" ({item.get('duration_ms', 0)}ms)" if item.get('duration_ms') else ""
                print(f"  {item_color}{item_icon}{Colors.RESET} {item['name']}{duration}")
                if item.get("message"):
                    print(f"    └─ {Colors.DIM}{item['message']}{Colors.RESET}")
        
        print()
    
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print()


async def _run_once(args: argparse.Namespace) -> int:
    """执行一次自检"""
    from app.core.database import AsyncSessionLocal
    from app.services.self_check_service import run_full_self_check
    
    async with AsyncSessionLocal() as session:
        result = await run_full_self_check(session)
    
    # 转换为 dict
    result_dict = result.model_dump()
    
    # 添加 summary 和 duration_ms
    result_dict["summary"] = result.summary
    result_dict["duration_ms"] = result.duration_ms
    
    # 时间格式化
    result_dict["started_at"] = result.started_at.isoformat()
    result_dict["finished_at"] = result.finished_at.isoformat()
    
    if args.json:
        # JSON 输出
        print(json.dumps(result_dict, indent=2, ensure_ascii=False, default=str))
    else:
        # 表格输出
        print_result_table(result_dict)
    
    # 确定退出码
    if result.overall_status.value == "fail":
        return 1
    elif result.overall_status.value == "warn" and args.fail_on_warn:
        return 2
    else:
        return 0


def main() -> None:
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Run VabHub self-check suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.runners.qa_self_check           # 运行自检，表格输出
  python -m app.runners.qa_self_check --json    # JSON 格式输出
  python -m app.runners.qa_self_check --fail-on-warn  # WARN 时也返回非零退出码

Exit Codes:
  0 - 所有检查通过或仅有 WARN（除非 --fail-on-warn）
  1 - 存在 FAIL
  2 - 存在 WARN（仅在 --fail-on-warn 时）
"""
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON to stdout instead of table format"
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Exit non-zero (code 2) if any WARN items"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress logger output (only show result)"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    if args.quiet or args.json:
        logger.remove()
    
    try:
        exit_code = asyncio.run(_run_once(args))
    except KeyboardInterrupt:
        print("\n中断")
        exit_code = 130
    except Exception as e:
        logger.exception(f"自检运行失败: {e}")
        if args.json:
            print(json.dumps({
                "error": str(e),
                "overall_status": "fail",
            }))
        else:
            print(f"{Colors.RED}自检运行失败: {e}{Colors.RESET}")
        exit_code = 1
    
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
