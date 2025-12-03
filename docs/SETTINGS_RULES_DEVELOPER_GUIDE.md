# SETTINGS-RULES-1 开发者指南

## 项目概述

**项目名称**: SETTINGS-RULES-1：全局 HR 策略 + 分辨率档位 + 三档模式（含 STRM/移动联动）
**模块位置**: 侧边栏「设定」模块下的 规则 / 订阅 & 下载 分页
**技术栈**: Vue 3 + TypeScript + Vuetify + Python FastAPI
**文档版本**: v1.0

---

## 架构设计

### 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 Vue 3    │    │   后端 API      │    │   数据库        │
│                 │    │                 │    │                 │
│ GlobalRules     │◄──►│ GlobalRule      │◄──►│ global_rules    │
│ Settings.vue    │    │ Settings        │    │ table           │
│                 │    │ Service         │    │                 │
│ - UI组件        │    │ - 验证逻辑      │    │ - 配置持久化    │
│ - 状态管理      │    │ - 业务逻辑      │    │ - 默认配置      │
│ - 交互处理      │    │ - 联动控制      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   搜索服务      │    │   订阅服务      │    │   文件操作服务  │
│                 │    │                 │    │                 │
│ SearchService   │    │ Subscription    │    │ TransferService │
│ - 种子筛选      │    │ Service         │    │ - 移动/复制逻辑 │
│ - 规则应用      │    │ - 自动下载      │    │ - C档降级处理   │
│ - 结果聚合      │    │ - 决策引擎      │    │ - HR保护检查    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件

#### 前端组件
- **GlobalRulesSettings.vue**: 主要设置页面
- **API Services**: 全局规则API调用封装
- **Type Definitions**: TypeScript类型定义

#### 后端服务
- **GlobalRuleSettings**: 数据模型和验证
- **Settings API**: RESTful API端点
- **Rule Engine**: 规则应用和过滤逻辑

#### 数据库
- **global_rules表**: 存储用户配置
- **默认配置**: 三档模式预设值

---

## 三档模式详细说明

### A档：保种安全模式

**目标用户**: 注重保种安全的新手用户
**使用场景**: 
- 刚开始接触PT下载
- 对保种规则不熟悉
- 希望避免H&R风险

**核心特性**:
```javascript
A_SAFE: {
  hr_policy: 'STRICT_SKIP',        // 严格跳过所有HR种子
  resolution_policy: 'MAX_TIER',   // 最高限制1080p
  resolution_tier: 'MID_1080P',    // 默认1080p
  source_quality_policy: 'NO_TRASH', // 禁用低质量源
  hdr_policy: 'SDR_ONLY',          // 只下载SDR版本
  codec_policy: 'ANY',             // 不限制编码
  subtitle_policy: 'ANY',          // 不限制字幕
  audio_lang_policy: 'ANY',        // 不限制音轨
  extra_feature_policy: 'FORBID_3D' // 禁止3D
}
```

**行为限制**:
- 本地整理：只允许复制/硬链接，禁止移动
- 网盘整理：禁止移动上传
- STRM生成：允许

### B档：平衡模式

**目标用户**: 有一定PT经验的普通用户
**使用场景**: 
- 熟悉基本保种规则
- 希望在质量和安全间平衡
- 大部分日常下载需求

**核心特性**:
```javascript
B_BALANCED: {
  hr_policy: 'SAFE_SKIP',          // 安全跳过高风险HR
  resolution_policy: 'AUTO',       // 智能选择分辨率
  resolution_tier: 'HIGH_4K',      // 默认4K
  source_quality_policy: 'NO_TRASH', // 禁用低质量源
  hdr_policy: 'ANY',               // 不限制HDR/SDR
  codec_policy: 'ANY',             // 不限制编码
  subtitle_policy: 'ANY',          // 不限制字幕
  audio_lang_policy: 'ANY',        // 不限制音轨
  extra_feature_policy: 'FORBID_3D' // 禁止3D
}
```

