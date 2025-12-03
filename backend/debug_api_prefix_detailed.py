"""
详细调试API前缀问题
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=== 详细调试API前缀问题 ===")
    
    try:
        # 导入设置
        from app.core.config import settings
        print(f"1. API_PREFIX 设置值: '{settings.API_PREFIX}'")
        print(f"   类型: {type(settings.API_PREFIX)}")
        print(f"   长度: {len(settings.API_PREFIX)}")
        
        # 检查是否是空字符串
        if settings.API_PREFIX == "":
            print("   ✅ API_PREFIX 是空字符串")
        elif settings.API_PREFIX == "/api":
            print("   ⚠️  API_PREFIX 是 '/api'")
        else:
            print(f"   ⚠️  API_PREFIX 是 '{settings.API_PREFIX}'")
        
        print("\n2. 检查漫画路由器前缀:")
        
        # 导入所有漫画路由器
        from app.api.manga_sync import router as manga_sync_router
        from app.api.manga_local import router as manga_local_router
        from app.api.manga_remote import router as manga_remote_router
        from app.api.manga_progress import router as manga_progress_router
        
        routers = [
            ("漫画同步", manga_sync_router),
            ("本地漫画", manga_local_router),
            ("远程漫画", manga_remote_router),
            ("阅读进度", manga_progress_router)
        ]
        
        for name, router in routers:
            prefix = getattr(router, 'prefix', '无')
            print(f"   {name}路由器前缀: '{prefix}'")
            
            # 计算实际路径
            actual_path = f"{settings.API_PREFIX}{prefix}"
            print(f"   实际路径: '{actual_path}'")
            
            # 检查路径是否重复
            if settings.API_PREFIX and prefix.startswith(settings.API_PREFIX):
                print(f"   ❌ {name}路由器前缀已经包含API前缀，会导致路径重复")
            else:
                print(f"   ✅ {name}路由器路径组合正常")
        
        print("\n3. 检查主应用注册方式:")
        
        # 导入主应用
        from app.main import app
        
        # 查找API路由器的注册
        api_router_registered = False
        for route in app.routes:
            if hasattr(route, 'router'):
                router = route.router
                if hasattr(router, 'prefix'):
                    prefix = router.prefix
                    if prefix == settings.API_PREFIX:
                        api_router_registered = True
                        print(f"   ✅ API路由器已注册，前缀: '{prefix}'")
                        break
        
        if not api_router_registered:
            print("   ❌ 未找到API路由器注册")
            
        print("\n4. 问题分析:")
        if settings.API_PREFIX == "/api":
            print("   ❌ 问题确认: API_PREFIX设置为'/api'，而漫画路由器前缀已经是'/api/manga/...'")
            print("      这会导致路径变成'/api/api/manga/...'，从而产生404错误")
            print("   💡 解决方案: 将API_PREFIX设置为空字符串，或者修改漫画路由器前缀")
        else:
            print("   🔍 需要进一步分析问题原因")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()