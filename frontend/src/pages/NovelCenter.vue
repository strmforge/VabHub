<template>
  <div class="novel-center-page">
    <v-container>
      <!-- 页面头部 -->
      <PageHeader
        title="小说中心"
        subtitle="集中管理本地小说 / 电子书，并串联 TTS 有声书播放"
      >
        <template v-slot:actions>
          <v-btn
            v-if="isDevMode"
            color="secondary"
            variant="outlined"
            size="small"
            prepend-icon="mdi-file-document-edit"
            @click="$router.push({ name: 'NovelImportDemo' })"
            class="mr-2"
          >
            TXT 导入（Dev）
          </v-btn>
          <v-btn
            color="info"
            variant="outlined"
            size="small"
            prepend-icon="mdi-book-open-variant"
            @click="$router.push({ name: 'ReadingHubPage' })"
            class="mr-2"
          >
            阅读中心
          </v-btn>
          <v-btn
            color="primary"
            variant="outlined"
            size="small"
            prepend-icon="mdi-headphones"
            @click="$router.push({ name: 'TTSCenter' })"
          >
            TTS 有声书中心
          </v-btn>
        </template>
      </PageHeader>

      <!-- 加载状态 -->
      <v-progress-linear
        v-if="loading"
        indeterminate
        color="primary"
        class="mb-4"
      />

      <!-- 顶部统计卡片 -->
      <v-row v-if="stats" class="mb-4">
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis mb-1">小说数量</div>
              <div class="text-h5">{{ stats.total_books.toLocaleString() }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis mb-1">文件数</div>
              <div class="text-h5">{{ stats.total_files.toLocaleString() }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis mb-1">作者数</div>
              <div class="text-h5">{{ stats.total_authors.toLocaleString() }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis mb-1">系列数</div>
              <div class="text-h5">{{ stats.total_series.toLocaleString() }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis mb-1">总占用空间</div>
              <div class="text-h5">{{ formatSizeMB(stats.total_size_mb) }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis mb-1">当前页有 TTS</div>
              <div class="text-h5">{{ currentPageHasTTS }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis mb-1">当前页活跃任务</div>
              <div class="text-h5">{{ currentPageActiveJobs }}</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 筛选区域 -->
      <v-card class="mb-4">
        <v-card-title>筛选条件</v-card-title>
        <v-divider />
        <v-card-text>
          <v-row>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="filters.keyword"
                label="关键字（标题/作者）"
                variant="outlined"
                density="compact"
                clearable
                @keyup.enter="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="filters.author"
                label="作者"
                variant="outlined"
                density="compact"
                clearable
                @keyup.enter="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="filters.series"
                label="系列"
                variant="outlined"
                density="compact"
                clearable
                @keyup.enter="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="filters.reading_status"
                :items="readingStatusOptions"
                label="阅读状态"
                variant="outlined"
                density="compact"
                @update:model-value="applyFilters"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" md="3">
              <v-select
                v-model="filters.has_tts"
                :items="hasTTSOptions"
                label="TTS 有声书"
                variant="outlined"
                density="compact"
                @update:model-value="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="9" class="d-flex align-center">
              <v-btn
                color="secondary"
                variant="outlined"
                @click="resetFilters"
                class="mr-2"
              >
                重置
              </v-btn>
              <v-btn
                color="primary"
                variant="elevated"
                @click="applyFilters"
              >
                应用筛选
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 小说列表 -->
      <v-card>
        <v-card-title class="d-flex align-center justify-space-between">
          <div>
            小说列表
            <span v-if="total > 0" class="text-body-2 text-medium-emphasis ml-2">
              (共 {{ total.toLocaleString() }} 本)
            </span>
          </div>
          <v-select
            v-model="pageSize"
            :items="[10, 20, 50]"
            label="每页数量"
            variant="outlined"
            density="compact"
            style="max-width: 120px;"
            @update:model-value="handlePageSizeChange"
          />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="items"
            :loading="loading"
            :items-per-page="pageSize"
            hide-default-footer
            no-data-text="暂无小说"
          >
            <!-- 收藏列 -->
            <template v-slot:item.favorite="{ item }">
              <v-btn
                size="small"
                variant="text"
                :color="item.is_favorite ? 'yellow' : 'default'"
                :icon="item.is_favorite ? 'mdi-heart' : 'mdi-heart-outline'"
                :loading="favoriteLoading[item.ebook.id]"
                @click="handleToggleFavorite(item)"
              >
                <v-tooltip activator="parent">
                  {{ item.is_favorite ? '取消收藏' : '添加到收藏' }}
                </v-tooltip>
              </v-btn>
            </template>

            <!-- 标题列 -->
            <template v-slot:item.title="{ item }">
              <div class="d-flex align-center">
                <!-- TTS 有声书图标 -->
                <v-icon
                  v-if="item.has_tts_audiobook"
                  size="small"
                  color="success"
                  class="mr-2"
                >
                  mdi-headphones
                  <v-tooltip activator="parent">已有 TTS 有声书</v-tooltip>
                </v-icon>
                <div>
                  <router-link
                    :to="{ name: 'WorkDetail', params: { ebookId: item.ebook.id } }"
                    class="text-decoration-none text-primary"
                  >
                    {{ item.ebook.title }}
                  </router-link>
                  <div v-if="item.ebook.original_title" class="text-caption text-medium-emphasis">
                    {{ item.ebook.original_title }}
                  </div>
                </div>
              </div>
            </template>

            <!-- 作者列 -->
            <template v-slot:item.author="{ item }">
              {{ item.ebook.author || '-' }}
            </template>

            <!-- 系列列 -->
            <template v-slot:item.series="{ item }">
              {{ item.ebook.series || '-' }}
            </template>

            <!-- 语言列 -->
            <template v-slot:item.language="{ item }">
              <v-chip
                v-if="item.ebook.language"
                size="small"
                variant="outlined"
              >
                {{ item.ebook.language }}
              </v-chip>
              <span v-else>-</span>
            </template>

            <!-- TTS / 有声书状态列 -->
            <template v-slot:item.tts_status="{ item }">
              <div>
                <div class="mb-1">
                  <v-chip
                    :color="item.has_tts_audiobook ? 'success' : 'default'"
                    size="small"
                    variant="flat"
                  >
                    {{ item.has_tts_audiobook ? '有 TTS 有声书' : '暂无 TTS' }}
                  </v-chip>
                </div>
                <div v-if="item.last_tts_job_status">
                  <v-chip
                    :color="getJobStatusColor(item.last_tts_job_status)"
                    size="x-small"
                    variant="flat"
                  >
                    {{ getJobStatusLabel(item.last_tts_job_status) }}
                  </v-chip>
                </div>
                <div v-else class="text-caption text-medium-emphasis">
                  暂无任务记录
                </div>
              </div>
            </template>

            <!-- 阅读进度列 -->
            <template v-slot:item.readingProgress="{ item }">
              <div class="d-flex align-center">
                <div class="flex-grow-1">
                  <div v-if="!item.reading.has_progress">
                    <v-chip size="small" variant="outlined" color="grey">
                      未开始阅读
                    </v-chip>
                  </div>
                  <div v-else-if="item.reading.is_finished">
                    <v-chip size="small" variant="flat" color="success">
                      已读完
                    </v-chip>
                  </div>
                  <div v-else>
                    <v-chip size="small" variant="flat" color="info" class="mb-1">
                      阅读中 {{ item.reading.progress_percent.toFixed(1) }}%
                    </v-chip>
                    <div v-if="item.reading.current_chapter_title" class="text-caption text-medium-emphasis">
                      当前章节：{{ item.reading.current_chapter_title }}
                    </div>
                    <div v-else-if="item.reading.current_chapter_index != null" class="text-caption text-medium-emphasis">
                      第 {{ (item.reading.current_chapter_index ?? 0) + 1 }} 章
                    </div>
                  </div>
                </div>
                <v-btn
                  size="small"
                  variant="text"
                  color="primary"
                  icon="mdi-book-open-page-variant"
                  @click="$router.push({ name: 'NovelReader', params: { ebookId: item.ebook.id } })"
                  class="ml-2"
                >
                  <v-icon size="small">mdi-book-open-page-variant</v-icon>
                  <v-tooltip activator="parent">阅读</v-tooltip>
                </v-btn>
              </div>
            </template>

            <!-- 听书进度列 -->
            <template v-slot:item.listening="{ item }">
              <div v-if="!item.listening.has_progress">
                <v-chip size="small" variant="outlined" color="default">
                  未开始
                </v-chip>
              </div>
              <div v-else-if="item.listening.is_finished">
                <v-chip size="small" variant="flat" color="success">
                  已听完
                </v-chip>
              </div>
              <div v-else>
                <div class="text-body-2 mb-1">
                  已听 {{ item.listening.progress_percent.toFixed(1) }}%
                </div>
                <div class="text-caption text-medium-emphasis">
                  当前：{{ item.listening.current_chapter_title || '未知章节' }}
                </div>
              </div>
            </template>

            <!-- 最近更新列 -->
            <template v-slot:item.updated_at="{ item }">
              {{ formatRelativeTime(item.ebook.updated_at) }}
            </template>

            <!-- 操作列 -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                size="small"
                variant="text"
                color="primary"
                prepend-icon="mdi-book-open-page-variant"
                @click="$router.push({ name: 'NovelReader', params: { ebookId: item.ebook.id } })"
                class="mr-1"
              >
                阅读
              </v-btn>
              <!-- 继续收听按钮：仅当有 TTS 有声书且有听书进度时显示 -->
              <v-btn
                v-if="item.has_tts_audiobook && item.listening.has_progress && !item.listening.is_finished"
                size="small"
                variant="text"
                color="purple"
                prepend-icon="mdi-headphones"
                @click="$router.push({ name: 'WorkDetail', params: { ebookId: item.ebook.id }, query: { autoplay: '1' } })"
                class="mr-1"
              >
                继续收听
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                color="default"
                @click="$router.push({ name: 'WorkDetail', params: { ebookId: item.ebook.id } })"
                class="mr-1"
              >
                详情
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                color="success"
                :loading="generatingTTS[item.ebook.id]"
                :disabled="generatingTTS[item.ebook.id]"
                @click="handleGenerateTTS(item.ebook.id)"
              >
                生成 TTS
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
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ebookApi, ttsUserApi, novelCenterApi, readingFavoriteApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { formatRelativeTime } from '@/utils/formatters'
import type { NovelCenterItem } from '@/types/novel'
// ReadingMediaType 用于 readingFavoriteApi 调用
import PageHeader from '@/components/common/PageHeader.vue'

const _router = useRouter() // 用于模板中的 $router
const toast = useToast()

// Dev 模式
const isDevMode = import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === 'true'

// 状态
const loading = ref(false)
const items = ref<NovelCenterItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const totalPages = ref(0)
const stats = ref<{
  total_books: number
  total_files: number
  total_authors: number
  total_series: number
  total_size_mb: number
} | null>(null)

// 筛选条件
const filters = ref({
  keyword: '',
  author: '',
  series: '',
  reading_status: '' as '' | 'not_started' | 'in_progress' | 'finished',
  has_tts: '' as '' | 'yes' | 'no'
})

// 阅读状态选项
const readingStatusOptions = [
  { title: '全部', value: '' },
  { title: '未开始', value: 'not_started' },
  { title: '进行中', value: 'in_progress' },
  { title: '已完成', value: 'finished' }
]

// TTS 状态选项
const hasTTSOptions = [
  { title: '全部', value: '' },
  { title: '仅有 TTS', value: 'yes' },
  { title: '无 TTS', value: 'no' }
]

// 生成 TTS 加载状态
const generatingTTS = ref<Record<number, boolean>>({})

// 收藏功能加载状态
const favoriteLoading = ref<Record<number, boolean>>({})

// 表格列
const headers = [
  { title: '收藏', key: 'favorite', sortable: false, width: '80px' },
  { title: '标题', key: 'title', sortable: true },
  { title: '作者', key: 'author', sortable: true },
  { title: '系列', key: 'series', sortable: true },
  { title: '语言', key: 'language', sortable: true },
  { title: 'TTS / 有声书状态', key: 'tts_status', sortable: false },
  { title: '阅读进度', key: 'readingProgress', sortable: false },
  { title: '听书进度', key: 'listening', sortable: false },
  { title: '最近更新', key: 'updated_at', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

// 计算属性：当前页 TTS 概览
const currentPageHasTTS = computed(() => {
  return items.value.filter(item => item.has_tts_audiobook === true).length
})

const currentPageActiveJobs = computed(() => {
  return items.value.filter(item => {
    const jobStatus = item.last_tts_job_status
    return jobStatus === 'queued' || jobStatus === 'running' || jobStatus === 'partial'
  }).length
})

// 加载统计信息
const loadStats = async () => {
  try {
    const response = await ebookApi.getStats()
    if (response.data?.success && response.data?.data) {
      stats.value = response.data.data
    }
  } catch (err: any) {
    console.warn('加载统计信息失败:', err)
    // 静默失败，不阻塞页面
  }
}

// 加载小说列表（使用聚合接口）
const loadEbooks = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value
    }
    
    if (filters.value.keyword) {
      params.keyword = filters.value.keyword
    }
    if (filters.value.author) {
      params.author = filters.value.author
    }
    if (filters.value.series) {
      params.series = filters.value.series
    }
    
    const response = await novelCenterApi.getList(params)
    
    let resultItems = response.items || []
    
    // 前端过滤：阅读状态
    if (filters.value.reading_status) {
      resultItems = resultItems.filter(item => {
        if (filters.value.reading_status === 'not_started') {
          return !item.reading.has_progress
        } else if (filters.value.reading_status === 'in_progress') {
          return item.reading.has_progress && !item.reading.is_finished
        } else if (filters.value.reading_status === 'finished') {
          return item.reading.is_finished
        }
        return true
      })
    }
    
    // 前端过滤：是否有 TTS
    if (filters.value.has_tts) {
      resultItems = resultItems.filter(item => {
        if (filters.value.has_tts === 'yes') {
          return item.has_tts_audiobook
        } else if (filters.value.has_tts === 'no') {
          return !item.has_tts_audiobook
        }
        return true
      })
    }
    
    items.value = resultItems
    total.value = response.total || 0
    page.value = response.page || 1
    pageSize.value = response.page_size || 20
    totalPages.value = response.total_pages || 0
  } catch (err: any) {
    console.error('加载小说列表失败:', err)
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
  loadEbooks()
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    keyword: '',
    author: '',
    series: '',
    reading_status: '',
    has_tts: ''
  }
  page.value = 1
  loadEbooks()
}

// 页码变化
const handlePageChange = (newPage: number) => {
  if (newPage !== page.value) {
    page.value = newPage
    loadEbooks()
  }
}

// 每页数量变化
const handlePageSizeChange = () => {
  page.value = 1
  loadEbooks()
}

// 生成 TTS
const handleGenerateTTS = async (ebookId: number) => {
  if (generatingTTS.value[ebookId]) return
  
  generatingTTS.value[ebookId] = true
  try {
    await ttsUserApi.enqueueForWork(ebookId)
    toast.success('TTS 任务已创建')
    
    // 重新加载当前页（获取最新状态）
    await loadEbooks()
  } catch (err: any) {
    console.error('创建 TTS 任务失败:', err)
    toast.error(err.response?.data?.detail || err.message || '创建失败')
  } finally {
    generatingTTS.value[ebookId] = false
  }
}

// 切换收藏状态
const handleToggleFavorite = async (item: NovelCenterItem) => {
  if (favoriteLoading.value[item.ebook.id]) return
  
  favoriteLoading.value[item.ebook.id] = true
  try {
    if (item.is_favorite) {
      // 取消收藏
      await readingFavoriteApi.removeFavorite({
        media_type: 'NOVEL',
        target_id: item.ebook.id
      })
      toast.success('已取消收藏')
    } else {
      // 添加收藏
      await readingFavoriteApi.addFavorite({
        media_type: 'NOVEL',
        target_id: item.ebook.id
      })
      toast.success('已添加到收藏')
    }
    
    // 重新加载当前页（获取最新状态）
    await loadEbooks()
  } catch (err: any) {
    console.error('操作收藏失败:', err)
    toast.error(err.response?.data?.detail || err.message || '操作失败')
  } finally {
    favoriteLoading.value[item.ebook.id] = false
  }
}

// 辅助函数
const formatSizeMB = (mb: number): string => {
  if (mb < 1024) {
    return `${mb.toFixed(2)} MB`
  } else {
    return `${(mb / 1024).toFixed(2)} GB`
  }
}

const getJobStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    queued: 'info',
    running: 'primary',
    success: 'success',
    partial: 'warning',
    failed: 'error'
  }
  return colors[status] || 'default'
}

const getJobStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    queued: '队列中',
    running: '生成中',
    success: '已完成',
    partial: '部分完成',
    failed: '失败'
  }
  return labels[status] || status
}

// 初始化
onMounted(() => {
  loadStats()
  loadEbooks()
})
</script>

<style scoped>
.novel-center-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>

