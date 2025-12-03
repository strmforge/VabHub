"""
日志服务
提供日志读取、过滤、搜索等功能
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger as loguru_logger

from app.core.config import settings


class LogService:
    """日志服务"""
    
    # 日志级别映射
    LEVEL_MAP = {
        "TRACE": 0,
        "DEBUG": 1,
        "INFO": 2,
        "SUCCESS": 3,
        "WARNING": 4,
        "ERROR": 5,
        "CRITICAL": 6
    }
    
    def __init__(self):
        self.log_dir = Path(settings.LOG_DIR)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """获取所有日志文件"""
        log_files = []
        
        # 获取所有日志文件
        for log_file in self.log_dir.glob("*.log"):
            try:
                stat = log_file.stat()
                log_files.append({
                    "name": log_file.name,
                    "path": str(log_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "error" if log_file.name.startswith("error_") else "general"
                })
            except Exception as e:
                loguru_logger.error(f"读取日志文件信息失败: {log_file} - {e}")
        
        # 按修改时间排序（最新的在前）
        log_files.sort(key=lambda x: x["modified"], reverse=True)
        
        return log_files
    
    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析日志行"""
        if not line or not line.strip():
            return None
        
        # 日志格式: {time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}
        # 示例: 2025-01-09 12:00:00 | INFO     | app.api.auth:login:45 - User logged in
        
        # 尝试匹配标准格式
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s+\| ([^:]+):([^:]+):(\d+) - (.+)"
        match = re.match(pattern, line.strip())
        
        if match:
            try:
                timestamp_str, level, module, function, line_num, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # 提取来源（模块名）
                source = module.split(".")[-1] if "." in module else module
                
                return {
                    "timestamp": timestamp.isoformat(),
                    "level": level.upper(),
                    "module": module,
                    "function": function,
                    "line": int(line_num),
                    "message": message,
                    "source": source,
                    "raw": line
                }
            except Exception as e:
                loguru_logger.debug(f"解析日志行失败: {line[:50]}... - {e}")
        
        # 如果标准格式匹配失败，尝试简化格式（只有时间和级别）
        simple_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s+\| (.+)"
        simple_match = re.match(simple_pattern, line.strip())
        
        if simple_match:
            try:
                timestamp_str, level, message = simple_match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                return {
                    "timestamp": timestamp.isoformat(),
                    "level": level.upper(),
                    "module": "unknown",
                    "function": "unknown",
                    "line": 0,
                    "message": message,
                    "source": "unknown",
                    "raw": line
                }
            except Exception:
                pass
        
        # 如果都匹配失败，返回原始行（级别为UNKNOWN）
        try:
            # 尝试提取时间戳
            time_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
            time_match = re.search(time_pattern, line)
            if time_match:
                timestamp = datetime.strptime(time_match.group(1), "%Y-%m-%d %H:%M:%S")
            else:
                timestamp = datetime.now()
        except Exception:
            timestamp = datetime.now()
        
        return {
            "timestamp": timestamp.isoformat(),
            "level": "UNKNOWN",
            "module": "unknown",
            "function": "unknown",
            "line": 0,
            "message": line.strip(),
            "source": "unknown",
            "raw": line
        }
    
    def read_logs(
        self,
        log_file: Optional[str] = None,
        level: Optional[str] = None,
        source: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Dict[str, Any]:
        """读取日志"""
        # 确定日志文件
        if log_file:
            log_path = self.log_dir / log_file
            if not log_path.exists():
                raise FileNotFoundError(f"日志文件不存在: {log_file}")
        else:
            # 使用最新的日志文件
            log_files = self.get_log_files()
            if not log_files:
                return {
                    "logs": [],
                    "total": 0,
                    "filtered": 0
                }
            log_path = Path(log_files[0]["path"])
        
        # 读取日志文件
        logs = []
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    log_entry = self.parse_log_line(line)
                    if not log_entry:
                        continue
                    
                    # 应用过滤
                    if level and log_entry["level"] != level.upper():
                        continue
                    
                    if source and source.lower() not in log_entry["source"].lower():
                        continue
                    
                    if keyword and keyword.lower() not in log_entry["message"].lower():
                        continue
                    
                    log_timestamp = datetime.fromisoformat(log_entry["timestamp"])
                    if start_time and log_timestamp < start_time:
                        continue
                    
                    if end_time and log_timestamp > end_time:
                        continue
                    
                    logs.append(log_entry)
        except Exception as e:
            loguru_logger.error(f"读取日志文件失败: {log_path} - {e}")
            raise
        
        # 按时间戳排序（最新的在前）
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 分页
        total = len(logs)
        paginated_logs = logs[offset:offset + limit]
        
        return {
            "logs": paginated_logs,
            "total": total,
            "filtered": len(paginated_logs),
            "offset": offset,
            "limit": limit
        }
    
    def get_log_statistics(self, log_file: Optional[str] = None) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            logs_data = self.read_logs(log_file=log_file, limit=10000)
            logs = logs_data["logs"]
            
            # 统计各级别数量
            level_counts = {
                "TRACE": 0,
                "DEBUG": 0,
                "INFO": 0,
                "SUCCESS": 0,
                "WARNING": 0,
                "ERROR": 0,
                "CRITICAL": 0
            }
            
            # 统计来源
            source_counts = {}
            
            for log in logs:
                level = log["level"]
                if level in level_counts:
                    level_counts[level] += 1
                
                source = log["source"]
                source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                "total": len(logs),
                "level_counts": level_counts,
                "source_counts": source_counts,
                "error_count": level_counts["ERROR"] + level_counts["CRITICAL"],
                "warning_count": level_counts["WARNING"],
                "info_count": level_counts["INFO"] + level_counts["SUCCESS"]
            }
        except Exception as e:
            loguru_logger.error(f"获取日志统计失败: {e}")
            return {
                "total": 0,
                "level_counts": {},
                "source_counts": {},
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0
            }
    
    def export_logs(
        self,
        log_file: Optional[str] = None,
        level: Optional[str] = None,
        source: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """导出日志"""
        # 读取日志
        logs_data = self.read_logs(
            log_file=log_file,
            level=level,
            source=source,
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            limit=100000  # 导出时限制最大数量
        )
        
        logs = logs_data["logs"]
        
        # 确定输出路径
        if not output_path:
            output_path = self.log_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # 写入文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for log in logs:
                    f.write(log["raw"] + "\n")
        except Exception as e:
            loguru_logger.error(f"导出日志失败: {output_path} - {e}")
            raise
        
        return output_path

