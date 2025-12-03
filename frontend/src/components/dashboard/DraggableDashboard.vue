<template>
  <div class="draggable-dashboard">
    <!-- 编辑模式工具栏 -->
    <v-card v-if="editMode" class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="auto">
            <v-btn
              color="success"
              prepend-icon="mdi-content-save"
              @click="saveLayout"
              :loading="saving"
            >
              保存布局
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              @click="showAddWidgetDialog = true"
            >
              添加组件
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn
              color="warning"
              prepend-icon="mdi-refresh"
              @click="resetLayout"
            >
              重置布局
            </v-btn>
          </v-col>
          <v-col cols="auto" class="ml-auto">
            <v-btn
              color="error"
              prepend-icon="mdi-close"
              @click="exitEditMode"
            >
              退出编辑
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 可拖拽网格布局 -->
    <grid-layout
      :layout="currentLayout"
      :col-num="cols"
      :row-height="rowHeight"
      :is-draggable="editMode"
      :is-resizable="editMode"
      :is-mirrored="false"
      :vertical-compact="true"
      :margin="margin"
      :use-css-transforms="true"
      @layout-updated="onLayoutChange"
    >
      <grid-item
        v-for="item in currentLayout"
        :key="item.i"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
        :i="item.i"
        :minW="item.minW || 2"
        :minH="item.minH || 2"
        :maxW="item.maxW || cols"
        :maxH="item.maxH || 20"
      >
        <v-card class="widget-card" :class="{ 'edit-mode': editMode }">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">{{ getWidgetIcon(item.i) }}</v-icon>
            <span>{{ getWidgetTitle(item.i) }}</span>
            <v-spacer></v-spacer>
            <v-btn
              v-if="editMode"
              icon="mdi-close"
              size="small"
              variant="text"
              @click="removeWidget(item.i)"
            ></v-btn>
          </v-card-title>
          <v-card-text>
            <component
              v-if="getWidgetComponent(item.i)"
              :is="getWidgetComponent(item.i)"
              v-bind="getWidgetProps(item.i)"
            />
            <div v-else class="text-center text-grey">
              组件 {{ item.i }} 尚未实现
            </div>
          </v-card-text>
        </v-card>
      </grid-item>
    </grid-layout>

    <!-- 添加组件对话框 -->
    <v-dialog v-model="showAddWidgetDialog" max-width="600">
      <v-card>
        <v-card-title>添加组件</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item
              v-for="widget in availableWidgets"
              :key="widget.widget_id"
              @click="addWidget(widget)"
            >
              <template v-slot:prepend>
                <v-icon>{{ widget.icon || 'mdi-widgets' }}</v-icon>
              </template>
              <v-list-item-title>{{ widget.name }}</v-list-item-title>
              <v-list-item-subtitle>{{ widget.description }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showAddWidgetDialog = false">取消</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { GridLayout, GridItem } from 'vue-grid-layout'
import { dashboardLayoutApi } from '@/services/api'
import { useToast } from 'vue-toastification'
import { useDashboardStore } from '@/stores/dashboard'

// 导入现有组件
import StatCard from '@/components/common/StatCard.vue'
import DownloadSpeedChart from '@/components/dashboard/DownloadSpeedChart.vue'
import SystemResourceMonitor from '@/components/dashboard/SystemResourceMonitor.vue'
import QuickActionsPanel from '@/components/dashboard/QuickActionsPanel.vue'
import RecentActivityTimeline from '@/components/dashboard/RecentActivityTimeline.vue'

const dashboardStore = useDashboardStore()
const dashboardData = computed(() => dashboardStore.dashboardData)
const stats = computed(() => dashboardStore.stats)

interface LayoutItem {
  i: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
}

interface Widget {
  widget_id: string
  name: string
  description?: string
  type: string
  component: string
  icon?: string
  enabled: boolean
}

const props = defineProps<{
  editMode?: boolean
  layoutId?: number
}>()

const emit = defineEmits<{
  (e: 'layout-saved', layoutId: number): void
  (e: 'edit-mode-changed', mode: boolean): void
}>()

const toast = useToast()

// 布局配置
const cols = ref(12)
const rowHeight = ref(30)
const margin = ref<[number, number]>([10, 10])
const currentLayout = ref<LayoutItem[]>([])
const originalLayout = ref<LayoutItem[]>([])

// 组件管理
const availableWidgets = ref<Widget[]>([])
const showAddWidgetDialog = ref(false)
const saving = ref(false)

// 编辑模式
const editMode = computed(() => props.editMode || false)

// 组件映射
const widgetComponents: Record<string, any> = {
  'stat-media': StatCard,
  'stat-downloads': StatCard,
  'stat-storage': StatCard,
  'stat-system': StatCard,
  'chart-download-speed': DownloadSpeedChart,
  'monitor-system-resource': SystemResourceMonitor,
  'panel-quick-actions': QuickActionsPanel,
  'timeline-recent-activity': RecentActivityTimeline
}

const widgetIcons: Record<string, string> = {
  'stat-media': 'mdi-movie',
  'stat-downloads': 'mdi-download',
  'stat-storage': 'mdi-harddisk',
  'stat-system': 'mdi-chip',
  'chart-download-speed': 'mdi-chart-line',
  'monitor-system-resource': 'mdi-monitor-dashboard',
  'panel-quick-actions': 'mdi-lightning-bolt',
  'timeline-recent-activity': 'mdi-clock-outline'
}

const widgetTitles: Record<string, string> = {
  'stat-media': '媒体资源',
  'stat-downloads': '活跃下载',
  'stat-storage': '存储使用',
  'stat-system': '系统负载',
  'chart-download-speed': '下载速度趋势',
  'monitor-system-resource': '系统资源',
  'panel-quick-actions': '快速操作',
  'timeline-recent-activity': '最近活动'
}

// 获取组件
const getWidgetComponent = (widgetId: string) => {
  return widgetComponents[widgetId] || null
}

const getWidgetIcon = (widgetId: string) => {
  return widgetIcons[widgetId] || 'mdi-widgets'
}

const getWidgetTitle = (widgetId: string) => {
  return widgetTitles[widgetId] || widgetId
}

const getWidgetProps = (widgetId: string) => {
  // 根据组件ID返回相应的props
  const props: Record<string, any> = {}
  
  switch (widgetId) {
    case 'stat-media':
      props.title = '媒体资源'
      props.value = stats.value.media.total
      props.icon = 'mdi-movie'
      props.color = 'primary'
      break
    case 'stat-downloads':
      props.title = '活跃下载'
      props.value = stats.value.downloads.active
      props.icon = 'mdi-download'
      props.color = 'success'
      props.subtitle = `总速度: ${formatSpeed(stats.value.downloads.totalSpeed)}`
      break
    case 'stat-storage':
      props.title = '存储使用'
      props.value = `${stats.value.storage.used.toFixed(1)}%`
      props.icon = 'mdi-harddisk'
      props.color = 'warning'
      props.progress = stats.value.storage.used
      break
    case 'stat-system':
      props.title = '系统负载'
      props.value = `${stats.value.system.cpu.toFixed(1)}%`
      props.icon = 'mdi-chip'
      props.color = 'info'
      props.subtitle = `内存: ${stats.value.system.memory.toFixed(1)}%`
      break
    case 'chart-download-speed':
      props.data = dashboardStore.downloadSpeedData
      break
    case 'monitor-system-resource':
      props.stats = dashboardData.value?.system_stats || { cpu: 0, memory: 0, disk: 0 }
      break
  }
  
  return props
}

const formatSpeed = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 B/s'
  if (bytes < 1024) return `${bytes} B/s`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB/s`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB/s`
}

