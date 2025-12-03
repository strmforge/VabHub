# SITE-MANAGER-1 用户迁移指南

## 概述

本指南帮助现有 `site.py` 用户平滑迁移到新的 SITE-MANAGER-1 系统。新系统提供了更强大的站点管理功能，包括健康检查、访问配置、分类管理等。

---

## 迁移前后对比

### 旧版 site.py 使用方式

```python
# 旧版：直接操作数据库模型
from app.models.site import Site

# 创建站点
site = Site(
    name="高清家园",
    url="https://hdhome.org",
    cookie="cookie_string",
    is_active=True
)
session.add(site)
session.commit()

# 获取站点
sites = session.query(Site).filter(Site.is_active == True).all()

# 更新站点
site.name = "新名称"
session.commit()
```

### 新版 SiteManagerService 使用方式

```python
# 新版：使用服务层API
from app.modules.site_manager.service import SiteManagerService
from app.schemas.site_manager import SiteUpdatePayload

# 创建站点
service = SiteManagerService(db)
site = await service.create_site({
    "name": "高清家园",
    "url": "https://hdhome.org", 
    "key": "hdhome",
    "domain": "hdhome.org",
    "category": "PT",
    "enabled": True
})

# 获取站点列表
from app.schemas.site_manager import SiteListFilter
filters = SiteListFilter(enabled=True)
sites = await service.list_sites(filters)

# 更新站点
update_payload = SiteUpdatePayload(name="新名称")
updated_site = await service.update_site(site.id, update_payload)
```

---

## 分步迁移指南

### 第一步：数据模型迁移

#### 1.1 运行数据库迁移脚本
```bash
cd backend
python migrate_add_site_manager_fields.py
```

**迁移内容**：
- 为 `sites` 表添加新字段：`key`, `domain`, `category`, `icon_url`, `priority`, `tags`
- 创建新表：`site_stats`, `site_access_configs`, `site_categories`, `site_health_checks`
- 初始化默认站点分类

#### 1.2 验证数据迁移
```python
# 检查新字段是否存在
from app.models.site import Site
site = session.query(Site).first()
print(f"Key: {site.key}")
print(f"Domain: {site.domain}")
print(f"Category: {site.category}")
```

### 第二步：代码迁移

#### 2.1 替换直接数据库操作

**旧代码**：
```python
from app.models.site import Site
from sqlalchemy.orm import Session

def get_active_sites(db: Session):
    return db.query(Site).filter(Site.is_active == True).all()

def create_site(db: Session, name: str, url: str):
    site = Site(name=name, url=url, is_active=True)
    db.add(site)
    db.commit()
    return site
```

**新代码**：
```python
from app.modules.site_manager.service import SiteManagerService
from app.schemas.site_manager import SiteListFilter, SiteCreatePayload

async def get_active_sites(service: SiteManagerService):
    filters = SiteListFilter(enabled=True)
    return await service.list_sites(filters)

async def create_site(service: SiteManagerService, name: str, url: str):
    payload = SiteCreatePayload(
        name=name,
        url=url,
        key=name.lower().replace(' ', ''),
        domain=url.split('/')[2],
        category="PT",
        enabled=True
    )
    return await service.create_site(payload)
```

#### 2.2 迁移站点查询逻辑

**旧代码**：
```python
# 复杂查询
sites = db.query(Site).filter(
    Site.is_active == True,
    Site.name.like('%高清%')
).order_by(Site.created_at.desc()).all()
```

**新代码**：
```python
# 使用过滤器
filters = SiteListFilter(
    enabled=True,
    keyword="高清"
)
sites = await service.list_sites(filters)
```

#### 2.3 迁移CookieCloud集成

**旧代码**：
```python
# 直接调用CookieCloud服务
from app.modules.cookiecloud import sync_site

def update_site_with_cookiecloud(site_id: int):
    site = db.query(Site).get(site_id)
    result = sync_site(site.cookiecloud_uuid, site.cookiecloud_password)
    # 手动更新健康状态
    site.last_checkin = datetime.now()
    db.commit()
```

