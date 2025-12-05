"""
简单的服务测试脚本
测试服务是否正常运行（不依赖健康检查）
"""

import asyncio
import sys
import httpx
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# 修复Windows编码问题
if sys.platform == "win32":
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


async def test_root():
    """测试根端点"""
    print("=" * 60)
    print("测试根端点 (/)")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/")
            
            if response.status_code == 200:
                print("[OK] 根端点响应正常")
                data = response.json()
                print(f"  名称: {data.get('name')}")
                print(f"  版本: {data.get('version')}")
                print(f"  API前缀: {data.get('api')}")
                return True
            else:
                print(f"[ERROR] 根端点响应异常: {response.status_code}")
                print(f"  响应: {response.text}")
                return False
    except httpx.ConnectError:
        print("[ERROR] 无法连接到后端服务")
        print("  请确保后端服务已启动")
        return False
    except httpx.ReadTimeout:
        print("[WARNING] 服务响应超时")
        print("  服务可能正在启动中或处理请求较慢")
        return False
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False


async def test_docs():
    """测试API文档端点"""
    print("")
    print("=" * 60)
    print("测试API文档端点 (/docs)")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/docs")
            
            if response.status_code == 200:
                print("[OK] API文档可访问")
                print("  URL: http://localhost:8000/docs")
                return True
            else:
                print(f"[ERROR] API文档不可访问: {response.status_code}")
                return False
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False


async def test_health_simple():
    """测试健康检查端点（简单版本，增加超时时间）"""
    print("")
    print("=" * 60)
    print("测试健康检查端点 (/health)")
    print("=" * 60)
    print("注意: 健康检查可能需要较长时间（检查数据库、缓存等）")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # 增加超时时间到30秒
            response = await client.get("http://localhost:8000/health")
            
            if response.status_code == 200:
                print("[OK] 健康检查通过")
                data = response.json()
                print(f"  状态: {data.get('status')}")
                checks = data.get('checks', {})
                print(f"  检查项数量: {len(checks)}")
                for check_name, check_result in checks.items():
                    status = check_result.get('status', 'unknown')
                    message = check_result.get('message', '')
                    status_icon = "[OK]" if status == "healthy" else "[ERROR]"
                    print(f"    {status_icon} {check_name}: {message}")
                return True
            else:
                print(f"[ERROR] 健康检查失败: {response.status_code}")
                print(f"  响应: {response.text[:200]}")
                return False
    except httpx.ReadTimeout:
        print("[WARNING] 健康检查超时（30秒）")
        print("  可能的原因:")
        print("    1. 数据库连接较慢")
        print("    2. 缓存检查耗时较长")
        print("    3. 服务正在初始化")
        print("  建议: 检查服务日志或数据库连接")
        return False
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("")
    print("=" * 60)
    print("VabHub 简单服务测试")
    print("=" * 60)
    print("")
    print("注意: 请确保后端服务已启动 (http://localhost:8000)")
    print("")
    
    results = []
    
    # 测试根端点
    results.append(("根端点", await test_root()))
    
    # 测试API文档
    results.append(("API文档", await test_docs()))
    
    # 测试健康检查（简单版本）
    results.append(("健康检查", await test_health_simple()))
    
    # 输出测试结果
    print("")
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print(f"[OK] {test_name}: 通过")
            passed += 1
        else:
            print(f"[ERROR] {test_name}: 失败")
            failed += 1
    
    print("")
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"通过率: {passed / len(results) * 100:.1f}%")
    print("")
    
    if failed == 0:
        print("[OK] 所有测试通过！")
        return 0
    else:
        print("[WARNING] 部分测试失败，请检查服务状态")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