// 加载布局
const loadLayout = async () => {
  try {
    const response = await dashboardLayoutApi.getLayout(props.layoutId)
    const layout = response.data
    
    if (layout) {
      cols.value = layout.cols || 12
      rowHeight.value = layout.row_height || 30
      margin.value = layout.margin || [10, 10]
      
      // 转换布局格式
      if (layout.layouts && layout.breakpoint) {
        const breakpointLayout = layout.layouts[layout.breakpoint] || layout.layouts['lg'] || []
        currentLayout.value = breakpointLayout.map((item: any) => ({
          i: item.i || item.id,
          x: item.x || 0,
          y: item.y || 0,
          w: item.w || 4,
          h: item.h || 4,
          minW: item.minW || 2,
          minH: item.minH || 2,
          maxW: item.maxW || cols.value,
          maxH: item.maxH || 20
        }))
      } else {
        // 如果没有保存的布局，使用默认布局
        currentLayout.value = getDefaultLayout()
      }
      
      originalLayout.value = JSON.parse(JSON.stringify(currentLayout.value))
    } else {
      // 如果没有布局，使用默认布局
      currentLayout.value = getDefaultLayout()
      originalLayout.value = JSON.parse(JSON.stringify(currentLayout.value))
    }
  } catch (error: any) {
    console.error('Failed to load layout:', error)
    // 如果加载失败，使用默认布局
    currentLayout.value = getDefaultLayout()
    originalLayout.value = JSON.parse(JSON.stringify(currentLayout.value))
  }
}

// 获取默认布局
const getDefaultLayout = (): LayoutItem[] => {
  return [
    { i: 'stat-media', x: 0, y: 0, w: 3, h: 2, minW: 2, minH: 2 },
    { i: 'stat-downloads', x: 3, y: 0, w: 3, h: 2, minW: 2, minH: 2 },
    { i: 'stat-storage', x: 6, y: 0, w: 3, h: 2, minW: 2, minH: 2 },
    { i: 'stat-system', x: 9, y: 0, w: 3, h: 2, minW: 2, minH: 2 },
    { i: 'chart-download-speed', x: 0, y: 2, w: 8, h: 6, minW: 4, minH: 4 },
    { i: 'monitor-system-resource', x: 8, y: 2, w: 4, h: 6, minW: 3, minH: 4 },
    { i: 'panel-quick-actions', x: 0, y: 8, w: 6, h: 4, minW: 3, minH: 3 },
    { i: 'timeline-recent-activity', x: 6, y: 8, w: 6, h: 4, minW: 3, minH: 3 }
  ]
}

