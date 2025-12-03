# SITE-MANAGER-1 部署检查清单

## 概述

本文档提供 SITE-MANAGER-1 生产环境部署的完整检查清单，包括数据库、API服务、前端集成和系统集成验证。

---

## 🗄️ 数据库部署检查

### 1. 数据库迁移
- [ ] **运行迁移脚本**
  ```bash
  cd backend
  python migrate_add_site_manager_fields.py
  ```
  
- [ ] **验证表结构**
  ```sql
  -- 检查新表是否存在
  .tables site_stats site_access_configs site_categories site_health_checks
  
  -- 检查sites表新字段
  PRAGMA table_info(sites);
  -- 应包含: key, domain, category, icon_url, priority, tags
  ```

- [ ] **验证数据完整性**
  ```python
  # 运行数据验证脚本
  python test_site_manager_integration.py
  ```

- [ ] **创建数据库备份**
  ```bash
  # SQLite
  cp vabhub.db vabhub.db.backup.$(date +%Y%m%d)
  
  # MySQL/PostgreSQL
  mysqldump -u username -p vabhub > vabhub_backup_$(date +%Y%m%d).sql
  ```

### 2. 性能优化
- [ ] **创建索引**
  ```sql
  -- 站点查询索引
  CREATE INDEX idx_sites_enabled ON sites(is_active);
  CREATE INDEX idx_sites_category ON sites(category);
  CREATE INDEX idx_sites_priority ON sites(priority DESC);
  CREATE INDEX idx_sites_key ON sites(key);
  CREATE INDEX idx_sites_domain ON sites(domain);
  
  -- 统计表索引
  CREATE INDEX idx_site_stats_health ON site_stats(health_status);
  CREATE INDEX idx_site_stats_site_id ON site_stats(site_id);
  ```

- [ ] **设置数据库连接池**
  ```python
  # 检查 database.py 配置
  engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
  )
  ```

---

## 🚀 API 服务部署检查

### 1. FastAPI 应用配置
- [ ] **验证应用启动**
  ```bash
  # 测试启动
  python -m uvicorn main:app --host 0.0.0.0 --port 8000
  
  # 检查健康状态
  curl http://localhost:8000/health
  ```

- [ ] **验证API路由注册**
  ```bash
  # 检查API文档
  curl http://localhost:8000/docs | grep "sites"
  
  # 验证关键端点
  curl http://localhost:8000/api/sites -H "Authorization: Bearer $TOKEN"
  ```

- [ ] **环境变量配置**
  ```bash
  # 检查必需环境变量
  echo $DATABASE_URL
  echo $SECRET_KEY
  echo $CORS_ORIGINS
  ```

### 2. 依赖项检查
- [ ] **Python 包版本**
  ```bash
  pip freeze | grep -E "(fastapi|sqlalchemy|pydantic)"
  
  # 关键版本要求
  # fastapi>=0.104.0
  # sqlalchemy>=2.0.0
  # pydantic>=2.0.0
  ```

- [ ] **系统依赖**
  ```bash
  # 检查 SQLite 版本（如果使用）
  sqlite3 --version
  
  # 检查 OpenSSL 版本（HTTPS支持）
  openssl version
  ```

### 3. 安全配置
- [ ] **HTTPS 配置**
  ```bash
  # 测试 HTTPS 访问
  curl -k https://your-domain.com/api/sites
  
  # 检查证书有效期
  openssl s_client -connect your-domain.com:443 | openssl x509 -noout -dates
  ```

- [ ] **认证中间件**
  ```bash
  # 测试未授权访问
  curl http://localhost:8000/api/sites
  # 应返回 401 Unauthorized
  ```

---

## 🌐 前端集成检查

### 1. API 客户端配置
- [ ] **TypeScript 类型定义**
  ```bash
  # 检查类型文件
  ls frontend/src/types/siteManager.ts
  
  # 验证类型编译
  cd frontend && npm run type-check
  ```

- [ ] **API 客户端配置**
  ```typescript
  // 检查 API 基础URL配置
  const API_BASE_URL = process.env.VUE_APP_API_URL || '/api';
  
  // 验证请求拦截器
  axios.interceptors.request.use(config => {
    config.headers.Authorization = `Bearer ${token}`;
    return config;
  });
  ```

### 2. 组件集成
- [ ] **路由配置**
  ```typescript
  // 检查路由注册
  {
    path: '/site-manager',
    name: 'SiteManager',
    component: () => import('@/pages/SiteManager.vue'),
    meta: { requiresAuth: true, title: '站点管理' }
  }
  ```

- [ ] **导航菜单**
  ```vue
  <!-- 检查侧边栏菜单项 -->
  <v-list-item
    prepend-icon="mdi-server"
    title="站点管理"
    :to="{ name: 'SiteManager' }"
  />
  ```

### 3. 构建验证
- [ ] **前端构建**
  ```bash
  cd frontend
  npm run build
  
  # 检查构建产物
  ls dist/
  ```

- [ ] **静态资源优化**
  ```bash
  # 检查资源大小
  du -sh dist/js/
  du -sh dist/css/
  
  # 验证 Gzip 压缩
  curl -H "Accept-Encoding: gzip" http://localhost:3000/js/app.js -I
  ```

