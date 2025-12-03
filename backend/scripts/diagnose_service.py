"""
服务诊断脚本
检查服务状态和可能的问题
"""

import sys
import subprocess
import socket
from pathlib import Path

# 修复Windows编码问题
if sys.platform == "win32":
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def check_port(port: int):
    """检查端口是否被占用"""
    print(f"[检查] 端口 {port} 状态...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"  [INFO] 端口 {port} 已被占用")
            return True
        else:
            print(f"  [INFO] 端口 {port} 未被占用")
            return False
    except Exception as e:
        print(f"  [ERROR] 检查端口失败: {e}")
        return False


def check_process(port: int):
    """检查占用端口的进程"""
    print(f"[检查] 占用端口 {port} 的进程...")
    try:
        if sys.platform == "win32":
            # Windows: 使用netstat查找进程
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.split('\n')
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"  [INFO] 进程ID: {pid}")
                        
                        # 尝试获取进程名称
                        try:
                            task_result = subprocess.run(
                                ['tasklist', '/FI', f'PID eq {pid}'],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            task_lines = task_result.stdout.split('\n')
                            if len(task_lines) > 2:
                                process_info = task_lines[2].split()
                                if process_info:
                                    print(f"  [INFO] 进程名称: {process_info[0]}")
                        except:
                            pass
                        
                        return pid
        else:
            # Linux/Mac: 使用lsof
            result = subprocess.run(
                ['lsof', '-i', f':{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        print(f"  [INFO] 进程ID: {pid}")
                        return pid
        
        print(f"  [WARNING] 无法找到占用端口 {port} 的进程")
        return None
    except Exception as e:
        print(f"  [ERROR] 检查进程失败: {e}")
        return None


def check_database():
    """检查数据库连接配置"""
    print("[检查] 数据库配置...")
    try:
        project_root = Path(__file__).parent.parent.parent
        backend_root = project_root / "backend"
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(backend_root))
        
        from app.core.config import settings
        
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite"):
            print(f"  [INFO] 数据库类型: SQLite")
            print(f"  [INFO] 数据库URL: {db_url}")
            # 检查SQLite文件是否存在
            if ":///" in db_url:
                db_path = db_url.split(":///")[-1]
                db_file = Path(db_path)
                if db_file.exists():
                    print(f"  [OK] 数据库文件存在: {db_file}")
                else:
                    print(f"  [WARNING] 数据库文件不存在: {db_file}")
                    print(f"  [INFO] 将在首次运行时自动创建")
        elif db_url.startswith("postgresql"):
            print(f"  [INFO] 数据库类型: PostgreSQL")
            print(f"  [INFO] 数据库URL: {db_url.split('@')[1] if '@' in db_url else '已配置'}")
            print(f"  [WARNING] 需要检查PostgreSQL服务是否运行")
        else:
            print(f"  [INFO] 数据库类型: 未知")
            print(f"  [INFO] 数据库URL: {db_url}")
        
        return True
    except Exception as e:
        print(f"  [ERROR] 检查数据库配置失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("VabHub 服务诊断")
    print("=" * 60)
    print("")
    
    port = 8000
    
    # 检查端口
    port_occupied = check_port(port)
    print("")
    
    if port_occupied:
        # 检查进程
        pid = check_process(port)
        print("")
        
        if pid:
            print(f"[建议] 如果服务无响应，可以尝试:")
            print(f"  1. 终止进程: taskkill /PID {pid} /F (Windows)")
            print(f"  2. 重新启动服务: python backend/scripts/start.py")
    else:
        print("[建议] 端口未被占用，可以启动服务:")
        print("  python backend/scripts/start.py")
    
    print("")
    
    # 检查数据库
    check_database()
    
    print("")
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("")
    print("[建议] 如果服务无响应，可能的原因:")
    print("  1. 服务正在启动中（数据库初始化等）")
    print("  2. 数据库连接问题")
    print("  3. 服务启动失败但端口仍被占用")
    print("")
    print("[解决] 建议操作:")
    print("  1. 检查服务日志")
    print("  2. 检查数据库连接")
    print("  3. 重启服务")
    print("")


if __name__ == "__main__":
    main()

