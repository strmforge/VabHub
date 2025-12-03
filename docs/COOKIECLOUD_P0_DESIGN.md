# COOKIECLOUD-1 P0 设计文档

## 项目概述

**目标**: 实现 浏览器 → CookieCloud → VabHub → PT站点 的一条链路  
**范围**: 只读式同步（Pull），全局配置+手动触发+定时Runner  
**集成**: 与SITE-MANAGER-1打通，支持站点标记"CookieCloud驱动"状态

---

## 📋 P0 调研结果

### 1. 现有基础设施巡检

#### ✅ 已发现的核心组件

**CookieCloudClient** (`app/core/cookiecloud.py`)
- 完整的HTTP客户端和基础解密框架
- **问题**: 解密算法错误（使用PBKDF2而非官方md5算法）
- **需要修复**: 第34行 `_derive_key()` 方法

**Site模型扩展** (`app/models/site.py`)
- 已有CookieCloud相关字段：
  ```python
  cookiecloud_uuid = Column(String(100), nullable=True)
  cookiecloud_password = Column(String(100), nullable=True)  
  cookiecloud_server = Column(String(500), nullable=True)
  ```
- 现有 `cookie` 字段可用于存储Cookie数据

**集成钩子系统** (`app/modules/site_manager/integration_hooks.py`)
- 已预留 `cookiecloud_sync_hook()` 函数（第56-74行）
- 已注册到 `SITE_UPDATED` 事件
- **当前状态**: 仅为占位符，需要实现实际逻辑

#### ❌ 缺失的基础设施

- **全局配置表**: 需要创建 `CookieCloudSettings` 模型
- **Cookie来源标记**: 需要在Site模型添加 `cookie_source` 枚举
- **同步服务**: 需要创建 `CookieCloudSyncService`

### 2. CookieCloud官方API约束

#### API接口规范
```http
# 下载接口（本阶段核心）
GET /get/:uuid
# 或
POST /get/:uuid

# 响应格式
{
  "encrypted": "<base64_encrypted_data>"
}
```

#### 官方解密算法
```javascript
// 官方标准算法
function cookie_decrypt(uuid, encrypted, password) {
    const CryptoJS = require('crypto-js');
    const the_key = CryptoJS.MD5(uuid+'-'+password).toString().substring(0,16);
    const decrypted = CryptoJS.AES.decrypt(encrypted, the_key).toString(CryptoJS.enc.Utf8);
    const parsed = JSON.parse(decrypted);
    return parsed; // { cookie_data, local_storage_data }
}
```

**关键差异**: 现有实现使用PBKDF2，官方要求MD5(uuid-password)\[:16\]

---

## 🏗️ 技术架构设计

### 数据流架构
```
CookieCloudSettings (全局配置)
        ↓
CookieCloudSyncService (同步逻辑)
        ↓
CookieCloudClient (HTTP请求+解密)
        ↓
Site.cookie更新 + cookie_source标记
        ↓
集成钩子系统触发通知
```

### 责任边界设计

#### 1. 配置管理层
- **CookieCloudSettings**: 全局配置存储
- **字段**: enabled, host, uuid, password, sync_interval_minutes, safe_host_whitelist
- **约束**: 永远只有一行记录（id=1）

#### 2. 同步服务层 
- **CookieCloudSyncService**: 核心同步逻辑
- **职责**: 
  - 读取全局配置
  - 调用CookieCloudClient获取数据
  - 按域名匹配站点
  - 更新Site.cookie和cookie_source
  - 记录同步状态和错误信息
#### 2. 同步服务层 ## 安全考虑

1. **密码存储**: **重要安全说明** - CookieCloud密码在数据库中以明文形式存储，这是为了与CookieCloud官方API的兼容性要求（需要原始密码进行MD5哈希）。虽然这在当前使用场景下是可以接受的，但需要注意：
   - 数据库访问权限必须严格控制
   - 备份数据应进行加密处理
   - 定期审计数据库访问日志
   - 在生产环境中应考虑额外的数据库加密层

2. **网络安全**: CookieCloud API调用使用HTTPS，确保传输安全。

3. **域名白名单**: 通过安全域名白名单限制Cookie同步范围，防止敏感Cookie泄露到不相关站点。

4. **速率限制**: 建议在API层添加同步频率限制，防止恶意用户频繁触发同步操作。

#### 3. 客户端层
- **CookieCloudClient**: HTTP请求和标准解密
- **修复**: 解密算法改为官方标准
- **复用**: 现有的域名匹配逻辑（第129行 `sync_to_sites()`）

