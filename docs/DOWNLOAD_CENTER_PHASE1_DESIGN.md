# 下载中心 UI v1 设计文档

## 现状分析

### 后端 API 能力

**现有接口**: `GET /download`

**查询参数**:
- `status`: 状态过滤 (downloading, completed, paused, error)
- `vabhub_only`: 只显示 VabHub 标签任务 (默认 true)
- `page`, `page_size`: 分页参数

**返回字段**:
```json
{
  "id": "string",
  "title": "string", 
  "status": "string",
  "progress": "float",
  "size_gb": "float",
  "downloaded_gb": "float",
  "speed_mbps": "float",
  "eta": "int",
  "media_type": "string",
  "extra_metadata": "object",
  "created_at": "datetime",
  "intel_hr_status": "string",  // Local Intel: SAFE/RISK/ACTIVE/UNKNOWN
  "intel_site_status": "string"  // Local Intel: OK/THROTTLED/ERROR/UNKNOWN
}
```

**数据来源**:
- 基础信息: `DownloadTask` 数据库模型
- 站点信息: `extra_metadata.site_id`
- HR 状态: Local Intel 集成查询
- 短剧标记: `media_type == 'short_drama'`

### 前端现状

**页面结构**: `Downloads.vue`
- ✅ 统计卡片 (正在下载、已暂停、已完成、总速度)
- ✅ 基础 Tab 切换
- ✅ 搜索功能
- ❌ 显示所有状态，包括历史完成记录

**组件结构**:
- `DownloadList.vue`: 任务列表容器
- `DownloadProgressCard.vue`: 单个任务卡片
- `SpeedLimitDialog.vue`: 限速设置对话框

## v1 设计约束

### 核心原则
1. **队列视角**: 下载中心专注于当前活动任务，不做历史坟场
2. **VabHub 专属**: 只显示 VabHub 管理的任务，不提供关闭选项
3. **信息优势**: 充分利用 HR 标记、站点信息、短剧标记等优势数据
4. **流程分离**: 完成任务的后续处理交给「媒体整理」页面

### 功能边界
- ✅ **包含**: 当前下载队列 (下载中/排队/暂停/出错)
- ✅ **包含**: 最近完成的少量任务 (20条，带跳转)
- ❌ **不包含**: 长期完成历史记录
- ❌ **不包含**: 非 VabHub 标签的刷流任务

### 状态定义
- `downloading`: 正在下 (有速度)
- `queued`: 等待中 / 检验中 / 准备中
- `paused`: 用户手动暂停
- `error`: tracker error / stalled / 下载器报错
- `completed`: 仅用于"刚完成"过渡状态

## 实施计划

### P1 - 后端增强
1. 扩展 `DownloadTaskResponse` 模型
2. 添加站点名称查询逻辑
3. 实现 HR 等级映射
4. 调整状态过滤行为

### P2 - 前端重构
1. 重新设计 Tab 结构
2. 优化统计卡片
3. 移除历史完成堆积
4. 永久隐藏"显示所有任务"选项

### P3 - 卡片 UI 强化
1. 信息层次优化
2. HR 标记显示
3. 站点信息突出
4. 响应式适配

### P4 - 流程串联
1. 下载中心 → 媒体整理跳转
2. 媒体整理 → 媒体详情跳转
3. 可选: 下载中心 → 媒体详情直接跳转

## VabHub 下载中心特色

| 功能 | VabHub v1 特点 |
|------|----------------|
| 任务范围 | 仅 VabHub 标签任务，避免干扰刷流任务 |
| 历史记录 | 整理后转移到媒体整理页，保持界面清爽 |
| HR 信息 | 详细等级 + 风险提示，辅助 HR 决策 |
| 站点信息 | 突出显示 + 过滤，快速定位来源 |
| 短剧标记 | 专门标识，方便短剧管理 |
| 流程串联 | 与媒体整理深度整合，闭环体验 |

## 技术要点

### 数据流
```
下载器 API → DownloadService → Local Intel → 响应模型 → 前端组件
```

### 关键字段映射
- `site_name`: `extra_metadata.site_id` → 站点配置查询
- `hr_level`: `intel_hr_status` → HR 等级映射函数
- `is_short_drama`: `media_type === 'short_drama'`
- `labels`: 下载器标签 + VabHub 标签

### 性能考虑
- 批量查询站点信息避免 N+1
- Local Intel 状态缓存复用
- 前端虚拟滚动处理大量任务

---

*设计文档版本: v1.0*  
*最后更新: 2025-11-28*
