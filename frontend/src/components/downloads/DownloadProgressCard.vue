<template>
  <v-card variant="outlined" class="download-progress-card">
    <v-card-title class="d-flex align-center justify-space-between">
      <div class="d-flex align-center">
        <v-icon :color="getStatusColor(download.status)" class="mr-2">
          {{ getStatusIcon(download.status) }}
        </v-icon>
        <span class="text-subtitle-1">{{ download.title }}</span>
      </div>
      <v-chip
        :color="getStatusColor(download.status)"
        size="small"
        variant="flat"
      >
        {{ getStatusText(download.status) }}
      </v-chip>
    </v-card-title>

    <v-card-text>
      <!-- 进度信息头部 -->
      <div class="progress-header mb-3">
        <div class="d-flex align-center justify-space-between mb-2">
          <div class="progress-info">
            <span class="text-h6 font-weight-medium">
              {{ download.progress?.toFixed(1) || 0 }}%
            </span>
            <span class="text-caption text-medium-emphasis ml-2">
              ({{ formatSize(download.downloaded_gb || 0) }} / {{ formatSize(download.size_gb || 0) }})
            </span>
          </div>
          
          <div class="progress-stats d-flex align-center ga-3">
            <!-- 下载速度 -->
            <div v-if="download.status === 'downloading'" class="stat-item d-flex align-center">
              <v-icon icon="mdi-speedometer" size="16" class="me-1" />
              <span class="text-caption">{{ formatSpeed((download.speed_mbps || 0) * 1024 * 1024) }}</span>
            </div>
            
            <!-- 预计剩余时间 -->
            <div v-if="download.status === 'downloading' && download.eta" class="stat-item d-flex align-center">
              <v-icon icon="mdi-clock-outline" size="16" class="me-1" />
              <span class="text-caption">ETA: {{ formatTime(download.eta) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 主进度条 -->
      <div class="main-progress mb-3">
        <v-progress-linear
          :model-value="download.progress || 0"
          :color="getProgressColor()"
          height="8"
          rounded
          :striped="download.status === 'downloading'"
          :indeterminate="download.status === 'waiting'"
        >
          <template #default="{ value }">
            <div class="progress-text">
              <span class="text-caption font-weight-medium">
                {{ value.toFixed(1) }}%
              </span>
            </div>
          </template>
        </v-progress-linear>
      </div>
      
      <!-- 详细统计信息 -->
      <div v-if="showDetails" class="progress-details">
        <v-row dense>
          <v-col cols="6" sm="3">
            <div class="detail-item">
              <div class="detail-label text-caption text-medium-emphasis">已下载</div>
              <div class="detail-value text-body-2 font-weight-medium">
                {{ formatSize(download.downloaded_gb || 0) }}
              </div>
            </div>
          </v-col>
          
          <v-col cols="6" sm="3">
            <div class="detail-item">
              <div class="detail-label text-caption text-medium-emphasis">总大小</div>
              <div class="detail-value text-body-2 font-weight-medium">
                {{ formatSize(download.size_gb || 0) }}
              </div>
            </div>
          </v-col>
          
          <v-col cols="6" sm="3">
            <div class="detail-item">
              <div class="detail-label text-caption text-medium-emphasis">下载速度</div>
              <div class="detail-value text-body-2 font-weight-medium">
                {{ formatSpeed((download.speed_mbps || 0) * 1024 * 1024) }}
              </div>
            </div>
          </v-col>
          
          <v-col cols="6" sm="3">
            <div class="detail-item">
              <div class="detail-label text-caption text-medium-emphasis">剩余时间</div>
              <div class="detail-value text-body-2 font-weight-medium">
                {{ download.eta ? formatTime(download.eta) : '--' }}
              </div>
            </div>
          </v-col>
        </v-row>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn
        icon="mdi-pause"
        size="small"
        variant="text"
        @click="$emit('pause', download)"
        :disabled="download.status === 'completed' || download.status === 'failed'"
      />
      <v-btn
        icon="mdi-play"
        size="small"
        variant="text"
        @click="$emit('resume', download)"
        :disabled="download.status !== 'paused'"
      />
      <v-btn
        icon="mdi-delete"
        size="small"
        variant="text"
        color="error"
        @click="$emit('delete', download)"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
interface Props {
  download: any
  showDetails?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showDetails: true
})

defineEmits<{
  pause: [download: any]
  resume: [download: any]
  delete: [download: any]
}>()

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    waiting: 'info',
    downloading: 'success',
    paused: 'warning',
    completed: 'primary',
    failed: 'error',
    cancelled: 'grey'
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status: string): string => {
  const icons: Record<string, string> = {
    waiting: 'mdi-clock-outline',
    downloading: 'mdi-download',
    paused: 'mdi-pause',
    completed: 'mdi-check-circle',
    failed: 'mdi-alert-circle',
    cancelled: 'mdi-cancel'
  }
  return icons[status] || 'mdi-help-circle'
}

const getStatusText = (status: string): string => {
  const texts: Record<string, string> = {
    waiting: '等待中',
    downloading: '下载中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getProgressColor = (): string => {
  const status = props.download.status
  
  if (status === 'failed') return 'error'
  if (status === 'paused') return 'warning'
  if (status === 'completed') return 'success'
  if (status === 'downloading') {
    const progress = props.download.progress || 0
    if (progress < 30) return 'info'
    if (progress < 70) return 'primary'
    return 'success'
  }
  
  return 'info'
}

const formatSpeed = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B/s'
  if (bytes < 1024) return `${bytes.toFixed(0)} B/s`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB/s`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB/s`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB/s`
}

const formatSize = (gb: number): string => {
  if (!gb || gb === 0) return '0 B'
  if (gb < 1) return `${(gb * 1024).toFixed(2)} MB`
  return `${gb.toFixed(2)} GB`
}

const formatTime = (seconds: number): string => {
  if (!seconds || seconds === 0) return '--'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) return `${hours}h ${mins}m`
  if (mins > 0) return `${mins}m ${secs}s`
  return `${secs}s`
}
</script>

<style scoped>
.download-progress-card {
  height: 100%;
}

.progress-header {
  .progress-info {
    display: flex;
    align-items: center;
  }
  
  .progress-stats {
    .stat-item {
      padding: 4px 8px;
      border-radius: 4px;
      background: rgba(var(--v-theme-surface), 0.5);
    }
  }
}

.main-progress {
  .v-progress-linear {
    border-radius: 4px;
  }
  
  .progress-text {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
}

.progress-details {
  .detail-item {
    .detail-label {
      margin-bottom: 4px;
    }
    
    .detail-value {
      color: rgb(var(--v-theme-on-surface));
    }
  }
}
</style>

