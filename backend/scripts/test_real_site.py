"""
实际PT站点测试脚本
用于测试站点识别和解析功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from app.modules.site_profile.service import SiteProfileService
from app.modules.site_profile.verifier import SiteVerifier
from app.modules.site_profile.parser import SiteParser
from loguru import logger


class MockSite:
    """模拟站点对象"""
    def __init__(self, name: str, url: str, cookie: str = None):
        self.id = 1
        self.name = name
        self.url = url
        self.cookie = cookie
        self.is_active = True


async def test_site_identification_real(site_name: str, site_url: str, cookie: str = None):
    """测试实际站点识别"""
    print("\n" + "="*60)
    print(f"测试站点识别: {site_name}")
    print("="*60)
    
    site = MockSite(site_name, site_url, cookie)
    profile_service = SiteProfileService()
    
    try:
        # 识别站点
        print(f"[INFO] 正在识别站点: {site_url}")
        profile = await profile_service.identify_site(site)
        
        if profile:
            meta = profile.get("meta", {})
            print("[OK] 站点识别成功!")
            print(f"  配置文件ID: {meta.get('id')}")
            print(f"  站点名称: {meta.get('name')}")
            print(f"  站点类型: {meta.get('family')}")
            print(f"  版本: {meta.get('version')}")
            return profile
        else:
            print("[FAIL] 未找到匹配的配置文件")
            return None
    except Exception as e:
        logger.error(f"识别站点失败: {e}")
        print(f"[FAIL] 识别失败: {e}")
        return None


async def test_site_verification_real(site_url: str, cookie: str = None):
    """测试实际站点验证"""
    print("\n" + "="*60)
    print(f"测试站点验证: {site_url}")
    print("="*60)
    
    verifier = SiteVerifier(site_url, cookie)
    
    # 测试NexusPHP验证规则
    nexusphp_rules = {
        "any": [
            {"meta_generator_equals": "NexusPHP"},
            {"title_contains": "NexusPHP"},
            {"selector_exists": "table.torrents"}
        ]
    }
    
    try:
        print("[INFO] 正在验证站点（NexusPHP规则）...")
        result = await verifier.verify(nexusphp_rules)
        print(f"[OK] 验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"验证站点失败: {e}")
        print(f"[FAIL] 验证失败: {e}")
        return False


async def test_site_parsing_real(site_url: str, cookie: str = None, page_url: str = None):
    """测试实际站点解析"""
    print("\n" + "="*60)
    print(f"测试站点解析: {page_url or site_url}")
    print("="*60)
    
    parser = SiteParser(site_url, cookie)
    
    # 测试列表解析规则
    parse_rules = {
        "list": {
            "row": "table.torrents > tbody > tr, table.torrent_table > tbody > tr",
            "fields": {
                "title_raw": {
                    "selector": "a[href*='details.php?id='], a[href*='/torrents.php?id=']",
                    "text": True
                },
                "size_bytes": {
                    "selector": "td.size",
                    "text": True,
                    "transform": "size"
                },
                "seeders": {
                    "selector": "td.seeders",
                    "text": True,
                    "transform": "int"
                }
            }
        }
    }
    
    try:
        print("[INFO] 正在解析站点内容...")
        result = await parser.parse(parse_rules, page_url)
        
        if result and "list" in result:
            items = result["list"]
            print(f"[OK] 解析成功! 找到 {len(items)} 个种子")
            if items:
                print("[INFO] 第一个种子示例:")
                first_item = items[0]
                for key, value in first_item.items():
                    print(f"  {key}: {value}")
        else:
            print("[WARN] 未找到种子列表")
        
        return result
    except Exception as e:
        logger.error(f"解析站点失败: {e}")
        print(f"[FAIL] 解析失败: {e}")
        return None


async def test_complete_workflow(site_name: str, site_url: str, cookie: str = None, page_url: str = None):
    """测试完整工作流程"""
    print("\n" + "="*60)
    print(f"完整工作流程测试: {site_name}")
    print("="*60)
    
    site = MockSite(site_name, site_url, cookie)
    profile_service = SiteProfileService()
    
    try:
        # 1. 识别站点
        print("\n[步骤1] 识别站点类型...")
        profile = await profile_service.identify_site(site)
        
        if not profile:
            print("[FAIL] 站点识别失败，无法继续")
            return False
        
        meta = profile.get("meta", {})
        print(f"[OK] 识别成功: {meta.get('name')} ({meta.get('family')})")
        
        # 2. 解析站点内容
        print("\n[步骤2] 解析站点内容...")
        result = await profile_service.parse_site_content(
            site,
            parse_type="list",
            page_url=page_url
        )
        
        if result and "list" in result:
            items = result["list"]
            print(f"[OK] 解析成功! 找到 {len(items)} 个种子")
        else:
            print("[WARN] 未找到种子列表")
        
        # 3. 获取站点类型
        print("\n[步骤3] 获取站点类型...")
        family = profile_service.get_site_family(site)
        print(f"[OK] 站点类型: {family}")
        
        return True
    except Exception as e:
        logger.error(f"完整工作流程测试失败: {e}")
        print(f"[FAIL] 测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("实际PT站点测试")
    print("="*60)
    print("\n注意: 此脚本需要真实的PT站点URL和Cookie")
    print("请在下方配置测试站点信息\n")
    
    # 配置测试站点（用户需要修改这些值）
    TEST_SITES = [
        {
            "name": "测试站点1",
            "url": "https://example-pt-site.com",  # 替换为真实站点URL
            "cookie": None,  # 替换为真实Cookie（可选）
            "page_url": None  # 种子列表页面URL（可选）
        },
        # 可以添加更多测试站点
    ]
    
    # 如果没有配置测试站点，显示提示
    if not TEST_SITES or TEST_SITES[0]["url"] == "https://example-pt-site.com":
        print("[INFO] 未配置测试站点")
        print("\n使用方法:")
        print("1. 编辑此脚本，修改 TEST_SITES 配置")
        print("2. 填入真实的PT站点URL和Cookie（可选）")
        print("3. 运行脚本进行测试")
        print("\n示例配置:")
        print('  TEST_SITES = [')
        print('      {')
        print('          "name": "我的PT站点",')
        print('          "url": "https://my-pt-site.com",')
        print('          "cookie": "your_cookie_here",')
        print('          "page_url": "https://my-pt-site.com/browse.php"')
        print('      }')
        print('  ]')
        return
    
    # 运行测试
    for test_site in TEST_SITES:
        if test_site["url"] == "https://example-pt-site.com":
            continue
        
        print(f"\n{'='*60}")
        print(f"测试站点: {test_site['name']}")
        print(f"{'='*60}")
        
        # 测试识别
        await test_site_identification_real(
            test_site["name"],
            test_site["url"],
            test_site.get("cookie")
        )
        
        # 测试验证
        await test_site_verification_real(
            test_site["url"],
            test_site.get("cookie")
        )
        
        # 测试解析
        await test_site_parsing_real(
            test_site["url"],
            test_site.get("cookie"),
            test_site.get("page_url")
        )
        
        # 完整工作流程
        await test_complete_workflow(
            test_site["name"],
            test_site["url"],
            test_site.get("cookie"),
            test_site.get("page_url")
        )
    
    print("\n" + "="*60)
    print("[OK] 所有测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

