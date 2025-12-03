#!/usr/bin/env python3
"""
调试漫画模块导入问题
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_manga_module_imports():
    """测试所有漫画模块的导入"""
    
    manga_modules = [
        "manga_sync",
        "manga_local", 
        "manga_remote",
        "manga_progress",
        "manga_source_admin",
        "reading_hub"
    ]
    
    print("🚀 开始测试漫画模块导入...")
    
    success_count = 0
    failed_modules = []
    
    for module_name in manga_modules:
        try:
            print(f"\n🔍 测试导入 {module_name}...")
            
            # 动态导入模块
            module = __import__(f"app.api.{module_name}", fromlist=["router"])
            
            # 检查路由器
            router = module.router
            print(f"✅ {module_name} 导入成功")
            print(f"   前缀: {router.prefix}")
            print(f"   标签: {router.tags}")
            print(f"   路由数量: {len(router.routes)}")
            
            success_count += 1
            
        except ImportError as e:
            print(f"❌ {module_name} 导入失败: {e}")
            failed_modules.append((module_name, str(e)))
        except AttributeError as e:
            print(f"❌ {module_name} 路由器属性错误: {e}")
            failed_modules.append((module_name, str(e)))
        except Exception as e:
            print(f"❌ {module_name} 导入时发生未知错误: {e}")
            failed_modules.append((module_name, str(e)))
    
    print(f"\n📊 导入测试结果:")
    print(f"   成功: {success_count}/{len(manga_modules)}")
    print(f"   失败: {len(failed_modules)}")
    
    if failed_modules:
        print(f"\n❌ 失败的模块:")
        for module_name, error in failed_modules:
            print(f"   - {module_name}: {error}")
        return False
    else:
        print(f"\n🎉 所有漫画模块导入成功!")
        return True

def test_manga_models_imports():
    """测试漫画相关模型的导入"""
    
    print(f"\n🔍 测试漫画相关模型导入...")
    
    manga_models = [
        "MangaSeriesLocal",
        "MangaChapterLocal", 
        "MangaSource",
        "MangaReadingProgress"
    ]
    
    success_count = 0
    failed_models = []
    
    for model_name in manga_models:
        try:
            # 尝试从不同模块导入模型
            if model_name in ["MangaSeriesLocal", "MangaChapterLocal"]:
                from app.models.manga_series_local import MangaSeriesLocal
                from app.models.manga_chapter_local import MangaChapterLocal
                print(f"✅ {model_name} 导入成功")
                success_count += 1
            elif model_name == "MangaSource":
                from app.models.manga_source import MangaSource
                print(f"✅ {model_name} 导入成功")
                success_count += 1
            elif model_name == "MangaReadingProgress":
                from app.models.manga_reading_progress import MangaReadingProgress
                print(f"✅ {model_name} 导入成功")
                success_count += 1
                
        except ImportError as e:
            print(f"❌ {model_name} 导入失败: {e}")
            failed_models.append((model_name, str(e)))
        except Exception as e:
            print(f"❌ {model_name} 导入时发生未知错误: {e}")
            failed_models.append((model_name, str(e)))
    
    print(f"\n📊 模型导入测试结果:")
    print(f"   成功: {success_count}/{len(manga_models)}")
    
    if failed_models:
        print(f"   失败: {len(failed_models)}")
        for model_name, error in failed_models:
            print(f"   - {model_name}: {error}")
        return False
    else:
        print(f"🎉 所有漫画模型导入成功!")
        return True

def test_manga_services_imports():
    """测试漫画相关服务的导入"""
    
    print(f"\n🔍 测试漫画相关服务导入...")
    
    manga_services = [
        "manga_sync_service",
        "manga_import_service", 
        "manga_remote_service",
        "manga_progress_service"
    ]
    
    success_count = 0
    failed_services = []
    
    for service_name in manga_services:
        try:
            # 动态导入服务
            module = __import__(f"app.services.{service_name}", fromlist=["*"])
            print(f"✅ {service_name} 导入成功")
            success_count += 1
            
        except ImportError as e:
            print(f"❌ {service_name} 导入失败: {e}")
            failed_services.append((service_name, str(e)))
        except Exception as e:
            print(f"❌ {service_name} 导入时发生未知错误: {e}")
            failed_services.append((service_name, str(e)))
    
    print(f"\n📊 服务导入测试结果:")
    print(f"   成功: {success_count}/{len(manga_services)}")
    
    if failed_services:
        print(f"   失败: {len(failed_services)}")
        for service_name, error in failed_services:
            print(f"   - {service_name}: {error}")
        return False
    else:
        print(f"🎉 所有漫画服务导入成功!")
        return True

def main():
    """主函数"""
    
    print("🚀 开始调试漫画模块导入问题...")
    
    # 测试模块导入
    modules_success = test_manga_module_imports()
    
    # 测试模型导入
    models_success = test_manga_models_imports()
    
    # 测试服务导入
    services_success = test_manga_services_imports()
    
    if modules_success and models_success and services_success:
        print("\n🎉 所有漫画相关导入测试通过!")
        print("\n💡 问题分析:")
        print("   如果模块导入都成功但API未注册，可能是:")
        print("   1. 后端服务启动时遇到运行时错误")
        print("   2. 数据库连接或模型定义问题")
        print("   3. FastAPI路由注册过程中的异常")
        sys.exit(0)
    else:
        print("\n❌ 导入测试失败，请检查相关模块")
        sys.exit(1)

if __name__ == "__main__":
    main()