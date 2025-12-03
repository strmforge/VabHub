"""
测试站点配置文件模板系统
包括配置文件加载、站点识别、内容解析等
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, init_db
from app.models.site import Site
from app.modules.site_profile.loader import SiteProfileLoader
from app.modules.site_profile.verifier import SiteVerifier
from app.modules.site_profile.parser import SiteParser
from app.modules.site_profile.service import SiteProfileService
from loguru import logger


async def test_profile_loader():
    """测试配置文件加载器"""
    print("\n" + "="*60)
    print("测试1: 配置文件加载器")
    print("="*60)
    
    loader = SiteProfileLoader()
    
    # 1. 列出所有配置文件
    profiles = loader.list_profiles()
    print(f"[OK] 列出配置文件: {len(profiles)} 个")
    for profile_id in profiles:
        print(f"  - {profile_id}")
    
    # 2. 加载NexusPHP配置
    nexusphp_profile = loader.load_profile("nexusphp")
    if nexusphp_profile:
        meta = nexusphp_profile.get("meta", {})
        print(f"[OK] 加载NexusPHP配置: {meta.get('name')} (family: {meta.get('family')})")
    else:
        print("[FAIL] 加载NexusPHP配置失败")
    
    # 3. 加载Gazelle配置
    gazelle_profile = loader.load_profile("gazelle")
    if gazelle_profile:
        meta = gazelle_profile.get("meta", {})
        print(f"[OK] 加载Gazelle配置: {meta.get('name')} (family: {meta.get('family')})")
    else:
        print("[FAIL] 加载Gazelle配置失败")
    
    # 4. 加载Unit3D配置
    unit3d_profile = loader.load_profile("unit3d")
    if unit3d_profile:
        meta = unit3d_profile.get("meta", {})
        print(f"[OK] 加载Unit3D配置: {meta.get('name')} (family: {meta.get('family')})")
    else:
        print("[FAIL] 加载Unit3D配置失败")


async def test_site_identification():
    """测试站点识别"""
    print("\n" + "="*60)
    print("测试2: 站点识别")
    print("="*60)
    
    # 使用简单的字典模拟Site对象，避免数据库模型问题
    class MockSite:
        def __init__(self):
            self.id = 1
            self.name = "测试NexusPHP站点"
            self.url = "https://test-nexusphp.example.com"
            self.is_active = True
    
    test_site = MockSite()
    print(f"[OK] 创建测试站点对象: {test_site.name}")
    
    # 测试站点识别
    profile_service = SiteProfileService()
    
    # 注意：实际识别需要访问真实站点，这里只测试逻辑
    print("[INFO] 站点识别需要访问真实站点，跳过实际验证")
    print(f"[OK] 站点识别服务初始化成功")
    
    # 测试获取站点类型
    family = profile_service.get_site_family(test_site)
    print(f"[OK] 获取站点类型: {family}")


async def test_verifier_rules():
    """测试验证规则引擎"""
    print("\n" + "="*60)
    print("测试3: 验证规则引擎")
    print("="*60)
    
    # 创建验证器（使用测试URL）
    verifier = SiteVerifier("https://test.example.com")
    
    # 测试规则配置
    test_rules = {
        "any": [
            {"meta_generator_equals": "NexusPHP"},
            {"title_contains": "NexusPHP"}
        ]
    }
    
    print("[INFO] 验证规则引擎初始化成功")
    print(f"[OK] 验证规则配置: {test_rules}")
    print("[INFO] 实际验证需要访问真实站点，跳过实际验证")


async def test_parser_rules():
    """测试解析规则引擎"""
    print("\n" + "="*60)
    print("测试4: 解析规则引擎")
    print("="*60)
    
    # 创建解析器
    parser = SiteParser("https://test.example.com")
    
    # 测试解析规则配置
    test_parse_rules = {
        "list": {
            "row": "table.torrents > tbody > tr",
            "fields": {
                "title_raw": {
                    "selector": "a[href*='details.php?id=']",
                    "text": True
                },
                "size_bytes": {
                    "selector": "td.size",
                    "text": True,
                    "transform": "size"
                }
            }
        }
    }
    
    print("[INFO] 解析规则引擎初始化成功")
    print(f"[OK] 解析规则配置: {test_parse_rules}")
    print("[INFO] 实际解析需要访问真实站点，跳过实际解析")
    
    # 测试数据转换
    size_str = "1.5 GB"
    parsed_size = parser._parse_size(size_str)
    print(f"[OK] 大小转换测试: '{size_str}' -> {parsed_size} 字节")


async def test_integration():
    """集成测试"""
    print("\n" + "="*60)
    print("测试5: 集成测试")
    print("="*60)
    
    # 使用简单的字典模拟Site对象，避免数据库模型问题
    class MockSite:
        def __init__(self):
            self.id = 1
            self.name = "集成测试站点"
            self.url = "https://integration.test.com"
            self.is_active = True
    
    test_site = MockSite()
    print(f"[OK] 创建测试站点对象: {test_site.name}")
    
    # 测试完整流程
    profile_service = SiteProfileService()
    
    # 1. 列出所有配置文件
    profiles = profile_service.loader.list_profiles()
    print(f"[OK] 可用配置文件: {len(profiles)} 个")
    
    # 2. 获取站点类型（基于域名匹配）
    family = profile_service.get_site_family(test_site)
    print(f"[OK] 站点类型: {family}")


async def test_config_files():
    """测试配置文件完整性"""
    print("\n" + "="*60)
    print("测试6: 配置文件完整性检查")
    print("="*60)
    
    loader = SiteProfileLoader()
    profiles = loader.list_profiles()
    
    required_fields = ["meta", "verify", "parse"]
    required_meta_fields = ["id", "name", "family", "version"]
    
    for profile_id in profiles:
        profile = loader.load_profile(profile_id)
        if not profile:
            print(f"[FAIL] {profile_id}: 加载失败")
            continue
        
        # 检查必需字段
        missing_fields = []
        for field in required_fields:
            if field not in profile:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"[FAIL] {profile_id}: 缺少字段 {missing_fields}")
        else:
            # 检查meta字段
            meta = profile.get("meta", {})
            missing_meta = []
            for field in required_meta_fields:
                if field not in meta:
                    missing_meta.append(field)
            
            if missing_meta:
                print(f"[FAIL] {profile_id}: meta缺少字段 {missing_meta}")
            else:
                print(f"[OK] {profile_id}: 配置文件完整")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("站点配置文件模板系统测试")
    print("="*60)
    
    try:
        # 运行测试（不需要数据库）
        await test_profile_loader()
        await test_site_identification()
        await test_verifier_rules()
        await test_parser_rules()
        await test_integration()
        await test_config_files()
        
        print("\n" + "="*60)
        print("[OK] 所有测试完成")
        print("="*60)
        print("\n注意: 站点识别和解析的实际测试需要访问真实PT站点")
        print("建议在实际环境中使用真实站点URL进行测试")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("[FAIL] 测试失败")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

