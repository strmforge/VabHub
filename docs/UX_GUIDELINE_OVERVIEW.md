# UX 组件指南

> UX-1 + UX-2 实现文档

## 概念

统一 UI 风格组件库，提供可复用的通用组件，确保整个应用的视觉一致性。

## 主题系统 (U1/U2)

### 主题配置文件

`frontend/src/styles/theme.ts` 定义了：
- 主色调、辅色
- 媒体类型专用色
- 圆角、阴影等样式变量
- Vuetify light/dark 主题配置

### 主题切换

通过 `useAppStore` 提供主题切换功能：

```typescript
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

// 切换主题
appStore.toggleTheme()

// 设置主题
appStore.setTheme('dark')

// 获取当前主题
const isDark = appStore.isDark
```

主题会自动持久化到 `localStorage`。

## 图标规范 (U5-1)

### 媒体类型图标

| 类型 | 图标 | 颜色 |
|------|------|------|
| 小说/电子书 | `mdi-book-open-page-variant` | 蓝色 #1976D2 |
| 有声书 | `mdi-headphones` | 紫色 #9C27B0 |
| 漫画 | `mdi-book-open-variant` | 橙色 #FF9800 |
| 音乐 | `mdi-music` | 绿色 #4CAF50 |
| 电影 | `mdi-movie` | 红色 #F44336 |
| 剧集 | `mdi-television` | 青色 #00BCD4 |

### 操作图标

| 操作 | 图标 |
|------|------|
| 播放 | `mdi-play` |
| 暂停 | `mdi-pause` |
| 收藏 | `mdi-heart` / `mdi-heart-outline` |
| 设置 | `mdi-cog` |
| 刷新 | `mdi-refresh` |
| 搜索 | `mdi-magnify` |

## 通用组件

### EmptyState

空状态组件，用于列表为空时的友好提示。

```vue
<EmptyState
  icon="mdi-book-open-blank-variant"
  title="暂无数据"
  description="这里还没有内容"
  action-text="去添加"
  @action="handleAdd"
/>
```

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| icon | string | `mdi-folder-open-outline` | 图标名称 |
| iconSize | number/string | 64 | 图标大小 |
| iconColor | string | `grey-lighten-1` | 图标颜色 |
| title | string | - | 标题（必填） |
| description | string | - | 描述文字 |
| actionText | string | - | 操作按钮文字 |
| actionColor | string | `primary` | 操作按钮颜色 |

#### Events

| 事件 | 说明 |
|------|------|
| action | 点击操作按钮时触发 |

### SectionCard

区块卡片组件，用于包装内容区域。

```vue
<SectionCard
  title="区块标题"
  subtitle="区块描述"
  icon="mdi-cog"
>
  <template #actions>
    <v-btn>操作</v-btn>
  </template>
  内容区域
</SectionCard>
```

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | string | - | 标题 |
| subtitle | string | - | 副标题 |
| icon | string | - | 标题图标 |
| iconColor | string | `primary` | 图标颜色 |
| rounded | string | `lg` | 圆角大小 |
| noPadding | boolean | false | 是否去除内边距 |

#### Slots

| 插槽 | 说明 |
|------|------|
| default | 内容区域 |
| title | 自定义标题 |
| subtitle | 自定义副标题 |
| actions | 标题栏右侧操作区 |

### FilterToolbar

过滤工具栏组件，用于列表页面的过滤控件。

```vue
<FilterToolbar @reset="handleReset">
  <v-col cols="3">
    <v-select v-model="filter1" :items="options1" />
  </v-col>
  <v-col cols="3">
    <v-select v-model="filter2" :items="options2" />
  </v-col>
</FilterToolbar>
```

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| showActions | boolean | true | 是否显示操作按钮 |
| showReset | boolean | true | 是否显示重置按钮 |
| showApply | boolean | false | 是否显示应用按钮 |

#### Events

| 事件 | 说明 |
|------|------|
| reset | 点击重置按钮时触发 |
| apply | 点击应用按钮时触发 |

## 使用建议

### 空状态
- 所有列表页面在无数据时使用 `EmptyState`
- 提供有意义的描述和操作建议
- 图标选择与内容相关

### 区块卡片
- 首页、控制台等页面使用 `SectionCard` 包装内容
- 保持标题简洁
- 合理使用图标

### 过滤工具栏
- 列表页面顶部使用 `FilterToolbar`
- 过滤控件放在 slot 中
- 提供重置功能

### SkeletonList

骨架屏列表组件，用于列表加载时的占位显示。

```vue
<SkeletonList
  :count="4"
  type="card"
  variant="grid"
  :cols="12"
  :sm="6"
  :md="4"
  :lg="3"
/>
```

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| count | number | 4 | 骨架屏数量 |
| type | string | `card` | 骨架屏类型 |
| variant | string | `grid` | 布局模式：grid/list/default |
| cols/sm/md/lg | number | - | 响应式列数 |

## 按钮文案规范 (U5-2)

| 动作 | 统一文案 |
|------|----------|
| 播放 | 播放 |
| 继续播放（有声书） | 继续收听 |
| 继续播放（音乐） | 继续播放 |
| 标记已读 | 全部标记为已读 |
| 刷新 | 刷新 |
| 保存 | 保存 |
| 取消 | 取消 |
| 确定 | 确定 |

## 过渡动画规范 (U5-3)

卡片 hover 效果：

```scss
.card-hover {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}
```

## 文件清单

- `frontend/src/styles/theme.ts` - 主题配置
- `frontend/src/composables/useTheme.ts` - 主题切换 composable
- `frontend/src/components/common/EmptyState.vue` - 空状态组件
- `frontend/src/components/common/SectionCard.vue` - 区块卡片组件
- `frontend/src/components/common/FilterToolbar.vue` - 过滤工具栏组件
- `frontend/src/components/common/SkeletonList.vue` - 骨架屏列表组件