---

## 🔗 系统集成检查

### 1. CookieCloud 集成
- [ ] **钩子系统注册**
  ```python
  # 检查钩子注册
  from app.modules.site_manager.integration_hooks import integration_hooks
  print(len(integration_hooks._hooks[IntegrationEvent.SITE_UPDATED]))
  ```

- [ ] **同步功能测试**
  ```bash
  # 创建测试站点验证同步
  curl -X POST http://localhost:8000/api/sites \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name":"test","url":"https://test.com"}'
  
  # 检查日志确认CookieCloud触发
  tail -f logs/app.log | grep "CookieCloud"
  ```

### 2. External Indexer 集成
- [ ] **健康站点获取**
  ```python
  # 测试服务方法
  service = SiteManagerService(db)
  sites = await service.get_active_healthy_sites()
  print(f"可用健康站点: {len(sites)}")
  ```

- [ ] **过滤逻辑验证**
  ```bash
  # 创建不同状态的测试站点
  # 验证过滤条件: enabled=True AND health_status!='ERROR'
  ```

### 3. Local Intel 集成
- [ ] **健康状态同步**
  ```bash
  # 触发健康检查
  curl -X POST http://localhost:8000/api/sites/1/health-check \
    -H "Authorization: Bearer $TOKEN"
  
  # 检查Local Intel同步日志
  tail -f logs/app.log | grep "Local Intel"
  ```

---

## 📊 性能和监控检查

### 1. 性能基准测试
- [ ] **API 响应时间**
  ```bash
  # 站点列表查询（< 200ms）
  time curl -s http://localhost:8000/api/sites > /dev/null
  
  # 站点详情查询（< 100ms）
  time curl -s http://localhost:8000/api/sites/1 > /dev/null
  
  # 健康检查（< 5000ms）
  time curl -s -X POST http://localhost:8000/api/sites/1/health-check > /dev/null
  ```

- [ ] **数据库查询优化**
  ```sql
  -- 检查慢查询
  EXPLAIN QUERY PLAN SELECT * FROM sites WHERE is_active = 1 ORDER BY priority DESC;
  
  -- 验证索引使用
  EXPLAIN QUERY PLAN SELECT * FROM site_stats WHERE health_status = 'ERROR';
  ```

### 2. 监控配置
- [ ] **日志配置**
  ```bash
  # 检查日志级别
  grep "log_level" config/app.py
  
  # 验证日志轮转
  ls -la logs/app.log*
  ```

- [ ] **健康检查端点**
  ```bash
  # 系统健康检查
  curl http://localhost:8000/health
  
  # 数据库连接检查
  curl http://localhost:8000/health/db
  ```

---

## 🧪 集成测试场景

### 场景1：完整站点管理流程
```bash
#!/bin/bash
# 完整流程测试脚本

TOKEN="your-test-token"
API_BASE="http://localhost:8000/api"

# 1. 创建站点
echo "1. 创建站点..."
SITE_ID=$(curl -s -X POST $API_BASE/sites \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"测试站点","url":"https://test.com","category":"PT"}' | \
  jq -r '.data.id')

echo "创建的站点ID: $SITE_ID"

# 2. 更新站点
echo "2. 更新站点..."
curl -s -X PUT $API_BASE/sites/$SITE_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"priority":2}' | jq -r '.data.name'

# 3. 健康检查
echo "3. 执行健康检查..."
curl -s -X POST $API_BASE/sites/$SITE_ID/health-check \
  -H "Authorization: Bearer $TOKEN" | jq -r '.data.status'

# 4. 导出配置
echo "4. 导出配置..."
curl -s -X POST $API_BASE/sites/export \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"site_ids":[$SITE_ID]}' | jq -r '.data | length'

# 5. 删除站点
echo "5. 删除站点..."
curl -s -X DELETE $API_BASE/sites/$SITE_ID \
  -H "Authorization: Bearer $TOKEN" | jq -r '.data'

echo "完整流程测试完成"
```

### 场景2：并发压力测试
```bash
#!/bin/bash
# 并发测试脚本

TOKEN="your-test-token"
API_BASE="http://localhost:8000/api"

# 并发创建100个站点
echo "并发创建测试..."
for i in {1..100}; do
  curl -s -X POST $API_BASE/sites \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"name\":\"测试站点$i\",\"url\":\"https://test$i.com\",\"category\":\"PT\"}" \
    > /dev/null &
done

wait
echo "并发创建完成"

# 并发健康检查
echo "并发健康检查..."
for i in {1..50}; do
  curl -s -X POST $API_BASE/sites/$i/health-check \
    -H "Authorization: Bearer $TOKEN" \
    > /dev/null &
done

wait
echo "并发健康检查完成"
```

