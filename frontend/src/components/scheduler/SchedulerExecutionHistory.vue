<template>
  <div>
    <v-data-table
      :headers="headers"
      :items="executions"
      :loading="loading"
      class="elevation-0"
    >
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

      <template v-slot:item.duration="{ item }">
        {{ item.duration ? formatDuration(item.duration) : '-' }}
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
          <div class="text-h6 mt-4 text-medium-emphasis">暂无执行历史</div>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { schedulerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  jobId: string
  loading: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

const { showToast } = useToast()

const executions = ref<any[]>([])

const headers = [
  { title: '状态', key: 'status', sortable: true },
  { title: '开始时间', key: 'started_at', sortable: true },
  { title: '完成时间', key: 'completed_at', sortable: true },
  { title: '耗时', key: 'duration', sortable: true },
  { title: '错误信息', key: 'error_message', sortable: false }
]

// 加载执行历史
const loadExecutions = async () => {
  if (!props.jobId || !props.jobId.trim()) return

  try {
    const response = await schedulerApi.getJobExecutions(props.jobId)
    executions.value = response.data || []
  } catch (error: any) {
    console.error('加载执行历史失败:', error)
    showToast('加载执行历史失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 获取状态颜色
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'running':
      return 'info'
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'grey'
  }
}

// 获取状态文本
const getStatusText = (status: string): string => {
  switch (status) {
    case 'running':
      return '运行中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    default:
      return status
  }
}

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 格式化时长
const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds.toFixed(2)}秒`
  } else if (seconds < 3600) {
    return `${(seconds / 60).toFixed(2)}分钟`
  } else {
    return `${(seconds / 3600).toFixed(2)}小时`
  }
}

// 监听jobId变化
watch(() => props.jobId, (newId) => {
  if (newId && newId.trim()) {
    loadExecutions()
  }
}, { immediate: true })

onMounted(() => {
  if (props.jobId && props.jobId.trim()) {
    loadExecutions()
  }
})

// 暴露刷新方法
defineExpose({
  loadExecutions
})
</script>