**新代码**：
```python
# 自动触发集成
from app.schemas.site_manager import SiteUpdatePayload

async def update_site_with_cookiecloud(service: SiteManagerService, site_id: int):
    # 更新站点会自动触发CookieCloud集成
    payload = SiteUpdatePayload(name="更新的站点名")
    updated_site = await service.update_site(site_id, payload)
    # CookieCloud同步和健康状态更新自动完成
    return updated_site
```

### 第三步：前端迁移

#### 3.1 API调用迁移

**旧代码**：
```javascript
// 直接调用旧API
const response = await fetch('/api/site/list', {
  method: 'GET',
  headers: { 'Authorization': `Bearer ${token}` }
});
const sites = await response.json();
```

**新代码**：
```javascript
// 使用新的Site Manager API
const response = await fetch('/api/sites?enabled=true', {
  method: 'GET',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const result = await response.json();
const sites = result.data;
```

#### 3.2 数据结构迁移

**旧数据结构**：
```javascript
{
  "id": 1,
  "name": "站点名称",
  "url": "https://example.com",
  "is_active": true
}
```

**新数据结构**：
```javascript
{
  "id": 1,
  "key": "site_key",
  "domain": "example.com",
  "category": "PT",
  "name": "站点名称", 
  "url": "https://example.com",
  "enabled": true,
  "stats": {
    "health_status": "OK",
    "last_seen_at": "2024-01-01T00:00:00Z"
  },
  "access_config": {
    "rss_url": "https://example.com/rss",
    "use_proxy": false
  }
}
```

---

## 常见迁移场景

### 场景1：现有站点列表页面

**迁移前**：
```python
@router.get("/sites")
async def get_sites():
    sites = db.query(Site).filter(Site.is_active == True).all()
    return [{"id": s.id, "name": s.name, "url": s.url} for s in sites]
```

**迁移后**：
```python
@router.get("/sites")
async def get_sites():
    service = SiteManagerService(db)
    filters = SiteListFilter(enabled=True)
    sites = await service.list_sites(filters)
    return {
        "success": True,
        "data": [site.dict() for site in sites]
    }
```

### 场景2：站点健康检查

**迁移前**：
```python
def check_site_health(site_id: int):
    site = db.query(Site).get(site_id)
    try:
        response = requests.get(site.url, timeout=10)
        return response.status_code == 200
    except:
        return False
```

**迁移后**：
```python
async def check_site_health(site_id: int):
    service = SiteManagerService(db)
    result = await service.check_site_health(site_id)
    return result.status == "OK"
```

### 场景3：站点配置导入

**迁移前**：
```python
def import_sites(sites_data):
    for data in sites_data:
        site = Site(name=data["name"], url=data["url"])
        db.add(site)
    db.commit()
```

**迁移后**：
```python
async def import_sites(sites_data):
    service = SiteManagerService(db)
    import_items = [SiteImportItem(**data) for data in sites_data]
    result = await service.import_sites(import_items)
    return result
```

---

## 数据迁移脚本

### 自动迁移脚本示例

