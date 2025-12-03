"""
检查后端服务状态
"""
import socket
import requests
import time

def check_port(host='localhost', port=8000):
    """检查端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_health_endpoint():
    """检查健康检查端点"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_docs_endpoint():
    """检查文档端点"""
    try:
        response = requests.get('http://localhost:8000/docs', timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("=== 检查后端服务状态 ===")
    
    # 检查端口
    port_open = check_port()
    print(f"端口8000是否开放: {'✅ 是' if port_open else '❌ 否'}")
    
    # 检查健康检查
    health_ok = check_health_endpoint()
    print(f"健康检查端点: {'✅ 正常' if health_ok else '❌ 异常'}")
    
    # 检查文档
    docs_ok = check_docs_endpoint()
    print(f"API文档端点: {'✅ 正常' if docs_ok else '❌ 异常'}")
    
    if not port_open:
        print("\n❌ 后端服务可能未启动或启动失败")
        print("请检查后端服务的启动日志")
    elif not health_ok:
        print("\n⚠️  后端服务已启动但健康检查异常")
        print("可能是数据库连接或其他服务初始化问题")
    elif not docs_ok:
        print("\n⚠️  后端服务已启动但API文档异常")
        print("可能是FastAPI应用配置问题")
    else:
        print("\n✅ 后端服务正常运行")
        
    # 如果服务未启动，等待并重试
    if not port_open:
        print("\n等待5秒后重试...")
        time.sleep(5)
        
        port_open = check_port()
        print(f"重试 - 端口8000是否开放: {'✅ 是' if port_open else '❌ 否'}")
        
        if port_open:
            health_ok = check_health_endpoint()
            print(f"重试 - 健康检查端点: {'✅ 正常' if health_ok else '❌ 异常'}")

if __name__ == "__main__":
    main()