"""
调试健康检查问题
"""
import requests
import json

def debug_health_check():
    """调试健康检查"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        print(f"健康检查状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 健康检查正常")
            health_data = response.json()
            print(f"健康状态: {health_data.get('status', 'unknown')}")
            
            # 显示详细的健康检查结果
            if 'checks' in health_data:
                print("\n详细健康检查结果:")
                for check_name, check_result in health_data['checks'].items():
                    status = check_result.get('status', 'unknown')
                    message = check_result.get('message', '无消息')
                    print(f"  {check_name}: {status} - {message}")
        else:
            print(f"❌ 健康检查失败")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text[:500]}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
    except requests.exceptions.Timeout:
        print("❌ 健康检查请求超时")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")

def check_individual_health():
    """检查单项健康检查"""
    health_checks = [
        "database",
        "cache_l1",
        "cache_l2", 
        "cache_l3",
        "disk",
        "memory"
    ]
    
    print("\n=== 检查单项健康检查 ===")
    for check_name in health_checks:
        try:
            response = requests.get(f'http://localhost:8000/health/{check_name}', timeout=5)
            print(f"{check_name}: 状态码 {response.status_code}")
            if response.status_code == 200:
                check_data = response.json()
                status = check_data.get('status', 'unknown')
                message = check_data.get('message', '无消息')
                print(f"  状态: {status}, 消息: {message}")
            else:
                try:
                    error_data = response.json()
                    print(f"  错误: {error_data}")
                except:
                    print(f"  响应: {response.text[:200]}")
        except Exception as e:
            print(f"{check_name}: 检查异常 - {e}")

def main():
    print("=== 调试健康检查问题 ===")
    
    # 调试健康检查
    debug_health_check()
    
    # 检查单项健康检查
    check_individual_health()
    
    print("\n=== 问题分析 ===")
    print("如果健康检查返回503状态码，说明后端服务遇到了初始化问题")
    print("常见问题包括:")
    print("1. 数据库连接失败")
    print("2. 缓存系统初始化失败")
    print("3. 磁盘空间不足")
    print("4. 内存不足")
    print("5. 其他服务依赖问题")

if __name__ == "__main__":
    main()