<template>
  <v-dialog
    v-model="modelValue"
    max-width="800"
    scrollable
    persistent
  >
    <v-card>
      <v-card-item class="py-3">
        <template #prepend>
          <v-icon icon="mdi-history" class="me-2" />
        </template>
        <v-card-title class="text-h6">
          执行记录
        </v-card-title>
        <v-card-subtitle v-if="workflowId">
          工作流ID: {{ workflowId }}
        </v-card-subtitle>
        <template #append>
          <v-btn
            icon="mdi-refresh"
            variant="text"
            size="small"
            @click="loadExecutions"
            :loading="loading"
          />
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="modelValue = false"
          />
        </template>
      </v-card-item>

      <v-card-text>
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>

        <div v-else-if="executions.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-history</v-icon>
          <div class="text-h6 text-medium-emphasis mb-2">暂无执行记录</div>
        </div>

        <v-list v-else density="compact">
          <v-list-item
            v-for="execution in executions"
            :key="execution.id"
            class="execution-item"
          >
            <template #prepend>
              <v-avatar
                :color="getStatusColor(execution.status)"
                size="40"
              >
                <v-icon color="white">{{ getStatusIcon(execution.status) }}</v-icon>
              </v-avatar>
            </template>

            <v-list-item-title>
              执行 #{{ execution.id }}
            </v-list-item-title>
            <v-list-item-subtitle>
              <div class="d-flex align-center flex-wrap ga-2 mt-1">
                <v-chip
                  :color="getStatusColor(execution.status)"
                  size="x-small"
                  variant="flat"
                >
                  {{ getStatusLabel(execution.status) }}
                </v-chip>
                <span class="text-caption text-medium-emphasis">
                  {{ formatDate(execution.started_at) }}
                </span>
                <span v-if="execution.completed_at" class="text-caption text-medium-emphasis">
                  耗时: {{ getDuration(execution.started_at, execution.completed_at) }}
                </span>
              </div>
              <div v-if="execution.error_message" class="text-caption text-error mt-1">
                {{ execution.error_message }}
              </div>
            </v-list-item-subtitle>

            <template #append>
              <v-btn
                icon="mdi-eye"
                size="small"
                variant="text"
                @click="viewExecutionDetail(execution)"
              />
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="modelValue = false"
        >
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 执行详情对话框 -->
    <v-dialog
      v-model="showDetailDialog"
      max-width="700"
      scrollable
    >
      <v-card v-if="selectedExecution">
        <v-card-item class="py-3">
          <v-card-title>执行详情 #{{ selectedExecution.id }}</v-card-title>
          <template #append>
            <v-btn
              icon="mdi-close"
              variant="text"
              size="small"
              @click="showDetailDialog = false"
            />
          </template>
        </v-card-item>
        <v-card-text>
          <v-list density="compact">
            <v-list-item>
              <v-list-item-title>状态</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip
                  :color="getStatusColor(selectedExecution.status)"
                  size="small"
                  variant="flat"
                >
                  {{ getStatusLabel(selectedExecution.status) }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>开始时间</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(selectedExecution.started_at) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="selectedExecution.completed_at">
              <v-list-item-title>完成时间</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(selectedExecution.completed_at) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="selectedExecution.error_message">
              <v-list-item-title>错误信息</v-list-item-title>
              <v-list-item-subtitle class="text-error">{{ selectedExecution.error_message }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="selectedExecution.result">
              <v-list-item-title>执行结果</v-list-item-title>
              <v-list-item-subtitle>
                <pre class="text-caption mt-2">{{ JSON.stringify(selectedExecution.result, null, 2) }}</pre>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

interface Props {
  modelValue: boolean
  workflowId?: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const loading = ref(false)
const executions = ref<any[]>([])
const showDetailDialog = ref(false)
const selectedExecution = ref<any>(null)

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loadExecutions = async () => {
  if (!props.workflowId) return

  loading.value = true
  try {
    const response = await api.get(`/workflows/${props.workflowId}/executions`, {
      params: {
        limit: 50
      }
    })
    executions.value = response.data
  } catch (error: any) {
    console.error('加载执行记录失败:', error)
    executions.value = []
  } finally {
    loading.value = false
  }
}

const viewExecutionDetail = (execution: any) => {
  selectedExecution.value = execution
  showDetailDialog.value = true
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    running: 'info',
    completed: 'success',
    failed: 'error'
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    running: 'mdi-loading',
    completed: 'mdi-check',
    failed: 'mdi-alert'
  }
  return icons[status] || 'mdi-help'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

const getDuration = (start: string, end: string) => {
  if (!start || !end) return ''
  try {
    const startDate = new Date(start)
    const endDate = new Date(end)
    const diff = endDate.getTime() - startDate.getTime()
    const seconds = Math.floor(diff / 1000)
    if (seconds < 60) return `${seconds}秒`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}分钟`
    const hours = Math.floor(minutes / 60)
    return `${hours}小时${minutes % 60}分钟`
  } catch {
    return ''
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.workflowId) {
    loadExecutions()
  }
})

watch(() => props.workflowId, () => {
  if (props.modelValue && props.workflowId) {
    loadExecutions()
  }
})
</script>

<style scoped>
.execution-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