// 加载可用组件列表
const loadWidgets = async () => {
  try {
    const response = await dashboardLayoutApi.getWidgets()
    availableWidgets.value = response.data || []
  } catch (error: any) {
    console.error('Failed to load widgets:', error)
    // 使用默认组件列表
    availableWidgets.value = [
      { widget_id: 'stat-media', name: '媒体资源', type: 'stats', component: 'StatCard', enabled: true },
      { widget_id: 'stat-downloads', name: '活跃下载', type: 'stats', component: 'StatCard', enabled: true },
      { widget_id: 'stat-storage', name: '存储使用', type: 'stats', component: 'StatCard', enabled: true },
      { widget_id: 'stat-system', name: '系统负载', type: 'stats', component: 'StatCard', enabled: true },
      { widget_id: 'chart-download-speed', name: '下载速度趋势', type: 'chart', component: 'DownloadSpeedChart', enabled: true },
      { widget_id: 'monitor-system-resource', name: '系统资源', type: 'monitor', component: 'SystemResourceMonitor', enabled: true },
      { widget_id: 'panel-quick-actions', name: '快速操作', type: 'panel', component: 'QuickActionsPanel', enabled: true },
      { widget_id: 'timeline-recent-activity', name: '最近活动', type: 'timeline', component: 'RecentActivityTimeline', enabled: true }
    ]
  }
}

// 布局变化处理
const onLayoutChange = (newLayout: LayoutItem[]) => {
  currentLayout.value = newLayout
}

// 保存布局
const saveLayout = async () => {
  saving.value = true
  try {
    // 转换布局格式
    const layouts: Record<string, any> = {
      lg: currentLayout.value.map(item => ({
        i: item.i,
        x: item.x,
        y: item.y,
        w: item.w,
        h: item.h,
        minW: item.minW,
        minH: item.minH,
        maxW: item.maxW,
        maxH: item.maxH
      }))
    }
    
    const widgets = currentLayout.value.map(item => item.i)
    
    const response = await dashboardLayoutApi.saveLayout({
      name: '默认布局',
      breakpoint: 'lg',
      cols: cols.value,
      row_height: rowHeight.value,
      margin: margin.value,
      layouts,
      widgets,
      is_default: true
    }, props.layoutId)
    
    toast.success('布局保存成功')
    originalLayout.value = JSON.parse(JSON.stringify(currentLayout.value))
    emit('layout-saved', response.data.layout_id)
  } catch (error: any) {
    console.error('Failed to save layout:', error)
    toast.error('保存布局失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 重置布局
const resetLayout = () => {
  currentLayout.value = JSON.parse(JSON.stringify(originalLayout.value))
  toast.info('布局已重置')
}

// 添加组件
const addWidget = (widget: Widget) => {
  if (!widgetComponents[widget.widget_id]) {
    toast.warning(`组件 ${widget.name} 尚未实现`)
    return
  }
  
  // 检查是否已存在
  if (currentLayout.value.some(item => item.i === widget.widget_id)) {
    toast.warning('该组件已存在')
    return
  }
  
  // 添加到布局
  const newItem: LayoutItem = {
    i: widget.widget_id,
    x: 0,
    y: Math.max(...currentLayout.value.map(item => item.y + item.h), 0),
    w: 4,
    h: 4,
    minW: 2,
    minH: 2
  }
  
  currentLayout.value.push(newItem)
  showAddWidgetDialog.value = false
  toast.success(`组件 ${widget.name} 已添加`)
}

// 移除组件
const removeWidget = (widgetId: string) => {
  const index = currentLayout.value.findIndex(item => item.i === widgetId)
  if (index !== -1) {
    currentLayout.value.splice(index, 1)
    toast.success('组件已移除')
  }
}

// 退出编辑模式
const exitEditMode = () => {
  emit('edit-mode-changed', false)
}

// 监听layoutId变化
watch(() => props.layoutId, () => {
  loadLayout()
}, { immediate: false })

// 初始化
onMounted(() => {
  loadLayout()
  loadWidgets()
})
</script>

<style lang="scss" scoped>
.draggable-dashboard {
  min-height: 100vh;
  padding: 20px;
}

.widget-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  &.edit-mode {
    border: 2px dashed rgba(var(--v-theme-primary), 0.5);
  }
  
  .v-card-title {
    flex-shrink: 0;
  }
  
  .v-card-text {
    flex: 1;
    overflow: auto;
  }
}

:deep(.vue-grid-layout) {
  background: transparent;
}

:deep(.vue-grid-item) {
  transition: all 200ms ease;
  transition-property: left, top, width, height;
  
  &.vue-grid-placeholder {
    background: rgba(var(--v-theme-primary), 0.2);
    border: 2px dashed rgba(var(--v-theme-primary), 0.5);
  }
  
  &.vue-resizable-handle {
    background: rgba(var(--v-theme-primary), 0.3);
  }
}
</style>

