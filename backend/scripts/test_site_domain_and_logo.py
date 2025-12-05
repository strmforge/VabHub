"""
测试站点域名管理和Logo资源系统
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal, init_db
from app.models.site import Site
from app.modules.site_domain.service import SiteDomainService
from app.modules.site_icon.service import SiteIconService
from app.modules.site_icon.resource_loader import SiteLogoResourceLoader
from loguru import logger


async def test_site_domain_management():
    """测试站点域名管理功能"""
    print("\n" + "="*60)
    print("测试1: 站点域名管理功能")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # 1. 创建测试站点
        test_site = Site(
            name="测试站点",
            url="https://test.example.com",
            is_active=True
        )
        db.add(test_site)
        await db.commit()
        await db.refresh(test_site)
        
        print(f"[OK] 创建测试站点: {test_site.name} (ID: {test_site.id})")
        
        # 2. 测试域名服务
        domain_service = SiteDomainService(db)
        
        # 2.1 获取或创建域名配置
        config = await domain_service.get_or_create_domain_config(test_site.id)
        print(f"[OK] 获取域名配置: {config.get_active_domains()}")
        
        # 2.2 添加新域名
        await domain_service.add_domain(test_site.id, "https://test2.example.com", is_active=True)
        config = await domain_service.get_domain_config(test_site.id)
        print(f"[OK] 添加域名后: {config.get_active_domains()}")
        
        # 2.3 切换域名
        await domain_service.switch_domain(test_site.id, "https://test2.example.com", "测试切换")
        config = await domain_service.get_domain_config(test_site.id)
        print(f"[OK] 切换域名后当前域名: {config.get_current_domain()}")
        
        # 2.4 获取最佳域名
        best_domain = await domain_service.get_best_domain(test_site.id)
        print(f"[OK] 最佳域名: {best_domain}")
        
        # 2.5 获取域名信息
        domain_info = await domain_service.get_domain_info(test_site.id)
        print(f"[OK] 域名信息: {domain_info}")
        
        # 清理
        await db.delete(test_site)
        await db.commit()
        print("[OK] 清理测试站点")


async def test_logo_resource_loader():
    """测试Logo资源加载器"""
    print("\n" + "="*60)
    print("测试2: Logo资源加载器")
    print("="*60)
    
    loader = SiteLogoResourceLoader()
    
    # 1. 测试获取Logo（不存在的）
    logo = loader.get_logo("999")
    print(f"[OK] 获取不存在的Logo: {logo is None}")
    
    # 2. 测试列出所有Logo
    logos = loader.list_logos()
    print(f"[OK] 列出所有Logo: {len(logos)} 个")
    
    # 3. 测试获取Logo路径
    logo_path = loader.get_logo_path("999")
    print(f"[OK] 获取Logo路径: {logo_path}")
    
    # 4. 测试资源目录
    print(f"[OK] 资源目录: {loader.resources_dir}")
    print(f"[OK] 资源目录存在: {loader.resources_dir.exists()}")


async def test_site_icon_service():
    """测试站点图标服务"""
    print("\n" + "="*60)
    print("测试3: 站点图标服务")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # 1. 创建测试站点
        test_site = Site(
            name="测试站点图标",
            url="https://test.example.com",
            is_active=True
        )
        db.add(test_site)
        await db.commit()
        await db.refresh(test_site)
        
        print(f"[OK] 创建测试站点: {test_site.name} (ID: {test_site.id})")
        
        # 2. 测试图标服务
        icon_service = SiteIconService(db)
        
        # 2.1 获取站点图标（应该生成SVG渐变）
        icon_data = await icon_service.get_site_icon(test_site, size=64)
        print(f"[OK] 获取站点图标类型: {icon_data.get('type')}")
        print(f"[OK] SVG存在: {icon_data.get('svg') is not None}")
        
        if icon_data.get('svg'):
            svg_preview = icon_data['svg'][:100] + "..." if len(icon_data['svg']) > 100 else icon_data['svg']
            print(f"[OK] SVG预览: {svg_preview}")
        
        # 2.2 测试刷新图标
        refreshed_icon = await icon_service.refresh_icon(test_site)
        print(f"[OK] 刷新图标类型: {refreshed_icon.get('type')}")
        
        # 清理
        await db.delete(test_site)
        await db.commit()
        print("[OK] 清理测试站点")


async def test_svg_gradient():
    """测试SVG渐变生成"""
    print("\n" + "="*60)
    print("测试4: SVG渐变生成")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        icon_service = SiteIconService(db)
        
        # 测试不同站点名称的渐变
        test_names = ["测试站点A", "TestSiteB", "示例站点"]
        
        for name in test_names:
            svg_data = icon_service._generate_svg_icon(name, size=64, site_id="123")
            svg = svg_data.get('svg', '')
            
            # 检查是否包含渐变
            has_gradient = 'linearGradient' in svg and 'hsl(' in svg
            print(f"[OK] {name}: 包含渐变 = {has_gradient}")
            
            if has_gradient:
                # 提取hue值
                import re
                hues = re.findall(r'hsl\((\d+)', svg)
                if hues:
                    print(f"   Hue值: {hues}")


async def test_integration():
    """集成测试"""
    print("\n" + "="*60)
    print("测试5: 集成测试（域名+图标）")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # 1. 创建测试站点
        test_site = Site(
            name="集成测试站点",
            url="https://integration.test.com",
            is_active=True
        )
        db.add(test_site)
        await db.commit()
        await db.refresh(test_site)
        
        print(f"[OK] 创建测试站点: {test_site.name} (ID: {test_site.id})")
        
        # 2. 配置域名
        domain_service = SiteDomainService(db)
        await domain_service.add_domain(test_site.id, "https://integration2.test.com", is_active=True)
        
        # 3. 获取最佳域名（应该使用域名配置）
        best_domain = await domain_service.get_best_domain(test_site.id)
        print(f"[OK] 最佳域名: {best_domain}")
        
        # 4. 获取图标（应该使用域名配置中的域名尝试favicon）
        icon_service = SiteIconService(db)
        icon_data = await icon_service.get_site_icon(test_site, size=64)
        print(f"[OK] 图标类型: {icon_data.get('type')}")
        
        # 清理
        await db.delete(test_site)
        await db.commit()
        print("[OK] 清理测试站点")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("站点域名管理和Logo资源系统测试")
    print("="*60)
    
    try:
        # 初始化数据库
        await init_db()
        print("[OK] 数据库初始化完成")
        
        # 运行测试
        await test_site_domain_management()
        await test_logo_resource_loader()
        await test_site_icon_service()
        await test_svg_gradient()
        await test_integration()
        
        print("\n" + "="*60)
        print("[OK] 所有测试完成")
        print("="*60)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("[FAIL] 测试失败")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

