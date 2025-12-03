<template>
  <div class="log-center">
    <PageHeader
      title="实时日志中心"
      subtitle="实时查看系统日志，支持多源聚合和智能过滤"
      icon="mdi-console-line"
    />

    <!-- 统计卡片 -->
    <v-row class="mb-4">
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">总日志数</div>
            <div class="text-h5">{{ statistics.total }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">错误数</div>
            <div class="text-h5 text-error">{{ statistics.error_count }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">警告数</div>
            <div class="text-h5 text-warning">{{ statistics.warning_count }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-caption text-medium-emphasis">连接状态</div>
            <div class="text-h5">
              <v-chip
                :color="isConnected ? 'success' : 'error'"
                size="small"
                class="mt-1"
              >
                {{ isConnected ? '已连接' : '未连接' }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 过滤工具栏 -->
    <v-card class="mb-4">
      <v-card-title>过滤设置</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.level"
              :items="levelOptions"
              label="日志级别"
              multiple
              chips
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.source"
              :items="sourceOptions"
              label="日志来源"
              multiple
              chips
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.keyword"
              label="关键词搜索"
              clearable
              prepend-inner-icon="mdi-magnify"
            />
          </v-col>
          <v-col cols="12" md="3" class="d-flex align-center">
            <v-btn
              color="primary"
              @click="applyFilters"
              :loading="loading"
            >
              应用过滤
            </v-btn>
            <v-btn
              color="secondary"
              variant="text"
              @click="clearFilters"
              class="ml-2"
            >
              清空
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 日志显示区域 -->
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>实时日志</span>
        <div>
          <v-btn
            icon="mdi-pause"
            variant="text"
            @click="togglePause"
            :color="isPaused ? 'error' : 'success'"
          />
          <v-btn
            icon="mdi-download"
            variant="text"
            @click="exportLogs"
          />
          <v-btn
            icon="mdi-delete"
            variant="text"
            @click="clearLogs"
            color="error"
          />
        </div>
      </v-card-title>
      <v-card-text>
        <div
          ref="logContainer"
          class="log-container"
          :class="{ 'log-paused': isPaused }"
        >
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="log-entry"
            :class="`log-${log.level.toLowerCase()}`"
          >
            <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
            <v-chip
              :color="getLevelColor(log.level)"
              size="x-small"
              class="log-level"
            >
              {{ log.level }}
            </v-chip>
            <v-chip
              size="x-small"
              variant="outlined"
              class="log-source"
            >
              {{ log.source }}/{{ log.component }}
            </v-chip>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="logs.length === 0" class="text-center text-medium-emphasis py-8">
            暂无日志
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import api from '@/services/api'

interface LogEntry {
  level: string
  message: string
  source: string
  component: string
  timestamp: string
}

const logs = ref<LogEntry[]>([])
const isConnected = ref(false)
const isPaused = ref(false)
const loading = ref(false)
const logContainer = ref<HTMLElement | null>(null)

const statistics = ref({
  total: 0,
  error_count: 0,
  warning_count: 0,
  by_level: {} as Record<string, number>,
  by_source: {} as Record<string, number>
})

const filters = ref({
  level: [] as string[],
  source: [] as string[],
  keyword: ''
})

const levelOptions = [
  { title: 'DEBUG', value: 'DEBUG' },
  { title: 'INFO', value: 'INFO' },
  { title: 'WARNING', value: 'WARNING' },
  { title: 'ERROR', value: 'ERROR' },
  { title: 'CRITICAL', value: 'CRITICAL' }
]

const sourceOptions = [
  { title: '核心系统', value: 'core' },
  { title: '插件', value: 'plugin' },
  { title: '下载器', value: 'downloader' },
  { title: '媒体服务器', value: 'media_server' },
  { title: '调度器', value: 'scheduler' },
  { title: 'API', value: 'api' },
  { title: '搜索', value: 'search' },
  { title: '订阅', value: 'subscription' },
  { title: '多模态', value: 'multimodal' }
]

let ws: WebSocket | null = null
let reconnectTimer: NodeJS.Timeout | null = null
const maxLogs = 1000

// 构建WebSocket URL
const getWebSocketUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_BASE_URL?.replace(/^https?:\/\//, '') || window.location.host
  const baseUrl = `${protocol}//${host}`
  
  const params = new URLSearchParams()
  if (filters.value.level.length > 0) {
    params.append('level', filters.value.level.join(','))
  }
  if (filters.value.source.length > 0) {
    params.append('source', filters.value.source.join(','))
  }
  if (filters.value.keyword) {
    params.append('keyword', filters.value.keyword)
  }
  
  const queryString = params.toString()
  return `${baseUrl}/api/log-center/ws/logs${queryString ? '?' + queryString : ''}`
}

// 连接WebSocket
const connectWebSocket = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    return
  }

  try {
    const url = getWebSocketUrl()
    ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('WebSocket连接已建立')
      isConnected.value = true
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'connection') {
          console.log('连接成功:', data.message)
        } else if (data.type === 'log_entry') {
          if (!isPaused.value) {
            addLog(data.data)
          }
        } else if (data.type === 'filters_updated') {
          console.log('过滤器已更新')
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      isConnected.value = false
    }

    ws.onclose = () => {
      console.log('WebSocket连接已关闭')
      isConnected.value = false
      
      // 自动重连
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null
          connectWebSocket()
        }, 3000)
      }
    }
  } catch (error) {
    console.error('创建WebSocket连接失败:', error)
    isConnected.value = false
  }
}

