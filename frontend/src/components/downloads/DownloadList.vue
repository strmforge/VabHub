<template>
  <div class="download-list">
    <!-- 批量操作工具栏 -->
    <v-card v-if="selected.length > 0" variant="flat" color="primary" class="mb-2">
      <v-card-text class="pa-2">
        <div class="d-flex align-center">
          <span class="text-body-2 mr-4">已选择 {{ selected.length }} 项</span>
          <v-btn
            size="small"
            variant="text"
            prepend-icon="mdi-pause"
            @click="$emit('batch-pause', selected)"
          >
            批量暂停
          </v-btn>
          <v-btn
            size="small"
            variant="text"
            prepend-icon="mdi-play"
            @click="$emit('batch-resume', selected)"
          >
            批量恢复
          </v-btn>
          <v-btn
            size="small"
            variant="text"
            prepend-icon="mdi-delete"
            color="error"
            @click="$emit('batch-delete', selected)"
          >
            批量删除
          </v-btn>
          <v-spacer />
          <v-btn
            size="small"
            variant="text"
            @click="$emit('clear-selection')"
          >
            取消选择
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
    
    <v-list>
      <!-- 全选 -->
      <v-list-item v-if="downloads.length > 0">
        <v-checkbox
          :model-value="isAllSelected"
          :indeterminate="isIndeterminate"
          @update:model-value="handleSelectAll"
          label="全选"
          hide-details
        />
      </v-list-item>
      
      <v-list-item
        v-for="download in downloads"
        :key="download.id"
        class="download-item"
      >
        <template v-slot:prepend>
          <v-checkbox
            :model-value="selected.includes(download.id)"
            @update:model-value="(val) => $emit('select', download.id, val ?? false)"
            hide-details
            class="mr-2"
          />
          <v-avatar :color="getStatusColor(download.status)">
            <v-icon color="white">{{ getStatusIcon(download.status) }}</v-icon>
          </v-avatar>
        </template>
        
        <v-list-item-title class="text-truncate">{{ download.title }}</v-list-item-title>
        <v-list-item-subtitle>
          <div class="d-flex align-center mt-1">
            <v-progress-linear
              :model-value="download.progress || 0"
              :color="getStatusColor(download.status)"
              height="6"
              rounded
              class="mr-2"
              style="flex: 1;"
            />
            <span class="text-caption font-weight-medium">{{ Math.round(download.progress || 0) }}%</span>
          </div>
          <div class="d-flex align-center flex-wrap ga-2 mt-2">
            <div class="text-caption text-medium-emphasis">
              <v-icon size="small" class="me-1">mdi-download</v-icon>
              {{ formatSize(download.downloaded_gb || 0) }} / {{ formatSize(download.size_gb || 0) }}
            </div>
            <div v-if="download.status === 'downloading'" class="text-caption text-medium-emphasis">
              <v-icon size="small" class="me-1">mdi-speedometer</v-icon>
              {{ formatSpeed((download.speed_mbps || 0) * 1024 * 1024) }}
            </div>
            <div v-if="download.status === 'downloading' && download.eta" class="text-caption text-medium-emphasis">
              <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
              ETA: {{ formatTime(download.eta) }}
            </div>
            <!-- 标签显示 -->
            <div v-if="download.tags && download.tags.length > 0" class="d-flex align-center flex-wrap ga-1">
              <v-chip
                v-for="tag in download.tags"
                :key="tag"
                size="x-small"
                :color="tag === 'VABHUB' ? 'primary' : 'secondary'"
                variant="flat"
                class="text-caption"
              >
                {{ tag }}
              </v-chip>
            </div>
            <v-chip
              v-if="download.media_type === 'short_drama'"
              size="x-small"
              color="purple"
              variant="flat"
              class="text-caption"
            >
              <v-icon size="14" class="me-1">mdi-drama-masks</v-icon>
              短剧
            </v-chip>
            <!-- Local Intel 状态（Phase 8） -->
            <v-chip
              v-if="download.intel_hr_status && download.intel_hr_status !== 'UNKNOWN'"
              size="x-small"
              :color="getHRStatusColor(download.intel_hr_status)"
              variant="flat"
              class="text-caption"
              @click.stop="goToLocalIntel(download)"
              style="cursor: pointer;"
            >
              <v-icon size="14" class="me-1">{{ getHRStatusIcon(download.intel_hr_status) }}</v-icon>
              {{ getHRStatusText(download.intel_hr_status) }}
            </v-chip>
            <v-chip
              v-if="download.intel_site_status && download.intel_site_status !== 'UNKNOWN'"
              size="x-small"
              :color="getSiteStatusColor(download.intel_site_status)"
              variant="flat"
              class="text-caption"
              @click.stop="goToLocalIntel(download)"
              style="cursor: pointer;"
            >
              <v-icon size="14" class="me-1">{{ getSiteStatusIcon(download.intel_site_status) }}</v-icon>
              {{ getSiteStatusText(download.intel_site_status) }}
            </v-chip>
          </div>
        </v-list-item-subtitle>
        
        <template v-slot:append>
          <div class="d-flex align-center ga-1">
            <!-- 速度限制按钮 -->
            <v-tooltip text="速度限制" location="left">
              <template #activator="{ props: tooltipProps }">
                <v-btn
                  v-bind="tooltipProps"
                  icon
                  size="small"
                  variant="text"
                  @click.stop="$emit('speed-limit', download)"
                >
                  <v-icon>mdi-speedometer</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
            
            <!-- 队列管理按钮 -->
            <v-menu>
              <template v-slot:activator="{ props: menuProps }">
                <v-btn
                  v-bind="menuProps"
                  icon
                  size="small"
                  variant="text"
                  @click.stop
                >
                  <v-icon>mdi-menu</v-icon>
                </v-btn>
              </template>
              <v-list>
                <v-list-item @click="$emit('queue-up', download.id)">
                  <template v-slot:prepend>
                    <v-icon>mdi-arrow-up</v-icon>
                  </template>
                  <v-list-item-title>上移</v-list-item-title>
                </v-list-item>
                <v-list-item @click="$emit('queue-down', download.id)">
                  <template v-slot:prepend>
                    <v-icon>mdi-arrow-down</v-icon>
                  </template>
                  <v-list-item-title>下移</v-list-item-title>
                </v-list-item>
                <v-list-item @click="$emit('queue-top', download.id)">
                  <template v-slot:prepend>
                    <v-icon>mdi-arrow-up-bold</v-icon>
                  </template>
                  <v-list-item-title>置顶</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
            
            <v-tooltip text="暂停/恢复" location="left">
              <template #activator="{ props: tooltipProps }">
                <v-btn
                  v-bind="tooltipProps"
                  icon
                  size="small"
                  variant="text"
                  @click="togglePause(download)"
                  :disabled="download.status === 'completed' || download.status === 'failed'"
                >
                  <v-icon>{{ download.status === 'paused' ? 'mdi-play' : 'mdi-pause' }}</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
            
            <v-tooltip text="删除" location="left">
              <template #activator="{ props: tooltipProps }">
                <v-btn
                  v-bind="tooltipProps"
                  icon
                  size="small"
                  variant="text"
                  color="error"
                  @click="handleDelete(download)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
          </div>
        </template>
      </v-list-item>
    </v-list>
    
    <div v-if="downloads.length === 0" class="text-center text-medium-emphasis py-8">
      暂无下载任务
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()

