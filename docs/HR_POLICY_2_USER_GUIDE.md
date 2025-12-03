# HR-POLICY-2 安全策略用户指南

## 概述

HR-POLICY-2 是 VabHub 的安全策略增强模块，旨在保护用户的 HR（Hit and Run）案例，防止误操作导致的数据丢失和站点封禁风险。

### 核心功能

- **下载前检查**：在添加新种子时评估 HR 风险
- **删除操作保护**：防止删除低分享率的 HR 案例
- **移动/整理保护**：智能处理 HR 文件的移动操作
- **自动清理保护**：保护待整理目录中的 HR 相关文件
- **多级配置**：支持全局、站点、订阅三级安全策略配置

## 配置说明

### 1. 全局安全策略设置

访问 **设置 → 安全策略** 进行全局配置：

#### 安全模式选择

- **安全模式 (SAFE)**：最高保护级别，所有 HR 相关操作都需要确认
- **平衡模式 (BALANCED)**：平衡保护与便利性，部分操作自动允许
- **激进模式 (AGGRESSIVE)**：最低保护级别，仅高风险操作需要确认

#### 基础保护设置

```yaml
hr_protection_enabled: true          # 启用 HR 保护
min_ratio_for_delete: 1.0           # 删除最低分享率要求
min_keep_hours: 72                   # 最少保种时间（小时）
hr_move_strategy: "copy"             # HR 文件移动策略
auto_approve_hours: 24               # 自动批准时间（小时）
```

#### HR 文件移动策略

- **复制移动 (copy)**：移动 HR 文件时创建副本，不影响做种
- **直接移动 (move)**：直接移动文件，可能影响做种
- **禁止移动 (deny)**：禁止移动任何 HR 文件

### 2. 站点级安全策略

为不同站点设置差异化的安全策略：

```yaml
site_key: "hdchina"
hr_sensitivity: "HIGH"               # 站点 HR 敏感度
min_ratio_for_delete: 1.2            # 站点特定的删除阈值
enabled: true                        # 是否启用站点策略
```

#### 站点 HR 敏感度

- **HIGH**：高敏感度站点，严格保护
- **MEDIUM**：中等敏感度站点，标准保护
- **LOW**：低敏感度站点，宽松保护

### 3. 订阅级安全策略

为特定订阅设置安全策略：

```yaml
subscription_id: 123
allow_hr: false                      # 是否允许 HR 种子
auto_approve: false                  # 是否自动批准 HR 操作
custom_threshold: 1.5                # 自定义阈值
```

## 使用指南

### 1. 下载安全检查

当您尝试下载新种子时，系统会自动执行安全检查：

#### 正常下载流程
1. 选择种子并点击下载
2. 系统检查站点 HR 策略
3. 如果无风险，直接开始下载
4. 如果有风险，显示确认对话框

#### HR 风险提示示例
```
⚠️ 需要用户确认
站点：hdchina
当前分享率：0.8
最低要求：1.0
建议：等待分享率达到要求后再下载
```

### 2. 删除操作保护

删除下载任务时的安全检查：

#### 被阻止的删除操作
```
🛡️ 安全策略阻止删除
原因：分享率过低 (0.3 < 1.0)
站点：hdchina
种子ID：123456
建议：继续做种提高分享率
```

#### 需要确认的删除操作
```
⚠️ 需要用户确认删除
当前分享率：1.1
保种时间：48小时
是否确认删除此任务？
```

### 3. 文件移动和整理

#### HR 文件移动保护
- 系统自动检测移动操作是否影响做种
- HR 文件默认使用复制策略
- 可在设置中调整移动策略

#### 整理操作示例
```
📁 文件整理
源路径：/downloads/movie.mkv
目标路径：/media/movies/movie.mkv
检测到：HR 案例
策略：复制移动（不影响做种）
```

### 4. 自动清理保护

系统保护待整理目录中的 HR 相关文件：

#### 清理安全检查
- 自动识别 HR 相关文件
- 阻止清理正在做种的文件
- 提供清理建议和替代方案

## 通知系统

### 安全策略通知类型

#### 1. SAFETY_BLOCKED 通知
```
🛡️ 安全策略阻止操作
操作类型：删除
阻止原因：分享率过低
站点：hdchina
种子ID：123456
```

#### 2. SAFETY_REQUIRE_CONFIRM 通知
```
⚠️ 安全策略需要用户确认
操作类型：移动
确认原因：影响 HR 做种
站点：hdchina
种子ID：123456
自动批准时间：2024-01-01 12:00:00
```

### Telegram 集成

使用 Telegram Bot 查询安全状态：

```
/admin safety_status
```

返回示例：
```
🛡️ 安全策略状态报告

🔧 全局设置:
• 安全模式: SAFE
• HR保护: ✅ 启用
• 删除最低分享率: 1.0
• 最少保种时间: 72小时
• HR移动策略: copy

📊 HR案例统计:
• 总案例数: 15
• 活跃案例: 8
• 已完成案例: 7
• 高风险案例: 2

📅 生成时间: 2024-01-01 10:30:00
```

