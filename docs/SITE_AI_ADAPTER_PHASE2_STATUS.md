# 站点 AI 适配模块 Phase AI-2 完成状态

## 概述

Phase AI-2 的目标是让 `ai_site_adapters` 表中生成的 AI 配置真正被 Local Intel 和 External Indexer 使用，实现"有则用、无则退"的安全增强。

## 完成时间

2025-11-21

## 实现内容

### 任务 A：类型安全的配置视图层 ✅

**文件：** `backend/app/core/site_ai_adapter/models.py`

**新增模型：**
- `ParsedAISiteSearchConfig`：解析后的搜索配置
- `ParsedAISiteDetailConfig`：解析后的详情页配置
- `ParsedAISiteHRConfig`：解析后的 HR 配置
- `ParsedAISiteAuthConfig`：解析后的认证配置
- `ParsedAISiteCategoriesConfig`：解析后的分类配置
- `ParsedAISiteAdapterConfig`：完整的解析后配置

**新增函数：** `backend/app/core/site_ai_adapter/service.py`
- `load_parsed_config(site_id, db)`：从数据库加载并解析 AI 配置，返回强类型的 `ParsedAISiteAdapterConfig`

**特点：**
- 所有文本字段自动 strip
- 使用 Optional 和默认值处理缺失字段
- 解析失败时只记录日志，返回 None

### 任务 B：AI 配置 → Local Intel Profile 转换 ✅

**文件：** `backend/app/core/site_ai_adapter/intel_bridge.py`

**新增函数：**
- `ai_config_to_intel_profile(site, cfg)`：将 AI 配置转换为 `IntelSiteProfile`

**集成点：**
- `backend/app/core/intel_local/site_profiles.py`：
  - 新增 `get_site_profile_with_ai_fallback()` 函数
  - 优先使用手工配置，如果没有则尝试从 AI 配置转换

- `backend/app/core/intel_local/factory.py`：
  - 在 `register_site_http_clients()` 中集成 AI 配置回退逻辑
  - 当站点没有手工配置时，自动尝试使用 AI 配置

**转换逻辑：**
- HR 配置：从 AI 配置的 `hr.enabled`、`hr.rules`、`hr.page_path` 转换
- 站内信配置：AI 配置中通常不包含，使用默认值（禁用）
- 站点防护配置：使用默认值

### 任务 C：AI 配置 → External Indexer Site Config 转换 ✅

**文件：** `backend/app/core/ext_indexer/ai_bridge.py`

**新增函数：**
- `ai_config_to_external_site_config(site, cfg)`：将 AI 配置转换为 `ExternalSiteConfig`

**集成点：**
- `backend/app/core/ext_indexer/site_importer.py`：
  - 新增 `get_site_config_with_ai_fallback()` 函数
  - 优先使用手工配置，如果没有则尝试从 AI 配置转换

- `backend/app/core/ext_indexer/search_provider.py`：
  - 在 `search()` 方法中，当没有手工配置的站点时，自动从数据库加载站点并使用 AI 配置

**转换逻辑：**
- 从 AI 配置的 `search.url` 判断是否支持搜索能力
- 从 AI 配置的 `detail.url` 判断是否支持详情能力
- 使用 AI 配置的 `engine` 字段作为框架类型

### 任务 D：调试 API ✅

**文件：** `backend/app/api/site_ai_adapter.py`

**新增接口：**
- `GET /api/admin/site-ai-adapter/effective-config/{site_id}`

**返回内容：**
- 原始 AI 配置的简要信息
- Local Intel 配置（手工/AI/无）
- External Indexer 配置（手工/AI/无）
- 当前生效策略说明（mode 字段）

## 使用优先级

### Local Intel

1. **手工配置优先**：如果 `config/intel_sites/*.yaml` 中存在站点配置，直接使用
2. **AI 配置回退**：如果没有手工配置，尝试从 `ai_site_adapters` 表加载并转换
3. **无配置**：如果都没有，站点不会被注册到 Local Intel（保持当前行为）

### External Indexer

1. **手工配置优先**：如果 `config/external_sites/*.yaml` 中存在站点配置，直接使用
2. **AI 配置回退**：如果没有手工配置，尝试从 `ai_site_adapters` 表加载并转换
3. **无配置**：如果都没有，站点不会出现在 External Indexer 的搜索列表中（保持当前行为）

## 回退策略

### 所有使用 AI 配置的地方都遵循以下策略：

1. **AI 配置不存在**：
   - 记录 DEBUG 日志
   - 返回 None，恢复到当前行为（不注册/不使用）

