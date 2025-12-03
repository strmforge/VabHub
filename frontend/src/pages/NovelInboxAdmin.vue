<template>
  <div>
    <v-container>
      <!-- 页面头部 -->
      <PageHeader
        title="小说 Inbox 导入日志"
        subtitle="查看 TXT/EPUB 自动导入状态，排查失败原因"
      >
        <template #actions>
          <v-btn
            color="primary"
            variant="elevated"
            prepend-icon="mdi-refresh"
            @click="openScanDialog"
          >
            立即扫描小说 Inbox
          </v-btn>
        </template>
      </PageHeader>

      <!-- 筛选区域 -->
      <v-card class="mt-4">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4">
              <v-select
                v-model="filters.status"
                :items="statusOptions"
                label="状态筛选"
                density="compact"
                variant="outlined"
                clearable
                @update:model-value="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="filters.path_substring"
                label="路径关键字搜索"
                density="compact"
                variant="outlined"
                clearable
                @keyup.enter="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-btn
                color="default"
                variant="outlined"
                block
                @click="resetFilters"
              >
                重置
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 日志表格 -->
      <v-card class="mt-4">
        <v-card-title>
          导入日志
          <v-spacer />
          <span class="text-body-2 text-medium-emphasis">
            共 {{ total }} 条
          </span>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="items"
            :loading="loading"
            :items-per-page="pageSize"
            hide-default-footer
            no-data-text="暂无导入日志"
          >
            <!-- 文件路径列 -->
            <template v-slot:item.original_path="{ item }">
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <span v-bind="props" class="text-truncate d-inline-block" style="max-width: 300px">
                    {{ item.original_path }}
                  </span>
                </template>
                <span>{{ item.original_path }}</span>
              </v-tooltip>
            </template>

            <!-- 状态列 -->
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.status)"
                size="small"
                variant="flat"
              >
                {{ getStatusLabel(item.status) }}
              </v-chip>
            </template>

            <!-- 原因/错误信息列 -->
            <template v-slot:item.reason="{ item }">
              <div v-if="item.reason || item.error_message">
                <v-tooltip location="top">
                  <template #activator="{ props }">
                    <span v-bind="props" class="text-caption text-truncate d-inline-block" style="max-width: 200px">
                      {{ item.reason || item.error_message }}
                    </span>
                  </template>
                  <span>{{ item.reason || item.error_message }}</span>
                </v-tooltip>
              </div>
              <span v-else class="text-caption text-medium-emphasis">—</span>
            </template>

            <!-- 关联作品列 -->
            <template v-slot:item.ebook="{ item }">
              <div v-if="item.ebook_id">
                <router-link
                  :to="{ name: 'WorkDetail', params: { ebookId: item.ebook_id } }"
                  class="text-decoration-none text-primary"
                >
                  {{ item.ebook_title || `EBook #${item.ebook_id}` }}
                </router-link>
                <div v-if="item.ebook_author" class="text-caption text-medium-emphasis">
                  {{ item.ebook_author }}
                </div>
              </div>
              <span v-else>—</span>
            </template>

            <!-- 文件大小列 -->
            <template v-slot:item.file_size="{ item }">
              {{ formatBytes(item.file_size || 0) }}
            </template>

            <!-- 修改时间列 -->
            <template v-slot:item.file_mtime="{ item }">
              <span v-if="item.file_mtime">
                {{ formatRelativeTime(item.file_mtime) }}
              </span>
              <span v-else>—</span>
            </template>

            <!-- 导入时间列 -->
            <template v-slot:item.created_at="{ item }">
              {{ formatRelativeTime(item.created_at) }}
            </template>

            <!-- 操作列 -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                v-if="item.ebook_id"
                size="small"
                variant="text"
                color="primary"
                @click="$router.push({ name: 'WorkDetail', params: { ebookId: item.ebook_id } })"
                class="mr-2"
              >
                查看作品
              </v-btn>
              <v-btn
                v-if="item.status === 'failed'"
                size="small"
                variant="text"
                color="warning"
                @click="handleRetry(item)"
              >
                重试导入
              </v-btn>
            </template>
          </v-data-table>

          <!-- 分页 -->
          <div v-if="totalPages > 1" class="d-flex align-center justify-center mt-4">
            <v-pagination
              v-model="page"
              :length="totalPages"
              :total-visible="7"
              @update:model-value="handlePageChange"
            />
            <v-select
              v-model="pageSize"
              :items="[10, 20, 50, 100]"
              density="compact"
              variant="outlined"
              style="width: 100px; margin-left: 16px"
              @update:model-value="handlePageSizeChange"
            />
          </div>
        </v-card-text>
      </v-card>
    </v-container>

    <!-- 扫描对话框 -->
    <v-dialog v-model="scanDialog" max-width="500">
      <v-card>
        <v-card-title>扫描小说 Inbox</v-card-title>
        <v-card-text>
          <v-switch
            v-model="scanOptions.generate_tts"
            label="为新导入小说自动创建 TTS 任务"
            color="primary"
            class="mb-4"
          />
          <v-text-field
            v-model.number="scanOptions.max_files"
            label="最多扫描文件数（留空表示不限制）"
            type="number"
            density="compact"
            variant="outlined"
            hint="限制单次扫描的文件数量，防止扫描过大目录"
            persistent-hint
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="default"
            variant="text"
            @click="scanDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :loading="scanning"
            @click="handleScan"
          >
            开始扫描
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { novelInboxApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { formatRelativeTime } from '@/utils/formatters'
import type { NovelInboxLogItem } from '@/types/audiobook'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const toast = useToast()

// 状态
const loading = ref(false)
const items = ref<NovelInboxLogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const totalPages = ref(0)

// 筛选条件
const filters = ref({
  status: '',
  path_substring: ''
})

// 状态选项
const statusOptions = [
  { title: '全部', value: '' },
  { title: '待处理', value: 'pending' },
  { title: '成功', value: 'success' },
  { title: '跳过', value: 'skipped' },
  { title: '失败', value: 'failed' }
]

// 表格列
const headers = [
  { title: '文件路径', key: 'original_path', sortable: false },
  { title: '状态', key: 'status', sortable: true },
  { title: '原因 / 错误信息', key: 'reason', sortable: false },
  { title: '关联作品', key: 'ebook', sortable: false },
  { title: '文件大小', key: 'file_size', sortable: true },
  { title: '修改时间', key: 'file_mtime', sortable: true },
  { title: '导入时间', key: 'created_at', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

// 扫描对话框
const scanDialog = ref(false)
const scanning = ref(false)
const scanOptions = ref({
  max_files: undefined as number | undefined,
  generate_tts: false
})

// 加载日志列表
const loadLogs = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value
    }
    
    if (filters.value.status) {
      params.status = filters.value.status
    }
    if (filters.value.path_substring) {
      params.path_substring = filters.value.path_substring
    }
    
    const response = await novelInboxApi.getLogs(params)
    
    items.value = response.items || []
    total.value = response.total || 0
    page.value = response.page || 1
    pageSize.value = response.page_size || 20
    totalPages.value = response.total_pages || 0
  } catch (err: any) {
    console.error('加载导入日志失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
    items.value = []
    total.value = 0
    totalPages.value = 0
  } finally {
    loading.value = false
  }
}

// 应用筛选
const applyFilters = () => {
  page.value = 1
  loadLogs()
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    status: '',
    path_substring: ''
  }
  page.value = 1
  loadLogs()
}

