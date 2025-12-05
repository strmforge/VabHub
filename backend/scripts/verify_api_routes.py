"""
验证API路由和响应模型
检查所有API端点是否使用统一响应模型
"""

import sys
from pathlib import Path

# 添加backend目录到路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from fastapi import APIRouter
from app.api import api_router
from app.core.schemas import BaseResponse

from scripts.api_test_config import API_PREFIX as CONFIG_API_PREFIX


def check_route_response_model(route):
    """检查路由的响应模型"""
    if hasattr(route, 'response_model'):
        return route.response_model
    return None


def get_all_routes(router: APIRouter, prefix: str = ""):
    """获取所有路由"""
    routes = []
    
    for route in router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            full_path = prefix + route.path
            for method in route.methods:
                if method != "HEAD":  # 跳过HEAD方法
                    response_model = check_route_response_model(route)
                    routes.append({
                        'method': method,
                        'path': full_path,
                        'response_model': response_model,
                        'route': route
                    })
        elif hasattr(route, 'routes'):  # 嵌套路由器
            nested_prefix = prefix + (getattr(route, 'prefix', '') or '')
            routes.extend(get_all_routes(route, nested_prefix))
    
    return routes


def main():
    """主函数"""
    print("=" * 80)
    print("API路由和响应模型验证")
    print("=" * 80)
    print()
    
    # 获取所有路由
    all_routes = get_all_routes(api_router, CONFIG_API_PREFIX)
    
    print(f"📊 发现 {len(all_routes)} 个API端点")
    print()
    
    # 分类统计
    using_base_response = []
    not_using_base_response = []
    special_routes = []
    
    for route_info in all_routes:
        method = route_info['method']
        path = route_info['path']
        response_model = route_info['response_model']
        
        # 跳过WebSocket路由
        if 'websocket' in path.lower() or 'ws' in path.lower():
            special_routes.append((method, path, "WebSocket协议"))
            continue
        
        # 跳过健康检查（特殊格式）
        if '/health' in path:
            special_routes.append((method, path, "健康检查（特殊格式）"))
            continue
        
        # 检查是否使用BaseResponse
        if response_model:
            # 检查是否是BaseResponse或其子类
            if response_model == BaseResponse:
                using_base_response.append((method, path))
            elif hasattr(response_model, '__origin__'):  # 泛型类型
                # 检查泛型的基础类型
                origin = response_model.__origin__
                if origin == BaseResponse or BaseResponse in getattr(response_model, '__args__', []):
                    using_base_response.append((method, path))
                else:
                    not_using_base_response.append((method, path, f"使用 {response_model}"))
            else:
                not_using_base_response.append((method, path, f"使用 {response_model}"))
        else:
            not_using_base_response.append((method, path, "未指定响应模型"))
    
    # 输出结果
    print("✅ 使用统一响应模型 (BaseResponse):")
    print(f"   共 {len(using_base_response)} 个端点")
    if len(using_base_response) > 0:
        for method, path in using_base_response[:10]:  # 只显示前10个
            print(f"   - {method:6} {path}")
        if len(using_base_response) > 10:
            print(f"   ... 还有 {len(using_base_response) - 10} 个端点")
    print()
    
    if not_using_base_response:
        print("⚠️  未使用统一响应模型:")
        print(f"   共 {len(not_using_base_response)} 个端点")
        for method, path, reason in not_using_base_response:
            print(f"   - {method:6} {path}")
            print(f"     原因: {reason}")
        print()
    
    if special_routes:
        print("ℹ️  特殊路由（不需要统一响应模型）:")
        print(f"   共 {len(special_routes)} 个端点")
        for method, path, reason in special_routes:
            print(f"   - {method:6} {path}")
            print(f"     原因: {reason}")
        print()
    
    # 统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    total_routes = len(all_routes)
    migrated_routes = len(using_base_response)
    special_count = len(special_routes)
    unmigrated_count = len(not_using_base_response)
    
    print(f"总路由数: {total_routes}")
    print(f"✅ 已迁移: {migrated_routes} ({migrated_routes/total_routes*100:.1f}%)")
    print(f"ℹ️  特殊路由: {special_count} ({special_count/total_routes*100:.1f}%)")
    print(f"⚠️  未迁移: {unmigrated_count} ({unmigrated_count/total_routes*100:.1f}%)")
    print()
    
    if unmigrated_count == 0:
        print("🎉 所有需要迁移的API端点都已使用统一响应模型！")
        return 0
    else:
        print("⚠️  仍有部分端点未使用统一响应模型，请检查上述列表")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