#### 4. 集成层
- **集成钩子**: 复用现有 `cookiecloud_sync_hook`
- **触发时机**: 站点更新、手动同步、定时任务
- **通知机制**: 更新SiteStats健康状态

### 存储策略

#### 全局配置存储
```sql
CREATE TABLE cookiecloud_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    enabled BOOLEAN DEFAULT FALSE NOT NULL,
    host VARCHAR(255),  -- https://cookiecloud.example.com
    uuid VARCHAR(128),
    password VARCHAR(128),  -- 明文存储，日志脱敏
    sync_interval_minutes INTEGER DEFAULT 60,
    safe_host_whitelist TEXT,  -- JSON数组
    last_sync_at DATETIME,
    last_status VARCHAR(32),  -- SUCCESS/ERROR/PARTIAL
    last_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 站点Cookie存储
```sql
-- 复用现有sites表，添加新字段
ALTER TABLE sites ADD COLUMN cookie_source VARCHAR(32) DEFAULT 'MANUAL';
ALTER TABLE sites ADD COLUMN last_cookiecloud_sync_at DATETIME;
```

**存储决策**: 复用 `Site.cookie` 字段，避免创建新表，简化数据模型。

---

## 🔧 关键技术决策

### 1. 解密算法修复
**位置**: `app/core/cookiecloud.py` 第34行  
**当前**: `hashlib.pbkdf2_hmac('sha1', password.encode(), b'saltysalt', 1003, 16)`  
**修复为**: `hashlib.md5(f"{uuid}-{password}".encode()).hexdigest()[:16].encode()`

### 2. 数据模型扩展
**策略**: 最小化变更，复用现有结构
- 新增 `CookieCloudSettings` 全局配置表
- 扩展 `Site` 模型添加 `cookie_source` 和 `last_cookiecloud_sync_at`
- 保持现有 `cookie` 字段不变

### 3. 集成方式选择
**复用现有钩子**: 在 `cookiecloud_sync_hook` 中实现实际逻辑  
**避免循环依赖**: 通过服务层调用，不在钩子中直接操作数据库

### 4. 性能优化考虑
**单次HTTP请求**: `sync_all_sites()` 只调用一次CookieCloud API  
**内存缓存**: 解密结果在内存中缓存，避免重复解密  
**域名匹配优化**: 复用现有的匹配算法

---

## 📊 实施计划

### P1: 数据模型 & 迁移
- [ ] 创建 `CookieCloudSettings` 模型和迁移脚本
- [ ] 扩展 `Site` 模型添加 `cookie_source` 枚举字段
- [ ] 添加索引优化查询性能

### P2: CookieCloud Client & 解密
- [ ] 修复 `CookieCloudClient` 解密算法
- [ ] 添加标准错误处理
- [ ] 创建数据结构定义

### P3: Sync Service & 集成
- [ ] 实现 `CookieCloudSyncService`
- [ ] 完善集成钩子逻辑
- [ ] 与SiteManager打通

### P4: API 设计
- [ ] 设置管理API
- [ ] 同步控制API
- [ ] 路由注册

### P5: 前端界面
- [ ] 设置页面UI
- [ ] 站点管理入口
- [ ] 状态显示

### P6: Runner & 文档
- [ ] 定时任务实现
- [ ] 测试场景
- [ ] 开发者文档

---

## ⚠️ 风险评估

### 技术风险
1. **解密算法兼容性**: 需要严格遵循官方标准
2. **数据一致性**: 多站点同步时的并发控制
3. **性能影响**: 大量站点时的同步效率

### 缓解策略
1. **充分测试**: 使用官方测试服务器验证解密算法
2. **事务控制**: 使用数据库事务保证数据一致性
3. **分批同步**: 实现分页和限流机制

---

## 🎯 成功标准

### 功能标准
- [ ] 成功从CookieCloud拉取并解密Cookie数据
- [ ] 按域名正确匹配到对应站点
- [ ] 手动和自动同步功能正常
- [ ] 前端配置界面友好易用

### 质量标准
- [ ] 解密算法与官方标准100%兼容
- [ ] 错误处理覆盖所有异常场景
- [ ] 性能满足：100个站点同步 < 30秒
- [ ] 文档完整，便于维护

---

**设计总结**: 基于现有基础设施进行最小化改造，复用已有组件，确保与SITE-MANAGER-1的深度集成，实现稳定可靠的CookieCloud同步功能。