**行为权限**:
- 本地整理：允许移动、复制、硬链接
- 网盘整理：允许移动上传
- STRM生成：允许

### C档：老司机模式

**目标用户**: PT经验丰富的老司机用户
**使用场景**: 
- 深度了解PT规则和保种策略
- 需要获取高质量资源
- 有完善的存储和网络环境

**核心特性**:
```javascript
C_PRO: {
  hr_policy: 'IGNORE',             // 忽略HR限制
  resolution_policy: 'AUTO',       // 智能选择分辨率
  resolution_tier: 'HIGH_4K',      // 默认4K
  source_quality_policy: 'ANY',    // 不限制源质量
  hdr_policy: 'HDR_PREFERRED',     // 优先HDR
  codec_policy: 'ANY',             // 不限制编码
  subtitle_policy: 'ANY',          // 不限制字幕
  audio_lang_policy: 'ANY',        // 不限制音轨
  extra_feature_policy: 'FORBID_3D' // 禁止3D
}
```

**行为限制（关键）**:
- 本地整理：**强制降级**为复制/硬链接，禁止移动删除源文件
- 网盘整理：**强制降级**为复制上传，禁止移动
- STRM生成：允许

---

## C档与STRM/移动联动机制

### 设计原理

C档模式的核心设计理念是**保护种子源文件**，避免因移动操作导致的保种炸雷。通过强制降级移动操作为复制操作，确保源文件始终保留在下载目录。

### 实现机制

#### 1. 前端UI控制
```vue
<!-- C档切换确认对话框 -->
<v-dialog v-model="showCModeDialog" max-width="500" persistent>
  <v-card>
    <v-card-title>切换到「老司机模式」</v-card-title>
    <v-card-text>
      <v-alert type="error" variant="tonal">
        如使用，系统将禁用『网盘移动上传』或『本地移动保存』，
        避免导致保种炸雷，请谨慎使用。
      </v-alert>
    </v-card-text>
  </v-card>
</v-dialog>
```

#### 2. 后端逻辑实现
```python
class TransferService:
    def transfer_file(self, config: FileOperationConfig):
        # C档模式检查
        if self.global_rules.hr_mode == 'C_PRO':
            if config.operation_mode == OperationMode.MOVE:
                # 强制降级为复制
                config.operation_mode = OperationMode.COPY
                logger.warning("C档模式：移动操作已降级为复制")
        
        # 执行文件操作
        return TransferHandler.transfer_file(config)
```

#### 3. 规则应用流程
```
用户选择C档 → 显示确认对话框 → 用户确认 → 保存配置
    ↓
下载任务创建 → 检查全局规则 → 识别C档模式 → 降级移动操作
    ↓
文件操作执行 → 源文件保留 → 保种安全维护
```

### 关键实现点

#### 文件操作降级
```python
def should_degrade_move_operation(self, hr_mode: str) -> bool:
    """
    判断是否需要降级移动操作
    
    Args:
        hr_mode: 当前HR模式
        
    Returns:
        bool: True表示需要降级为复制
    """
    return hr_mode == 'C_PRO'
```

#### 日志记录
```python
def log_operation_degradation(self, original_mode: str, new_mode: str):
    """记录操作降级日志"""
    logger.warning(
        f"文件操作降级: {original_mode} → {new_mode} "
        f"(C档模式保护机制)"
    )
```

---

## 策略选项详细说明

### HR策略选项

| 策略值 | 中文名称 | 行为描述 | 适用场景 |
|--------|----------|----------|----------|
| `IGNORE` | 忽略 | 完全不管HR，显示所有种子 | C档老司机模式 |
| `SAFE_SKIP` | 安全跳过 | 默认跳过H&R/HR等高风险种子 | B档平衡模式 |
| `STRICT_SKIP` | 严格跳过 | 跳过H&R/HR/H3/H5/UNKNOWN等所有HR种子 | A档保种安全模式 |