```python
#!/usr/bin/env python3
"""
站点数据自动迁移脚本
将现有站点数据迁移到新的Site Manager格式
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.modules.site_manager.service import SiteManagerService
from app.models.site import Site
from sqlalchemy import select, text
from loguru import logger

async def migrate_existing_sites():
    """迁移现有站点数据"""
    
    async with AsyncSessionLocal() as db:
        service = SiteManagerService(db)
        
        # 获取所有现有站点
        result = await db.execute(select(Site))
        sites = result.scalars().all()
        
        logger.info(f"开始迁移 {len(sites)} 个站点...")
        
        migrated_count = 0
        for site in sites:
            try:
                # 生成key和domain（如果为空）
                if not site.key:
                    site.key = site.name.lower().replace(' ', '').replace('-', '')
                
                if not site.domain:
                    site.domain = site.url.replace('http://', '').replace('https://', '').split('/')[0]
                
                if not site.category:
                    site.category = 'PT'  # 默认分类
                
                # 创建SiteStats记录（如果不存在）
                from app.models.site import SiteStats
                stats_result = await db.execute(
                    select(SiteStats).where(SiteStats.site_id == site.id)
                )
                if not stats_result.scalar_one_or_none():
                    stats = SiteStats(
                        site_id=site.id,
                        health_status='OK'
                    )
                    db.add(stats)
                
                # 创建SiteAccessConfig记录（如果不存在）
                from app.models.site import SiteAccessConfig
                config_result = await db.execute(
                    select(SiteAccessConfig).where(SiteAccessConfig.site_id == site.id)
                )
                if not config_result.scalar_one_or_none():
                    config = SiteAccessConfig(site_id=site.id)
                    db.add(config)
                
                migrated_count += 1
                logger.info(f"迁移站点: {site.name} -> key: {site.key}, domain: {site.domain}")
                
            except Exception as e:
                logger.error(f"迁移站点 {site.name} 失败: {e}")
        
        await db.commit()
        logger.info(f"✅ 迁移完成: {migrated_count}/{len(sites)} 个站点")

if __name__ == "__main__":
    asyncio.run(migrate_existing_sites())
```

---

## 回滚方案

### 数据库回滚

如果迁移出现问题，可以执行以下回滚操作：

```sql
-- 备份现有数据（迁移前执行）
CREATE TABLE sites_backup AS SELECT * FROM sites;

-- 回滚站点表结构（如果需要）
-- 注意：这会丢失新功能的数据
DROP TABLE site_stats;
DROP TABLE site_access_configs;
DROP TABLE site_categories;
DROP TABLE site_health_checks;

-- 恢复原始站点数据
DELETE FROM sites;
INSERT INTO sites SELECT * FROM sites_backup;
```

### 代码回滚

保留旧的 `site.py` 文件作为备份：

```bash
# 备份旧文件
cp app/api/site.py app/api/site.py.backup

# 如果需要回滚，恢复旧文件
cp app/api/site.py.backup app/api/site.py
```

---

## 验证清单

迁移完成后，请验证以下功能：

### 后端验证
- [ ] 数据库迁移脚本执行成功
- [ ] 所有现有站点数据完整保留
- [ ] 新字段和表正确创建
- [ ] SiteManagerService 正常工作
- [ ] API 端点响应正确

### 前端验证
- [ ] 站点列表页面正常显示
- [ ] 站点详情页面数据完整
- [ ] 健康检查功能正常
- [ ] 导入导出功能正常

### 集成验证
- [ ] CookieCloud 集成正常触发
- [ ] External Indexer 可以获取健康站点
- [ ] Local Intel 状态同步正常

---

## 常见问题

### Q1: 迁移后现有站点没有分类？
**A**: 运行数据迁移脚本会为现有站点设置默认分类 "PT"。

### Q2: 健康检查历史数据丢失？
**A**: 新系统会重新开始记录健康检查历史，旧数据不会迁移。

### Q3: CookieCloud 配置需要重新设置？
**A**: 不需要，现有的 CookieCloud 配置会保留，但需要重新验证连接。

### Q4: 前端页面显示异常？
**A**: 检查前端代码是否使用了新的 API 端点和数据结构。

### Q5: 性能问题？
**A**: 新系统增加了更多功能，可能需要优化数据库查询和缓存策略。

---

## 技术支持

如果在迁移过程中遇到问题，请：

1. 检查日志文件：`logs/site_manager.log`
2. 运行诊断脚本：`python test_site_manager_integration.py`
3. 联系技术支持团队

---

## 版本兼容性

| 旧版本 | 新版本 | 兼容性 | 备注 |
|--------|--------|--------|------|
| v1.x | v2.0 | 部分兼容 | 需要数据迁移 |
| v2.0+ | v2.0+ | 完全兼容 | 无需迁移 |

---

**迁移完成后，您将获得以下新功能**：
- 🏥 自动健康检查和状态监控
- 🔧 灵活的访问配置管理  
- 📊 详细的站点统计和分析
- 🏷️ 站点分类和标签管理
- 📤 站点配置导入导出
- 🔗 与其他模块的深度集成