interface Props {
  downloads: any[]
  selected?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  selected: () => []
})

const emit = defineEmits<{
  refresh: []
  select: [id: string, selected: boolean]
  'select-all': [selected: boolean]
  'clear-selection': []
  'batch-pause': [ids: string[]]
  'batch-resume': [ids: string[]]
  'batch-delete': [ids: string[]]
  'queue-up': [id: string]
  'queue-down': [id: string]
  'queue-top': [id: string]
  'speed-limit': [download: any]
}>()

// 全选状态
const isAllSelected = computed(() => {
  return props.downloads.length > 0 && props.selected.length === props.downloads.length
})

const isIndeterminate = computed(() => {
  return props.selected.length > 0 && props.selected.length < props.downloads.length
})

const handleSelectAll = (selected: boolean | null) => {
  emit('select-all', selected ?? false)
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    downloading: 'primary',
    paused: 'warning',
    completed: 'success',
    failed: 'error'
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    downloading: 'mdi-download',
    paused: 'mdi-pause',
    completed: 'mdi-check',
    failed: 'mdi-alert'
  }
  return icons[status] || 'mdi-help'
}

const formatSpeed = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 B/s'
  if (bytes < 1024) return `${bytes.toFixed(0)} B/s`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB/s`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB/s`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB/s`
}

const formatSize = (gb: number) => {
  if (!gb || gb === 0) return '0 B'
  if (gb < 1) return `${(gb * 1024).toFixed(2)} MB`
  return `${gb.toFixed(2)} GB`
}

const formatTime = (seconds: number) => {
  if (!seconds || seconds === 0) return '--'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) return `${hours}h ${mins}m`
  if (mins > 0) return `${mins}m ${secs}s`
  return `${secs}s`
}

const togglePause = async (download: any) => {
  try {
    if (download.status === 'paused') {
      await api.post(`/downloads/${download.id}/resume`)
    } else {
      await api.post(`/downloads/${download.id}/pause`)
    }
    emit('refresh')
  } catch (error: any) {
    console.error('操作失败:', error)
    alert('操作失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const handleDelete = async (download: any) => {
  if (!confirm(`确定要删除下载任务"${download.title}"吗？`)) {
    return
  }
  
  try {
    await api.delete(`/downloads/${download.id}`)
    emit('refresh')
  } catch (error: any) {
    console.error('删除失败:', error)
    alert('删除失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

// Local Intel 状态相关函数（Phase 8）
const getHRStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    SAFE: 'success',
    ACTIVE: 'warning',
    RISK: 'error',
    UNKNOWN: 'grey'
  }
  return colors[status] || 'grey'
}

const getHRStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    SAFE: 'mdi-shield-check',
    ACTIVE: 'mdi-shield-alert',
    RISK: 'mdi-shield-alert-outline',
    UNKNOWN: 'mdi-shield-question'
  }
  return icons[status] || 'mdi-shield-question'
}

const getHRStatusText = (status: string) => {
  const texts: Record<string, string> = {
    SAFE: 'HR安全',
    ACTIVE: 'HR中',
    RISK: 'HR风险',
    UNKNOWN: '未知'
  }
  return texts[status] || '未知'
}

const getSiteStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    OK: 'success',
    THROTTLED: 'warning',
    ERROR: 'error',
    UNKNOWN: 'grey'
  }
  return colors[status] || 'grey'
}

const getSiteStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    OK: 'mdi-check-circle',
    THROTTLED: 'mdi-speedometer',
    ERROR: 'mdi-alert-circle',
    UNKNOWN: 'mdi-help-circle'
  }
  return icons[status] || 'mdi-help-circle'
}

const getSiteStatusText = (status: string) => {
  const texts: Record<string, string> = {
    OK: '站点正常',
    THROTTLED: '站点限流',
    ERROR: '站点错误',
    UNKNOWN: '未知'
  }
  return texts[status] || '未知'
}

const goToLocalIntel = (download: any) => {
  // 跳转到 Local Intel 面板，如果有站点信息则预填过滤
  const site = download.extra_metadata?.site_id || download.extra_metadata?.site
  if (site) {
    router.push({ name: 'LocalIntel', query: { site } })
  } else {
    router.push({ name: 'LocalIntel' })
  }
}
</script>

<style lang="scss" scoped>
.download-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

