<template>
  <div class="task-center-page">
    <!-- 顶部 PageHeader -->
    <PageHeader title="任务 & 下载中心" subtitle="统一查看 TTS 生成、音乐下载等任务状态">
      <template v-slot:actions>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-music"
          @click="$router.push({ name: 'MusicCenter' })"
          class="mr-2"
        >
          音乐中心
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-text-to-speech"
          @click="$router.push({ name: 'DevTTSJobs' })"
        >
          TTS 任务
        </v-btn>
      </template>
    </PageHeader>

    <v-container fluid>
      <!-- 过滤区域 -->
      <v-row class="mb-4">
        <v-col cols="12" sm="4" md="3">
          <v-select
            v-model="filterMediaType"
            :items="mediaTypeOptions"
            item-title="label"
            item-value="value"
            label="媒体类型"
            variant="outlined"
            density="compact"
            hide-details
            clearable
          />
        </v-col>
        <v-col cols="12" sm="4" md="3">
          <v-select
            v-model="filterKind"
            :items="kindOptions"
            item-title="label"
            item-value="value"
            label="任务类型"
            variant="outlined"
            density="compact"
            hide-details
            clearable
          />
        </v-col>
        <v-col cols="12" sm="4" md="3">
          <v-select
            v-model="filterStatus"
            :items="statusOptions"
            item-title="label"
            item-value="value"
            label="状态"
            variant="outlined"
            density="compact"
            hide-details
            clearable
          />
        </v-col>
        <v-col cols="12" sm="12" md="3" class="d-flex align-center">
          <v-btn
            variant="outlined"
            color="primary"
            @click="loadTasks"
            :loading="loading"
          >
            <v-icon left>mdi-refresh</v-icon>
            刷新
          </v-btn>
        </v-col>
      </v-row>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <!-- 错误状态 -->
      <v-alert v-else-if="error" type="error" variant="tonal" class="mb-4">
        {{ error }}
        <template v-slot:append>
          <v-btn variant="text" size="small" @click="loadTasks">重试</v-btn>
        </template>
      </v-alert>

      <!-- 任务列表 -->
      <v-card v-else>
        <v-data-table
          :headers="headers"
          :items="tasks"
          :items-per-page="pageSize"
          :loading="loading"
          class="elevation-0"
          @click:row="onRowClick"
        >
          <!-- 标题列 -->
          <template v-slot:item.title="{ item }">
            <div>
              <div class="font-weight-medium">{{ item.title }}</div>
              <div v-if="item.sub_title" class="text-caption text-medium-emphasis">
                {{ item.sub_title }}
              </div>
            </div>
          </template>

          <!-- 任务类型列 -->
          <template v-slot:item.kind="{ item }">
            <v-chip :color="getKindColor(item.kind)" size="small" variant="flat">
              {{ getKindLabel(item.kind) }}
            </v-chip>
          </template>

          <!-- 媒体类型列 -->
          <template v-slot:item.media_type="{ item }">
            <v-chip :color="getMediaColor(item.media_type)" size="x-small" variant="tonal">
              {{ getMediaLabel(item.media_type) }}
            </v-chip>
          </template>

          <!-- 状态列 -->
          <template v-slot:item.status="{ item }">
            <v-chip :color="getStatusColor(item.status)" size="small" variant="flat">
              <v-icon v-if="item.status === 'running'" start size="small" class="rotating">
                mdi-loading
              </v-icon>
              {{ getStatusLabel(item.status) }}
            </v-chip>
          </template>

          <!-- 进度列 -->
          <template v-slot:item.progress="{ item }">
            <div v-if="item.progress != null" class="d-flex align-center" style="min-width: 100px;">
              <v-progress-linear
                :model-value="item.progress"
                :color="item.status === 'success' ? 'success' : 'primary'"
                height="6"
                rounded
                class="mr-2"
              />
              <span class="text-caption">{{ item.progress }}%</span>
            </div>
            <span v-else class="text-caption text-medium-emphasis">-</span>
          </template>

          <!-- 时间列 -->
          <template v-slot:item.updated_at="{ item }">
            <span class="text-caption">{{ formatDate(item.updated_at) }}</span>
          </template>

          <!-- 错误列 -->
          <template v-slot:item.last_error="{ item }">
            <v-tooltip v-if="item.last_error" location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" color="error" size="small">mdi-alert-circle</v-icon>
              </template>
              <span>{{ item.last_error }}</span>
            </v-tooltip>
            <span v-else>-</span>
          </template>

          <!-- 空状态 -->
          <template v-slot:no-data>
            <div class="text-center py-8">
              <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-clipboard-list-outline</v-icon>
              <div class="text-h6 text-medium-emphasis mb-2">暂无任务</div>
              <div class="text-body-2 text-disabled">
                TTS 生成和音乐下载任务会显示在这里
              </div>
            </div>
          </template>
        </v-data-table>

        <!-- 分页 -->
        <v-divider />
        <div class="d-flex justify-space-between align-center pa-4">
          <span class="text-caption text-medium-emphasis">
            共 {{ total }} 条任务
          </span>
          <v-pagination
            v-model="page"
            :length="Math.ceil(total / pageSize)"
            :total-visible="5"
            density="compact"
            @update:model-value="loadTasks"
          />
        </div>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { taskCenterApi } from '@/services/api'
