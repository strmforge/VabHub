# 智能子系统测试概览

## 概述

本文档描述了 VabHub 智能子系统的测试覆盖情况。智能子系统包括：

1. **AI 站点适配模块** (`site_ai_adapter`)
2. **Local Intel 智能监控** (`intel_local`)
3. **外部索引桥接** (`ext_indexer`)

## 测试目录结构

```
backend/tests/
├── conftest.py                          # 共享 fixtures（数据库会话等）
├── site_ai_adapter/
│   ├── test_service_basic.py            # 基本分析与缓存测试
│   └── test_frequency_and_flags.py     # 频率限制和标志测试
├── intel_local/
│   └── test_ai_fallback_profiles.py    # AI 回退生成 Local Intel profile 测试
└── ext_indexer/
    ├── test_ai_fallback_site_config.py # AI 回退生成 External site config 测试
    └── test_search_merge_and_source.py  # 搜索结果合并与 source 标记测试
```

## 测试覆盖范围

### 1. AI 站点适配模块 (`site_ai_adapter`)

#### test_service_basic.py
- ✅ 成功分析并保存站点配置
- ✅ 分析失败时保存错误信息
- ✅ 成功加载并解析配置
- ✅ 加载不存在的配置
- ✅ 加载无效 JSON 配置

#### test_frequency_and_flags.py
- ✅ 频率限制防止重复分析
- ✅ 频率限制在间隔后允许重新分析
- ✅ disabled 标志阻止分析
- ✅ disabled 标志不会覆盖现有配置
- ✅ 首次分析允许执行

### 2. Local Intel + AI 回退 (`intel_local`)

#### test_ai_fallback_profiles.py
- ✅ AI 正常回退：当没有手工配置时，从 AI 配置生成 profile
- ✅ AI 被 disabled 时不进行回退
- ✅ 手工优先：当存在手工配置且 manual_profile_preferred=True 时，优先使用手工配置
- ✅ 存在手工配置但 manual_profile_preferred=False 时，仍然使用手工配置
- ✅ 既没有手工配置也没有 AI 配置时返回 None

### 3. External Indexer + AI 回退 (`ext_indexer`)

#### test_ai_fallback_site_config.py
- ✅ AI 正常回退：当没有手工配置时，从 AI 配置生成 external site config
- ✅ AI 被 disabled 时不进行回退
- ✅ 手工优先：当存在手工配置且 manual_profile_preferred=True 时，优先使用手工配置
- ✅ 既没有手工配置也没有 AI 配置时返回 None

#### test_search_merge_and_source.py
- ✅ 搜索结果合并并正确标记 source
- ✅ 搜索结果按 site_id + torrent_id 去重
- ✅ 搜索跳过需要人机验证的站点
- ✅ 搜索多个站点并合并结果

## 运行测试

### 前置要求

确保已安装测试依赖：

```bash
cd VabHub/backend
pip install pytest pytest-asyncio
```

### 运行所有测试

```bash
cd VabHub/backend
pytest -q
```

### 运行特定模块的测试

```bash
# 只运行 AI 站点适配模块测试
pytest tests/site_ai_adapter/ -q

# 只运行 Local Intel 测试
pytest tests/intel_local/ -q

# 只运行 External Indexer 测试
pytest tests/ext_indexer/ -q
```

### 运行特定测试文件

```bash
pytest tests/site_ai_adapter/test_service_basic.py -q
```

### 显示详细输出

```bash
pytest -v
```

## 测试设计原则

1. **完全隔离**：所有测试使用内存 SQLite 数据库，不污染正式数据库
2. **Mock 外部依赖**：不访问真实的 HTTP/LLM 服务，全部使用 mock
3. **独立执行**：每个测试函数都是独立的，可以单独运行
4. **清晰断言**：每个测试都有明确的断言，验证预期行为

## 后续扩展方向

以下功能可以考虑添加测试：

1. **HR 事件流测试**：测试 Local Intel 的 HR 监控和事件处理
2. **站点风控事件测试**：测试站点防护和风控逻辑
3. **AI 配置转换边界情况**：测试各种边界情况和异常输入
4. **性能测试**：测试大量站点配置加载和搜索的性能
5. **集成测试**：测试多个模块协同工作的场景

## 注意事项

- 所有测试都使用 `pytest.mark.asyncio` 标记，因为涉及异步数据库操作
- 测试数据库使用内存 SQLite，每次测试后自动清理
- Mock 对象用于模拟外部服务（Cloudflare API、HTTP 客户端等）
- 测试不依赖真实的外部服务或网络连接

