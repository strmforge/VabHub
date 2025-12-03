"""
测试新实现的端点
验证参数名差异的兼容性和功能正确性
"""

import asyncio
import httpx
import json
from typing import Dict, List, Any
from loguru import logger

# 配置
BASE_URL = "http://localhost:8001"
TIMEOUT = 10.0

# 测试用例
TEST_CASES = [
    # 下载器管理
    {
        "name": "获取下载器实例列表",
        "method": "GET",
        "url": f"{BASE_URL}/api/dl/instances",
        "expected_status": 200
    },
    {
        "name": "获取下载器统计信息（使用did参数）",
        "method": "GET",
        "url": f"{BASE_URL}/api/dl/test-instance/stats",
        "expected_status": [200, 404]  # 404如果实例不存在也是正常的
    },
    {
        "name": "测试下载器连接（使用did参数）",
        "method": "POST",
        "url": f"{BASE_URL}/api/dl/test-instance/test",
        "expected_status": [200, 400, 404]
    },
    
    # 网关签名
    {
        "name": "网关签名",
        "method": "POST",
        "url": f"{BASE_URL}/api/gateway/sign",
        "data": {
            "path": "/test/path",
            "method": "GET"
        },
        "expected_status": 200
    },
    
    # 插件管理
    {
        "name": "获取插件注册表",
        "method": "GET",
        "url": f"{BASE_URL}/api/plugins/registry",
        "expected_status": 200
    },
    {
        "name": "安装插件（使用pid参数）",
        "method": "POST",
        "url": f"{BASE_URL}/api/plugins/test-plugin/install",
        "expected_status": [200, 400, 404]
    },
    
    # 规则集管理
    {
        "name": "获取规则集配置",
        "method": "GET",
        "url": f"{BASE_URL}/api/ruleset",
        "expected_status": 200
    },
    {
        "name": "更新规则集配置",
        "method": "PUT",
        "url": f"{BASE_URL}/api/ruleset",
        "data": {
            "rules": {
                "default": {
                    "quality": "1080p",
                    "min_seeders": 5
                }
            }
        },
        "expected_status": 200
    },
    
    # 刮削器管理
    {
        "name": "获取刮削器配置",
        "method": "GET",
        "url": f"{BASE_URL}/api/scraper/config",
        "expected_status": 200
    },
    {
        "name": "更新刮削器配置",
        "method": "PUT",
        "url": f"{BASE_URL}/api/scraper/config",
        "data": {
            "tmdb_enabled": True,
            "cache_enabled": True
        },
        "expected_status": 200
    },
    {
        "name": "测试刮削器（TMDB）",
        "method": "POST",
        "url": f"{BASE_URL}/api/scraper/test?scraper_type=tmdb&test_query=The Matrix",
        "expected_status": [200, 400]
    },
    
    # 密钥管理
    {
        "name": "获取密钥状态",
        "method": "GET",
        "url": f"{BASE_URL}/api/secrets/status",
        "expected_status": 200
    },
    
    # 参数名兼容性测试
    {
        "name": "获取下载详情（使用task_id）",
        "method": "GET",
        "url": f"{BASE_URL}/api/downloads/test-task-id",
        "expected_status": [200, 404]
    },
    {
        "name": "获取下载详情（使用download_id，应该兼容）",
        "method": "GET",
        "url": f"{BASE_URL}/api/downloads/test-download-id",
        "expected_status": [200, 404],
        "note": "FastAPI路由参数名不影响URL匹配，应该能正常工作"
    },
    {
        "name": "暂停下载（使用task_id）",
        "method": "POST",
        "url": f"{BASE_URL}/api/downloads/test-task-id/pause",
        "expected_status": [200, 404]
    },
    {
        "name": "恢复下载（使用download_id，应该兼容）",
        "method": "POST",
        "url": f"{BASE_URL}/api/downloads/test-download-id/resume",
        "expected_status": [200, 404],
        "note": "FastAPI路由参数名不影响URL匹配，应该能正常工作"
    },
    {
        "name": "获取订阅详情（使用subscription_id）",
        "method": "GET",
        "url": f"{BASE_URL}/api/subscriptions/1",
        "expected_status": [200, 404]
    },
    {
        "name": "获取订阅详情（使用sid，应该兼容）",
        "method": "GET",
        "url": f"{BASE_URL}/api/subscriptions/1",
        "expected_status": [200, 404],
        "note": "FastAPI路由参数名不影响URL匹配，应该能正常工作"
    },
    {
        "name": "获取任务详情（使用task_id）",
        "method": "GET",
        "url": f"{BASE_URL}/api/tasks/test-task-id",
        "expected_status": [200, 404]
    },
    {
        "name": "重试任务（使用tid，应该兼容）",
        "method": "POST",
        "url": f"{BASE_URL}/api/tasks/test-tid/retry",
        "expected_status": [200, 404],
        "note": "FastAPI路由参数名不影响URL匹配，应该能正常工作"
    }
]


