"""
系统资源监控服务
提供CPU、内存、磁盘等系统资源的实时监控和历史记录
"""

import psutil
import platform
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache


class SystemMonitor:
    """系统资源监控服务"""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.cache = get_cache()
        
        # 历史数据存储（内存中，最近1000条）
        self.cpu_history = deque(maxlen=1000)
        self.memory_history = deque(maxlen=1000)
        self.disk_history = deque(maxlen=1000)
        self.network_history = deque(maxlen=1000)
    
    async def get_system_resources(self) -> Dict:
        """
        获取系统资源使用情况
        
        Returns:
            系统资源数据
        """
        try:
            # CPU使用率（多核平均）
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 磁盘使用情况
            if platform.system() == "Windows":
                disk = psutil.disk_usage('C:')
            else:
                disk = psutil.disk_usage('/')
            
            # 网络使用情况
            network = psutil.net_io_counters()
            
            # 构建数据
            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "usage_percent": round(cpu_percent, 2),
                    "usage_per_core": [round(c, 2) for c in cpu_per_core],
                    "count": cpu_count,
                    "frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
                    "frequency_max_mhz": round(cpu_freq.max, 2) if cpu_freq else None
                },
                "memory": {
                    "usage_percent": round(memory.percent, 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "free_gb": round(memory.free / (1024**3), 2)
                },
                "swap": {
                    "usage_percent": round(swap.percent, 2),
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "free_gb": round(swap.free / (1024**3), 2)
                },
                "disk": {
                    "usage_percent": round(disk.percent, 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                    "bytes_sent_gb": round(network.bytes_sent / (1024**3), 2),
                    "bytes_recv_gb": round(network.bytes_recv / (1024**3), 2)
                }
            }
            
            # 保存到历史记录
            self._save_to_history(data)
            
            return data
            
        except Exception as e:
            logger.error(f"获取系统资源失败: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _save_to_history(self, data: Dict):
        """保存到历史记录"""
        timestamp = datetime.utcnow()
        
        self.cpu_history.append({
            "timestamp": timestamp.isoformat(),
            "usage_percent": data["cpu"]["usage_percent"]
        })
        
        self.memory_history.append({
            "timestamp": timestamp.isoformat(),
            "usage_percent": data["memory"]["usage_percent"],
            "used_gb": data["memory"]["used_gb"]
        })
        
        self.disk_history.append({
            "timestamp": timestamp.isoformat(),
            "usage_percent": data["disk"]["usage_percent"],
            "used_gb": data["disk"]["used_gb"]
        })
        
        self.network_history.append({
            "timestamp": timestamp.isoformat(),
            "bytes_sent": data["network"]["bytes_sent"],
            "bytes_recv": data["network"]["bytes_recv"]
        })
    
    def get_cpu_history(self, limit: int = 100) -> List[Dict]:
        """获取CPU历史记录"""
        return list(self.cpu_history)[-limit:]
    
    def get_memory_history(self, limit: int = 100) -> List[Dict]:
        """获取内存历史记录"""
        return list(self.memory_history)[-limit:]
    
    def get_disk_history(self, limit: int = 100) -> List[Dict]:
        """获取磁盘历史记录"""
        return list(self.disk_history)[-limit:]
    
    def get_network_history(self, limit: int = 100) -> List[Dict]:
        """获取网络历史记录"""
        return list(self.network_history)[-limit:]
    
    def get_all_history(self, limit: int = 100) -> Dict:
        """获取所有历史记录"""
        return {
            "cpu": self.get_cpu_history(limit),
            "memory": self.get_memory_history(limit),
            "disk": self.get_disk_history(limit),
            "network": self.get_network_history(limit)
        }
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.cpu_history:
            return {
                "cpu": {"avg": 0, "min": 0, "max": 0},
                "memory": {"avg": 0, "min": 0, "max": 0},
                "disk": {"avg": 0, "min": 0, "max": 0}
            }
        
        cpu_values = [h["usage_percent"] for h in self.cpu_history]
        memory_values = [h["usage_percent"] for h in self.memory_history]
        disk_values = [h["usage_percent"] for h in self.disk_history]
        
        return {
            "cpu": {
                "avg": round(sum(cpu_values) / len(cpu_values), 2),
                "min": round(min(cpu_values), 2),
                "max": round(max(cpu_values), 2)
            },
            "memory": {
                "avg": round(sum(memory_values) / len(memory_values), 2),
                "min": round(min(memory_values), 2),
                "max": round(max(memory_values), 2)
            },
            "disk": {
                "avg": round(sum(disk_values) / len(disk_values), 2),
                "min": round(min(disk_values), 2),
                "max": round(max(disk_values), 2)
            }
        }


# 全局系统监控实例
_system_monitor: Optional[SystemMonitor] = None


def get_system_monitor(db: Optional[AsyncSession] = None) -> SystemMonitor:
    """获取系统监控实例（单例）"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor(db)
    return _system_monitor

