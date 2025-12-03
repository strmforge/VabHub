<template>
  <div class="dev-tts-storage-page">
    <v-container>
      <PageHeader
        title="TTS 存储管理（Dev）"
        subtitle="查看和管理 TTS 存储目录"
      />

      <!-- Dev 警告 -->
      <v-alert
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-4"
        icon="mdi-alert"
      >
        <template v-slot:prepend>
          <v-icon>mdi-alert</v-icon>
        </template>
        <strong>Dev 专用 / 高危操作</strong>：此页面用于管理 TTS 缓存目录，清理操作不可恢复。只影响 TTS 临时文件，不会删除已导入的有声书。
      </v-alert>

      <!-- Storage 概览卡片 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center justify-space-between">
          <div class="d-flex align-center">
            <v-icon class="mr-2" color="info">mdi-folder-information</v-icon>
            <span>存储概览</span>
          </div>
          <v-btn
            icon
            variant="text"
            @click="loadOverview"
            :loading="loadingOverview"
          >
            <v-icon>mdi-refresh</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-progress-linear
            v-if="loadingOverview"
            indeterminate
            color="primary"
            class="mb-4"
          />

          <div v-if="overview && !loadingOverview">
            <v-row class="mb-4">
              <v-col cols="12">
                <div class="text-body-2 mb-1">存储路径</div>
                <div class="text-body-1 font-weight-medium">{{ overview.root }}</div>
              </v-col>
            </v-row>

            <v-row class="mb-4">
              <v-col cols="12" md="6">
                <div class="text-body-2 mb-1">总文件数</div>
                <div class="text-h6">{{ overview.total_files.toLocaleString() }}</div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-body-2 mb-1">总大小</div>
                <div class="text-h6">{{ formatBytes(overview.total_size_bytes) }}</div>
              </v-col>
            </v-row>

            <!-- 按分类统计 -->
            <v-divider class="my-4" />
            <div class="text-body-2 mb-2">按分类统计</div>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>类别</th>
                  <th>文件数</th>
                  <th>大小</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(stats, category) in overview.by_category" :key="category">
                  <td>
                    <v-chip size="small" :color="getCategoryColor(category)" variant="flat">
                      {{ getCategoryLabel(category) }}
                    </v-chip>
                  </td>
                  <td>{{ stats.files.toLocaleString() }}</td>
                  <td>{{ formatBytes(stats.size_bytes) }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-card-text>
      </v-card>

      <!-- 自动清理状态 -->
      <v-card class="mb-4" v-if="overview && overview.auto_cleanup">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-auto-fix</v-icon>
          <span>自动清理状态</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            自动清理由外部定时器触发（cron/systemd），此处仅展示最近执行结果。
          </v-alert>
          
          <v-row>
            <v-col cols="12" md="6">
              <div class="text-body-2 mb-1">启用状态</div>
              <v-chip
                :color="overview.auto_cleanup.enabled ? 'success' : 'default'"
                size="small"
                variant="flat"
              >
                {{ overview.auto_cleanup.enabled ? '已启用' : '未启用' }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="6" v-if="overview.auto_cleanup.last_run_at">
              <div class="text-body-2 mb-1">最近运行时间</div>
              <div class="text-body-1">
                {{ formatDateTime(overview.auto_cleanup.last_run_at) }}
                <span class="text-medium-emphasis ml-2">
                  ({{ formatRelativeTime(overview.auto_cleanup.last_run_at) }})
                </span>
              </div>
            </v-col>
          </v-row>

          <v-row v-if="overview.auto_cleanup.last_run_status" class="mt-2">
            <v-col cols="12" md="4">
              <div class="text-body-2 mb-1">最近状态</div>
              <v-chip
                :color="getAutoCleanupStatusColor(overview.auto_cleanup.last_run_status)"
                size="small"
                variant="flat"
              >
                {{ getAutoCleanupStatusLabel(overview.auto_cleanup.last_run_status) }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="4" v-if="overview.auto_cleanup.last_run_freed_bytes && overview.auto_cleanup.last_run_freed_bytes > 0">
              <div class="text-body-2 mb-1">释放空间</div>
              <div class="text-body-1">{{ formatBytes(overview.auto_cleanup.last_run_freed_bytes || 0) }}</div>
            </v-col>
            <v-col cols="12" md="4" v-if="overview.auto_cleanup.last_run_reason">
              <div class="text-body-2 mb-1">原因</div>
              <div class="text-body-2 text-medium-emphasis">{{ overview.auto_cleanup.last_run_reason }}</div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 存储策略概要 -->
      <v-card class="mb-4" v-if="storagePolicy">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-cog</v-icon>
          <span>当前存储策略：{{ storagePolicy.name }}</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            本策略只在"按策略清理"模式下生效。手动参数模式不受此策略影响。
          </v-alert>
          <v-row>
            <v-col cols="12" md="4">
              <v-card variant="outlined" class="pa-3">
                <div class="text-caption text-medium-emphasis mb-1">Playground</div>
                <div class="text-body-2">保留 ≥ {{ storagePolicy.playground.min_keep_days }} 天</div>
                <div class="text-body-2">至少 {{ storagePolicy.playground.min_keep_files }} 个</div>
                <div class="text-body-2">至多 {{ storagePolicy.playground.max_keep_files ?? '∞' }} 个</div>
              </v-card>
            </v-col>
            <v-col cols="12" md="4">
              <v-card variant="outlined" class="pa-3">
                <div class="text-caption text-medium-emphasis mb-1">Job</div>
                <div class="text-body-2">保留 ≥ {{ storagePolicy.job.min_keep_days }} 天</div>
                <div class="text-body-2">至少 {{ storagePolicy.job.min_keep_files }} 个</div>
                <div class="text-body-2">至多 {{ storagePolicy.job.max_keep_files ?? '∞' }} 个</div>
              </v-card>
            </v-col>
            <v-col cols="12" md="4">
              <v-card variant="outlined" class="pa-3">
                <div class="text-caption text-medium-emphasis mb-1">Other</div>
                <div class="text-body-2">保留 ≥ {{ storagePolicy.other.min_keep_days }} 天</div>
                <div class="text-body-2">至少 {{ storagePolicy.other.min_keep_files }} 个</div>
                <div class="text-body-2">至多 {{ storagePolicy.other.max_keep_files ?? '∞' }} 个</div>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 清理策略配置 + 预览 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="warning">mdi-broom</v-icon>
          <span>清理策略</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-form ref="cleanupForm" v-model="cleanupFormValid">
            <!-- 模式切换 -->
            <v-row>
              <v-col cols="12">
                <div class="text-body-2 mb-2">清理模式</div>
                <v-radio-group v-model="cleanupMode" inline>
                  <v-radio label="手动参数模式" value="manual" />
                  <v-radio label="按策略推荐模式" value="policy" />
                </v-radio-group>
              </v-col>
            </v-row>

            <v-divider class="my-4" />

            <!-- 手动参数配置（仅在手动模式下显示） -->
            <div v-if="cleanupMode === 'manual'">
              <v-row>
                <v-col cols="12" md="4">
                  <v-select
                    v-model="cleanupRequest.scope"
                    :items="scopeOptions"
                    label="清理范围"
                    variant="outlined"
                    density="compact"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model.number="cleanupRequest.min_age_days"
                    label="最小保留天数"
                    type="number"
                    variant="outlined"
                    density="compact"
                    :min="0"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model.number="cleanupRequest.max_files"
                    label="最大匹配文件数"
                    type="number"
                    variant="outlined"
                    density="compact"
                    :min="0"
                  />
                </v-col>
              </v-row>
            </div>

            <!-- 策略模式提示 -->
            <v-alert
              v-if="cleanupMode === 'policy'"
              type="info"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              将使用当前存储策略自动计算清理集合，忽略手动参数。
            </v-alert>

            <v-row>
              <v-col cols="12">
                <v-btn
                  color="primary"
                  :loading="loadingPreview"
                  @click="handlePreview"
                >
                  <v-icon start>mdi-eye</v-icon>
                  {{ cleanupMode === 'policy' ? '按策略预览清理' : '预览清理' }}
                </v-btn>
              </v-col>
            </v-row>
          </v-form>

          <!-- 预览结果 -->
          <v-card v-if="previewResult" class="mt-4" variant="outlined">
            <v-card-title class="text-body-1">
              预览结果
            </v-card-title>
            <v-divider />
            <v-card-text>
              <!-- 策略模式提示 -->
              <v-alert
                v-if="previewResult.used_policy && previewResult.policy_name"
                type="success"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                <strong>按策略推荐</strong>：当前预览基于存储策略 <code>{{ previewResult.policy_name }}</code> 的推荐清理结果。
              </v-alert>
              <div class="mb-4">
                <div class="text-body-2 mb-1">匹配文件数</div>
                <div class="text-h6">{{ previewResult.total_matched_files.toLocaleString() }}</div>
              </div>
              <div class="mb-4">
                <div class="text-body-2 mb-1">预计释放空间</div>
                <div class="text-h6 text-warning">{{ formatBytes(previewResult.total_freed_bytes) }}</div>
              </div>

              <!-- 示例列表 -->
              <v-divider class="my-4" />
              <div class="text-body-2 mb-2">示例文件（前 {{ previewResult.sample.length }} 条）</div>
              <v-data-table
                :headers="previewHeaders"
                :items="previewResult.sample"
                :items-per-page="10"
                density="compact"
                no-data-text="无匹配文件"
              >
                <template v-slot:item.size_bytes="{ item }">
                  {{ formatBytes(item.size_bytes) }}
                </template>
                <template v-slot:item.mtime="{ item }">
                  {{ formatDateTime(item.mtime) }}
                </template>
                <template v-slot:item.category="{ item }">
                  <v-chip size="x-small" :color="getCategoryColor(item.category)" variant="flat">
                    {{ getCategoryLabel(item.category) }}
                  </v-chip>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-card-text>
      </v-card>

      <!-- 执行清理 -->
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="error">mdi-delete-alert</v-icon>
          <span>执行清理</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert
            type="error"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            <strong>警告</strong>：此操作不可恢复。只影响 TTS 缓存目录，不会删除已导入的有声书。
          </v-alert>

          <v-checkbox
            v-model="cleanupRequest.dry_run"
            label="预览模式（不实际删除）"
            density="compact"
            class="mb-4"
          />

          <v-btn
            color="error"
            :loading="loadingCleanup"
            :disabled="!previewResult || previewResult.total_matched_files === 0"
            @click="handleCleanup"
          >
            <v-icon start>mdi-delete</v-icon>
            {{ cleanupRequest.dry_run ? '预览执行' : '执行清理' }}
          </v-btn>

          <!-- 清理结果 -->
          <v-card v-if="cleanupResult" class="mt-4" variant="outlined" color="success">
            <v-card-text>
              <div class="text-body-1 font-weight-medium mb-2">清理完成</div>
              <div class="text-body-2">{{ cleanupResult.message }}</div>
              <div class="text-body-2 mt-2">
                删除文件：{{ cleanupResult.deleted_files.toLocaleString() }} 个
              </div>
              <div class="text-body-2">
                释放空间：{{ formatBytes(cleanupResult.freed_bytes) }}
              </div>
            </v-card-text>
          </v-card>
        </v-card-text>
      </v-card>

      <!-- TTS Runner 使用说明 -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-console</v-icon>
          <span>TTS Runner 使用说明</span>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            TTS 生成和清理由后台 Runner 执行，建议通过 systemd 或 cron 定时调用。
          </v-alert>
          
          <div class="text-body-2 mb-3">
            <strong>TTS 生成 Worker</strong>（处理队列中的 TTS 任务）：
          </div>
          <v-code class="mb-4 pa-2 d-block" style="background: #f5f5f5; border-radius: 4px;">
            python -m app.runners.tts_worker
          </v-code>
          
          <div class="text-body-2 mb-3">
            <strong>TTS 存储清理</strong>（按策略清理过期文件）：
          </div>
          <v-code class="mb-4 pa-2 d-block" style="background: #f5f5f5; border-radius: 4px;">
            python -m app.runners.tts_cleanup
          </v-code>
          
          <v-divider class="my-4" />
          
          <div class="text-body-2 text-medium-emphasis">
            <strong>建议配置：</strong>
            <ul class="mt-2">
              <li><code>tts_worker</code>：每 5-10 分钟运行一次，或作为常驻服务</li>
              <li><code>tts_cleanup</code>：每天运行一次（如凌晨 3:00）</li>
            </ul>
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { devTTSStorageApi } from '@/services/api'
import type {
  TTSStorageOverviewResponse,
  TTSStorageCleanupPreviewRequest,
  TTSStorageCleanupPreviewResponse,
  TTSStorageCleanupExecuteRequest,
  TTSStorageCleanupExecuteResponse,
  TTSStoragePolicy
} from '@/types/tts'
import { formatDateTime, formatRelativeTime } from '@/utils/formatters'
import PageHeader from '@/components/common/PageHeader.vue'

const toast = useToast()

// 状态
const loadingOverview = ref(false)
const overview = ref<TTSStorageOverviewResponse | null>(null)
const loadingPolicy = ref(false)
const storagePolicy = ref<TTSStoragePolicy | null>(null)
const cleanupMode = ref<'manual' | 'policy'>('manual')
const loadingPreview = ref(false)
const previewResult = ref<TTSStorageCleanupPreviewResponse | null>(null)
const loadingCleanup = ref(false)
const cleanupResult = ref<TTSStorageCleanupExecuteResponse | null>(null)
const cleanupFormValid = ref(false)

// 清理请求
const cleanupRequest = ref<TTSStorageCleanupExecuteRequest>({
  scope: 'all',
  min_age_days: 7,
  max_files: 10000,
  dry_run: false
})

// 选项
const scopeOptions = [
  { title: '全部', value: 'all' },
  { title: '仅 Playground', value: 'playground_only' },
  { title: '仅 Job', value: 'job_only' },
  { title: '仅其他', value: 'other_only' }
]

// 预览表格列
const previewHeaders = [
  { title: '路径', key: 'path', sortable: true },
  { title: '大小', key: 'size_bytes', sortable: true },
  { title: '修改时间', key: 'mtime', sortable: true },
  { title: '类别', key: 'category', sortable: true }
]

// 加载概览
const loadOverview = async () => {
  loadingOverview.value = true
  try {
    overview.value = await devTTSStorageApi.getOverview()
  } catch (err: any) {
    console.error('加载存储概览失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
  } finally {
    loadingOverview.value = false
  }
}

// 加载策略
const loadPolicy = async () => {
  loadingPolicy.value = true
  try {
    storagePolicy.value = await devTTSStorageApi.getPolicy()
  } catch (err: any) {
    console.error('加载存储策略失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载策略失败')
  } finally {
    loadingPolicy.value = false
  }
}

// 预览清理
const handlePreview = async () => {
  loadingPreview.value = true
  previewResult.value = null
  cleanupResult.value = null
  try {
    const previewReq: TTSStorageCleanupPreviewRequest = {
      scope: cleanupRequest.value.scope,
      min_age_days: cleanupRequest.value.min_age_days,
      max_files: cleanupRequest.value.max_files,
      mode: cleanupMode.value
    }
    previewResult.value = await devTTSStorageApi.previewCleanup(previewReq)
    const modeText = cleanupMode.value === 'policy' ? '（按策略）' : ''
    toast.success(`找到 ${previewResult.value.total_matched_files} 个匹配文件${modeText}`)
  } catch (err: any) {
    console.error('预览清理失败:', err)
    toast.error(err.response?.data?.detail || err.message || '预览失败')
  } finally {
    loadingPreview.value = false
  }
}

// 执行清理
const handleCleanup = async () => {
  if (!previewResult.value || previewResult.value.total_matched_files === 0) {
    toast.warning('请先预览清理计划')
    return
  }

  if (!cleanupRequest.value.dry_run) {
    // 确认对话框
    const confirmed = confirm(
      `确定要删除 ${previewResult.value.total_matched_files} 个文件吗？\n` +
      `将释放 ${formatBytes(previewResult.value.total_freed_bytes)} 空间。\n\n` +
      `此操作不可恢复！`
    )

    if (!confirmed) {
      return
    }
  }

  loadingCleanup.value = true
  cleanupResult.value = null
  try {
    const cleanupReq: TTSStorageCleanupExecuteRequest = {
      ...cleanupRequest.value,
      mode: cleanupMode.value
    }
    const result = await devTTSStorageApi.runCleanup(cleanupReq)
    cleanupResult.value = result

    if (result.dry_run) {
      toast.info(result.message)
    } else {
      toast.success(result.message)
      // 刷新概览
      await loadOverview()
      // 刷新预览
      await handlePreview()
    }
  } catch (err: any) {
    console.error('执行清理失败:', err)
    toast.error(err.response?.data?.detail || err.message || '清理失败')
  } finally {
    loadingCleanup.value = false
  }
}

// 辅助函数
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

const getCategoryColor = (category: string): string => {
  const colors: Record<string, string> = {
    job: 'primary',
    playground: 'success',
    other: 'default'
  }
  return colors[category] || 'default'
}

const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    job: 'Job',
    playground: 'Playground',
    other: '其他'
  }
  return labels[category] || category
}

const getAutoCleanupStatusColor = (status: string | null): string => {
  if (!status) return 'default'
  const colors: Record<string, string> = {
    success: 'success',
    skipped: 'warning',
    failed: 'error'
  }
  return colors[status] || 'default'
}

const getAutoCleanupStatusLabel = (status: string | null): string => {
  if (!status) return '未知'
  const labels: Record<string, string> = {
    success: '成功',
    skipped: '跳过',
    failed: '失败'
  }
  return labels[status] || status
}

onMounted(() => {
  loadOverview()
  loadPolicy()
})
</script>

<style scoped>
.dev-tts-storage-page {
  min-height: 100vh;
}
</style>