### 场景3：数据一致性测试
```python
#!/usr/bin/env python3
"""数据一致性测试脚本"""

import asyncio
import aiohttp
import json

async def consistency_test():
    """测试并发操作的数据一致性"""
    
    async with aiohttp.ClientSession() as session:
        # 并发更新同一个站点
        tasks = []
        for i in range(10):
            task = update_site(session, 1, f"更新名称{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 验证最终状态
        final_site = await get_site(session, 1)
        print(f"最终站点名称: {final_site['name']}")

async def update_site(session, site_id, name):
    """更新站点"""
    url = f"http://localhost:8000/api/sites/{site_id}"
    data = {"name": name}
    
    async with session.put(url, json=data) as response:
        return await response.json()

async def get_site(session, site_id):
    """获取站点"""
    url = f"http://localhost:8000/api/sites/{site_id}"
    
    async with session.get(url) as response:
        return await response.json()

if __name__ == "__main__":
    asyncio.run(consistency_test())
```

---

## 🔧 故障排除指南

### 常见问题及解决方案

#### 1. 数据库迁移失败
**症状**: 迁移脚本执行报错
**排查步骤**:
```bash
# 1. 检查数据库文件权限
ls -la vabhub.db

# 2. 检查磁盘空间
df -h

# 3. 手动执行SQL验证
sqlite3 vabhub.db "SELECT COUNT(*) FROM sites;"
```

**解决方案**:
```bash
# 备份现有数据库
cp vabhub.db vabhub.db.emergency_backup

# 重新运行迁移
python migrate_add_site_manager_fields.py --force
```

#### 2. API 服务启动失败
**症状**: FastAPI 应用无法启动
**排查步骤**:
```bash
# 1. 检查Python环境
python --version
pip list | grep fastapi

# 2. 检查端口占用
netstat -tulpn | grep 8000

# 3. 检查环境变量
env | grep -E "(DATABASE|SECRET|CORS)"
```

**解决方案**:
```bash
# 重新安装依赖
pip install -r requirements.txt

# 使用不同端口
uvicorn main:app --host 0.0.0.0 --port 8001
```

#### 3. 前端集成异常
**症状**: 前端页面显示错误或API调用失败
**排查步骤**:
```bash
# 1. 检查浏览器控制台错误
# F12 -> Console

# 2. 检查网络请求
# F12 -> Network

# 3. 验证API响应
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/sites
```

**解决方案**:
```typescript
// 检查API基础URL配置
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-domain.com/api' 
  : 'http://localhost:8000/api';
```

#### 4. 集成钩子不触发
**症状**: CookieCloud/Local Intel集成不工作
**排查步骤**:
```python
# 检查钩子注册
from app.modules.site_manager.integration_hooks import integration_hooks
print(integration_hooks._hooks)

# 手动触发测试
await integration_hooks.trigger_event(
    IntegrationEvent.SITE_UPDATED,
    site=test_site
)
```

**解决方案**:
```python
# 重新注册钩子
from app.modules.site_manager.integration_hooks import register_default_hooks
register_default_hooks()
```

---

## ⚠️ 部署前限制确认

### 关键限制检查
- [ ] **确认CookieCloud集成仅为事件框架**（需要实际实现）
- [ ] **确认Local Intel集成仅为事件框架**（需要实际实现）
- [ ] **确认数据库约束已添加**（防止孤立记录）
- [ ] **确认生产环境错误处理已优化**

### 依赖团队确认
- [ ] CookieCloud团队确认集成实现计划
- [ ] Local Intel团队确认集成实现计划
- [ ] 运维团队确认监控和告警配置

## 📋 部署前最终检查清单

### 环境检查
- [ ] 服务器资源充足（CPU > 2核，内存 > 4GB）
- [ ] 磁盘空间 > 10GB 可用
- [ ] 网络连接正常
- [ ] 防火墙配置正确（端口 80, 443, 8000）

### 服务检查
- [ ] 数据库服务运行正常
- [ ] FastAPI 应用启动成功
- [ ] 前端构建无错误
- [ ] 反向代理配置正确

### 功能检查
- [ ] 用户认证正常
- [ ] 站点CRUD操作正常
- [ ] 健康检查功能正常
- [ ] 导入导出功能正常
- [ ] 集成钩子触发正常

### 性能检查
- [ ] API响应时间 < 200ms
- [ ] 数据库查询优化
- [ ] 静态资源压缩
- [ ] 缓存策略配置

### 安全检查
- [ ] HTTPS证书有效
- [ ] 认证中间件启用
- [ ] 敏感信息加密
- [ ] 日志不包含密码

---

## 📞 技术支持

### 紧急联系
- **开发团队**: dev-team@company.com
- **运维团队**: ops-team@company.com
- **24小时值班**: +86-xxx-xxxx-xxxx

### 文档资源
- [API契约文档](./SITE_MANAGER_API_CONTRACT.md)
- [迁移指南](./SITE_MANAGER_MIGRATION_GUIDE.md)
- [故障排除日志](../logs/)

### 监控工具
- **应用监控**: http://monitor.company.com
- **数据库监控**: http://db-monitor.company.com
- **日志分析**: http://log-center.company.com

---

**部署完成后，请确认以下指标**：
- ✅ 所有检查项通过
- ✅ 性能指标达标
- ✅ 监控告警正常
- ✅ 备份策略就绪
- ✅ 回滚方案验证

🎉 **恭喜！SITE-MANAGER-1 部署成功！**