**实现逻辑**:
```python
def filter_by_hr_policy(self, torrents: List[Torrent], policy: str) -> List[Torrent]:
    """根据HR策略过滤种子"""
    if policy == 'IGNORE':
        return torrents
    
    filtered = []
    high_risk_tags = ['H&R', 'HR', 'H3', 'H5', 'UNKNOWN']
    
    for torrent in torrents:
        if policy == 'SAFE_SKIP':
            # 只过滤最高风险标签
            if not any(tag in torrent.tags for tag in ['H&R', 'HR']):
                filtered.append(torrent)
        elif policy == 'STRICT_SKIP':
            # 过滤所有HR相关标签
            if not any(tag in torrent.tags for tag in high_risk_tags):
                filtered.append(torrent)
    
    return filtered
```

### 分辨率策略选项

| 策略值 | 中文名称 | 行为描述 | 默认档位 |
|--------|----------|----------|----------|
| `AUTO` | 自动选择 | 根据档位和内容类型自动选择合适分辨率 | 档位推荐 |
| `MAX_TIER` | 最高档位 | 只限制最高分辨率，允许低分辨率 | 用户设定 |
| `FIXED_TIER` | 固定档位 | 只选择指定分辨率档位的种子 | 用户设定 |

**分辨率档位定义**:
```python
RESOLUTION_TIERS = {
    'LOW_720P': {
        'max_resolution': '720p',
        'description': '标清720p及以下'
    },
    'MID_1080P': {
        'max_resolution': '1080p', 
        'description': '高清1080p及以下'
    },
    'HIGH_4K': {
        'max_resolution': '4K',
        'description': '超高清4K及以下'
    }
}
```

### 源质量策略选项

| 策略值 | 中文名称 | 行为描述 | 过滤标签 |
|--------|----------|----------|----------|
| `ANY` | 任意 | 不限制源质量 | 无过滤 |
| `NO_TRASH` | 禁用低质 | 禁用CAM/TS/TC等明显低质量源 | CAM, TS, TC |
| `HIGH_ONLY` | 仅高质量 | 只要REMUX/BLURAY/UHD/高码WEB-DL | 保留高质量 |

### HDR策略选项

| 策略值 | 中文名称 | 行为描述 | 适用设备 |
|--------|----------|----------|----------|
| `ANY` | 任意 | 不限制HDR或SDR | 所有设备 |
| `HDR_PREFERRED` | HDR优先 | 优先HDR，但不强制 | HDR设备 |
| `SDR_ONLY` | 仅SDR | 只选择SDR版本 | 老电视/无HDR |

### 编码偏好选项

| 策略值 | 中文名称 | 行为描述 | 推荐场景 |
|--------|----------|----------|----------|
| `ANY` | 任意 | 不限制编码格式 | 兼容性优先 |
| `PREFER_H265` | H265优先 | 优先H265/HEVC编码 | 存储空间有限 |
| `PREFER_H264` | H264优先 | 优先H264/AVC编码 | 兼容性优先 |

### 字幕策略选项

| 策略值 | 中文名称 | 行为描述 | 语言支持 |
|--------|----------|----------|----------|
| `ANY` | 任意 | 不限制字幕 | 所有语言 |
| `REQUIRE_ZH` | 必须中文 | 必须包含中文字幕 | 中文用户 |

### 音轨语言策略选项

| 策略值 | 中文名称 | 行为描述 | 适用场景 |
|--------|----------|----------|----------|
| `ANY` | 任意 | 不限制音轨语言 | 所有场景 |
| `ORIGINAL_PREFERRED` | 原声优先 | 优先原声，接受多语言 | 影音爱好者 |
| `AVOID_MANDARIN_ONLY` | 避开纯国语 | 避免只有国语配音的资源 | 原声偏好者 |

### 3D策略选项

| 策略值 | 中文名称 | 行为描述 | 用户群体 |
|--------|----------|----------|----------|
| `ALLOW_3D` | 允许3D | 包含3D版本 | 3D设备用户 |
| `FORBID_3D` | 禁止3D | 过滤掉所有3D版本 | 大部分用户 |

---

## API接口文档

### 基础信息

