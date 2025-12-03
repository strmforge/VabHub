"""
检查端口8000是否被占用
"""
import socket
import requests

def check_port(port=8000):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def test_health_endpoint():
    """测试健康检查端点"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code, response.text[:200] if response.text else ""
    except requests.exceptions.ConnectionError:
        return "连接失败", ""
    except requests.exceptions.Timeout:
        return "超时", ""
    except Exception as e:
        return f"其他错误: {e}", ""

print("=== 端口检查 ===")
if check_port(8000):
    print("✅ 端口8000被占用")
else:
    print("❌ 端口8000未被占用")

print("\n=== 健康检查端点测试 ===")
status, text = test_health_endpoint()
print(f"状态: {status}")
if text:
    print(f"响应: {text}")

print("\n=== 测试其他端点 ===")
endpoints = ["/", "/docs", "/openapi.json"]
for endpoint in endpoints:
    try:
        response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
        print(f"{endpoint}: {response.status_code}")
    except Exception as e:
        print(f"{endpoint}: 错误 - {e}")