import type { TaskCenterItem } from '@/types/taskCenter'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const toast = useToast()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const tasks = ref<TaskCenterItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)

// 过滤
const filterMediaType = ref<string | null>(null)
const filterKind = ref<string | null>(null)
const filterStatus = ref<string | null>(null)

// 表头
const headers = [
  { title: '任务', key: 'title', sortable: false },
  { title: '类型', key: 'kind', sortable: false, width: '100px' },
  { title: '媒体', key: 'media_type', sortable: false, width: '80px' },
  { title: '状态', key: 'status', sortable: false, width: '100px' },
  { title: '进度', key: 'progress', sortable: false, width: '140px' },
  { title: '更新时间', key: 'updated_at', sortable: false, width: '120px' },
  { title: '错误', key: 'last_error', sortable: false, width: '60px' },
]

// 选项
const mediaTypeOptions = [
  { label: '全部', value: null },
  { label: '小说', value: 'novel' },
  { label: '有声书', value: 'audiobook' },
  { label: '漫画', value: 'manga' },
  { label: '音乐', value: 'music' },
  { label: '电影', value: 'movie' },
  { label: '剧集', value: 'series' },
  { label: '其他', value: 'other' },
]

const kindOptions = [
  { label: '全部', value: null },
  { label: '下载', value: 'download' },
  { label: 'TTS', value: 'tts' },
  { label: '导入', value: 'import' },
  { label: '订阅', value: 'subscription' },
  { label: '其他', value: 'other' },
]

const statusOptions = [
  { label: '全部', value: null },
  { label: '等待中', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '成功', value: 'success' },
  { label: '失败', value: 'failed' },
  { label: '跳过', value: 'skipped' },
]

// 加载任务
const loadTasks = async () => {
  try {
    loading.value = true
    error.value = null
    const data = await taskCenterApi.list({
      media_type: filterMediaType.value || undefined,
      kind: filterKind.value || undefined,
      status: filterStatus.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    tasks.value = data.items
    total.value = data.total
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    console.error('加载任务列表失败:', err)
    error.value = e.response?.data?.detail || e.message || '加载失败'
    toast.error(error.value || '加载失败')
  } finally {
    loading.value = false
  }
}

// 点击行
const onRowClick = (_event: Event, { item }: { item: TaskCenterItem }) => {
  if (item.route_name && item.route_params) {
    router.push({ name: item.route_name, params: item.route_params })
  } else if (item.route_name) {
    router.push({ name: item.route_name })
  }
}

// 辅助函数
const getKindColor = (kind: string): string => {
  const colors: Record<string, string> = {
    download: 'blue',
    tts: 'purple',
    import: 'green',
    subscription: 'orange',
    other: 'grey',
  }
  return colors[kind] || 'grey'
}

const getKindLabel = (kind: string): string => {
  const labels: Record<string, string> = {
    download: '下载',
    tts: 'TTS',
    import: '导入',
    subscription: '订阅',
    other: '其他',
  }
  return labels[kind] || kind
}

const getMediaColor = (type: string): string => {
  const colors: Record<string, string> = {
    novel: 'blue',
    audiobook: 'purple',
    manga: 'orange',
    music: 'green',
    movie: 'red',
    series: 'teal',
    other: 'grey',
  }
  return colors[type] || 'grey'
}

const getMediaLabel = (type: string): string => {
  const labels: Record<string, string> = {
    novel: '小说',
    audiobook: '有声书',
    manga: '漫画',
    music: '音乐',
    movie: '电影',
    series: '剧集',
    other: '其他',
  }
  return labels[type] || type
}

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'grey',
    running: 'primary',
    success: 'success',
    failed: 'error',
    skipped: 'warning',
  }
  return colors[status] || 'grey'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    skipped: '跳过',
  }
  return labels[status] || status
}

const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const mins = Math.floor(diff / (1000 * 60))
      return mins <= 1 ? '刚刚' : `${mins}分钟前`
    }
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 监听过滤变化
watch([filterMediaType, filterKind, filterStatus], () => {
  page.value = 1
  loadTasks()
})

// 初始化
onMounted(() => {
  loadTasks()
})
</script>

<style scoped lang="scss">
.task-center-page {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-surface));
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

:deep(.v-data-table tbody tr) {
  cursor: pointer;
  
  &:hover {
    background-color: rgba(var(--v-theme-primary), 0.04);
  }
}
</style>