// 打开扫描对话框
const openScanDialog = () => {
  scanOptions.value = {
    max_files: undefined,
    generate_tts: false
  }
  scanDialog.value = true
}

// 执行扫描
const handleScan = async () => {
  scanning.value = true
  try {
    const payload: any = {
      generate_tts: scanOptions.value.generate_tts
    }
    if (scanOptions.value.max_files) {
      payload.max_files = scanOptions.value.max_files
    }
    
    const result = await novelInboxApi.scan(payload)
    
    toast.success(
      `扫描完成：扫描 ${result.scanned_files} 个，导入 ${result.imported_count} 个，` +
      `跳过 ${result.skipped_already_imported + result.skipped_failed_before} 个，` +
      `创建 TTS Job ${result.tts_jobs_created} 个`
    )
    
    scanDialog.value = false
    await loadLogs()
  } catch (err: any) {
    console.error('扫描失败:', err)
    toast.error(err.response?.data?.detail || err.message || '扫描失败')
  } finally {
    scanning.value = false
  }
}

// 重试导入
const handleRetry = async (item: NovelInboxLogItem) => {
  toast.info('v1 版本暂不支持单文件重试，请使用"立即扫描"功能')
  // TODO: 后续可以实现单文件重试
}

// 状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'success':
      return 'success'
    case 'skipped':
      return 'default'
    case 'failed':
      return 'error'
    case 'pending':
      return 'info'
    default:
      return 'default'
  }
}

// 状态标签
const getStatusLabel = (status: string) => {
  switch (status) {
    case 'success':
      return '成功'
    case 'skipped':
      return '跳过'
    case 'failed':
      return '失败'
    case 'pending':
      return '待处理'
    default:
      return status
  }
}

// 格式化字节数
const formatBytes = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let v = bytes
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(1)} ${units[i]}`
}

// 分页处理
const handlePageChange = () => {
  loadLogs()
}

const handlePageSizeChange = () => {
  page.value = 1
  loadLogs()
}

// 初始化
onMounted(() => {
  loadLogs()
})
</script>

