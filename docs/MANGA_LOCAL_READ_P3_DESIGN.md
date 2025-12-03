# Manga Local Read P3 - Reading Core Integration 设计文档

## 📋 项目概述

**目标**: 将本地漫画阅读进度完全接入 Reading 中心系统，实现与远程漫画统一的进度管理体验。

**现状**: Reading 核心基础设施已基本完善，需要修复集成问题并确保各端点正确支持本地漫画。

---

## 🔍 P0 - 现状巡检：Reading 核心技术债务分析

### 后端现状

#### ✅ 已完善的部分
1. **ReadingMediaType 枚举**: 已支持 `MANGA = "MANGA"`
2. **MangaReadingProgress 模型**: 完整的进度数据结构
   ```python
   class MangaReadingProgress(Base):
       user_id: int
       series_id: int  # 引用 manga_series_local.id
       chapter_id: int  # 引用 manga_chapter_local.id
       last_page_index: int  # 从 1 开始
       total_pages: int
       is_finished: bool
       last_read_at: datetime
   ```

3. **ReadingHubService**: 已完整集成漫画进度
   - 正确查询本地漫画进度
   - 生成进度标签: "第 X 话 · 第 Y 页"
   - 支持 ongoing/history/activity 列表

4. **进度 API**: `/api/manga/local/progress` 已实现
   - GET/POST `/series/{series_id}` - 进度管理
   - GET `/history` - 阅读历史

#### ❌ 发现的问题

1. **路由名称错误**: ReadingHubService 中漫画条目使用 `route_name="NovelReader"`
   - **影响**: 前端"继续阅读"按钮跳转错误
   - **修复**: 改为 `route_name="MangaReader"`

2. **TG 枚举支持**: 需要确认 TG 命令是否支持 `ReadingMediaType.MANGA`
   - **风险**: TG 可能无法识别本地漫画类型
   - **验证**: 检查 TG commands/reading.py 实现

3. **URL Builder**: TG 链接构造可能不支持 `/manga/read/` 路径
   - **风险**: TG "继续阅读"链接可能错误
   - **验证**: 检查 TG URL 构造逻辑

### 前端现状

#### ✅ 已有基础
- MangaReaderPage.vue 存在进度保存逻辑
- 阅读中心页面已支持混合媒体类型显示

#### ❌ 集成缺口
- MangaReaderPage 可能未调用进度 API
- 进度恢复逻辑可能缺失

### 本次 P3 修复范围

**只修复关键集成问题，不重构现有架构**:

1. ✅ **后端路由修复**: 修正 ReadingHubService 中的 route_name
2. ✅ **MangaReaderPage 接线**: 确保调用现有进度 API
3. ✅ **进度恢复实现**: 添加从 Reading 中心恢复进度的逻辑
4. ✅ **TG 命令验证**: 确保 TG 支持 MANGA 类型
5. ✅ **URL Builder 修复**: 确保 TG 链接正确指向本地漫画阅读器

**不修改的内容**:
- 不添加新的 media_type (复用现有 MANGA)
- 不修改 MangaReadingProgress 模型结构
- 不重构 ReadingHubService 核心逻辑

---

## 🎯 P1 - 后端：稳定的本地漫画阅读身份

### Media Type 策略

**决策**: 沿用 `media_type="MANGA"`，通过 `series_id` 范围区分本地/远程

```python
# 本地漫画: series_id 引用 manga_series_local.id
# 远程漫画: series_id 引用 manga_series_remote.id (如果存在)
ReadingMediaType.MANGA  # 统一类型，不区分来源
```

### 进度 Payload 结构

**复用现有结构，无需修改**:
```python
# MangaReadingProgressUpdate Schema (已存在)
{
    "series_id": 123,      # 本地系列 ID
    "chapter_id": 456,     # 当前章节 ID  
    "last_page_index": 10, # 当前页码 (从1开始)
    "total_pages": 30,     # 章节总页数
    "is_finished": false   # 是否读完
}
```

### 统一更新接口

**现有 API 已满足需求**:
```python
POST /api/manga/local/progress/series/{series_id}
# 调用 manga_progress_service.upsert_progress()
# 内部已集成 ReadingHubService 逻辑
```

