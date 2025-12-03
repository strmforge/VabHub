# DOWNLOAD-CENTER-UI-2 下载中心小迭代 v2 设计文档

## 项目概述

**一句话目标**: 让下载中心真正变成"只看 VabHub 管的任务 + 自动整理完成就自然退场 + 失败任务便于手动整理"，同时清理掉现有 UI 重复代码和小瑕疵。

**基于版本**: DOWNLOAD-CENTER-UI-1  
**迭代性质**: 小迭代优化，专注于核心使用体验

---

## P0 – 现状巡检结果

### 后端现状分析

#### ✅ 已有能力
1. **API 结构完整**: `/api/downloads/` 提供完整的 CRUD 操作
2. **标签支持**: `DownloadTaskResponse.labels` 字段已存在
3. **过滤机制**: `vabhub_only` 参数已实现（默认 True）
4. **扩展字段**: 支持站点信息、HR 等级、短剧标记等

#### ❌ 缺失能力
1. **管理标识**: 缺少 `is_vabhub_managed` 明确字段
2. **整理状态**: 缺少 `organize_status` 跟踪字段
3. **自动退场**: 没有基于整理状态的过滤逻辑
4. **状态同步**: 与 MediaOrganizer/TransferHistory 状态未对齐

#### 📊 关键数据结构
```python
# 当前 DownloadTaskResponse
class DownloadTaskResponse(BaseModel):
    id: str
    title: str
    status: str
    progress: float
    labels: List[str] = []  # 已有，但需增强
    site_name: Optional[str] = None
    hr_level: Optional[str] = None
    is_short_drama: bool = False
    # ... 其他字段
    
# 需要新增的字段
    is_vabhub_managed: bool = False      # P1 新增
    organize_status: str = "NONE"        # P1 新增
```

### 前端现状分析

#### ✅ 已有能力
1. **Tab 结构**: 5 个 Tab（全部/下载中/排队中/异常/最近完成）
2. **卡片 UI**: 完整的任务卡片展示（进度、站点、HR、标签等）
3. **手动整理**: `ManualTransferDialog.vue` 组件已存在
4. **操作功能**: 暂停/恢复/删除/限速等完整操作

#### ❌ 存在问题
1. **重复代码**: 4 个 Tab 中存在约 250+ 行重复的卡片 UI 模板
2. **组件耦合**: UI 逻辑内联在页面组件中，难以维护
3. **状态展示**: 缺少入库状态的直观展示
4. **过滤固化**: vabhub_only 过滤在后端，前端无控制

#### 🎨 UI 重复代码问题
```vue
<!-- 每个Tab都重复这段代码（约250行） -->
<v-list-item v-for="download in filteredDownloads" :key="download.id">
  <template v-slot:prepend>
    <v-checkbox ... />
  </template>
  <template v-slot:title>
    <!-- 标题和标签展示 -->
    <v-chip v-if="download.site_name" ... />
    <v-chip v-if="download.hr_level" ... />
    <v-chip v-for="label in download.labels" ... />
  </template>
  <template v-slot:subtitle>
    <!-- 进度条和状态 -->
    <v-progress-linear ... />
  </template>
  <template v-slot:append>
    <!-- 操作按钮 -->
    <v-btn @click="handlePauseTask" ... />
  </template>
</v-list-item>
```

---

## P1–P6 实施计划

### P1 – 后端：VabHub 管理任务识别 + 入库状态字段

#### 1.1 标签/管理标记设计
**目标**: 明确标识哪些任务是 VabHub 管理的

**实现方案**:
```python
# config.py 新增配置
VABHUB_TORRENT_LABELS: List[str] = [
    "vabhub",      # VabHub 默认标签
    "moviepilot",  # MoviePilot 兼容
    "auto",        # 自动添加标签
    # 管理员可扩展
]

# DownloadTask 模型新增字段
class DownloadTask(Base):
    # ... 现有字段
    is_vabhub_managed: bool = False      # 新增：是否VabHub管理
    organize_status: str = "NONE"        # 新增：整理状态
    
# 服务层计算逻辑
async def calculate_is_vabhub_managed(self, labels: List[str]) -> bool:
    """根据标签列表判断是否为VabHub管理的任务"""
    if not labels:
        return False
    return any(label.lower() in [l.lower() for l in settings.VABHUB_TORRENT_LABELS] 
               for label in labels)
```

#### 1.2 入库状态字段设计
**目标**: 跟踪任务的整理状态，支持自动退场

**状态机设计**:
```
NONE → AUTO_OK → (从工作视图消失)
     → AUTO_FAILED → MANUAL_PENDING → MANUAL_DONE → (从工作视图消失)
     → MANUAL_PENDING → MANUAL_DONE → (从工作视图消失)
```

**字段定义**:
```python
class OrganizeStatus(str, Enum):
    NONE = "NONE"                    # 未开始整理
    AUTO_OK = "AUTO_OK"              # 自动整理成功
    AUTO_FAILED = "AUTO_FAILED"      # 自动整理失败
    MANUAL_PENDING = "MANUAL_PENDING" # 等待手动整理
    MANUAL_DONE = "MANUAL_DONE"      # 手动整理完成
```