async def test_endpoint(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """测试单个端点"""
    name = test_case["name"]
    method = test_case["method"]
    url = test_case["url"]
    expected_status = test_case.get("expected_status", 200)
    data = test_case.get("data")
    note = test_case.get("note", "")
    
    if not isinstance(expected_status, list):
        expected_status = [expected_status]
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            elif method == "PUT":
                response = await client.put(url, json=data)
            elif method == "DELETE":
                response = await client.delete(url)
            else:
                return {
                    "name": name,
                    "status": "error",
                    "error": f"不支持的HTTP方法: {method}"
                }
            
            status_ok = response.status_code in expected_status
            result = {
                "name": name,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "status": "pass" if status_ok else "fail",
                "note": note
            }
            
            # 尝试解析响应
            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text[:200]  # 限制长度
            
            return result
            
    except httpx.TimeoutException:
        return {
            "name": name,
            "url": url,
            "status": "error",
            "error": "请求超时"
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": "error",
            "error": str(e)
        }


async def test_websocket():
    """测试 WebSocket 连接"""
    try:
        import websockets
        uri = "ws://localhost:8001/api/ws/ws"
        
        async with websockets.connect(uri) as websocket:
            # 发送订阅消息
            subscribe_msg = {
                "type": "subscribe",
                "topics": ["dashboard", "downloads"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            
            # 等待响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            return {
                "name": "WebSocket连接测试",
                "status": "pass",
                "response": response_data
            }
    except ImportError:
        return {
            "name": "WebSocket连接测试",
            "status": "skip",
            "note": "websockets库未安装，跳过测试"
        }
    except Exception as e:
        return {
            "name": "WebSocket连接测试",
            "status": "error",
            "error": str(e)
        }


async def main():
    """主函数"""
    logger.info("开始测试新实现的端点...")
    
    results = []
    
    # 测试HTTP端点
    for test_case in TEST_CASES:
        logger.info(f"测试: {test_case['name']}")
        result = await test_endpoint(test_case)
        results.append(result)
        
        if result["status"] == "pass":
            logger.success(f"✓ {result['name']} - 状态码: {result['status_code']}")
        elif result["status"] == "fail":
            logger.warning(f"✗ {result['name']} - 状态码: {result['status_code']} (期望: {result['expected_status']})")
        else:
            logger.error(f"✗ {result['name']} - 错误: {result.get('error', '未知错误')}")
    
    # 测试WebSocket
    logger.info("测试 WebSocket 连接...")
    ws_result = await test_websocket()
    results.append(ws_result)
    
    if ws_result["status"] == "pass":
        logger.success(f"✓ {ws_result['name']}")
    elif ws_result["status"] == "skip":
        logger.info(f"- {ws_result['name']} - {ws_result.get('note', '')}")
    else:
        logger.error(f"✗ {ws_result['name']} - 错误: {ws_result.get('error', '未知错误')}")
    
    # 统计结果
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    errors = sum(1 for r in results if r["status"] == "error")
    skipped = sum(1 for r in results if r["status"] == "skip")
    total = len(results)
    
    print("\n" + "="*60)
    print("测试结果统计")
    print("="*60)
    print(f"总计: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"错误: {errors}")
    print(f"跳过: {skipped}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    # 保存详细结果
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "success_rate": passed/total*100
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    logger.info("测试结果已保存到 test_results.json")
    
    # 返回退出码
    if failed > 0 or errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

