"""
检查后端日志
查看后端日志以了解具体的错误原因
"""

import sys
from pathlib import Path
from loguru import logger
from datetime import datetime, timedelta

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings


def check_logs(log_type: str = "error", lines: int = 50, hours: int = 24):
    """检查日志文件"""
    log_dir = Path(settings.LOG_DIR)
    
    if not log_dir.exists():
        logger.error(f"日志目录不存在: {log_dir}")
        return
    
    # 确定日志文件
    if log_type == "error":
        # 查找最新的错误日志
        error_logs = sorted(log_dir.glob("error_*.log"), reverse=True)
        if error_logs:
            log_file = error_logs[0]
        else:
            logger.warning("未找到错误日志文件")
            return
    elif log_type == "all":
        # 查找最新的所有日志
        all_logs = sorted(log_dir.glob("vabhub_*.log"), reverse=True)
        if all_logs:
            log_file = all_logs[0]
        else:
            logger.warning("未找到日志文件")
            return
    else:
        logger.error(f"未知的日志类型: {log_type}")
        return
    
    logger.info(f"检查日志文件: {log_file}")
    logger.info(f"文件大小: {log_file.stat().st_size / 1024:.2f} KB")
    
    # 读取日志
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        
        # 过滤时间范围
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_lines = []
        
        for line in all_lines:
            # 尝试解析时间戳
            try:
                # 格式: 2025-11-13 20:51:42.675 | ...
                if " | " in line:
                    time_str = line.split(" | ")[0]
                    log_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                    if log_time >= cutoff_time:
                        filtered_lines.append(line)
                else:
                    # 如果没有时间戳，包含所有行
                    filtered_lines.append(line)
            except:
                # 如果解析失败，包含该行
                filtered_lines.append(line)
        
        # 显示最后N行
        display_lines = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
        
        logger.info(f"\n最近 {len(display_lines)} 条日志（过去 {hours} 小时）:")
        logger.info("="*80)
        
        for line in display_lines:
            print(line.rstrip())
        
        logger.info("="*80)
        logger.info(f"\n总共 {len(filtered_lines)} 条日志（过去 {hours} 小时）")
        logger.info(f"日志文件总行数: {len(all_lines)}")
        
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")


def search_logs(keyword: str, log_type: str = "all", hours: int = 24):
    """搜索日志中的关键词"""
    log_dir = Path(settings.LOG_DIR)
    
    if not log_dir.exists():
        logger.error(f"日志目录不存在: {log_dir}")
        return
    
    # 查找日志文件
    if log_type == "error":
        log_files = sorted(log_dir.glob("error_*.log"), reverse=True)
    else:
        log_files = sorted(log_dir.glob("vabhub_*.log"), reverse=True)
    
    if not log_files:
        logger.warning("未找到日志文件")
        return
    
    logger.info(f"搜索关键词: {keyword}")
    logger.info(f"在 {len(log_files)} 个日志文件中搜索\n")
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    matches = []
    
    for log_file in log_files[:3]:  # 只检查最近3个日志文件
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if keyword.lower() in line.lower():
                        # 检查时间
                        try:
                            if " | " in line:
                                time_str = line.split(" | ")[0]
                                log_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                                if log_time >= cutoff_time:
                                    matches.append((log_file.name, line.rstrip()))
                        except:
                            matches.append((log_file.name, line.rstrip()))
        except Exception as e:
            logger.warning(f"读取日志文件失败 {log_file}: {e}")
    
    if matches:
        logger.info(f"找到 {len(matches)} 条匹配记录:")
        logger.info("="*80)
        for file_name, line in matches[-50:]:  # 只显示最后50条
            print(f"[{file_name}] {line}")
        logger.info("="*80)
    else:
        logger.info("未找到匹配的记录")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查后端日志")
    parser.add_argument("--type", choices=["error", "all"], default="error", help="日志类型")
    parser.add_argument("--lines", type=int, default=50, help="显示行数")
    parser.add_argument("--hours", type=int, default=24, help="时间范围（小时）")
    parser.add_argument("--search", type=str, help="搜索关键词")
    
    args = parser.parse_args()
    
    if args.search:
        search_logs(args.search, args.type, args.hours)
    else:
        check_logs(args.type, args.lines, args.hours)


if __name__ == "__main__":
    main()