#### 1.3 默认过滤策略
**服务层修改**:
```python
async def list_downloads(
    self, 
    status: Optional[str] = None,
    vabhub_only: bool = True,        # 保持现有默认值
    hide_organized: bool = True      # P3 新增：隐藏已整理任务
) -> List[dict]:
    query = select(DownloadTask)
    
    # VabHub 任务过滤
    if vabhub_only:
        query = query.where(DownloadTask.is_vabhub_managed == True)
    
    # 自动退场过滤（P3）
    if hide_organized:
        query = query.where(
            DownloadTask.organize_status.notin_(["AUTO_OK", "MANUAL_DONE"])
        )
    
    # ... 其他过滤逻辑
```

### P2 – 前端：抽出 DownloadTaskCard 组件 + 接入新字段

#### 2.1 组件设计
**新建组件**: `frontend/src/components/download/DownloadTaskCard.vue`

**Props 设计**:
```typescript
interface DownloadTaskCardProps {
  task: DownloadTask              // 任务数据
  selected?: boolean              // 是否选中
  showSelection?: boolean         // 是否显示选择框
  compact?: boolean               // 紧凑模式
  onOpenOrganize?: (taskId: string) => void    // 手动整理回调
  onToggleSelection?: (taskId: string) => void // 选择回调
  onPause?: (taskId: string) => void           // 暂停回调
  onResume?: (taskId: string) => void          // 恢复回调
  onDelete?: (taskId: string) => void          // 删除回调
  onSpeedLimit?: (task: DownloadTask) => void  // 限速回调
}
```

#### 2.2 卡片内容增强
**新增展示信息**:
```vue
<template>
  <v-list-item class="download-task-card">
    <!-- 现有内容：标题、进度、操作按钮 -->
    
    <!-- P2 新增：VabHub 管理标识 -->
    <v-chip 
      v-if="task.is_vabhub_managed" 
      size="x-small" 
      color="primary" 
      variant="tonal"
    >
      <v-icon start size="12">mdi-check-circle</v-icon>
      VabHub
    </v-chip>
    
    <!-- P2 新增：入库状态 -->
    <v-chip 
      :color="getOrganizeStatusColor(task.organize_status)"
      :variant="task.organize_status === 'AUTO_OK' ? 'flat' : 'tonal'"
      size="x-small"
    >
      <v-icon start size="12">{{ getOrganizeStatusIcon(task.organize_status) }}</v-icon>
      {{ getOrganizeStatusText(task.organize_status) }}
    </v-chip>
    
    <!-- P2 新增：手动整理按钮（按需显示） -->
    <v-btn 
      v-if="showManualOrganizeButton(task)"
      size="small" 
      color="warning"
      @click="$emit('openOrganize', task.id)"
    >
      <v-icon start>mdi-folder-move</v-icon>
      手动整理
    </v-btn>
  </v-list-item>
</template>
```

#### 2.3 Tab 重构
**重构前后对比**:
```vue
<!-- 重构前：每个Tab 250+ 行重复代码 -->
<v-window-item value="downloading">
  <v-list>
    <v-list-item v-for="download in downloads" :key="download.id">
      <!-- 250行内联模板 -->
    </v-list-item>
  </v-list>
</v-window-item>

<!-- 重构后：每个Tab 10行代码 -->
<v-window-item value="downloading">
  <v-list>
    <DownloadTaskCard
      v-for="download in downloads"
      :key="download.id"
      :task="download"
      :selected="selectedDownloads.includes(download.id)"
      @openOrganize="handleOpenOrganize"
      @toggleSelection="toggleSelection"
      @pause="handlePauseTask"
      @resume="handleResumeTask"
      @delete="handleDeleteTask"
      @speedLimit="handleSpeedLimit"
    />
  </v-list>
</v-window-item>
```

### P3 – 过滤 & 展示逻辑：只看"自己人" + 自动退场规则

#### 3.1 只看 VabHub 管理任务
**前端实现**:
```vue
<!-- Downloads.vue 顶部提示 -->
<v-alert type="info" variant="tonal" class="mb-4">
  <v-icon start>mdi-information</v-icon>
  仅显示打上 VabHub 标签的下载任务，刷流/无标签任务不会出现在此处。
  需要纳入管理的任务，可在下载器中手动添加标签。
</v-alert>

<script setup>
// API 调用保持 vabhub_only=true（后端默认值）
const { data } = await downloadApi.getDownloads({
  status: activeTab.value,
  vabhub_only: true,    // 硬编码为 true，不提供开关
  hide_organized: true  // P3 新增：自动退场
})
</script>
```

#### 3.2 自动退场逻辑
**实现策略**:
1. **工作视图过滤**: 默认不显示 `organize_status = AUTO_OK/MANUAL_DONE` 的任务
2. **最近完成 Tab**: 显示所有完成的任务（无论整理状态），但限制时间范围
3. **状态更新**: 整理完成后更新 `organize_status`，前端自动隐藏

