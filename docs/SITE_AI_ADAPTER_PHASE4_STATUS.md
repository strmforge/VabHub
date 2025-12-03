# Phase AI-4 完成状态

## 概述

Phase AI-4 为站点 AI 适配功能添加了每站点的控制开关和可信度评分功能。

## 新增功能

### 1. 每站点的 AI 开关与优先策略

每个站点现在可以单独控制 AI 适配行为：

- **`ai_disabled`**: 完全禁用本站点的 AI 适配（不调用、不回退）
- **`ai_manual_profile_preferred`**: 如果既有人工配置也有 AI 配置，优先使用人工配置

### 2. AI 结果可信度评分

针对 AI 生成的配置，在 `ai_site_adapters` 记录上存储一个 0-100 的 `confidence_score`（当前阶段固定为 80，后续可智能化）。

### 3. 错误记录

在 `ai_site_adapters` 记录上存储 `last_error` 字段，记录最近一次 AI 调用失败的摘要（最多 500 字符）。

## 数据库变更

### 新增字段

在 `ai_site_adapters` 表中新增以下字段：

- `disabled` (INTEGER NOT NULL DEFAULT 0): 是否禁用本站点的 AI 适配
- `manual_profile_preferred` (INTEGER NOT NULL DEFAULT 0): 是否优先使用人工配置
- `confidence_score` (INTEGER): AI 配置可信度分数（0-100，可为 NULL）
- `last_error` (TEXT): 最近一次 AI 调用失败摘要（可为 NULL）

### 迁移脚本

迁移脚本 `backend/scripts/migrate_ai_site_adapter_schema.py` 已更新，会自动检查并添加新字段到现有表中。

## 后端变更

### 1. 模型层

- **`backend/app/models/ai_site_adapter.py`**: 添加了新字段到 `AISiteAdapter` ORM 模型
- **`backend/app/core/site_ai_adapter/models.py`**: 
  - 在 `AISiteAdapterConfig` 中添加了 `confidence_score` 字段
  - 在 `ParsedAISiteAdapterConfig` 中添加了 `confidence_score` 字段

### 2. 服务层

- **`backend/app/core/site_ai_adapter/service.py`**:
  - `analyze_and_save_for_site`: 成功时设置 `confidence_score = 80` 并清空 `last_error`；失败时更新 `last_error` 并保留旧配置
  - `maybe_auto_analyze_site`: 如果站点 `disabled=True`，直接返回，不发起请求
  - `load_parsed_config`: 从数据库记录中读取 `confidence_score` 并设置到解析后的配置中

- **`backend/app/core/site_ai_adapter/settings.py`**: 新增 `update_site_ai_settings` 函数，用于更新站点的 AI 适配设置

- **`backend/app/core/site_ai_adapter/status.py`**: 
  - `AISiteAdapterStatus` 添加了新字段：`disabled`, `manual_profile_preferred`, `confidence_score`, `last_error_preview`
  - `get_ai_adapter_status_for_site` 更新以考虑 `disabled` 和 `manual_profile_preferred` 标志

### 3. AI 回退逻辑

- **`backend/app/core/intel_local/site_profiles.py`**: `get_site_profile_with_ai_fallback` 更新以检查 `ai_disabled` 和 `ai_manual_profile_preferred` 标志
- **`backend/app/core/ext_indexer/site_importer.py`**: `get_site_config_with_ai_fallback` 更新以检查 `ai_disabled` 和 `ai_manual_profile_preferred` 标志

### 4. API 层

- **`backend/app/api/site.py`**:
  - `SiteCreate` 添加了 `ai_disabled` 和 `ai_manual_profile_preferred` 字段
  - `SiteResponse` 添加了 `ai_disabled`, `ai_manual_profile_preferred`, `ai_confidence_score` 字段
  - `create_site` 和 `update_site` 支持设置 AI 适配相关字段
  - `list_sites` 和 `get_site` 返回新的 AI 相关字段

- **`backend/app/api/site_ai_adapter.py`**: `get_effective_config` 返回新的 AI 相关字段（`ai_disabled`, `ai_manual_profile_preferred`, `ai_confidence_score`, `last_error_preview`）

## 前端变更

### 1. 站点编辑对话框

- **`frontend/src/components/site/SiteDialog.vue`**: 
  - 添加了 "AI 适配设置（实验性功能）" 区域
  - 添加了两个开关：
    - "禁用 AI 适配（本站点）"
    - "优先使用人工配置（存在人工配置时）"
  - 表单加载和保存时正确处理新字段

### 2. 站点卡片

- **`frontend/src/components/site/SiteCard.vue`**: 
  - AI 状态显示更新：如果 `ai_disabled=true`，图标和颜色会明显不同（显示 "已禁用" 标识）
  - 工具提示中显示 `ai_disabled`、`ai_manual_profile_preferred` 和 `ai_confidence_score` 状态

### 3. AI 调试对话框

- **`frontend/src/components/site/SiteAIAdapterDebugDialog.vue`**: 
  - 显示 `ai_disabled` 状态（用芯片显示）
  - 显示 `ai_manual_profile_preferred` 状态（用芯片显示）
  - 显示 `ai_confidence_score`（用颜色编码的芯片显示：>=80 绿色，>=60 黄色，<60 红色）
  - 显示 `last_error_preview`（如果有错误，用错误提示框显示）

## 行为说明

### 优雅降级

所有新逻辑都是可选增强：

- 没有 AI 记录 → 行为与现在完全一样
- 有 AI 记录但新字段为 NULL → 使用默认值（视为未禁用、无特别优先）
- AI 适配功能全局禁用 → 所有站点都不使用 AI 适配

### 优先级逻辑

1. **手工配置优先**：如果存在手工配置，优先使用（无论 `ai_manual_profile_preferred` 设置如何）
2. **AI 禁用检查**：如果 `ai_disabled=True`，完全不使用 AI 配置（不回退）
3. **优先人工配置标志**：如果 `ai_manual_profile_preferred=True` 且存在手工配置，使用手工配置；否则，如果存在 AI 配置，使用 AI 配置

## 自检步骤

### 后端自检

```bash
cd backend

# 检查模型导入
python -c "from app.models.ai_site_adapter import AISiteAdapter; print('ai model ok')"

# 检查状态模块导入
python -c "from app.core.site_ai_adapter.status import get_ai_adapter_status_for_site; print('status ok')"

# 检查配置
python -c "from app.core.config import settings; print('AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES:', settings.AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES)"

# 运行迁移脚本（如果数据库已存在）
python scripts/migrate_ai_site_adapter_schema.py
```

### 前端自检

```bash
cd frontend

# 运行 lint
npm run lint

# 构建检查
npm run build
```

## 注意事项

1. **向后兼容**：所有新字段都是可选的，现有数据会自动使用默认值
2. **实验性功能**：UI 中明确标注为"实验性功能"，避免用户误以为这是必须配置的功能
3. **无第三方项目名称**：代码、文档、注释、UI 中都没有出现任何第三方项目名称
4. **固定可信度分数**：当前 `confidence_score` 固定为 80，后续可以基于 AI 响应质量、配置完整性等因素智能化计算

## 完成时间

Phase AI-4 已完成所有任务（A、B、C、D、E）。
