# FRONTEND-DOWNLOADS-SPEEDLIMIT-1：下载限速弹窗组件 & Docker 构建修复

## 任务背景

GitHub Actions / Docker 构建阶段前端 `pnpm run build` 报错：
```
Vite 报错：Could not load /app/frontend/src/components/downloads/SpeedLimitDialog.vue
引用来源：src/pages/Downloads.vue?vue&type=script&setup=true&lang.ts
```

## 问题根因分析 (P0)

### 调查结果

通过 `git check-ignore -v` 命令发现：
```bash
$ git check-ignore -v frontend/src/components/downloads/SpeedLimitDialog.vue
.gitignore:13:downloads/        frontend/src/components/downloads/SpeedLimitDialog.vue
```

**根本原因**：`.gitignore` 第 13 行的 `downloads/` 规则（来自 Python distutils 标准模板）过于宽泛，意外匹配了：
- `frontend/src/components/downloads/` 目录
- 导致该目录下的所有组件文件不被 Git 跟踪
- Docker 构建时从 Git clone 的代码中缺失这些文件

### 受影响文件

```
frontend/src/components/downloads/
├── DownloadList.vue          # 下载列表组件
├── DownloadProgressCard.vue  # 下载进度卡片组件
└── SpeedLimitDialog.vue      # 速度限制对话框组件（完整实现）
```

## 修复方案 (P1)

### 修改 .gitignore

将第 13 行：
```gitignore
downloads/
```

修改为：
```gitignore
/downloads/
```

添加前导斜杠使规则只匹配根目录下的 `downloads/` 文件夹，而不会匹配子目录中的同名文件夹。

### 验证

修复后验证：
```bash
$ git check-ignore -v frontend/src/components/downloads/SpeedLimitDialog.vue
# 退出码 1，表示文件不再被忽略
```

## 组件分析 (P2-P3)

### SpeedLimitDialog.vue 已完整实现

组件已存在且功能完整，包含：

**Props**：
- `modelValue: boolean` - 控制显隐
- `taskId?: string | null` - 单任务 ID
- `taskIds?: string[]` - 批量任务 ID 列表
- `downloader?: string` - 下载器名称（全局限速）
- `currentDownloadLimit?: number | null` - 当前下载限速
- `currentUploadLimit?: number | null` - 当前上传限速

**Emits**：
- `update:modelValue` - 更新显隐状态
- `saved` - 保存成功回调

**功能支持**：
1. 单任务限速设置
2. 批量任务限速设置
3. 全局下载器限速设置

### Downloads.vue 集成

`Downloads.vue` 已正确集成 `SpeedLimitDialog`：
- 导入路径：`@/components/downloads/SpeedLimitDialog.vue`
- 支持单任务限速 (`handleSpeedLimit`)
- 支持批量限速 (`handleBatchSpeedLimit`)

## 构建验证 (P4-P5)

### 类型检查
```bash
$ pnpm vue-tsc --noEmit
# 通过
```

### 前端构建
```bash
$ pnpm run build
# ✓ built in 8.58s
```

### Docker 构建

修复 `.gitignore` 后，需要将 `frontend/src/components/downloads/` 添加到 Git 跟踪：
```bash
git add frontend/src/components/downloads/
git commit -m "fix: 修复 .gitignore 规则，恢复 downloads 组件跟踪"
```

## 经验总结

1. **gitignore 规则要具体**：通用的目录名（如 `downloads/`、`build/`）应使用绝对路径 `/downloads/` 或更具体的路径模式
2. **Docker 构建失败要追根溯源**：看似"文件缺失"的问题可能是 gitignore 配置问题
3. **组件目录命名注意**：避免使用与常见 Python/Node 目录重名的名称，或确保 gitignore 规则不会误伤

## 后续扩展点

- [ ] 支持按分类限速（电影/剧集/短剧等）
- [ ] 实时显示当前下载速度辅助设置
- [ ] 限速预设模板（如：白天限速、夜间全速）

---

**完成日期**：2025-12-06
**影响范围**：前端构建、Docker 多阶段构建
**风险等级**：低（仅配置修改）