- **Base URL**: `/api/settings/rules`
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

### 端点列表

#### 1. 获取全局规则设置

```http
GET /api/settings/rules/global
```

**响应示例**:
```json
{
  "data": {
    "hr_mode": "B_BALANCED",
    "hr_policy": "SAFE_SKIP",
    "resolution_policy": "AUTO",
    "resolution_tier": "HIGH_4K",
    "source_quality_policy": "NO_TRASH",
    "hdr_policy": "ANY",
    "codec_policy": "ANY",
    "subtitle_policy": "ANY",
    "audio_lang_policy": "ANY",
    "extra_feature_policy": "FORBID_3D"
  },
  "message": "获取全局规则设置成功"
}
```

#### 2. 更新全局规则设置

```http
PUT /api/settings/rules/global
```

**请求体**:
```json
{
  "hr_mode": "C_PRO",
  "hr_policy": "IGNORE",
  "resolution_policy": "AUTO",
  "resolution_tier": "HIGH_4K",
  "source_quality_policy": "ANY",
  "hdr_policy": "HDR_PREFERRED",
  "codec_policy": "ANY",
  "subtitle_policy": "ANY",
  "audio_lang_policy": "ANY",
  "extra_feature_policy": "FORBID_3D"
}
```

**响应示例**:
```json
{
  "data": {
    // 同请求体内容
  },
  "message": "全局规则设置更新成功"
}
```

#### 3. 重置全局规则设置

```http
POST /api/settings/rules/global/reset
```

**响应示例**:
```json
{
  "data": {
    "hr_mode": "B_BALANCED",
    // ... 其他默认配置
  },
  "message": "全局规则设置已重置为默认值"
}
```

#### 4. 获取模式配置预设

```http
GET /api/settings/rules/global/mode-profiles
```

**响应示例**:
```json
{
  "data": {
    "A_SAFE": {
      "hr_policy": "STRICT_SKIP",
      "resolution_policy": "MAX_TIER",
      // ... A档完整配置
    },
    "B_BALANCED": {
      "hr_policy": "SAFE_SKIP",
      "resolution_policy": "AUTO",
      // ... B档完整配置
    },
    "C_PRO": {
      "hr_policy": "IGNORE",
      "resolution_policy": "AUTO",
      // ... C档完整配置
    }
  },
  "message": "获取模式配置预设成功"
}
```

---

## 前端集成要点

### 关键组件

#### 1. GlobalRulesSettings.vue
```vue
<template>
  <div class="global-rules-settings">
    <!-- 页面标题 -->
    <PageHeader title="全局下载规则（HR / 画质 / 语言偏好）" />
    
    <!-- 三档模式选择 -->
    <v-card>
      <v-card-title>HR模式选择</v-card-title>
      <!-- C档切换确认对话框 -->
      <v-dialog v-model="showCModeDialog">
        <!-- 确认内容 -->
      </v-dialog>
    </v-card>
    
    <!-- 各种策略设置卡片 -->
    <!-- ... -->
    
    <!-- 操作按钮区域 -->
    <v-card>
      <v-card-text>
        <!-- 底栏提示 -->
        <div class="text-caption">
          上述规则为全局默认设置，个别订阅可在高级规则中覆盖。
        </div>
        <!-- 按钮组 -->
      </v-card-text>
    </v-card>
  </div>
</template>
```

#### 2. 核心JavaScript逻辑
```javascript
// 三档模式默认配置映射
const defaultProfiles = {
  A_SAFE: {
    hr_policy: 'STRICT_SKIP',
    resolution_policy: 'MAX_TIER',
    // ... 完整配置
  },
  B_BALANCED: {
    hr_policy: 'SAFE_SKIP',
    resolution_policy: 'AUTO',
    // ... 完整配置
  },
  C_PRO: {
    hr_policy: 'IGNORE',
    resolution_policy: 'AUTO',
    // ... 完整配置
  }
}

// C档切换处理
const selectHrMode = (mode: string) => {
  if (mode === 'C_PRO' && settings.hr_mode !== 'C_PRO') {
    // 显示确认对话框
    showCModeDialog.value = true
    pendingMode.value = mode
  } else {
    settings.hr_mode = mode
  }
}

// 重置为当前档默认
const resetToCurrentModeDefault = () => {
  const currentMode = settings.hr_mode
  const defaultProfile = defaultProfiles[currentMode]
  Object.assign(settings, defaultProfile)
  settings.hr_mode = currentMode // 保持当前模式
}
```

