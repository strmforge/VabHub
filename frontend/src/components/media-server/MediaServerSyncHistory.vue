<template>
  <div>
    <v-data-table
      :headers="headers"
      :items="syncHistory"
      :loading="loading"
      class="elevation-0"
    >
      <template v-slot:item.sync_type="{ item }">
        <v-chip
          :color="getSyncTypeColor(item.sync_type)"
          size="small"
          variant="flat"
        >
          {{ getSyncTypeText(item.sync_type) }}
        </v-chip>
      </template>

      <template v-slot:item.status="{ item }">
        <v-chip
          :color="getStatusColor(item.status)"
          size="small"
          variant="flat"
        >
          {{ getStatusText(item.status) }}
        </v-chip>
      </template>

      <template v-slot:item.started_at="{ item }">
        {{ formatDateTime(item.started_at) }}
      </template>

      <template v-slot:item.completed_at="{ item }">
        {{ item.completed_at ? formatDateTime(item.completed_at) : '-' }}
      </template>

      <template v-slot:item.items_synced="{ item }">
        {{ item.items_synced || 0 }}
      </template>

      <template v-slot:item.error_message="{ item }">
        <div v-if="item.error_message" class="text-error">
          <v-icon size="small" class="mr-1">mdi-alert-circle</v-icon>
          {{ item.error_message }}
        </div>
        <span v-else class="text-medium-emphasis">-</span>
      </template>

      <template v-slot:no-data>
        <div class="text-center py-8">
          <v-icon size="64" color="grey-lighten-1">mdi-history</v-icon>
          <div class="text-h6 mt-4 text-medium-emphasis">暂无同步历史</div>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { mediaServerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  serverId: number | null
  loading: boolean
}>()

const { showToast } = useToast()

const syncHistory = ref<any[]>([])

const headers = [
  { title: '同步类型', key: 'sync_type', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: '开始时间', key: 'started_at', sortable: true },
  { title: '完成时间', key: 'completed_at', sortable: true },
  { title: '同步数量', key: 'items_synced', sortable: true },
  { title: '错误信息', key: 'error_message', sortable: false }
]

// 加载同步历史
const loadSyncHistory = async () => {
  if (!props.serverId) return

  try {
    const response = await mediaServerApi.getSyncHistory(props.serverId)
    syncHistory.value = response.data || []
  } catch (error: any) {
    console.error('加载同步历史失败:', error)
    showToast('加载同步历史失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 获取同步类型颜色
const getSyncTypeColor = (type: string): string => {
  switch (type) {
    case 'libraries':
      return 'primary'
    case 'metadata':
      return 'info'
    case 'watched_status':
      return 'success'
    case 'playback_status':
      return 'warning'
    default:
      return 'grey'
  }
}

// 获取同步类型文本
const getSyncTypeText = (type: string): string => {
  switch (type) {
    case 'libraries':
      return '媒体库'
    case 'metadata':
      return '元数据'
    case 'watched_status':
      return '观看状态'
    case 'playback_status':
      return '播放状态'
    default:
      return type
  }
}

// 获取状态颜色
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    case 'running':
      return 'info'
    default:
      return 'grey'
  }
}

// 获取状态文本
const getStatusText = (status: string): string => {
  switch (status) {
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    case 'running':
      return '运行中'
    default:
      return status
  }
}

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 监听serverId变化
watch(() => props.serverId, (newId) => {
  if (newId) {
    loadSyncHistory()
  }
}, { immediate: true })

onMounted(() => {
  if (props.serverId) {
    loadSyncHistory()
  }
})
</script>