## 故障排除

### 常见问题

#### 1. 下载被误阻止

**问题**：正常的下载被安全策略阻止

**解决方案**：
1. 检查站点 HR 敏感度设置
2. 调整全局安全模式为 BALANCED
3. 为特定订阅设置 `allow_hr: true`

#### 2. 删除操作无法执行

**问题**：无法删除已完成的下载任务

**解决方案**：
1. 检查当前分享率是否达到要求
2. 继续做种直到满足最低分享率
3. 临时调整站点安全策略

#### 3. 文件整理失败

**问题**：文件整理操作被阻止

**解决方案**：
1. 检查文件是否属于 HR 案例
2. 调整 HR 移动策略为 "copy"
3. 等待 HR 案例完成后再整理

#### 4. 通知过多

**问题**：收到过多的安全策略通知

**解决方案**：
1. 调整安全模式为 AGGRESSIVE
2. 在通知设置中关闭安全通知
3. 为信任的站点设置 LOW 敏感度

### 性能优化

#### 1. 安全检查性能

安全策略检查设计为高性能操作：
- 单次评估时间 < 10ms
- 并发评估支持
- 智能缓存机制

#### 2. 数据库优化

- HR 案例索引优化
- 配置数据缓存
- 批量查询支持

### 日志和调试

#### 启用调试模式

在设置中启用调试模式查看详细的安全检查日志：

```yaml
debug_enabled: true
log_level: "DEBUG"
```

#### 日志示例

```
[2024-01-01 10:30:00] DEBUG: SafetyPolicyEngine.evaluate
  - Action: download
  - Site: hdchina
  - HR Case: ACTIVE
  - Decision: REQUIRE_CONFIRM
  - Processing Time: 5.2ms
```

## 最佳实践

### 1. 站点配置建议

#### 高要求站点（如 HDC、TTG）
```yaml
hr_sensitivity: "HIGH"
min_ratio_for_delete: 1.5
min_keep_hours: 168  # 7天
hr_move_strategy: "copy"
```

#### 普通站点（如 HDChina、CHD）
```yaml
hr_sensitivity: "MEDIUM"
min_ratio_for_delete: 1.0
min_keep_hours: 72   # 3天
hr_move_strategy: "copy"
```

#### 宽松站点（如 PTer、OurBits）
```yaml
hr_sensitivity: "LOW"
min_ratio_for_delete: 0.8
min_keep_hours: 48   # 2天
hr_move_strategy: "move"
```

### 2. 订阅管理建议

#### 重要订阅
```yaml
allow_hr: false
auto_approve: false
custom_threshold: 1.2
```

#### 普通订阅
```yaml
allow_hr: true
auto_approve: true
custom_threshold: 1.0
```

### 3. 日常维护

1. **定期检查**：使用 `/admin safety_status` 查看安全状态
2. **及时处理**：及时处理需要确认的操作
3. **监控 HR**：关注活跃 HR 案例的状态
4. **备份配置**：定期备份安全策略配置

## API 参考

### 安全设置 API

#### 获取全局安全设置
```http
GET /api/settings/safety/global
```

#### 更新全局安全设置
```http
POST /api/settings/safety/global
Content-Type: application/json

{
  "mode": "SAFE",
  "hr_protection_enabled": true,
  "min_ratio_for_delete": 1.0,
  "min_keep_hours": 72,
  "hr_move_strategy": "copy",
  "auto_approve_hours": 24
}
```

#### 获取站点安全设置
```http
GET /api/settings/safety/site/{site_key}
```

#### 更新站点安全设置
```http
POST /api/settings/safety/site/{site_key}
Content-Type: application/json

{
  "hr_sensitivity": "HIGH",
  "min_ratio_for_delete": 1.2,
  "enabled": true
}
```

### 安全评估 API

#### 手动安全评估
```http
POST /api/safety/evaluate
Content-Type: application/json

{
  "action": "download",
  "site_key": "hdchina",
  "torrent_id": "123456",
  "trigger": "user_web"
}
```

响应示例：
```json
{
  "success": true,
  "data": {
    "decision": "REQUIRE_CONFIRM",
    "reason_code": "HR_ACTIVE",
    "message": "检测到活跃HR案例，需要用户确认",
    "requires_user_action": true,
    "processing_time_ms": 5.2
  }
}
```

## 版本历史

### v2.0.0 (当前版本)
- ✅ 完整的安全策略引擎
- ✅ 多级配置支持
- ✅ 通知系统集成
- ✅ Telegram Bot 集成
- ✅ 性能优化
- ✅ 完整的测试覆盖

### v1.0.0 (基础版本)
- ✅ 基础 HR 保护
- ✅ 简单配置选项
- ✅ 基本通知功能

## 技术支持

如果您在使用过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查系统日志中的错误信息
3. 使用调试模式获取详细信息
4. 联系技术支持团队

---

**注意**：本功能旨在保护您的站点账号安全，请合理配置安全策略，平衡安全性与便利性。
