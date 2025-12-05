#!/usr/bin/env python3
"""
测试过往版本功能适配器
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "VabHub" / "backend"))

from app.core.legacy_validator import validate_legacy_functions
from app.core.legacy_adapter import get_legacy_adapter


def test_adapter_basic():
    """测试适配器基本功能"""
    print("\n" + "=" * 80)
    print("测试适配器基本功能")
    print("=" * 80)
    
    adapter = get_legacy_adapter()
    
    # 1. 测试获取可用功能列表
    print("\n1. 获取可用功能列表:")
    functions = adapter.get_available_functions()
    for func_name, func_info in functions.items():
        print(f"  - {func_name}: {func_info['description']}")
        print(f"    版本: {', '.join(func_info['versions'])}")
    
    # 2. 测试路径检查
    print("\n2. 检查路径:")
    from app.core.legacy_adapter import LEGACY_PATHS
    for version, path in LEGACY_PATHS.items():
        exists = path.exists() if path else False
        status = "✅" if exists else "❌"
        print(f"  {status} {version}: {path}")


def test_recommendation_engine():
    """测试推荐引擎"""
    print("\n" + "=" * 80)
    print("测试推荐引擎")
    print("=" * 80)
    
    try:
        adapter = get_legacy_adapter()
        
        # 尝试获取推荐引擎
        engine = adapter.get_instance("recommendation_engine", version="vabhub_1")
        
        if engine:
            print("✅ 推荐引擎加载成功")
            
            # 测试生成初始推荐
            try:
                recommendations = engine.generate_initial_recommendations(user_id=1)
                print(f"✅ 生成初始推荐成功，返回 {len(recommendations)} 个推荐")
                if recommendations:
                    print(f"  示例: {recommendations[0]}")
            except Exception as e:
                print(f"❌ 生成初始推荐失败: {e}")
            
            # 测试更新推荐
            try:
                recommendations = engine.update_recommendations(user_id=1)
                print(f"✅ 更新推荐成功，返回 {len(recommendations)} 个推荐")
                if recommendations:
                    print(f"  示例: {recommendations[0]}")
            except Exception as e:
                print(f"❌ 更新推荐失败: {e}")
        else:
            print("❌ 推荐引擎加载失败")
            
    except Exception as e:
        print(f"❌ 测试推荐引擎出错: {e}")
        import traceback
        traceback.print_exc()


def test_media_parser():
    """测试媒体解析器"""
    print("\n" + "=" * 80)
    print("测试媒体解析器")
    print("=" * 80)
    
    try:
        adapter = get_legacy_adapter()
        
        # 尝试获取媒体解析器
        parser = adapter.get_instance("media_parser", version="vabhub_1")
        
        if parser:
            print("✅ 媒体解析器加载成功")
            
            # 测试解析文件名
            test_files = [
                "Movie.Title.2024.1080p.BluRay.x264.mkv",
                "TV.Show.S01E01.1080p.WEB-DL.mkv",
                "Anime.Title.E01.1080p.mkv"
            ]
            
            for test_file in test_files:
                try:
                    result = parser.parse_filename(test_file)
                    if result:
                        print(f"✅ 解析成功: {test_file}")
                        print(f"  标题: {getattr(result, 'title', 'N/A')}")
                        print(f"  类型: {getattr(result, 'media_type', 'N/A')}")
                        print(f"  置信度: {getattr(result, 'confidence', 0.0):.2f}")
                    else:
                        print(f"⚠️  解析返回空结果: {test_file}")
                except Exception as e:
                    print(f"❌ 解析失败: {test_file} - {e}")
        else:
            print("❌ 媒体解析器加载失败")
            
    except Exception as e:
        print(f"❌ 测试媒体解析器出错: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=" * 80)
    print("过往版本功能适配器测试")
    print("=" * 80)
    
    # 1. 运行完整验证
    print("\n运行完整验证...")
    validate_legacy_functions()
    
    # 2. 测试适配器基本功能
    test_adapter_basic()
    
    # 3. 测试推荐引擎
    test_recommendation_engine()
    
    # 4. 测试媒体解析器
    test_media_parser()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

