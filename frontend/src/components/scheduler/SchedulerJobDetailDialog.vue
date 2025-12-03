<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="900"
    scrollable
  >
    <v-card v-if="jobData">
      <v-card-title class="d-flex align-center justify-space-between">
        <span class="text-h5">{{ jobData.name }}</span>
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-card-text>
        <v-tabs v-model="activeTab" bg-color="surface">
          <v-tab value="info">
            <v-icon start>mdi-information</v-icon>
            任务信息
          </v-tab>
          <v-tab value="executions">
            <v-icon start>mdi-history</v-icon>
            执行历史
          </v-tab>
        </v-tabs>

        <v-window v-model="activeTab" class="mt-4">
          <!-- 任务信息标签页 -->
          <v-window-item value="info">
            <v-row>
              <v-col cols="12" md="6">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">基本信息</v-card-title>
                  <v-card-text>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">任务ID</div>
                      <div class="text-body-1">{{ jobData.id }}</div>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">任务名称</div>
                      <div class="text-body-1">{{ jobData.name }}</div>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">任务类型</div>
                      <div class="text-body-1">{{ jobData.task_type }}</div>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">状态</div>
                      <v-chip
                        :color="getStatusColor(jobData.status)"
                        size="small"
                        variant="flat"
                      >
                        {{ getStatusText(jobData.status) }}
                      </v-chip>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">启用状态</div>
                      <v-chip
                        :color="jobData.enabled ? 'success' : 'grey'"
                        size="small"
                        variant="flat"
                      >
                        {{ jobData.enabled ? '启用' : '禁用' }}
                      </v-chip>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="12" md="6">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">触发器信息</v-card-title>
                  <v-card-text>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">触发器类型</div>
                      <div class="text-body-1">{{ jobData.trigger_type }}</div>
                    </div>
                    <div class="mb-3" v-if="jobData.trigger_config">
                      <div class="text-caption text-medium-emphasis">触发器配置</div>
                      <pre class="text-body-2">{{ JSON.stringify(jobData.trigger_config, null, 2) }}</pre>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">下次运行时间</div>
                      <div class="text-body-1">
                        {{ jobData.next_run_time ? formatDateTime(jobData.next_run_time) : '-' }}
                      </div>
                    </div>
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">最后运行时间</div>
                      <div class="text-body-1">
                        {{ jobData.last_run_time ? formatDateTime(jobData.last_run_time) : '-' }}
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="12">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">执行统计</v-card-title>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" sm="4">
                        <div class="text-center">
                          <div class="text-h4 text-primary">{{ jobData.run_count || 0 }}</div>
                          <div class="text-caption text-medium-emphasis">总运行次数</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="4">
                        <div class="text-center">
                          <div class="text-h4 text-success">{{ jobData.success_count || 0 }}</div>
                          <div class="text-caption text-medium-emphasis">成功次数</div>
                        </div>
                      </v-col>
                      <v-col cols="12" sm="4">
                        <div class="text-center">
                          <div class="text-h4 text-error">{{ jobData.fail_count || 0 }}</div>
                          <div class="text-caption text-medium-emphasis">失败次数</div>
                        </div>
                      </v-col>
                    </v-row>
                    <v-divider class="my-4" />
                    <div class="text-center">
                      <div class="text-h5">
                        成功率: {{ jobData.run_count > 0
                          ? ((jobData.success_count / jobData.run_count) * 100).toFixed(1)
                          : 0 }}%
                      </div>
                      <v-progress-linear
                        :model-value="jobData.run_count > 0
                          ? (jobData.success_count / jobData.run_count) * 100
                          : 0"
                        :color="getSuccessRateColor(jobData.run_count > 0
                          ? (jobData.success_count / jobData.run_count) * 100
                          : 0)"
                        height="24"
                        rounded
                        class="mt-2"
                      />
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>

          <!-- 执行历史标签页 -->
          <v-window-item value="executions">
            <SchedulerExecutionHistory
              :job-id="jobId || ''"
              :loading="loadingExecutions"
              @refresh="loadExecutions"
            />
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          prepend-icon="mdi-play"
          @click="runJob"
          :loading="running"
        >
          立即执行
        </v-btn>
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 加载状态 -->
    <v-card v-else>
      <v-card-text class="text-center py-8">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <div class="mt-4 text-body-2 text-medium-emphasis">加载中...</div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { schedulerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import SchedulerExecutionHistory from './SchedulerExecutionHistory.vue'

const props = defineProps<{
  modelValue: boolean
  jobId: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  refresh: []
}>()

const { showToast } = useToast()

const jobData = ref<any>(null)
const activeTab = ref('info')
const loading = ref(false)
const loadingExecutions = ref(false)
const running = ref(false)

// 加载任务详情
const loadJobDetails = async () => {
  if (!props.jobId) return

  try {
    loading.value = true
    const response = await schedulerApi.getJob(props.jobId)
    jobData.value = response.data
  } catch (error: any) {
    console.error('加载任务详情失败:', error)
    showToast('加载任务详情失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

// 加载执行历史
const loadExecutions = async () => {
  loadingExecutions.value = true
  // 执行历史由子组件加载
  loadingExecutions.value = false
}

// 立即执行任务
const runJob = async () => {
  if (!props.jobId) return

  if (!confirm('确定要立即执行这个任务吗？')) {
    return
  }

  try {
    running.value = true
    await schedulerApi.runJob(props.jobId)
    showToast('任务执行成功', 'success')
    emit('refresh')
    await loadJobDetails()
  } catch (error: any) {
    showToast('任务执行失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    running.value = false
  }
}

// 监听对话框打开
watch(() => props.modelValue, (newVal) => {
  if (newVal && props.jobId) {
    loadJobDetails()
    activeTab.value = 'info'
  }
})

// 监听jobId变化
watch(() => props.jobId, (newId) => {
  if (newId && props.modelValue) {
    loadJobDetails()
  }
})

// 获取状态颜色
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'running':
      return 'info'
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    case 'disabled':
      return 'grey'
    default:
      return 'warning'
  }
}

// 获取状态文本
const getStatusText = (status: string): string => {
  switch (status) {
    case 'pending':
      return '待执行'
    case 'running':
      return '运行中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    case 'disabled':
      return '禁用'
    default:
      return status
  }
}

// 获取成功率颜色
const getSuccessRateColor = (rate: number): string => {
  if (rate >= 90) return 'success'
  if (rate >= 70) return 'warning'
  return 'error'
}

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}
</script>