### ReadingHubService 修复

**关键修复**: route_name 错误
```python
# 当前 (错误)
route_name="NovelReader"

# 修复后
route_name="MangaReader"
route_params={"seriesId": series.id, "chapterId": progress.chapter_id}
```

---

## 🔌 P2 - MangaReaderPage 接线 + 进度恢复

### 进度保存集成

**在现有翻页逻辑中添加 API 调用**:
```vue
<!-- MangaReaderPage.vue -->
<script setup>
import { mangaLocalApi } from '@/api/manga-local'

// 现有的翻页监听器
watch(currentPageIndex, async (newIndex) => {
  // 添加进度保存
  if (currentSeriesId && currentChapterId) {
    try {
      await mangaLocalApi.updateProgress(currentSeriesId, {
        series_id: currentSeriesId,
        chapter_id: currentChapterId,
        last_page_index: newIndex + 1, // 转换为1基索引
        total_pages: totalPages,
        is_finished: newIndex + 1 >= totalPages
      })
    } catch (error) {
      console.warn('进度保存失败:', error)
      // 不阻塞阅读体验
    }
  }
})

// 章节切换时保存进度
watch(currentChapterId, async (newChapterId) => {
  if (newChapterId && currentSeriesId) {
    try {
      await mangaLocalApi.updateProgress(currentSeriesId, {
        series_id: currentSeriesId,
        chapter_id: newChapterId,
        last_page_index: 1, // 新章节从第1页开始
        total_pages: totalPages,
        is_finished: false
      })
    } catch (error) {
      console.warn('章节进度保存失败:', error)
    }
  }
})
</script>
```

### 进度恢复实现

**页面加载时恢复上次阅读位置**:
```vue
<script setup>
// 新增进度恢复逻辑
const restoreReadingProgress = async () => {
  if (!currentSeriesId) return
  
  try {
    const response = await mangaLocalApi.getProgress(currentSeriesId)
    const progress = response.data
    
    if (progress && progress.chapter_id) {
      // 验证章节是否存在
      const targetChapter = readyChapters.value.find(
        ch => ch.id === progress.chapter_id
      )
      
      if (targetChapter) {
        // 跳转到上次阅读的章节
        await router.replace({
          name: 'MangaReader',
          params: { 
            seriesId: currentSeriesId, 
            chapterId: progress.chapter_id 
          },
          query: { 
            page: progress.last_page_index 
          }
        })
      } else {
        // 章节不存在，跳转到第1话
        const firstChapter = readyChapters.value[0]
        if (firstChapter) {
          await router.replace({
            name: 'MangaReader',
            params: { 
              seriesId: currentSeriesId, 
              chapterId: firstChapter.id 
            }
          })
        }
      }
    }
  } catch (error) {
    console.warn('进度恢复失败:', error)
    // 失败时继续使用默认逻辑
  }
}

// 在 onMounted 中调用
onMounted(async () => {
  await loadSeriesDetail()
  await restoreReadingProgress() // 新增
})
</script>
```

### 异常处理策略

**确保进度 API 故障不影响阅读**:
- API 调用失败时仅在 console 记录
- 不显示错误提示避免干扰用户
- 进度恢复失败时使用默认章节

---

## 🌐 P3 - Web 阅读中心集成

### 后端 ReadingHubService 验证

**确认现有实现正确性**:
```python
# ReadingHubService.list_ongoing_reading() - 已正确实现
# ✅ 正确查询本地漫画进度
# ✅ 正确生成进度标签
# ❌ route_name 需要修复 (已在 P1 解决)
```

### 前端阅读中心适配

**确保本地漫画正确显示**:
```vue
<!-- 阅读中心混合视图 -->
<template v-if="item.media_type === 'MANGA'">
  <div class="media-tag">漫画 · 本地</div>
  <h3>{{ item.title }}</h3>
  <p class="progress">{{ item.progress_label }}</p>
  <button @click="continueReading(item)">继续阅读</button>
</template>

<script setup>
const continueReading = (item) => {
  if (item.route_name === 'MangaReader') {
    router.push({
      name: 'MangaReader',
      params: {
        seriesId: item.route_params.seriesId,
        chapterId: item.route_params.chapterId
      }
    })
  }
}
</script>
```

