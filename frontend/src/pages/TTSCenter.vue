<template>
  <div class="tts-center-page">
    <v-container>
      <PageHeader
        title="TTS 有声书中心"
        subtitle="查看和管理 TTS 有声书生成任务"
      />

      <!-- 通知提示 -->
      <v-alert
        type="info"
        variant="tonal"
        density="compact"
        class="mb-4"
        icon="mdi-bell-outline"
      >
        <template v-slot:prepend>
          <v-icon>mdi-bell-outline</v-icon>
        </template>
        当 TTS 任务完成时，会在页面右上角的铃铛中收到通知。
      </v-alert>

      <!-- 批量生成 TTS 任务卡片 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-play-circle-multiple</v-icon>
          <span>批量生成 TTS 任务</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <!-- 筛选表单 -->
          <v-form ref="batchFilterForm" v-model="batchFilterValid">
            <v-row>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="batchFilter.language"
                  label="语言"
                  placeholder="如: zh-CN"
                  variant="outlined"
                  density="compact"
                  clearable
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="batchFilter.author_substring"
                  label="作者包含"
                  variant="outlined"
                  density="compact"
                  clearable
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="batchFilter.series_substring"
                  label="系列包含"
                  variant="outlined"
                  density="compact"
                  clearable
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model="batchFilter.tag_keyword"
                  label="标签关键字"
                  variant="outlined"
                  density="compact"
                  clearable
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model.number="batchFilter.max_candidates"
                  label="最大候选数"
                  type="number"
                  variant="outlined"
                  density="compact"
                  :min="1"
                  :max="500"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" md="4">
                <v-checkbox
                  v-model="batchFilter.only_without_audiobook"
                  label="只选择没有任何有声书的作品"
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-checkbox
                  v-model="batchFilter.only_without_active_job"
                  label="只选择没有活跃任务的作品"
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-checkbox
                  v-model="batchEnqueueRequest.skip_if_has_tts"
                  label="跳过已经有 TTS 有声书的作品"
                  density="compact"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-btn
                  color="primary"
                  :loading="loadingPreview"
                  @click="handlePreviewBatch"
                >
                  <v-icon start>mdi-eye</v-icon>
                  预览候选作品
                </v-btn>
              </v-col>
            </v-row>
          </v-form>

          <!-- 预览结果 -->
          <v-card v-if="batchPreviewResult" class="mt-4" variant="outlined">
            <v-card-title class="text-body-1">
              共匹配 {{ batchPreviewResult.total_candidates }} 个作品
            </v-card-title>
            <v-divider />
            <v-card-text>
              <v-data-table
                :headers="batchPreviewHeaders"
                :items="batchPreviewResult.items"
                :items-per-page="10"
                no-data-text="暂无候选作品"
              >
                <template v-slot:item.title="{ item }">
                  <router-link
                    :to="{ name: 'WorkDetail', params: { ebookId: item.ebook_id } }"
                    class="text-primary text-decoration-none"
                  >
                    {{ item.title }}
                  </router-link>
                </template>
                <template v-slot:item.has_audiobook="{ item }">
                  <v-chip size="small" :color="item.has_audiobook ? 'info' : 'default'" variant="flat">
                    {{ item.has_audiobook ? '有有声书' : '无有声书' }}
                  </v-chip>
                </template>
                <template v-slot:item.has_tts_audiobook="{ item }">
                  <v-chip size="small" :color="item.has_tts_audiobook ? 'success' : 'default'" variant="flat">
                    {{ item.has_tts_audiobook ? '有 TTS' : '无 TTS' }}
                  </v-chip>
                </template>
                <template v-slot:item.active_job_status="{ item }">
                  <v-chip
                    v-if="item.active_job_status"
                    size="small"
                    :color="getTTSStatusColor(item.active_job_status)"
                    variant="flat"
                  >
                    {{ getTTSStatusLabel(item.active_job_status) }}
                  </v-chip>
                  <span v-else class="text-medium-emphasis">-</span>
                </template>
              </v-data-table>

              <!-- 执行区 -->
              <v-row class="mt-4">
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model.number="batchEnqueueRequest.max_new_jobs"
                    label="本次最多创建 Job 数量"
                    type="number"
                    variant="outlined"
                    density="compact"
                    :min="1"
                    :max="200"
                  />
                </v-col>
                <v-col cols="12" md="8" class="d-flex align-center">
                  <v-btn
                    color="success"
                    :loading="loadingEnqueue"
                    :disabled="!batchPreviewResult || batchPreviewResult.items.length === 0"
                    @click="handleEnqueueBatch"
                  >
                    <v-icon start>mdi-play-circle-multiple</v-icon>
                    批量创建 TTS 任务
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-card-text>
      </v-card>

      <!-- 简要说明块 -->
      <v-card class="mb-4" v-if="ttsHealth">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-information</v-icon>
          <span>TTS 系统状态</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4">
              <div class="text-body-2 mb-1">Provider</div>
              <v-chip size="small" color="primary" variant="flat">
                {{ ttsHealth.provider || '未配置' }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="4">
              <div class="text-body-2 mb-1">状态</div>
              <v-chip
                size="small"
                :color="getHealthStatusColor(ttsHealth.status)"
                variant="flat"
              >
                {{ getHealthStatusLabel(ttsHealth.status) }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="4" v-if="ttsHealth.last_used_at">
              <div class="text-body-2 mb-1">最近使用</div>
              <div class="text-caption text-medium-emphasis">
                {{ formatRelativeTime(ttsHealth.last_used_at) }}
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 主表格 -->
      <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
          <div class="d-flex align-center">
            <v-icon class="mr-2" color="purple">mdi-text-to-speech</v-icon>
            <span>TTS 任务列表</span>
          </div>
          <div class="d-flex align-center gap-2">
            <v-select
              v-model="statusFilter"
              :items="statusFilterOptions"
              label="状态筛选"
              variant="outlined"
              density="compact"
              hide-details
              style="max-width: 200px;"
              clearable
            />
            <v-btn
              icon
              variant="text"
              @click="loadOverview"
              :loading="loading"
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </div>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <!-- 加载状态 -->
          <v-progress-linear
            v-if="loading"
            indeterminate
            color="primary"
            class="mb-4"
          />

          <!-- 表格 -->
          <v-data-table
            v-if="!loading"
            :headers="tableHeaders"
            :items="overviewItems"
            :items-per-page="20"
            no-data-text="暂无 TTS 任务"
          >
            <template v-slot:item.ebook_title="{ item }">
              <router-link
                :to="{ name: 'WorkDetail', params: { ebookId: item.ebook_id } }"
                class="text-primary text-decoration-none"
              >
                {{ item.ebook_title }}
              </router-link>
            </template>

            <template v-slot:item.ebook_author="{ item }">
              <span class="text-body-2">{{ item.ebook_author || '-' }}</span>
            </template>

            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getTTSStatusColor(item.status)"
                size="small"
                variant="flat"
              >
                <v-icon
                  start
                  size="small"
                  :icon="getTTSStatusIcon(item.status)"
                ></v-icon>
                {{ getTTSStatusLabel(item.status) }}
              </v-chip>
            </template>

            <template v-slot:item.progress="{ item }">
              <div v-if="item.progress && item.progress.total_chapters">
                <span class="text-body-2">
                  {{ item.progress.generated_chapters || 0 }} / {{ item.progress.total_chapters }}
                </span>
                <v-progress-linear
                  :model-value="
                    item.progress.total_chapters > 0
                      ? ((item.progress.generated_chapters || 0) / item.progress.total_chapters) * 100
                      : 0
                  "
                  color="primary"
                  height="6"
                  class="mt-1"
                />
              </div>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.requested_at="{ item }">
              <div class="text-body-2">
                {{ formatDate(item.requested_at) }}
              </div>
              <div class="text-caption text-medium-emphasis">
                {{ formatRelativeTime(item.requested_at) }}
              </div>
            </template>

            <template v-slot:item.last_message="{ item }">
              <span
                v-if="item.last_message"
                class="text-body-2"
                :class="{
                  'text-error': item.status === 'failed',
                  'text-warning': item.status === 'partial'
                }"
              >
                {{ item.last_message }}
              </span>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                v-if="item.status === 'failed' || item.status === 'partial'"
                size="small"
                color="primary"
                variant="outlined"
                :loading="enqueueLoading[item.ebook_id]"
                @click="handleRequeue(item)"
              >
                <v-icon start size="small">mdi-refresh</v-icon>
                重新生成
              </v-btn>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import { ttsUserApi, adminSettingsApi } from '@/services/api'
import type {
  UserTTSJobOverviewItem,
  UserTTSBatchFilter,
  UserTTSBatchPreviewResponse,
  UserTTSBatchEnqueueRequest,
  UserTTSBatchEnqueueResult
} from '@/types/tts'
// formatRelativeTime 在本地定义
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

// 状态
const loading = ref(false)
const overviewItems = ref<UserTTSJobOverviewItem[]>([])
const statusFilter = ref<string | null>(null)
const ttsHealth = ref<any>(null)
const enqueueLoading = ref<Record<number, boolean>>({})

// 批量生成状态
const batchFilterValid = ref(false)
const batchFilter = ref<UserTTSBatchFilter>({
  language: null,
  author_substring: null,
  series_substring: null,
  tag_keyword: null,
  only_without_audiobook: true,
  only_without_active_job: true,
  max_candidates: 100
})
const batchEnqueueRequest = ref<UserTTSBatchEnqueueRequest>({
  filter: batchFilter.value,
  max_new_jobs: 20,
  skip_if_has_tts: true
})
const batchPreviewResult = ref<UserTTSBatchPreviewResponse | null>(null)
const loadingPreview = ref(false)
const loadingEnqueue = ref(false)
const batchEnqueueResult = ref<UserTTSBatchEnqueueResult | null>(null)

// 批量预览表格列
const batchPreviewHeaders = [
  { title: '标题', key: 'title', sortable: true },
  { title: '作者', key: 'author', sortable: true },
  { title: '语言', key: 'language', sortable: true },
  { title: '有声书', key: 'has_audiobook', sortable: false },
  { title: 'TTS 有声书', key: 'has_tts_audiobook', sortable: false },
  { title: '活跃 Job', key: 'active_job_status', sortable: false },
  { title: '最近 Job', key: 'last_job_status', sortable: false }
]

// 状态筛选选项
const statusFilterOptions = [
  { title: '全部', value: null },
  { title: '队列中', value: 'queued' },
  { title: '生成中', value: 'running' },
  { title: '部分完成', value: 'partial' },
  { title: '已完成', value: 'success' },
  { title: '失败', value: 'failed' }
]

// 表格列
const tableHeaders = [
  { title: '作品标题', key: 'ebook_title', sortable: true },
  { title: '作者', key: 'ebook_author', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: '进度', key: 'progress', sortable: false },
  { title: '最近执行', key: 'requested_at', sortable: true },
  { title: '信息', key: 'last_message', sortable: false },
  { title: '操作', key: 'actions', sortable: false }
]

// 加载概览
const loadOverview = async () => {
  loading.value = true
  try {
    const params: any = { limit: 50 }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const items = await ttsUserApi.getOverview(params)
    overviewItems.value = items
  } catch (err: any) {
    console.error('加载 TTS 概览失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 加载 TTS 健康状态
const loadTTSHealth = async () => {
  try {
    const response = await adminSettingsApi.getTTSSettings()
    if (response.data) {
      ttsHealth.value = {
        provider: response.data.provider,
        status: response.data.status,
        last_used_at: response.data.last_used_at
      }
    }
  } catch (err: any) {
    console.warn('加载 TTS 健康状态失败:', err)
  }
}

// 重新生成
const handleRequeue = async (item: UserTTSJobOverviewItem) => {
  enqueueLoading.value[item.ebook_id] = true
  try {
    const response = await ttsUserApi.enqueueForWork(item.ebook_id)
    if (response.success) {
      toast.success(response.message || '已加入 TTS 队列')
      // 刷新列表
      await loadOverview()
    } else {
      toast.error(response.message || '操作失败')
    }
  } catch (err: any) {
    console.error('重新生成 TTS 失败:', err)
    toast.error(err.response?.data?.detail || err.message || '操作失败')
  } finally {
    enqueueLoading.value[item.ebook_id] = false
  }
}

// 批量预览
const handlePreviewBatch = async () => {
  loadingPreview.value = true
  batchPreviewResult.value = null
  try {
    // 更新请求中的 filter
    batchEnqueueRequest.value.filter = batchFilter.value
    const result = await ttsUserApi.batchPreview(batchFilter.value)
    batchPreviewResult.value = result
    toast.success(`找到 ${result.total_candidates} 个候选作品`)
  } catch (err: any) {
    console.error('预览批量 TTS 失败:', err)
    toast.error(err.response?.data?.detail || err.message || '预览失败')
  } finally {
    loadingPreview.value = false
  }
}

// 批量创建 TTS 任务
const handleEnqueueBatch = async () => {
  if (!batchPreviewResult.value || batchPreviewResult.value.items.length === 0) {
    toast.warning('请先预览候选作品')
    return
  }

  // 确认对话框
  const estimatedCount = Math.min(
    batchEnqueueRequest.value.max_new_jobs,
    batchPreviewResult.value.items.length
  )
  const confirmed = confirm(
    `预计会为 ${estimatedCount} 个作品创建新任务。\n` +
    `会消耗 TTS 配额（视配置）。\n\n` +
    `确定要继续吗？`
  )

  if (!confirmed) {
    return
  }

  loadingEnqueue.value = true
  batchEnqueueResult.value = null
  try {
    // 确保 filter 是最新的
    batchEnqueueRequest.value.filter = batchFilter.value
    const result = await ttsUserApi.batchEnqueue(batchEnqueueRequest.value)
    batchEnqueueResult.value = result

    // 显示结果
    const message = [
      `新建任务: ${result.enqueued_new_jobs}`,
      result.already_had_jobs > 0 ? `已有任务: ${result.already_had_jobs}` : null,
      result.skipped_has_audiobook > 0 ? `跳过（已有有声书）: ${result.skipped_has_audiobook}` : null,
      result.skipped_has_tts > 0 ? `跳过（已有 TTS）: ${result.skipped_has_tts}` : null,
      result.skipped_has_active_job > 0 ? `跳过（活跃任务）: ${result.skipped_has_active_job}` : null
    ].filter(Boolean).join('\n')

    toast.success(message, { timeout: 5000 })

    // 刷新列表和预览
    await loadOverview()
    await handlePreviewBatch()
  } catch (err: any) {
    console.error('批量创建 TTS 任务失败:', err)
    toast.error(err.response?.data?.detail || err.message || '批量创建失败')
  } finally {
    loadingEnqueue.value = false
  }
}

// 辅助函数
const getTTSStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    queued: 'info',
    running: 'primary',
    partial: 'warning',
    success: 'success',
    failed: 'error'
  }
  return colors[status] || 'default'
}

const getTTSStatusIcon = (status: string): string => {
  const icons: Record<string, string> = {
    queued: 'mdi-clock-outline',
    running: 'mdi-play-circle',
    partial: 'mdi-alert-circle',
    success: 'mdi-check-circle',
    failed: 'mdi-alert-circle'
  }
  return icons[status] || 'mdi-help-circle'
}

const getTTSStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    queued: '队列中',
    running: '生成中',
    partial: '部分完成',
    success: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

const getHealthStatusColor = (status?: string): string => {
  const colors: Record<string, string> = {
    ok: 'success',
    degraded: 'warning',
    disabled: 'default'
  }
  return colors[status || ''] || 'default'
}

const getHealthStatusLabel = (status?: string): string => {
  const labels: Record<string, string> = {
    ok: '正常',
    degraded: '降级',
    disabled: '已禁用'
  }
  return labels[status || ''] || status || '未知'
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatRelativeTimeLocal = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return formatDate(dateStr)
}

// 使用本地定义的 formatRelativeTime
const formatRelativeTime = formatRelativeTimeLocal

// 监听状态筛选变化
watch(statusFilter, () => {
  loadOverview()
})

// 初始化
onMounted(() => {
  loadOverview()
  loadTTSHealth()
})
</script>

<style scoped>
.tts-center-page {
  min-height: 100vh;
}
</style>

