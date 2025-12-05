<template>
  <v-list-item 
    class="download-task-card"
    :class="{ 'selected': selected }"
    @click="handleToggleSelection"
  >
    <!-- 选择框 -->
    <template v-slot:prepend v-if="showSelection">
      <v-checkbox
        :model-value="selected"
        @update:model-value="handleToggleSelection"
        @click.stop
        density="compact"
        hide-details
      />
    </template>

    <!-- 任务标题和标签 -->
    <template v-slot:title>
      <div class="download-title">
        <!-- 任务名称 -->
        <div class="text-truncate font-weight-medium">
          {{ task.title || task.name || '未知任务' }}
        </div>
        
        <!-- 标签和状态信息 -->
        <div class="d-flex align-center ga-2 mt-1">
          <!-- VabHub 管理标识 - DOWNLOAD-CENTER-UI-2 -->
          <v-chip
            v-if="task.is_vabhub_managed"
            size="x-small"
            color="primary"
            variant="tonal"
            class="vabhub-chip"
          >
            <v-icon start size="12">mdi-check-circle</v-icon>
            VabHub
          </v-chip>

          <!-- 站点信息 -->
          <v-chip
            v-if="task.site_name"
            size="x-small"
            variant="tonal"
            :color="getSiteColor(task.site_name)"
            class="site-chip"
          >
            <v-icon start size="12">mdi-server</v-icon>
            {{ task.site_name }}
          </v-chip>

          <!-- HR等级标记 -->
          <v-chip
            v-if="task.hr_level && task.hr_level !== 'NONE'"
            size="x-small"
            :variant="task.hr_level === 'HR' ? 'flat' : 'tonal'"
            :color="getHRColor(task.hr_level)"
            class="hr-chip"
          >
            <v-icon start size="12">{{ getHRIcon(task.hr_level) }}</v-icon>
            {{ task.hr_level }}
          </v-chip>

          <!-- 短剧标记 -->
          <v-chip
            v-if="task.is_short_drama"
            size="x-small"
            variant="tonal"
            color="purple"
            class="short-drama-chip"
          >
            <v-icon start size="12">mdi-star</v-icon>
            短剧
          </v-chip>

          <!-- 整理状态 - DOWNLOAD-CENTER-UI-2 -->
          <v-chip
            :color="getOrganizeStatusColor(task.organize_status)"
            :variant="task.organize_status === 'AUTO_OK' ? 'flat' : 'tonal'"
            size="x-small"
            class="organize-status-chip"
          >
            <v-icon start size="12">{{ getOrganizeStatusIcon(task.organize_status) }}</v-icon>
            {{ getOrganizeStatusText(task.organize_status) }}
          </v-chip>

          <!-- 其他标签 -->
          <v-chip
            v-for="label in getDisplayLabels(task.labels)"
            :key="label"
            size="x-small"
            variant="outlined"
            color="grey"
            class="label-chip"
          >
            {{ label }}
          </v-chip>
        </div>
      </div>
    </template>

    <!-- 进度条和详细信息 -->
    <template v-slot:subtitle>
      <div class="progress-section mt-2">
        <!-- 进度条 -->
        <v-progress-linear
          :model-value="task.progress || 0"
          :color="getProgressColor(task.status)"
          height="6"
          rounded
          class="mb-1"
        >
          <template v-slot:default="{ value }">
            <small class="text-caption">{{ Math.round(value) }}%</small>
          </template>
        </v-progress-linear>

        <!-- 详细信息 -->
        <div class="d-flex justify-space-between align-center text-caption">
          <div class="progress-info">
            <span>{{ formatSize(task.downloaded_size ?? (task.downloaded_gb ?? 0) * 1024) }} / {{ formatSize(task.total_size ?? (task.size_gb ?? 0) * 1024) }}</span>
            <span v-if="task.eta && task.status === 'downloading'" class="ml-2">
              剩余 {{ formatETA(typeof task.eta === 'number' ? task.eta : 0) }}
            </span>
          </div>
          
          <div class="speed-info" v-if="task.status === 'downloading'">
            <v-icon size="12" color="primary">mdi-download</v-icon>
            {{ formatSpeed(task.download_speed || task.speed_mbps || 0) }}
            <v-icon size="12" color="success" class="ml-1" v-if="task.upload_speed">
              mdi-upload
            </v-icon>
            <span v-if="task.upload_speed" class="text-success">
              {{ formatSpeed(task.upload_speed) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 状态和时间信息 -->
      <div class="d-flex justify-space-between align-center mt-2">
        <v-chip
          :color="getStatusColor(task.status)"
          size="x-small"
          variant="tonal"
        >
          <v-icon start size="12">{{ getStatusIcon(task.status) }}</v-icon>
          {{ getStatusText(task.status) }}
        </v-chip>

        <div class="text-caption text-medium-emphasis">
          添加于 {{ formatTime(task.added_at || task.created_at) }}
        </div>
      </div>

      <!-- P4: 存储位置信息 -->
      <div v-if="task.save_path" class="storage-info text-caption text-medium-emphasis mt-1">
        <v-icon size="12" class="mr-1">mdi-harddisk</v-icon>
        存储：{{ task.save_path }}
      </div>
    </template>

    <!-- 操作按钮 -->
    <template v-slot:append>
      <div class="d-flex flex-column ga-1">
        <!-- 主要操作按钮 -->
        <v-btn
          v-if="task.status === 'downloading'"
          variant="text"
          size="small"
          color="orange"
          icon="mdi-pause"
          @click.stop="handlePauseTask"
        >
          <v-icon size="16">mdi-pause</v-icon>
          <v-tooltip activator="parent">暂停</v-tooltip>
        </v-btn>

        <v-btn
          v-if="task.status === 'paused'"
          variant="text"
          size="small"
          color="success"
          icon="mdi-play"
          @click.stop="handleResumeTask"
        >
          <v-icon size="16">mdi-play</v-icon>
          <v-tooltip activator="parent">继续</v-tooltip>
        </v-btn>

        <v-btn
          v-if="task.status === 'queued'"
          variant="text"
          size="small"
          color="primary"
          icon="mdi-arrow-up-bold"
          @click.stop="handleQueueTop"
        >
          <v-icon size="16">mdi-arrow-up-bold</v-icon>
          <v-tooltip activator="parent">置顶</v-tooltip>
        </v-btn>

        <!-- 手动整理按钮 - DOWNLOAD-CENTER-UI-2 -->
        <v-btn
          v-if="showManualOrganizeButton"
          variant="text"
          size="small"
          color="warning"
          icon="mdi-folder-move"
          @click.stop="handleOpenOrganize"
        >
          <v-icon size="16">mdi-folder-move</v-icon>
          <v-tooltip activator="parent">手动整理</v-tooltip>
        </v-btn>

        <!-- 次要操作按钮 -->
        <v-btn
          variant="text"
          size="small"
          color="grey"
          icon="mdi-speedometer"
          @click.stop="handleSpeedLimit"
        >
          <v-icon size="16">mdi-speedometer</v-icon>
          <v-tooltip activator="parent">限速</v-tooltip>
        </v-btn>

        <v-btn
          variant="text"
          size="small"
          color="error"
          icon="mdi-delete"
          @click.stop="handleDeleteTask"
        >
          <v-icon size="16">mdi-delete</v-icon>
          <v-tooltip activator="parent">删除</v-tooltip>
        </v-btn>
      </div>
    </template>
  </v-list-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 接口定义
interface DownloadTask {
  id: string
  name?: string
  title?: string
  status: string
  progress?: number
  // 大小字段（兼容不同格式）
  size_gb?: number
  total_size?: number
  downloaded_gb?: number
  downloaded_size?: number
  // 速度字段
  speed_mbps?: number
  download_speed?: number
  upload_speed?: number
  // 时间估算
  eta?: number | string
  // 站点和标签
  site_name?: string
  hr_level?: string
  is_short_drama?: boolean
  labels?: string[]
  added_at?: string
  created_at?: string
  // DOWNLOAD-CENTER-UI-2 新增字段
  is_vabhub_managed?: boolean
  organize_status?: string
  save_path?: string  // P4: 存储位置字段
}

interface Props {
  task: DownloadTask
  selected?: boolean
  showSelection?: boolean
  compact?: boolean
}

interface Emits {
  (e: 'toggleSelection', taskId: string): void
  (e: 'pause', taskId: string): void
  (e: 'resume', taskId: string): void
  (e: 'queueTop', taskId: string): void
  (e: 'delete', taskId: string): void
  (e: 'speedLimit', task: DownloadTask): void
  (e: 'openOrganize', taskId: string): void // DOWNLOAD-CENTER-UI-2 新增
}

// Props 和 Emits
const props = withDefaults(defineProps<Props>(), {
  selected: false,
  showSelection: true,
  compact: false
})

const emit = defineEmits<Emits>()

// 计算属性 - 是否显示手动整理按钮
const showManualOrganizeButton = computed(() => {
  const status = props.task.organize_status
  return status === 'AUTO_FAILED' || status === 'MANUAL_PENDING'
})

// 事件处理方法
const handleToggleSelection = () => {
  emit('toggleSelection', props.task.id)
}

const handlePauseTask = () => {
  emit('pause', props.task.id)
}

const handleResumeTask = () => {
  emit('resume', props.task.id)
}

const handleQueueTop = () => {
  emit('queueTop', props.task.id)
}

const handleDeleteTask = () => {
  emit('delete', props.task.id)
}

const handleSpeedLimit = () => {
  emit('speedLimit', props.task)
}

const handleOpenOrganize = () => {
  emit('openOrganize', props.task.id)
}

// 辅助方法 - 站点颜色
const getSiteColor = (siteName?: string): string => {
  if (!siteName) return 'grey'
  const siteColors: Record<string, string> = {
    'hdchina': 'blue',
    'chdbits': 'purple',
    'mteam': 'orange',
    'pter': 'green',
    'ourbits': 'red',
    'hdtime': 'indigo',
    'hdatmos': 'teal'
  }
  return siteColors[siteName.toLowerCase()] || 'grey'
}

// 辅助方法 - HR 颜色和图标
const getHRColor = (hrLevel?: string): string => {
  const colors: Record<string, string> = {
    'NONE': 'grey',
    'H&R': 'orange',
    'HR': 'red',
    'H3': 'purple',
    'H5': 'red-darken-2'
  }
  return colors[hrLevel || 'NONE'] || 'grey'
}

const getHRIcon = (hrLevel?: string): string => {
  const icons: Record<string, string> = {
    'NONE': 'mdi-shield-check',
    'H&R': 'mdi-alert',
    'HR': 'mdi-alert-circle',
    'H3': 'mdi-alert-octagon',
    'H5': 'mdi-alert-octagram'
  }
  return icons[hrLevel || 'NONE'] || 'mdi-shield-check'
}

// DOWNLOAD-CENTER-UI-2: 整理状态相关方法
const getOrganizeStatusColor = (status?: string): string => {
  const colors: Record<string, string> = {
    'NONE': 'grey',
    'AUTO_OK': 'success',
    'AUTO_FAILED': 'error',
    'MANUAL_PENDING': 'warning',
    'MANUAL_DONE': 'success'
  }
  return colors[status || 'NONE'] || 'grey'
}

const getOrganizeStatusIcon = (status?: string): string => {
  const icons: Record<string, string> = {
    'NONE': 'mdi-clock-outline',
    'AUTO_OK': 'mdi-check-circle',
    'AUTO_FAILED': 'mdi-alert-circle',
    'MANUAL_PENDING': 'mdi-human-handsup',
    'MANUAL_DONE': 'mdi-check-all'
  }
  return icons[status || 'NONE'] || 'mdi-clock-outline'
}

const getOrganizeStatusText = (status?: string): string => {
  const texts: Record<string, string> = {
    'NONE': '未整理',
    'AUTO_OK': '自动完成',
    'AUTO_FAILED': '自动失败',
    'MANUAL_PENDING': '待手动',
    'MANUAL_DONE': '手动完成'
  }
  return texts[status || 'NONE'] || '未整理'
}

// 辅助方法 - 进度颜色
const getProgressColor = (status: string): string => {
  const colors: Record<string, string> = {
    'downloading': 'primary',
    'completed': 'success',
    'paused': 'warning',
    'error': 'error',
    'queued': 'info'
  }
  return colors[status] || 'grey'
}

// 辅助方法 - 状态相关
const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    'downloading': 'success',
    'completed': 'primary',
    'paused': 'warning',
    'error': 'error',
    'queued': 'info'
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status: string): string => {
  const icons: Record<string, string> = {
    'downloading': 'mdi-download',
    'completed': 'mdi-check',
    'paused': 'mdi-pause',
    'error': 'mdi-alert-circle',
    'queued': 'mdi-clock-outline'
  }
  return icons[status] || 'mdi-help-circle'
}

const getStatusText = (status: string): string => {
  const texts: Record<string, string> = {
    'downloading': '下载中',
    'completed': '已完成',
    'paused': '已暂停',
    'error': '异常',
    'queued': '排队中'
  }
  return texts[status] || '未知'
}

// 辅助方法 - 标签处理
const getDisplayLabels = (labels?: string[]): string[] => {
  if (!labels || !Array.isArray(labels)) return []
  
  // 过滤掉 VabHub 相关标签，因为已经有专门的 VabHub 标识了
  const vabhubLabels = ['vabhub', 'moviepilot', 'auto']
  return labels.filter(label => 
    label && 
    !vabhubLabels.includes(label.toLowerCase())
  ).slice(0, 3) // 最多显示3个其他标签
}

// 辅助方法 - 格式化
const formatSize = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${units[i]}`
}

const formatSpeed = (mbps: number): string => {
  if (!mbps || mbps === 0) return '0 B/s'
  return formatSize(mbps * 1024 * 1024) + '/s'
}

const formatETA = (seconds: number): string => {
  if (!seconds || seconds <= 0) return '未知'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟`
  } else {
    return '1分钟内'
  }
}

const formatTime = (timeStr?: string): string => {
  if (!timeStr) return '未知'
  
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) {
      const hours = Math.floor(diff / (1000 * 60 * 60))
      if (hours === 0) {
        const minutes = Math.floor(diff / (1000 * 60))
        return minutes <= 1 ? '刚刚' : `${minutes}分钟前`
      }
      return `${hours}小时前`
    } else if (days === 1) {
      return '昨天'
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return date.toLocaleDateString()
    }
  } catch {
    return '未知'
  }
}
</script>

<style scoped>
.download-task-card {
  transition: background-color 0.2s ease;
}

.download-task-card:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.download-task-card.selected {
  background-color: rgba(25, 118, 210, 0.08);
}

.download-title {
  line-height: 1.4;
}

.progress-section {
  min-height: 60px;
}

.chip {
  max-width: 100px;
}

.vabhub-chip {
  font-weight: 600;
}

.organize-status-chip {
  font-weight: 500;
}
</style>