### 资源缺失处理

**本地漫画被删除时的容错**:
```vue
<script setup>
// 在 MangaReaderPage.vue 中
const validateChapterExists = async (chapterId) => {
  try {
    await mangaLocalApi.getChapterPages(chapterId)
    return true
  } catch (error) {
    console.warn('章节不存在:', error)
    return false
  }
}

// 进度恢复时验证
if (await validateChapterExists(progress.chapter_id)) {
  // 章节存在，正常跳转
} else {
  // 章节不存在，显示提示或跳转第1话
  showWarning('上次阅读的章节已被删除，将从第1话开始')
}
</script>
```

---

## 📱 P4 - TG 侧补完

### TG 命令验证

**检查现有 TG 实现**:
```python
# backend/app/modules/bots/commands/reading.py
# 需要验证:
# 1. /reading_manga 是否包含本地漫画
# 2. ReadingMediaType.MANGA 是否被正确处理
# 3. URL builder 是否支持 /manga/read/ 路径
```

### 本地漫画标识

**在 TG 显示中区分来源**:
```python
# 通过 series_id 范围或 source 信息判断
if is_local_manga(series_id):
    display_text = f"[M] 本地漫画：{title}"
else:
    display_text = f"[M] {title}"
```

### URL Builder 修复

**确保 TG 链接正确**:
```python
def build_manga_reading_url(series_id, chapter_id, page_index=None):
    base_url = f"{WEB_BASE_URL}/manga/read/{series_id}/{chapter_id}"
    if page_index and page_index > 1:
        return f"{base_url}?page={page_index}"
    return base_url
```

---

## 🧪 P5 - QA 测试场景

### 场景 A: 单设备续读
1. 在 Web MangaReader 打开本地漫画，翻页到第5话第10页
2. 返回阅读中心，检查"正在阅读"列表
3. 确认显示: "《漫画名》第5话 · 第10页"
4. 点击"继续阅读"，验证跳转到正确位置

### 场景 B: 跨入口续读  
1. 在漫画中心打开本地漫画，阅读几页
2. 使用 TG /reading_recent 命令
3. 确认列表包含本地漫画记录
4. 使用 /reading_open <index>，验证浏览器打开正确位置

### 场景 C: 删除后容错
1. 人为删除某章节的本地文件
2. 从阅读中心打开该漫画
3. 验证不崩溃，显示"资源缺失"提示
4. 确认能跳转到其他可用章节

---

## 📝 P6 - 文档更新

### 完成状态说明

**在 Phase 2 完成报告中添加**:
```markdown
## P3 功能补完状态

### 已完成集成
- ✅ ReadingHubService 路由修复
- ✅ MangaReaderPage 进度 API 集成  
- ✅ 进度恢复逻辑实现
- ✅ Web 阅读中心本地漫画支持
- ✅ TG 命令本地漫画识别

### 技术实现
- 复用现有 MANGA media_type，通过 series_id 区分来源
- 利用现有 MangaReadingProgress 模型和 API
- 最小化修改，专注集成问题修复

### 用户体验
- 本地漫画完全融入 Reading 中心生态系统
- 进度在 Web 和 TG 端统一显示和管理
- 跨设备无缝续读体验
```

---

## 🎯 成功指标

### 功能完整性
- ✅ 本地漫画进度正确保存到 Reading 系统
- ✅ 阅读中心显示本地漫画"正在阅读"记录  
- ✅ TG 命令支持本地漫画查看和打开
- ✅ 跨设备进度同步正常工作

### 用户体验
- 🎯 "继续阅读"按钮正确跳转到本地漫画
- 🎯 进度标签准确显示"第 X 话 · 第 Y 页"
- 🎯 资源删除时有友好提示，不崩溃
- 🎯 TG 链接能正确打开 Web 阅读器

---

**文档版本**: 1.0  
**设计日期**: 2024年当前日期  
**预计工期**: 1-2天  
**实施策略**: 最小化修改，专注集成修复