### API服务封装
```typescript
// services/api/globalRules.ts
export const globalRulesApi = {
  async getGlobalRules(): Promise<ApiResponse<GlobalRuleSettings>> {
    return api.get('/settings/rules/global')
  },
  
  async updateGlobalRules(settings: GlobalRuleSettings): Promise<ApiResponse<GlobalRuleSettings>> {
    return api.put('/settings/rules/global', settings)
  },
  
  async resetGlobalRules(): Promise<ApiResponse<GlobalRuleSettings>> {
    return api.post('/settings/rules/global/reset')
  },
  
  async getModeProfiles(): Promise<ApiResponse<ModeProfiles>> {
    return api.get('/settings/rules/global/mode-profiles')
  }
}
```

---

## 后端实现要点

### 数据模型

```python
# models/global_rules.py
class GlobalRuleSettings(BaseModel):
    hr_mode: HRMode = HRMode.BALANCED
    hr_policy: HRPolicy = HRPolicy.SAFE_SKIP
    resolution_policy: ResolutionPolicy = ResolutionPolicy.AUTO
    resolution_tier: ResolutionTier = ResolutionTier.HIGH_4K
    source_quality_policy: SourceQualityPolicy = SourceQualityPolicy.NO_TRASH
    hdr_policy: HDRPolicy = HDRPolicy.ANY
    codec_policy: CodecPolicy = CodecPolicy.ANY
    subtitle_policy: SubtitlePolicy = SubtitlePolicy.ANY
    audio_lang_policy: AudioLangPolicy = AudioLangPolicy.ANY
    extra_feature_policy: ExtraFeaturePolicy = ExtraFeaturePolicy.FORBID_3D

class HRMode(str, Enum):
    SAFE = "A_SAFE"
    BALANCED = "B_BALANCED"
    PRO = "C_PRO"
```

### 服务层实现

```python
# services/global_rules_service.py
class GlobalRulesService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_settings(self, user_id: int) -> GlobalRuleSettings:
        """获取用户全局规则设置"""
        settings = await self.db.get(GlobalRuleSettings, user_id)
        if not settings:
            # 返回默认设置
            return GlobalRuleSettings()
        return settings
    
    async def update_settings(self, user_id: int, settings: GlobalRuleSettings) -> GlobalRuleSettings:
        """更新用户全局规则设置"""
        existing = await self.db.get(GlobalRuleSettings, user_id)
        if existing:
            # 更新现有设置
            for field, value in settings.dict().items():
                setattr(existing, field, value)
        else:
            # 创建新设置
            settings.user_id = user_id
            self.db.add(settings)
        
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
    
    def apply_rules_to_torrents(self, torrents: List[Torrent], rules: GlobalRuleSettings) -> List[Torrent]:
        """将全局规则应用到种子列表"""
        filtered = torrents
        
        # 应用HR策略
        filtered = self._filter_by_hr_policy(filtered, rules.hr_policy)
        
        # 应用分辨率策略
        filtered = self._filter_by_resolution_policy(filtered, rules.resolution_policy, rules.resolution_tier)
        
        # 应用源质量策略
        filtered = self._filter_by_source_quality(filtered, rules.source_quality_policy)
        
        # 应用其他策略...
        
        return filtered
```

### 文件操作联动