```python
# 后端 API 参数扩展
@router.get("/", response_model=BaseResponse)
async def list_downloads(
    status: Optional[str] = Query(None),
    vabhub_only: bool = Query(True),           # 现有
    hide_organized: bool = Query(True),        # P3 新增
    recent_hours: int = Query(24),             # P3 新增：最近完成时间范围
    db = Depends(get_db)
):
```

#### 3.3 失败任务处理
**手动整理触发条件**:
```typescript
// 前端判断逻辑
function showManualOrganizeButton(task: DownloadTask): boolean {
  return task.organize_status === 'AUTO_FAILED' || 
         task.organize_status === 'MANUAL_PENDING'
}

// 整理状态颜色和图标
function getOrganizeStatusColor(status: string): string {
  switch (status) {
    case 'AUTO_OK': return 'success'
    case 'AUTO_FAILED': return 'error'
    case 'MANUAL_PENDING': return 'warning'
    case 'MANUAL_DONE': return 'success'
    default: return 'grey'
  }
}
```

### P4 – 小增强：存储位置、媒体库状态 & 文档

#### 4.1 存储位置展示
**利用现有字段**:
```vue
<!-- DownloadTaskCard 新增存储信息 -->
<div class="storage-info text-caption text-medium-emphasis">
  <v-icon size="12" class="mr-1">mdi-harddisk</v-icon>
  存储：{{ getStorageTypeText(task.dest_storage) }}
  <span v-if="task.save_path">
    · {{ task.save_path }}
  </span>
</div>
```

#### 4.2 媒体库状态（可选）
**如果数据链路完善**:
```vue
<!-- 已入库标记 -->
<v-chip 
  v-if="task.library_id"
  size="x-small" 
  color="success"
  @click="navigateToLibrary(task.library_id)"
>
  <v-icon start size="12">mdi-check-all</v-icon>
  已入库
</v-chip>
```

### P5 – QA 验收场景

#### 5.1 核心场景
1. **正常流程**: 订阅 → 下载 → 自动整理成功 → 任务退场
2. **失败处理**: 自动整理失败 → 显示手动整理按钮 → 手动整理成功 → 任务退场
3. **刷流隔离**: 无标签任务 → 不出现在下载中心
4. **标签管理**: 手动添加标签 → 任务出现在下载中心

#### 5.2 边界场景
1. **标签配置修改**: 管理员修改白名单后的过滤变化
2. **状态回退**: 已整理任务的状态查询和显示
3. **并发处理**: 多个任务同时整理的状态更新

### P6 – 总结报告

#### 6.1 预期成果
1. **代码质量**: 消除 250+ 行重复 UI 代码
2. **用户体验**: 专注核心任务，自动退场减少干扰
3. **维护性**: 组件化设计，便于后续扩展
4. **功能完整**: 完整的手动整理工作流

#### 6.2 对用户习惯的影响
1. **专注性提升**: 只看 VabHub 管理的任务，刷流不干扰
2. **界面清爽**: 已完成任务自动退场，减少视觉噪音
3. **操作便利**: 失败任务有明确的手动整理入口

---

## 技术实现要点

### 数据库迁移
```sql
-- P1 需要的数据库迁移
ALTER TABLE download_tasks 
ADD COLUMN is_vabhub_managed BOOLEAN DEFAULT FALSE,
ADD COLUMN organize_status VARCHAR(20) DEFAULT 'NONE';

-- 创建索引优化查询
CREATE INDEX idx_download_tasks_vabhub_managed ON download_tasks(is_vabhub_managed);
CREATE INDEX idx_download_tasks_organize_status ON download_tasks(organize_status);
```

### 配置管理
```python
# config.py 新增
VABHUB_TORRENT_LABELS: List[str] = [
    "vabhub",
    "moviepilot", 
    "auto"
]
```

### 类型定义
```typescript
// frontend/src/types/download.ts
export interface DownloadTask {
  // 现有字段
  id: string
  title: string
  status: string
  labels: string[]
  
  // P1 新增字段
  is_vabhub_managed: boolean
  organize_status: 'NONE' | 'AUTO_OK' | 'AUTO_FAILED' | 'MANUAL_PENDING' | 'MANUAL_DONE'
  
  // P4 增强字段
  dest_storage?: string
  library_id?: number
}
```

---

## 风险评估

### 技术风险
- **数据库迁移**: 需要谨慎处理现有数据
- **状态同步**: 与 MediaOrganizer 的状态对齐复杂度
- **性能影响**: 新增字段和索引的查询性能

### 用户体验风险
- **习惯改变**: 用户可能需要适应新的过滤逻辑
- **功能缺失**: 移除"查看全部任务"可能影响调试

### 缓解措施
- **渐进式部署**: 分阶段启用新功能
- **回退机制**: 保留配置开关支持旧行为
- **文档完善**: 提供详细的迁移和使用指南

---

**文档版本**: v1.0  
**创建时间**: 2025-11-28  
**预计实施周期**: 2-3 天