// 断开WebSocket
const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

// 添加日志
const addLog = (log: LogEntry) => {
  logs.value.unshift(log)
  
  // 限制日志数量
  if (logs.value.length > maxLogs) {
    logs.value = logs.value.slice(0, maxLogs)
  }
  
  // 自动滚动到底部
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = 0
    }
  })
}

// 应用过滤器
const applyFilters = () => {
  disconnectWebSocket()
  logs.value = []
  connectWebSocket()
  loadStatistics()
}

// 清空过滤器
const clearFilters = () => {
  filters.value = {
    level: [],
    source: [],
    keyword: ''
  }
  applyFilters()
}

// 切换暂停状态
const togglePause = () => {
  isPaused.value = !isPaused.value
}

// 导出日志
const exportLogs = async () => {
  try {
    const params = new URLSearchParams()
    if (filters.value.level.length > 0) {
      params.append('level', filters.value.level.join(','))
    }
    if (filters.value.source.length > 0) {
      params.append('source', filters.value.source.join(','))
    }
    if (filters.value.keyword) {
      params.append('keyword', filters.value.keyword)
    }
    params.append('format', 'json')
    params.append('hours', '24')
    
    const response = await api.get('/log-center/export', {
      params,
      responseType: 'blob'
    })
    
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_${new Date().toISOString().replace(/[:.]/g, '-')}.json`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出日志失败:', error)
    alert('导出日志失败')
  }
}

// 清空日志
const clearLogs = async () => {
  if (!confirm('确定要清空所有日志吗？')) {
    return
  }
  
  try {
    await api.delete('/log-center/clear')
    logs.value = []
  } catch (error) {
    console.error('清空日志失败:', error)
    alert('清空日志失败')
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await api.get('/log-center/statistics', {
      params: { hours: 24 }
    })
    if (response.data) {
      statistics.value = response.data
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 格式化时间戳
const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取级别颜色
const getLevelColor = (level: string) => {
  const colors: Record<string, string> = {
    DEBUG: 'grey',
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    CRITICAL: 'error'
  }
  return colors[level] || 'grey'
}

onMounted(() => {
  connectWebSocket()
  loadStatistics()
  
  // 定期更新统计信息
  const statsInterval = setInterval(loadStatistics, 30000) // 每30秒更新一次
  
  onUnmounted(() => {
    disconnectWebSocket()
    clearInterval(statsInterval)
  })
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped lang="scss">
.log-center {
  padding: 20px;
}

.log-container {
  height: 600px;
  overflow-y: auto;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  
  &.log-paused {
    opacity: 0.7;
  }
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
  
  &:hover {
    background: rgba(var(--v-theme-primary), 0.05);
  }
  
  &.log-error,
  &.log-critical {
    background: rgba(var(--v-theme-error), 0.05);
  }
  
  &.log-warning {
    background: rgba(var(--v-theme-warning), 0.05);
  }
}

.log-timestamp {
  color: rgba(var(--v-theme-on-surface), 0.6);
  min-width: 160px;
  flex-shrink: 0;
}

.log-level {
  min-width: 70px;
  flex-shrink: 0;
}

.log-source {
  min-width: 120px;
  flex-shrink: 0;
}

.log-message {
  flex: 1;
  word-break: break-word;
  color: rgb(var(--v-theme-on-surface));
}
</style>

