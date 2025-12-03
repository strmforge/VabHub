"""
调试主应用中的API路由器注册
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=== 调试主应用API路由器注册 ===")
    
    try:
        # 导入主应用
        from app.main import app
        print("✅ 主应用导入成功")
        
        # 检查应用的路由
        print(f"主应用路由总数: {len(app.routes)}")
        
        # 查找API路由
        api_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and route.path:
                path_str = str(route.path)
                if '/api' in path_str:
                    api_routes.append(path_str)
        
        print(f"主应用中API路由数量: {len(api_routes)}")
        if api_routes:
            print("API路由:")
            for route in api_routes[:20]:
                print(f"  - {route}")
        else:
            print("❌ 主应用中没有API路由")
        
        # 检查漫画相关路由
        manga_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and route.path:
                path_str = str(route.path)
                if 'manga' in path_str or 'reading' in path_str:
                    manga_routes.append(path_str)
        
        print(f"主应用中漫画相关路由数量: {len(manga_routes)}")
        if manga_routes:
            print("漫画路由:")
            for route in manga_routes:
                print(f"  - {route}")
        else:
            print("❌ 主应用中没有漫画相关路由")
            
        # 检查是否有API路由器被注册
        print("\n=== 检查路由器注册 ===")
        
        # 导入API路由器
        from app.api import api_router
        print("✅ API路由器导入成功")
        
        # 检查API路由器是否在主应用的路由中
        api_router_in_app = False
        for route in app.routes:
            if hasattr(route, 'router') and route.router == api_router:
                api_router_in_app = True
                print("✅ API路由器已注册到主应用")
                break
        
        if not api_router_in_app:
            print("❌ API路由器未注册到主应用")
            
        # 检查settings配置
        try:
            from app.core.config import settings
            print(f"API前缀设置: {settings.API_PREFIX}")
        except Exception as e:
            print(f"⚠️  无法获取settings: {e}")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()