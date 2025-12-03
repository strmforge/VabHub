<template>
  <v-container fluid>
    <!-- 页面标题 -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon size="32" color="primary" class="mr-3">mdi-clock-outline</v-icon>
          <h1 class="text-h4">调度器状态监控</h1>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-sync"
            @click="syncTasks"
            :loading="syncing"
          >
            同步任务
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- 统计卡片 -->
    <v-row v-if="statistics">
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="primary" class="mr-3">mdi-format-list-bulleted</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">总任务数</div>
                <div class="text-h5">{{ statistics.total_tasks || 0 }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="success" class="mr-3">mdi-check-circle</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">启用任务</div>
                <div class="text-h5">{{ statistics.enabled_tasks || 0 }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="info" class="mr-3">mdi-chart-line</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">总体成功率</div>
                <div class="text-h5">{{ (statistics.overall_success_rate || 0).toFixed(1) }}%</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="warning" class="mr-3">mdi-alert</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">失败任务</div>
                <div class="text-h5">{{ statistics.failed_tasks || 0 }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 任务列表 -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <span>定时任务列表</span>
            <div class="d-flex align-center ga-2">
              <v-select
                v-model="filterStatus"
                :items="statusOptions"
                label="状态"
                variant="outlined"
                density="compact"
                style="width: 150px"
                clearable
                @update:model-value="loadJobs"
              />
              <v-select
                v-model="filterEnabled"
                :items="enabledOptions"
                label="启用状态"
                variant="outlined"
                density="compact"
                style="width: 150px"
                clearable
                @update:model-value="loadJobs"
              />
              <v-btn
                icon="mdi-refresh"
                variant="text"
                size="small"
                @click="loadJobs"
                :loading="loading"
              />
            </div>
          </v-card-title>

          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="jobs"
              :loading="loading"
              class="elevation-0"
              :items-per-page="20"
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

              <template v-slot:item.enabled="{ item }">
                <v-chip
                  :color="item.enabled ? 'success' : 'grey'"
                  size="small"
                  variant="flat"
                >
                  {{ item.enabled ? '启用' : '禁用' }}
                </v-chip>
              </template>

              <template v-slot:item.next_run_time="{ item }">
                {{ item.next_run_time ? formatDateTime(item.next_run_time) : '-' }}
              </template>

              <template v-slot:item.last_run_time="{ item }">
                {{ item.last_run_time ? formatDateTime(item.last_run_time) : '-' }}
              </template>

              <template v-slot:item.success_rate="{ item }">
                <div class="d-flex align-center">
                  <v-progress-circular
                    :model-value="item.success_rate"
                    :color="getSuccessRateColor(item.success_rate)"
                    size="24"
                    width="3"
                    class="mr-2"
                  >
                    {{ item.success_rate.toFixed(0) }}%
                  </v-progress-circular>
                  <span class="text-body-2">
                    {{ item.success_count }}/{{ item.run_count }}
                  </span>
                </div>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn
                  icon="mdi-eye"
                  variant="text"
                  size="small"
                  @click="viewJobDetails(item)"
                />
                <v-btn
                  icon="mdi-play"
                  variant="text"
                  size="small"
                  color="primary"
                  @click="runJob(item.id)"
                  :loading="runningJobs.includes(item.id)"
                />
              </template>

              <template v-slot:no-data>
                <div class="text-center py-8">
                  <v-icon size="64" color="grey-lighten-1">mdi-clock-outline</v-icon>
                  <div class="text-h6 mt-4 text-medium-emphasis">暂无任务</div>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 任务详情对话框 -->
    <SchedulerJobDetailDialog
      v-model="detailDialogVisible"
      :job-id="selectedJobId"
      @refresh="loadJobs"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { schedulerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import SchedulerJobDetailDialog from '@/components/scheduler/SchedulerJobDetailDialog.vue'

const { showToast } = useToast()

const jobs = ref<any[]>([])
const statistics = ref<any>(null)
const loading = ref(false)
const syncing = ref(false)
const filterStatus = ref<string | null>(null)
const filterEnabled = ref<boolean | null>(null)
const detailDialogVisible = ref(false)
const selectedJobId = ref<string | null>(null)
const runningJobs = ref<string[]>([])

const statusOptions = [
  { title: '待执行', value: 'pending' },
  { title: '运行中', value: 'running' },
  { title: '已完成', value: 'completed' },
  { title: '失败', value: 'failed' },
  { title: '禁用', value: 'disabled' }
]

const enabledOptions = [
  { title: '启用', value: true },
  { title: '禁用', value: false }
]

const headers = [
  { title: '任务名称', key: 'name', sortable: true },
  { title: '任务类型', key: 'task_type', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: '启用', key: 'enabled', sortable: true },
  { title: '下次运行', key: 'next_run_time', sortable: true },
  { title: '最后运行', key: 'last_run_time', sortable: true },
  { title: '成功率', key: 'success_rate', sortable: true },
  { title: '运行次数', key: 'run_count', sortable: true },
  { title: '操作', key: 'actions', sortable: false, align: 'end' }
]

// 计算成功率
const getSuccessRate = (job: any): number => {
  return job.run_count > 0
    ? (job.success_count / job.run_count) * 100
    : 0
}

// 加载任务列表
const loadJobs = async () => {
  try {
    loading.value = true
    const params: any = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterEnabled.value !== null) params.enabled = filterEnabled.value
    
    const response = await schedulerApi.getJobs(params)
    jobs.value = response.data || []
  } catch (error: any) {
    console.error('加载任务列表失败:', error)
    showToast('加载任务列表失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await schedulerApi.getStatistics()
    statistics.value = response.data
  } catch (error: any) {
    console.error('加载统计信息失败:', error)
  }
}

// 同步任务
const syncTasks = async () => {
  try {
    syncing.value = true
    await schedulerApi.syncTasks()
    showToast('同步成功', 'success')
    await Promise.all([loadJobs(), loadStatistics()])
  } catch (error: any) {
    showToast('同步失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    syncing.value = false
  }
}

// 查看任务详情
const viewJobDetails = (job: any) => {
  selectedJobId.value = job.id
  detailDialogVisible.value = true
}

// 立即执行任务
const runJob = async (jobId: string) => {
  if (!confirm('确定要立即执行这个任务吗？')) {
    return
  }

  try {
    runningJobs.value.push(jobId)
    await schedulerApi.runJob(jobId)
    showToast('任务执行成功', 'success')
    await loadJobs()
  } catch (error: any) {
    showToast('任务执行失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    runningJobs.value = runningJobs.value.filter(id => id !== jobId)
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

onMounted(() => {
  loadJobs()
  loadStatistics()
})
</script>

<script lang="ts">
export default {
  name: 'SchedulerMonitor'
}
</script>

<style scoped>
.v-card {
  border-radius: 12px;
}
</style>

