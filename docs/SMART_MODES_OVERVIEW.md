# 智能子系统运行模式概览

本文档定义了 VabHub 智能子系统的三种运行模式，供用户根据自身需求选择合适的配置。

## 模块说明

智能子系统包含三个核心模块：

1. **Local Intel（本地智能）**：提供 HR 保护、站点防风控、站内信监控等功能
2. **External Indexer（外部索引桥接）**：集成外部 PT 索引引擎的搜索能力
3. **AI Site Adapter（站点 AI 适配）**：通过 LLM 自动生成站点适配配置

## 运行模式

### 1. 纯本地模式（安全 / 无外网依赖）

**适用场景**：
- 对数据隐私要求极高的用户
- 无外网访问或希望完全本地运行
- 只需要基础的 HR 保护功能

**配置示例**：
```bash
INTEL_ENABLED=true
EXTERNAL_INDEXER_ENABLED=false
AI_ADAPTER_ENABLED=false
```

**功能说明**：
- ✅ Local Intel：仅使用本地逻辑（HR 保护 + 简单分析），不开启 AI 适配
- ❌ External Indexer：关闭
- ❌ AI Site Adapter：关闭

**自动生效的功能**：
- HR MOVE→COPY 保护（始终开启，无需用户理解）
- 站点访问频率监控（避免触发风控）

**用户界面**：
- Local Intel 看板默认隐藏（需开启 `VITE_DEV_MODE=true` 才能看到）
- 普通用户界面不显示智能相关入口

---

### 2. 增强模式（有外网，但适度使用）

**适用场景**：
- 有外网访问能力
- 希望使用智能功能但不想过度依赖外部服务
- 平衡功能性和稳定性

**配置示例**：
```bash
INTEL_ENABLED=true
EXTERNAL_INDEXER_ENABLED=true
EXTERNAL_INDEXER_MIN_RESULTS=10
AI_ADAPTER_ENABLED=true
AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES=120
```

**功能说明**：
- ✅ Local Intel：开启
- ✅ External Indexer：开启，但提高 `EXTERNAL_INDEXER_MIN_RESULTS` 到 10，避免频繁调用外部服务
- ✅ AI Site Adapter：开启，但频率限制调高到 120 分钟，减少分析频率

**自动生效的功能**：
- HR MOVE→COPY 保护
- 站点访问频率监控
- 站点自动适配（新增/修改站点时自动触发，但频率受限）
- 搜索结果补充（仅在本地结果不足时调用外部索引）

**用户界面**：
- Local Intel 看板默认隐藏（需开启 `VITE_DEV_MODE=true`）
- 站点编辑时自动触发 AI 分析（后台静默运行）

---

### 3. 实验模式（对"站点自动适配"兴趣很大的人用）

**适用场景**：
- 对站点自动适配功能非常感兴趣
- 愿意尝试实验性功能
- 能够接受可能的配置不准确

**配置示例**：
```bash
INTEL_ENABLED=true
EXTERNAL_INDEXER_ENABLED=true
EXTERNAL_INDEXER_MIN_RESULTS=20
AI_ADAPTER_ENABLED=true
AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES=60
```

**功能说明**：
- ✅ Local Intel：开启
- ✅ External Indexer：开启
- ✅ AI Site Adapter：开启，使用默认频率限制（60 分钟）

**自动生效的功能**：
- 所有增强模式的功能
- 更频繁的站点自动适配分析
- 更积极的搜索结果补充

**重要提示**：
- ⚠️ 这是实验功能，不保证 100% 准确
- ⚠️ 后端会在新增/修改站点时自动触发 AI 分析
- ⚠️ External Indexer 可能会访问外部索引服务
- ⚠️ 建议在测试环境先验证效果

**用户界面**：
- 与增强模式相同
- 可通过 `VITE_DEV_MODE=true` 查看 AI 适配调试面板

---

## 模式选择建议

| 模式 | 外网需求 | 隐私要求 | 功能丰富度 | 推荐用户 |
|------|---------|---------|-----------|---------|
| 纯本地模式 | ❌ 无 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 隐私敏感用户 |
| 增强模式 | ✅ 有 | ⭐⭐⭐ | ⭐⭐⭐⭐ | 大多数用户 |
| 实验模式 | ✅ 有 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 技术爱好者 |

## 配置检查

配置完成后，可以通过以下方式检查智能子系统状态：

1. **健康检查 API**：
   ```bash
   curl http://localhost:8092/api/smart/health
   ```

2. **查看日志**：
   检查后端日志中是否有智能子系统相关的错误信息

3. **功能验证**：
   - Local Intel：检查 HR 保护是否生效（MOVE 操作是否自动转为 COPY）
   - External Indexer：搜索时查看是否有外部结果补充
   - AI Site Adapter：新增站点后检查是否有 AI 生成的配置

## 注意事项

1. **数据库迁移**：首次启用 Local Intel 前，请确保已执行相关数据库迁移脚本
2. **外部服务配置**：
   - External Indexer 需要配置 `EXTERNAL_INDEXER_MODULE`
   - AI Site Adapter 需要部署 Cloudflare Pages 适配器（或使用官方默认端点）
3. **性能影响**：增强模式和实验模式会增加外部 API 调用，可能影响响应速度
4. **开发者模式**：Local Intel / External Indexer 的 UI 面板默认隐藏，需要设置 `VITE_DEV_MODE=true` 才能看到

