# SITE-MANAGER-1 P0 现状巡检与方案设计

## 现有站点信息分布情况

### 1. 核心站点模型 (已存在)
**文件**: `app/models/site.py`
```python
class Site(Base):
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    cookie = Column(Text, nullable=True)
    cookiecloud_uuid = Column(String(100), nullable=True)
    cookiecloud_password = Column(String(100), nullable=True)
    cookiecloud_server = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    user_data = Column(JSON, nullable=True)
    last_checkin = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2. 站点防护配置 (已存在)
**文件**: `app/models/intel_local.py`
```python
class SiteGuardProfile(Base):
    __tablename__ = "site_guard_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    site = Column(String(100), nullable=False, unique=True, index=True)
    last_block_start = Column(DateTime, nullable=True)
    last_block_end = Column(DateTime, nullable=True)
    last_block_cause = Column(String(255), nullable=True)
    safe_scan_minutes = Column(Integer, default=10)
    safe_pages_per_hour = Column(Integer, default=200)
```

### 3. 站点API (已存在)
**文件**: `app/api/site.py`
- 完整的CRUD操作：创建、列表、详情、更新、删除
- CookieCloud同步功能
- 站点连接测试
- 批量签到
- 站点图标管理

### 4. 站点标识系统
**现有标识方式**:
- `site.key`: 内部标识 (如 "hdhome", "pttime") - **需要添加**
- `site.url`: 完整URL (如 "https://hdhome.org")
- `site.name`: 显示名称
- `site_guard_profiles.site`: 站点字符串标识

## 数据源分析

### 静态配置信息
- **位置**: `sites` 表
- **内容**: 站点基本信息、访问配置、Cookie配置
- **特点**: 用户手动配置，相对稳定

### 运行时统计信息
- **位置**: 
  - `sites.user_data` (JSON格式存储上传下载量等)
  - `site_guard_profiles` (风控状态、扫描历史)
  - `hr_cases` (HR案例记录)
- **内容**: 动态变化的统计数据
- **特点**: 系统自动更新，需要实时查询

### Local Intel 相关
- **位置**: `app/models/intel_local.py`
- **内容**: HR状态、站点防护配置、站内信事件
- **标识**: 使用字符串形式的站点名称

### External Indexer 相关
- **位置**: `app/api/ext_indexer.py`
- **内容**: 外部索引器配置和搜索
- **标识**: 通常使用域名或站点key

## 扩展方案设计

### 1. 数据模型扩展策略
**原则**: 复用现有Site模型，补充必要字段

**新增字段**:
```python
# Site模型新增字段
key = Column(String(50), unique=True, index=True)  # 内部标识
domain = Column(String(255))                       # 主域名
category = Column(String(50))                      # 类型：PT/BT/小说/漫画/音乐
icon_url = Column(String(500), nullable=True)     # 站点图标URL
enabled = Column(Boolean, default=True)           # 启用状态 (复用is_active)
priority = Column(Integer, default=0)             # 优先级
tags = Column(String(500), nullable=True)         # 自定义标签
```

### 2. 统计模型策略
**新建SiteStats表**:
```python
class SiteStats(Base):
    __tablename__ = "site_stats"
    
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True)
    upload_bytes = Column(BigInteger, default=0)
    download_bytes = Column(BigInteger, default=0)
    ratio = Column(Float, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    health_status = Column(String(20), default="OK")
```

### 3. 访问配置模型策略
**新建SiteAccessConfig表**:
```python
class SiteAccessConfig(Base):
    __tablename__ = "site_access_configs"
    
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), index=True)
    rss_url = Column(String(500), nullable=True)
    api_key = Column(String(255), nullable=True)
    auth_header = Column(String(500), nullable=True)
    cookie = Column(Text, nullable=True)  # 加密存储
    user_agent = Column(String(500), nullable=True)
    use_api_mode = Column(Boolean, default=False)
    use_proxy = Column(Boolean, default=False)
    use_browser_emulation = Column(Boolean, default=False)
    min_interval_seconds = Column(Integer, default=10)
    max_concurrent_requests = Column(Integer, default=1)
```

## 与现有系统的边界划分

### SETTINGS-RULES-1 边界
- **SETTINGS-RULES-1负责**: HR策略、分辨率档位、三档模式、下载规则
- **SITE-MANAGER-1负责**: 站点启用/停用、优先级、访问配置、健康状态、连通性

### Local Intel 集成
- **复用**: `site_guard_profiles` 表的风控配置
- **扩展**: 增加健康检查状态同步
- **标识统一**: 使用Site.id替代字符串站点名称

### CookieCloud 集成
- **复用**: 现有CookieCloud同步逻辑
- **扩展**: 同步结果更新SiteStats健康状态
- **配置统一**: Cookie配置迁移到SiteAccessConfig

### External Indexer 集成
- **过滤**: 只处理enabled=True且health_status!="ERROR"的站点
- **配置**: 从SiteAccessConfig读取访问参数
- **标识**: 使用Site.key或domain进行匹配

## 实施优先级

### Phase 1: 数据模型扩展 (P1)
1. 扩展Site模型，添加key、domain、category等字段
2. 创建SiteStats和SiteAccessConfig表
3. 数据迁移脚本，将现有数据迁移到新结构

### Phase 2: API扩展 (P2)
1. 基于现有site.py API扩展新的端点
2. 添加健康检查、导入导出功能
3. 保持现有API兼容性

### Phase 3: 前端实现 (P3-P4)
1. 新增侧边栏【站点管理】模块
2. 实现站点墙和卡片视图
3. 站点详情抽屉和编辑表单

### Phase 4: 系统集成 (P5)
1. 与CookieCloud同步集成
2. External Indexer过滤集成
3. Local Intel状态同步

### Phase 5: 测试文档 (P6)
1. 完整测试场景
2. 开发者指南
3. 部署文档

## 风险控制

### 数据迁移风险
- 现有Site表包含重要数据，需要谨慎迁移
- 建议先在测试环境验证迁移脚本
- 保留原字段作为备份，确保兼容性

### API兼容性风险
- 现有site.py API已有大量使用
- 新增API端点使用不同前缀避免冲突
- 保持现有API响应格式不变

### 前端集成风险
- 新增侧边栏模块需要考虑现有布局
- 响应式设计确保移动端兼容性
- 与现有插件页风格保持一致

## 总结

现有系统已有良好的站点管理基础，SITE-MANAGER-1项目主要是在此基础上进行扩展和统一，而非重新构建。通过复用现有Site模型和API，可以大幅降低开发风险和复杂度，确保与现有系统的良好兼容性。