2. **AI 配置解析失败**：
   - 记录 WARNING 日志，包含错误详情
   - 返回 None，恢复到当前行为

3. **AI 配置转换失败**：
   - 记录 WARNING 日志，包含转换失败原因
   - 返回 None，恢复到当前行为

4. **AI_ADAPTER_ENABLED = false**：
   - 所有 AI 配置相关逻辑短路
   - 只记录 DEBUG 日志，不尝试加载或转换

## 日志说明

### INFO 级别
- `"站点 {site} 使用 AI 生成的配置（回退模式）"`：成功使用 AI 配置时
- `"成功将 AI 配置转换为 Local Intel Profile"`：转换成功时
- `"成功将 AI 配置转换为 External Site Config"`：转换成功时

### DEBUG 级别
- `"AI 适配功能已禁用，跳过..."`：功能未启用时
- `"站点 {site} 没有 AI 适配配置"`：配置不存在时
- `"站点 {site} 使用手工配置"`：使用手工配置时

### WARNING 级别
- `"将 AI 配置转换为 ... 失败"`：转换失败时
- `"解析站点 {site_id} 的 AI 适配配置失败"`：解析失败时

### ERROR 级别
- `"加载站点 {site_id} 的 AI 适配配置时发生错误"`：加载过程异常时

## 模块使用情况

### Local Intel

**使用 AI 配置的位置：**
- `backend/app/core/intel_local/factory.py::register_site_http_clients()`
  - 当站点没有手工配置时，尝试使用 AI 配置生成 `IntelSiteProfile`
  - 用于注册 HTTP 客户端，支持 HR 页面和站内信页面的抓取

**影响范围：**
- HR 监控：如果 AI 配置包含 HR 规则，可以自动启用 HR 监控
- 站内信监控：当前 AI 配置不包含站内信配置，使用默认值（禁用）

### External Indexer

**使用 AI 配置的位置：**
- `backend/app/core/ext_indexer/search_provider.py::search()`
  - 当没有手工配置的站点时，从数据库加载站点并使用 AI 配置
  - 用于扩展搜索站点列表

**影响范围：**
- 搜索功能：AI 配置的站点可以出现在搜索列表中
- 详情功能：如果 AI 配置包含详情页 URL，可以支持详情查询

## 向后兼容性

✅ **完全向后兼容**

- 所有已有手工配置的站点不受影响
- 没有 AI 配置的站点行为不变
- AI 配置解析/转换失败时，系统行为恢复到修改前
- 所有新功能都通过 `AI_ADAPTER_ENABLED` 开关控制

## 测试建议

### 1. 导入检查
```bash
cd backend
python -c "from app.core.site_ai_adapter import load_parsed_config, ParsedAISiteAdapterConfig; print('ok')"
python -c "from app.core.ext_indexer.search_provider import ExternalIndexerSearchProvider; print('ok')"
```

### 2. 功能测试

**场景 1：有手工配置的站点**
- 创建站点，确认使用手工配置（不触发 AI 配置）

**场景 2：无手工配置但有 AI 配置的站点**
- 创建站点并等待 AI 适配完成
- 确认 Local Intel 和 External Indexer 可以使用 AI 配置

**场景 3：无任何配置的站点**
- 创建站点但 AI 适配失败
- 确认系统行为不变（不注册到 Local Intel/External Indexer）

**场景 4：调试 API**
```bash
curl http://localhost:8092/api/admin/site-ai-adapter/effective-config/1
```

## 后续扩展方向

1. **Local Intel HR 规则增强**
   - 使用 AI 配置中的 `hr.rules` 增强 HR 检测逻辑
   - 根据规则的 `pattern`、`location`、`severity` 进行更精确的 HR 判断

2. **External Indexer 搜索实现**
   - 根据 AI 配置的 `search.url`、`search.query_params` 构建实际搜索请求
   - 使用 `detail.selectors` 解析搜索结果和详情页

3. **前端 UI 展示**
   - 在站点管理页面显示"AI 适配状态"
   - 展示生效的配置来源（手工/AI/无）

## 注意事项

1. **配置优先级**：手工配置始终优先，AI 配置只是回退方案
2. **错误处理**：所有 AI 配置相关错误都不应影响主流程
3. **性能考虑**：AI 配置加载和转换是同步操作，但频率较低（主要在站点注册时）
4. **日志监控**：建议监控 WARNING/ERROR 日志，及时发现 AI 配置问题

---

**文档版本：** 1.0  
**最后更新：** 2025-11-21