```python
# services/transfer_service.py
class TransferService:
    def __init__(self, global_rules_service: GlobalRulesService):
        self.global_rules_service = global_rules_service
    
    async def transfer_file(self, user_id: int, config: FileOperationConfig) -> TransferResult:
        """执行文件传输操作"""
        # 获取用户全局规则
        rules = await self.global_rules_service.get_settings(user_id)
        
        # C档模式检查
        if rules.hr_mode == HRMode.PRO and config.operation_mode == OperationMode.MOVE:
            # 强制降级为复制
            config.operation_mode = OperationMode.COPY
            logger.warning(f"C档模式：移动操作已降级为复制操作")
        
        # 执行实际传输
        result = await self._execute_transfer(config)
        
        return result
```

---

## 常见问题和注意事项

### 开发注意事项

#### 1. C档模式的安全性
- **必须**确保C档模式下的移动操作被正确降级
- **必须**在UI中显示明确的警告信息
- **必须**记录操作降级的详细日志

#### 2. 规则优先级
- 全局规则是默认设置
- 订阅级别的高级规则可以覆盖全局规则
- 系统级保护规则（如C档降级）具有最高优先级

#### 3. 性能考虑
- 规则过滤应该在数据库层面尽可能优化
- 大量种子的筛选需要考虑分页和缓存
- 配置变更应该实时生效，不需要重启服务

### 常见陷阱

#### 1. C档降级失效
```python
# 错误实现：没有检查C档模式
def transfer_file(self, config):
    return self.execute_move(config)  # 直接执行移动

# 正确实现：检查并降级
def transfer_file(self, config, user_rules):
    if user_rules.hr_mode == 'C_PRO' and config.mode == 'MOVE':
        config.mode = 'COPY'  # 降级
    return self.execute_operation(config)
```

#### 2. 规则覆盖逻辑错误
```python
# 错误实现：全局规则总是覆盖订阅规则
def apply_rules(self, torrent, global_rules, subscription_rules):
    return global_rules.apply(torrent)  # 忽略订阅规则

# 正确实现：订阅规则优先
def apply_rules(self, torrent, global_rules, subscription_rules):
    if subscription_rules.exists():
        return subscription_rules.apply(torrent)
    return global_rules.apply(torrent)
```

#### 3. 类型安全问题
```typescript
// 错误实现：缺少类型检查
function applyMode(mode: string) {
  settings.hr_mode = mode  // 可能传入无效值
}

// 正确实现：使用枚举类型
function applyMode(mode: HRMode) {
  if (Object.values(HRMode).includes(mode)) {
    settings.hr_mode = mode
  } else {
    throw new Error(`Invalid HR mode: ${mode}`)
  }
}
```

### 调试技巧

#### 1. 规则应用日志
```python
logger.info(f"应用全局规则: {rules.dict()}")
logger.info(f"原始种子数量: {len(original_torrents)}")
logger.info(f"过滤后种子数量: {len(filtered_torrents)}")
logger.debug(f"被过滤的种子: {[t.name for t in original_torrents if t not in filtered_torrents]}")
```

#### 2. 前端状态调试
```javascript
// 在开发环境中启用详细日志
if (process.env.NODE_ENV === 'development') {
  console.log('当前全局规则设置:', settings)
  console.log('模式配置预设:', defaultProfiles)
}
```

---

## 测试策略

### 单元测试
- 规则过滤逻辑测试
- 模式切换逻辑测试
- API端点功能测试

### 集成测试
- 前后端API集成测试
- 文件操作联动测试
- 数据库持久化测试

### 端到端测试
- 完整用户操作流程测试
- 不同场景下的行为验证
- 性能和稳定性测试

---

## 维护和扩展

### 添加新策略
1. 在后端添加新的枚举值
2. 更新数据模型
3. 实现过滤逻辑
4. 更新前端UI组件
5. 添加相应的测试用例

### 修改现有策略
1. 评估影响范围
2. 更新相关文档
3. 实现向后兼容
4. 添加迁移脚本
5. 进行全面测试

---

**文档维护**: 本文档应随功能更新及时维护，确保开发团队始终有准确的技术参考。

**最后更新**: 2024年XX月XX日  
**维护人员**: ____________  
**版本**: v1.0
