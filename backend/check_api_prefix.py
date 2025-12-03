"""
检查API前缀设置
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from app.core.config import settings
        print(f"API_PREFIX 设置值: '{settings.API_PREFIX}'")
        
        # 检查是否是空字符串
        if settings.API_PREFIX == "":
            print("✅ API_PREFIX 是空字符串，这是正确的")
        elif settings.API_PREFIX == "/api":
            print("⚠️  API_PREFIX 是 '/api'，这会导致路径重复")
        else:
            print(f"⚠️  API_PREFIX 是 '{settings.API_PREFIX}'，需要检查")
            
        # 检查漫画路由器的实际路径
        print("\n=== 检查漫画路由器的实际路径 ===")
        
        # 导入漫画路由器
        from app.api.manga_sync import router as manga_sync_router
        print(f"漫画同步路由器前缀: '{manga_sync_router.prefix}'")
        
        # 计算实际路径
        actual_path = f"{settings.API_PREFIX}{manga_sync_router.prefix}"
        print(f"实际路径: '{actual_path}'")
        
        # 检查路径是否重复
        if settings.API_PREFIX and manga_sync_router.prefix.startswith(settings.API_PREFIX):
            print("❌ 路径重复！漫画路由器前缀已经包含API前缀")
        else:
            print("✅ 路径组合正常")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()