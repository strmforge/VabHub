<template>
  <div class="tts-jobs-page">
    <v-container>
      <!-- 标题区 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-format-list-bulleted</v-icon>
          <span>TTS 任务管理</span>
          <v-chip size="small" color="primary" class="ml-2">开发工具</v-chip>
        </v-card-title>
        <v-card-subtitle>
          TTS 生成任务队列和状态追踪
        </v-card-subtitle>
      </v-card>

      <!-- 操作栏 -->
      <v-card class="mb-4">
        <v-card-actions>
          <v-btn
            color="primary"
            variant="elevated"
            prepend-icon="mdi-refresh"
            @click="loadJobs"
            :loading="loading"
          >
            刷新
          </v-btn>
          <v-spacer />
          <v-btn
            color="success"
            variant="elevated"
            prepend-icon="mdi-play"
            @click="handleRunNext"
            :loading="runNextLoading"
            :disabled="loading"
          >
            执行下一个 Job
          </v-btn>
        </v-card-actions>
      </v-card>

      <!-- 批量执行控制区 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-play-circle-multiple</v-icon>
          <span>批量执行</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row align="center">
            <v-col cols="12" md="4">
              <v-text-field
                v-model.number="maxJobsInput"
                type="number"
                label="一次执行 Job 数量"
                hint="为空 = 使用后端默认值（5）"
                persistent-hint
                min="1"
                max="100"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-btn
                color="info"
                variant="elevated"
                prepend-icon="mdi-play-circle-multiple"
                @click="handleRunBatch"
                :loading="runBatchLoading"
                :disabled="loading"
                block
              >
                执行批量 Job
              </v-btn>
            </v-col>
            <v-col cols="12">
              <v-alert type="info" variant="tonal" density="compact" class="mt-2">
                <small>
                  仅用于开发 / 调试。生产环境建议通过定时任务或 systemd 调用 Runner。
                </small>
              </v-alert>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 加载状态 -->
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4"></v-progress-linear>

      <!-- 错误提示 -->
      <v-alert v-if="errorMessage" type="error" class="mb-4">
        {{ errorMessage }}
      </v-alert>

      <!-- 消息提示 -->
      <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="5000" location="top">
        {{ snackbarMessage }}
        <template v-slot:actions>
          <v-btn variant="text" @click="snackbar = false">关闭</v-btn>
        </template>
      </v-snackbar>

      <!-- Job 列表表格 -->
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-table</v-icon>
          <span>任务列表</span>
          <v-chip size="small" class="ml-2" color="info">
            {{ jobs.length }}
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="jobs"
            :items-per-page="20"
            class="elevation-0"
            no-data-text="暂无任务"
          >
            <template v-slot:item.id="{ item }">
              <strong>#{{ item.id }}</strong>
            </template>

            <template v-slot:item.ebook_id="{ item }">
              <router-link :to="`/works/${item.ebook_id}`" class="text-primary">
                {{ item.ebook_id }}
              </router-link>
            </template>

            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.status)"
                size="small"
                variant="flat"
              >
                {{ getStatusLabel(item.status) }}
              </v-chip>
            </template>

            <template v-slot:item.provider="{ item }">
              <v-chip v-if="item.provider" size="small" color="primary" variant="outlined">
                {{ item.provider }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.requested_at="{ item }">
              {{ formatDateTime(item.requested_at) }}
            </template>

            <template v-slot:item.started_at="{ item }">
              <span v-if="item.started_at">{{ formatDateTime(item.started_at) }}</span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.finished_at="{ item }">
              <span v-if="item.finished_at">{{ formatDateTime(item.finished_at) }}</span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.progress="{ item }">
              <span v-if="item.total_chapters">
                {{ item.processed_chapters }} / {{ item.total_chapters }}
              </span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.created_files_count="{ item }">
              <v-chip size="small" color="success" variant="flat">
                {{ item.created_files_count }}
              </v-chip>
            </template>

            <template v-slot:item.error_count="{ item }">
              <v-chip
                v-if="item.error_count > 0"
                size="small"
                color="error"
                variant="flat"
              >
                {{ item.error_count }}
              </v-chip>
              <span v-else class="text-medium-emphasis">0</span>
            </template>

            <template v-slot:item.last_error="{ item }">
              <v-tooltip v-if="item.last_error">
                <template v-slot:activator="{ props }">
                  <span
                    v-bind="props"
                    class="text-error text-truncate d-inline-block"
                    style="max-width: 200px;"
                  >
                    {{ truncateError(item.last_error) }}
                  </span>
                </template>
                <span>{{ item.last_error }}</span>
              </v-tooltip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { devTTSJobsApi } from '@/services/api'
import type { TTSJob } from '@/types/tts'
import { formatDateTime } from '@/utils/formatters'

// 状态
const loading = ref(false)
const runNextLoading = ref(false)
const runBatchLoading = ref(false)
const errorMessage = ref<string | null>(null)
const jobs = ref<TTSJob[]>([])
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref<'success' | 'error' | 'warning' | 'info'>('success')
const maxJobsInput = ref<number | null>(null)

// 表格列定义
const headers = [
  { title: 'ID', key: 'id', sortable: true },
  { title: '作品 ID', key: 'ebook_id', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: 'Provider', key: 'provider', sortable: false },
  { title: '创建时间', key: 'requested_at', sortable: true },
  { title: '开始时间', key: 'started_at', sortable: true },
  { title: '完成时间', key: 'finished_at', sortable: true },
  { title: '进度', key: 'progress', sortable: false },
  { title: '新建文件数', key: 'created_files_count', sortable: true },
  { title: '错误数', key: 'error_count', sortable: true },
  { title: '最后错误', key: 'last_error', sortable: false }
]

// 加载 Job 列表
const loadJobs = async () => {
  loading.value = true
  errorMessage.value = null

  try {
    const data = await devTTSJobsApi.list({ limit: 100 })
    jobs.value = data
  } catch (err: any) {
    console.error('加载 TTS Jobs 失败:', err)
    errorMessage.value = err.response?.data?.error_message || 
                        err.response?.data?.message || 
                        err.message || 
                        '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 执行下一个 Job
const handleRunNext = async () => {
  runNextLoading.value = true

  try {
    const result = await devTTSJobsApi.runNext()
    
    if (result.success) {
      snackbarMessage.value = `Job 执行完成，状态: ${result.job?.status || 'unknown'}`
      snackbarColor.value = 'success'
      snackbar.value = true
      
      // 刷新列表
      await loadJobs()
    } else {
      snackbarMessage.value = result.message || result.reason || '执行失败'
      snackbarColor.value = 'warning'
      snackbar.value = true
    }
  } catch (err: any) {
    console.error('执行 Job 失败:', err)
    snackbarMessage.value = err.response?.data?.message || err.message || '执行失败，请稍后重试'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    runNextLoading.value = false
  }
}

// 批量执行 Job
const handleRunBatch = async () => {
  runBatchLoading.value = true

  try {
    const maxJobs = maxJobsInput.value && maxJobsInput.value > 0 ? maxJobsInput.value : undefined
    const result = await devTTSJobsApi.runBatch(maxJobs)
    
    // 生成提示消息
    snackbarMessage.value = result.message || `本次执行 ${result.run_jobs} 个 Job：成功 ${result.succeeded_jobs}，部分完成 ${result.partial_jobs}，失败 ${result.failed_jobs}`
    
    if (result.failed_jobs > 0) {
      snackbarColor.value = 'warning'
    } else if (result.succeeded_jobs > 0 || result.partial_jobs > 0) {
      snackbarColor.value = 'success'
    } else {
      snackbarColor.value = 'info'
    }
    
    snackbar.value = true
    
    // 刷新列表
    await loadJobs()
  } catch (err: any) {
    console.error('批量执行 Job 失败:', err)
    snackbarMessage.value = err.response?.data?.message || err.response?.data?.detail || err.message || '批量执行失败，请稍后重试'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    runBatchLoading.value = false
  }
}

// 获取状态颜色
const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    queued: 'grey',
    running: 'info',
    success: 'success',
    partial: 'warning',
    failed: 'error'
  }
  return colors[status] || 'default'
}

// 获取状态标签
const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    queued: '排队中',
    running: '运行中',
    success: '成功',
    partial: '部分成功',
    failed: '失败'
  }
  return labels[status] || status
}

// 截断错误信息
const truncateError = (error: string): string => {
  if (error.length <= 50) return error
  return error.substring(0, 50) + '...'
}

// 组件挂载时加载
onMounted(() => {
  loadJobs()
})
</script>

<style scoped>
.tts-jobs-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>

