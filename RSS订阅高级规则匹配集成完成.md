# RSS订阅高级规则匹配集成完成

## 📋 概述

已将订阅服务中的高级规则匹配系统集成到RSS订阅功能中，替换了之前简单的规则匹配逻辑。

## ✅ 完成的工作

### 1. 创建高级规则匹配引擎 (`RSSRuleEngine`)

**文件**: `backend/app/modules/rss/rule_engine.py`

**功能**:
- ✅ 评估RSS项是否符合订阅的高级规则
- ✅ 支持所有订阅规则字段的检查：
  - `quality` - 质量要求（4K、1080p等）
  - `resolution` - 分辨率要求
  - `effect` - 特效要求（HDR、DV等）
  - `min_seeders` - 最小做种数要求
  - `include` - 包含规则（支持关键字和正则表达式）
  - `exclude` - 排除规则（支持关键字和正则表达式）
  - `filter_groups` - 发布组过滤（支持白名单和黑名单）
  - `search_rules` - 搜索规则（文件大小、编码、发布组等）
  - 电视剧季数和集数匹配

**特点**:
- 支持正则表达式匹配
- 支持多关键字匹配（用 `|` 分隔）
- 支持发布组白名单和黑名单
- 返回详细的匹配结果（匹配分数、原因、失败的规则等）

### 2. 集成到RSS订阅服务

**文件**: `backend/app/modules/rss/service.py`

**更改**:
- ✅ 在 `RSSSubscriptionService` 中初始化 `RSSRuleEngine`
- ✅ 在 `_process_rss_item` 方法中使用规则引擎替代简单的规则检查
- ✅ 保留 `_check_subscription_rules` 方法（标记为已废弃）用于向后兼容

### 3. 规则匹配流程

```
RSS项 → 提取媒体信息 → 匹配订阅 → 使用规则引擎评估 → 触发下载
```

**详细流程**:
1. RSS项到达 → 提取媒体信息（标题、年份、质量等）
2. 匹配订阅（根据标题、年份、类型等）
3. 使用规则引擎评估（检查所有高级规则）
4. 如果匹配 → 触发下载
5. 如果不匹配 → 记录失败原因并跳过

## 🎯 支持的规则类型

### 1. 基础规则

- **质量规则**: 4K、1080p、720p、480p
- **分辨率规则**: 2160p、1080p、720p等
- **特效规则**: HDR、Dolby Vision等
- **做种数规则**: 最小做种数要求

### 2. 包含规则 (`include`)

支持格式：
- 关键字：`"HDR"` - 标题必须包含 "HDR"
- 多关键字：`"HDR|DV"` - 标题必须包含 "HDR" 或 "DV"
- 正则表达式：`"\\d{4}p"` - 标题必须匹配正则表达式

### 3. 排除规则 (`exclude`)

支持格式：
- 关键字：`"CAM"` - 标题不能包含 "CAM"
- 多关键字：`"CAM|TS|TC"` - 标题不能包含任何这些关键字
- 正则表达式：`"\\d{3}p"` - 标题不能匹配正则表达式

### 4. 发布组过滤 (`filter_groups`)

支持格式：
- 列表：`["Group1", "Group2"]` - 只允许这些发布组
- 字典（白名单）：`{"whitelist": ["Group1", "Group2"]}` - 只允许这些发布组
- 字典（黑名单）：`{"blacklist": ["BadGroup"]}` - 排除这些发布组
- 字典（组合）：`{"whitelist": ["Group1"], "blacklist": ["BadGroup"]}` - 白名单和黑名单组合

### 5. 搜索规则 (`search_rules`)

支持规则：
- `min_size_gb`: 最小文件大小（GB）
- `max_size_gb`: 最大文件大小（GB）
- `codec`: 编码要求（H.264、H.265等）
- `group`: 发布组要求

### 6. 电视剧特殊规则

- 季数匹配：检查标题中是否包含正确的季数（S01、S02等）
- 集数匹配：检查标题中是否包含正确的集数（E01、E02等）

## 📊 规则评估结果

规则引擎返回详细的结果：

```python
{
    "matched": bool,           # 是否匹配
    "score": float,            # 匹配分数（0-1）
    "reason": str,             # 匹配原因
    "failed_rules": List[str], # 未通过的规则列表
    "matched_rules": List[str] # 通过的规则列表
}
```

## 🔄 迁移说明

### 旧方法（已废弃）

```python
# 旧方法：简单的规则检查
if not self._check_subscription_rules(extracted_info, matched_subscription):
    return {"downloaded": False, "error": "不满足订阅规则"}
```

### 新方法（推荐）

```python
# 新方法：使用高级规则引擎
rule_result = self.rule_engine.evaluate_rss_item(
    item,
    extracted_info,
    matched_subscription
)

if not rule_result.get("matched"):
    return {
        "downloaded": False,
        "error": f"不满足订阅规则: {rule_result.get('reason')}",
        "rule_result": rule_result
    }
```

## 🎉 优势

1. **完整的规则支持**: 支持所有订阅规则字段
2. **灵活匹配**: 支持关键字、正则表达式、发布组过滤等
3. **详细反馈**: 返回详细的匹配结果和失败原因
4. **易于扩展**: 规则引擎可以轻松扩展新的规则类型
5. **统一逻辑**: 与订阅服务的规则匹配逻辑保持一致

## 📝 使用示例

### 示例1：基础规则

```python
# 订阅规则：
# - quality: "1080p"
# - resolution: "1080p"
# - min_seeders: 10

# RSS项: "Movie Name 2024 1080p HDR"
# 结果: 匹配（满足所有规则）
```

### 示例2：包含规则

```python
# 订阅规则：
# - include: "HDR|Dolby Vision"

# RSS项: "Movie Name 2024 1080p HDR"
# 结果: 匹配（包含 "HDR"）
```

### 示例3：排除规则

```python
# 订阅规则：
# - exclude: "CAM|TS|TC"

# RSS项: "Movie Name 2024 CAM"
# 结果: 不匹配（触发排除规则）
```

### 示例4：发布组过滤

```python
# 订阅规则：
# - filter_groups: {"whitelist": ["Group1", "Group2"], "blacklist": ["BadGroup"]}

# RSS项: "Movie Name 2024 [Group1]"
# 结果: 匹配（在白名单中）

# RSS项: "Movie Name 2024 [BadGroup]"
# 结果: 不匹配（在黑名单中）
```

## 🚀 下一步

1. ✅ 完成高级规则匹配引擎
2. ✅ 集成到RSS订阅服务
3. ⚠️ 测试规则匹配功能
4. ⚠️ 添加规则匹配日志记录
5. ⚠️ 优化规则匹配性能

## 📚 相关文件

- `backend/app/modules/rss/rule_engine.py` - 规则引擎
- `backend/app/modules/rss/service.py` - RSS订阅服务
- `backend/app/modules/subscription/service.py` - 订阅服务（参考）
- `backend/app/models/subscription.py` - 订阅模型

